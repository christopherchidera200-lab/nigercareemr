"""
NigerCare EMR – Medical Records Lambda Handler
Routes:
  GET  /records?patient_id=xxx  → patient's records
  POST /records                 → create record (doctor only)
  GET  /records/{id}            → single record
  PUT  /records/{id}            → update (doctor/admin)
"""
import json
import os
import uuid
import boto3
import logging
from datetime import datetime, timezone
from boto3.dynamodb.conditions import Key

logger = logging.getLogger()
logger.setLevel(logging.INFO)

_table = None
_audit_tbl = None

def _get_table():
    global _table
    if _table is None:
        db = boto3.resource("dynamodb", region_name=os.environ.get("REGION","us-east-1"))
        _table = db.Table(os.environ["MEDICAL_RECORDS_TABLE"])
    return _table

def _get_audit():
    global _audit_tbl
    if _audit_tbl is None:
        db = boto3.resource("dynamodb", region_name=os.environ.get("REGION","us-east-1"))
        _audit_tbl = db.Table(os.environ["AUDIT_LOGS_TABLE"])
    return _audit_tbl

CORS_HEADERS = {
    "Access-Control-Allow-Origin":  "*",
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
    "Access-Control-Allow-Methods": "OPTIONS,GET,POST,PUT",
    "Content-Type": "application/json",
}
VALID_TYPES = {"DIAGNOSIS", "LAB_RESULT", "PRESCRIPTION", "NOTE", "IMAGING", "PROCEDURE"}


def _resp(status, body):
    return {"statusCode": status, "headers": CORS_HEADERS, "body": json.dumps(body, default=str)}

def _claims(event):
    return event.get("requestContext", {}).get("authorizer", {}).get("claims", {})

def _groups(claims):
    g = claims.get("cognito:groups", "")
    return [g] if isinstance(g, str) else (g or [])

def _audit(uid, action, rid):
    try:
        _get_audit().put_item(Item={
            "log_id":    str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id":   uid, "action": action, "resource": rid,
            "expires_at": int(datetime.now(timezone.utc).timestamp()) + 7776000,
        })
    except Exception as e:
        logger.warning("Audit failed: %s", e)


def list_records(event, claims):
    params     = event.get("queryStringParameters") or {}
    patient_id = params.get("patient_id")
    groups     = _groups(claims)

    if not patient_id:
        return _resp(400, {"error": "patient_id query parameter required"})

    # Patients can only access their own records
    if "Patients" in groups and claims.get("sub") != patient_id:
        return _resp(403, {"error": "Access denied"})

    try:
        result = _get_table().query(
            KeyConditionExpression=Key("patient_id").eq(patient_id),
            ScanIndexForward=False,
            Limit=50,
        )
        _audit(claims.get("email", "unknown"), "LIST_RECORDS", patient_id)
        return _resp(200, {"records": result.get("Items", []), "count": result.get("Count", 0)})
    except Exception as e:
        logger.error("list_records error: %s", e)
        return _resp(500, {"error": "Failed to retrieve records"})


def create_record(event, claims, body):
    groups = _groups(claims)
    if "Doctors" not in groups and "Admins" not in groups:
        return _resp(403, {"error": "Only doctors can create medical records"})

    required = ["patient_id", "record_type", "title", "content"]
    missing  = [f for f in required if not body.get(f)]
    if missing:
        return _resp(400, {"error": f"Missing: {', '.join(missing)}"})

    if body["record_type"] not in VALID_TYPES:
        return _resp(400, {"error": f"Invalid record_type. Valid: {', '.join(VALID_TYPES)}"})

    now       = datetime.now(timezone.utc).isoformat()
    record_id = f"{now}#{str(uuid.uuid4())[:8]}"  # time-sorted SK
    caller    = claims.get("email", "unknown")

    item = {
        "patient_id":       body["patient_id"],
        "record_id":        record_id,
        "record_type":      body["record_type"],
        "doctor_id":        claims.get("sub", "unknown"),
        "doctor_name":      claims.get("name", "Unknown Doctor"),
        "title":            body["title"].strip(),
        "content":          body["content"],
        "attachments":      body.get("attachments", []),
        "appointment_id":   body.get("appointment_id", ""),
        "is_confidential":  body.get("is_confidential", False),
        "created_at":       now,
        "updated_at":       now,
        "created_by":       caller,
    }

    try:
        _get_table().put_item(Item=item)
        _audit(caller, "CREATE_RECORD", record_id)
        return _resp(201, {"record_id": record_id, "message": "Medical record created"})
    except Exception as e:
        logger.error("create_record error: %s", e)
        return _resp(500, {"error": "Failed to create record"})


def get_record(event, claims, record_id):
    params     = event.get("queryStringParameters") or {}
    patient_id = params.get("patient_id")
    if not patient_id:
        return _resp(400, {"error": "patient_id query parameter required"})

    groups = _groups(claims)
    if "Patients" in groups and claims.get("sub") != patient_id:
        return _resp(403, {"error": "Access denied"})

    try:
        result = _get_table().get_item(Key={"patient_id": patient_id, "record_id": record_id})
        item   = result.get("Item")
        if not item:
            return _resp(404, {"error": "Record not found"})
        if item.get("is_confidential") and "Patients" in groups:
            return _resp(403, {"error": "This record is restricted"})
        _audit(claims.get("email", "unknown"), "VIEW_RECORD", record_id)
        return _resp(200, item)
    except Exception as e:
        logger.error("get_record error: %s", e)
        return _resp(500, {"error": "Failed to retrieve record"})


def update_record(event, claims, record_id, body):
    groups = _groups(claims)
    if "Doctors" not in groups and "Admins" not in groups:
        return _resp(403, {"error": "Insufficient permissions"})

    patient_id = body.get("patient_id")
    if not patient_id:
        return _resp(400, {"error": "patient_id required in body"})

    updatable = ["title", "content", "attachments", "is_confidential"]
    updates   = {k: v for k, v in body.items() if k in updatable}
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()

    expr       = "SET " + ", ".join(f"#{k} = :{k}" for k in updates)
    attr_names = {f"#{k}": k for k in updates}
    attr_vals  = {f":{k}": v for k, v in updates.items()}

    try:
        _get_table().update_item(
            Key={"patient_id": patient_id, "record_id": record_id},
            UpdateExpression=expr,
            ExpressionAttributeNames=attr_names,
            ExpressionAttributeValues=attr_vals,
            ConditionExpression="attribute_exists(record_id)",
        )
        _audit(claims.get("email", "unknown"), "UPDATE_RECORD", record_id)
        return _resp(200, {"message": "Record updated"})
    except _get_table().meta.client.exceptions.ConditionalCheckFailedException:
        return _resp(404, {"error": "Record not found"})
    except Exception as e:
        logger.error("update_record error: %s", e)
        return _resp(500, {"error": "Failed to update record"})


def lambda_handler(event, context):
    if event.get("httpMethod") == "OPTIONS":
        return _resp(200, {})

    claims = _claims(event)
    method = event.get("httpMethod", "")
    path   = event.get("path", "")
    parts  = path.strip("/").split("/")
    rid    = parts[1] if len(parts) > 1 else None

    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return _resp(400, {"error": "Invalid JSON"})

    if method == "GET" and not rid:
        return list_records(event, claims)
    elif method == "POST" and not rid:
        return create_record(event, claims, body)
    elif method == "GET" and rid:
        return get_record(event, claims, rid)
    elif method == "PUT" and rid:
        return update_record(event, claims, rid, body)
    else:
        return _resp(405, {"error": "Method not allowed"})
