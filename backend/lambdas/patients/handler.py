"""
NigerCare EMR – Patients Lambda Handler
Routes:
  GET    /patients          → list patients (admin/doctor only)
  POST   /patients          → create patient profile
  GET    /patients/{id}     → get patient by ID
  PUT    /patients/{id}     → update patient
  DELETE /patients/{id}     → deactivate patient (admin only)
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
        _table = db.Table(os.environ["PATIENTS_TABLE"])
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
    "Access-Control-Allow-Methods": "OPTIONS,GET,POST,PUT,DELETE",
    "Content-Type": "application/json",
}


def _resp(status: int, body) -> dict:
    return {"statusCode": status, "headers": CORS_HEADERS, "body": json.dumps(body, default=str)}


def _get_claims(event: dict) -> dict:
    ctx = event.get("requestContext", {})
    return ctx.get("authorizer", {}).get("claims", {})


def _log_audit(user_id: str, action: str, resource_id: str):
    try:
        _get_audit().put_item(Item={
            "log_id":    str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id":   user_id,
            "action":    action,
            "resource":  resource_id,
            "expires_at": int(datetime.now(timezone.utc).timestamp()) + 7776000,
        })
    except Exception as e:
        logger.warning("Audit failed: %s", e)


def _require_role(claims: dict, allowed_roles: list) -> bool:
    groups = claims.get("cognito:groups", "") or ""
    if isinstance(groups, str):
        groups = [groups]
    return any(g in allowed_roles for g in groups)


# ─── Handlers ────────────────────────────────────────────────────────────────

def list_patients(event, claims):
    if not _require_role(claims, ["Admins", "Doctors"]):
        return _resp(403, {"error": "Insufficient permissions"})

    try:
        result = _get_table().scan(
            FilterExpression="record_type = :rt",
            ExpressionAttributeValues={":rt": "PROFILE"},
            Limit=100,
        )
        return _resp(200, {"patients": result.get("Items", []), "count": result.get("Count", 0)})
    except Exception as e:
        logger.error("list_patients error: %s", e)
        return _resp(500, {"error": "Failed to retrieve patients"})


def create_patient(event, claims, body):
    required = ["firstName", "lastName", "dateOfBirth", "gender", "phone"]
    missing  = [f for f in required if not body.get(f)]
    if missing:
        return _resp(400, {"error": f"Missing required fields: {', '.join(missing)}"})

    patient_id = str(uuid.uuid4())
    now        = datetime.now(timezone.utc).isoformat()
    caller     = claims.get("email", "unknown")

    item = {
        "patient_id":   patient_id,
        "record_type":  "PROFILE",
        "firstName":    body["firstName"].strip(),
        "lastName":     body["lastName"].strip(),
        "dateOfBirth":  body["dateOfBirth"],
        "gender":       body["gender"],
        "phone":        body["phone"].strip(),
        "email":        body.get("email", "").strip().lower(),
        "address":      body.get("address", ""),
        "bloodGroup":   body.get("bloodGroup", ""),
        "allergies":    body.get("allergies", []),
        "status":       "ACTIVE",
        "created_by":   caller,
        "created_at":   now,
        "updated_at":   now,
    }

    try:
        _get_table().put_item(Item=item)
        _log_audit(caller, "CREATE_PATIENT", patient_id)
        return _resp(201, {"patient_id": patient_id, "message": "Patient created successfully"})
    except Exception as e:
        logger.error("create_patient error: %s", e)
        return _resp(500, {"error": "Failed to create patient"})


def get_patient(event, claims, patient_id):
    caller = claims.get("email", "unknown")
    groups = claims.get("cognito:groups", "")
    if isinstance(groups, str):
        groups = [groups]

    # Patients can only view their own record
    if "Patients" in groups and claims.get("sub") != patient_id:
        return _resp(403, {"error": "Access denied"})

    try:
        result = _get_table().get_item(Key={"patient_id": patient_id, "record_type": "PROFILE"})
        item   = result.get("Item")
        if not item:
            return _resp(404, {"error": "Patient not found"})
        _log_audit(caller, "VIEW_PATIENT", patient_id)
        return _resp(200, item)
    except Exception as e:
        logger.error("get_patient error: %s", e)
        return _resp(500, {"error": "Failed to retrieve patient"})


def update_patient(event, claims, patient_id, body):
    if not _require_role(claims, ["Admins", "Doctors"]):
        return _resp(403, {"error": "Insufficient permissions"})

    updatable = ["firstName", "lastName", "phone", "email", "address", "bloodGroup", "allergies", "status"]
    updates   = {k: v for k, v in body.items() if k in updatable}

    if not updates:
        return _resp(400, {"error": "No valid fields to update"})

    updates["updated_at"] = datetime.now(timezone.utc).isoformat()

    expr       = "SET " + ", ".join(f"#{k} = :{k}" for k in updates)
    attr_names = {f"#{k}": k for k in updates}
    attr_vals  = {f":{k}": v for k, v in updates.items()}

    try:
        _get_table().update_item(
            Key={"patient_id": patient_id, "record_type": "PROFILE"},
            UpdateExpression=expr,
            ExpressionAttributeNames=attr_names,
            ExpressionAttributeValues=attr_vals,
            ConditionExpression="attribute_exists(patient_id)",
        )
        _log_audit(claims.get("email", "unknown"), "UPDATE_PATIENT", patient_id)
        return _resp(200, {"message": "Patient updated successfully"})
    except _get_table().meta.client.exceptions.ConditionalCheckFailedException:
        return _resp(404, {"error": "Patient not found"})
    except Exception as e:
        logger.error("update_patient error: %s", e)
        return _resp(500, {"error": "Failed to update patient"})


def delete_patient(event, claims, patient_id):
    if not _require_role(claims, ["Admins"]):
        return _resp(403, {"error": "Only administrators can deactivate patients"})

    try:
        _get_table().update_item(
            Key={"patient_id": patient_id, "record_type": "PROFILE"},
            UpdateExpression="SET #status = :s, updated_at = :ua",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":s":  "DEACTIVATED",
                ":ua": datetime.now(timezone.utc).isoformat(),
            },
            ConditionExpression="attribute_exists(patient_id)",
        )
        _log_audit(claims.get("email", "unknown"), "DEACTIVATE_PATIENT", patient_id)
        return _resp(200, {"message": "Patient deactivated"})
    except _get_table().meta.client.exceptions.ConditionalCheckFailedException:
        return _resp(404, {"error": "Patient not found"})
    except Exception as e:
        logger.error("delete_patient error: %s", e)
        return _resp(500, {"error": "Failed to deactivate patient"})


# ─── Router ──────────────────────────────────────────────────────────────────

def lambda_handler(event, context):
    if event.get("httpMethod") == "OPTIONS":
        return _resp(200, {})

    claims = _get_claims(event)
    method = event.get("httpMethod", "")
    path   = event.get("path", "")
    parts  = path.strip("/").split("/")
    # parts[0] = "patients", parts[1] = optional patient_id

    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return _resp(400, {"error": "Invalid JSON body"})

    patient_id = parts[1] if len(parts) > 1 else None

    if method == "GET" and not patient_id:
        return list_patients(event, claims)
    elif method == "POST" and not patient_id:
        return create_patient(event, claims, body)
    elif method == "GET" and patient_id:
        return get_patient(event, claims, patient_id)
    elif method == "PUT" and patient_id:
        return update_patient(event, claims, patient_id, body)
    elif method == "DELETE" and patient_id:
        return delete_patient(event, claims, patient_id)
    else:
        return _resp(405, {"error": "Method not allowed"})
