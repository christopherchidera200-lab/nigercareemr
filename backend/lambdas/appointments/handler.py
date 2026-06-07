"""
NigerCare EMR – Appointments Lambda Handler
Routes:
  GET    /appointments               → list (filtered by role)
  POST   /appointments               → create appointment
  GET    /appointments/{id}          → get single appointment
  PUT    /appointments/{id}          → update / reschedule
  DELETE /appointments/{id}          → cancel
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
        db = boto3.resource("dynamodb", region_name=os.environ.get("REGION", "us-east-1"))
        _table = db.Table(os.environ["APPOINTMENTS_TABLE"])
    return _table


def _get_audit():
    global _audit_tbl
    if _audit_tbl is None:
        db = boto3.resource("dynamodb", region_name=os.environ.get("REGION", "us-east-1"))
        _audit_tbl = db.Table(os.environ["AUDIT_LOGS_TABLE"])
    return _audit_tbl


CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
    "Access-Control-Allow-Methods": "OPTIONS,GET,POST,PUT,DELETE",
    "Content-Type": "application/json",
}
VALID_STATUSES = {"PENDING", "CONFIRMED", "CANCELLED", "COMPLETED", "NO_SHOW"}


def _resp(status: int, body) -> dict:
    return {"statusCode": status, "headers": CORS_HEADERS, "body": json.dumps(body, default=str)}


def _claims(event):
    return event.get("requestContext", {}).get("authorizer", {}).get("claims", {})


def _groups(claims):
    g = claims.get("cognito:groups", "")
    return [g] if isinstance(g, str) else (g or [])


def _audit(user_id, action, resource_id):
    try:
        _get_audit().put_item(Item={
            "log_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": user_id,
            "action": action,
            "resource": resource_id,
            "expires_at": int(datetime.now(timezone.utc).timestamp()) + 7776000,
        })
    except Exception as e:
        logger.warning("Audit failed: %s", e)


def list_appointments(event, claims):
    groups = _groups(claims)
    user_sub = claims.get("sub", "")
    params = event.get("queryStringParameters") or {}

    try:
        if "Patients" in groups:
            result = _get_table().query(
                IndexName="patient-date-index",
                KeyConditionExpression=Key("patient_id").eq(user_sub),
                ScanIndexForward=False,
                Limit=50,
            )
        elif "Doctors" in groups:
            doctor_id = params.get("doctor_id", user_sub)
            result = _get_table().query(
                IndexName="doctor-date-index",
                KeyConditionExpression=Key("doctor_id").eq(doctor_id),
                ScanIndexForward=False,
                Limit=50,
            )
        else:
            # Admins – scan all (limited)
            result = _get_table().scan(Limit=100)

        return _resp(200, {"appointments": result.get("Items", []), "count": result.get("Count", 0)})
    except Exception as e:
        logger.error("list_appointments error: %s", e)
        return _resp(500, {"error": "Failed to retrieve appointments"})


def create_appointment(event, claims, body):
    required = ["patient_id", "doctor_id", "appointment_date", "reason"]
    missing = [f for f in required if not body.get(f)]
    if missing:
        return _resp(400, {"error": f"Missing: {', '.join(missing)}"})

    appt_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    caller = claims.get("email", "unknown")

    item = {
        "appointment_id": appt_id,
        "appointment_date": body["appointment_date"],
        "patient_id": body["patient_id"],
        "doctor_id": body["doctor_id"],
        "reason": body["reason"].strip(),
        "notes": body.get("notes", ""),
        "status": "PENDING",
        "type": body.get("type", "IN_PERSON"),
        "duration_minutes": body.get("duration_minutes", 30),
        "created_by": caller,
        "created_at": now,
        "updated_at": now,
    }

    try:
        _get_table().put_item(Item=item)
        _audit(caller, "CREATE_APPOINTMENT", appt_id)
        return _resp(201, {"appointment_id": appt_id, "message": "Appointment booked"})
    except Exception as e:
        logger.error("create_appointment error: %s", e)
        return _resp(500, {"error": "Failed to create appointment"})


def get_appointment(event, claims, appt_id):
    try:
        result = _get_table().query(
            KeyConditionExpression=Key("appointment_id").eq(appt_id),
            Limit=1,
        )
        items = result.get("Items", [])
        if not items:
            return _resp(404, {"error": "Appointment not found"})
        return _resp(200, items[0])
    except Exception as e:
        logger.error("get_appointment error: %s", e)
        return _resp(500, {"error": "Failed to retrieve appointment"})


def update_appointment(event, claims, appt_id, body):
    groups = _groups(claims)
    if "Patients" not in groups and "Doctors" not in groups and "Admins" not in groups:
        return _resp(403, {"error": "Insufficient permissions"})

    updatable = ["appointment_date", "reason", "notes", "status", "type", "duration_minutes"]
    updates = {k: v for k, v in body.items() if k in updatable}

    if "status" in updates and updates["status"] not in VALID_STATUSES:
        return _resp(400, {"error": f"Invalid status. Valid: {', '.join(VALID_STATUSES)}"})

    if not updates:
        return _resp(400, {"error": "No valid fields to update"})

    updates["updated_at"] = datetime.now(timezone.utc).isoformat()

    try:
        # Get existing record to obtain sort key
        result = _get_table().query(
            KeyConditionExpression=Key("appointment_id").eq(appt_id), Limit=1
        )
        items = result.get("Items", [])
        if not items:
            return _resp(404, {"error": "Appointment not found"})

        item = items[0]
        expr = "SET " + ", ".join(f"#{k} = :{k}" for k in updates)
        attr_names = {f"#{k}": k for k in updates}
        attr_vals = {f":{k}": v for k, v in updates.items()}

        _get_table().update_item(
            Key={"appointment_id": appt_id, "appointment_date": item["appointment_date"]},
            UpdateExpression=expr,
            ExpressionAttributeNames=attr_names,
            ExpressionAttributeValues=attr_vals,
        )
        _audit(claims.get("email", "unknown"), "UPDATE_APPOINTMENT", appt_id)
        return _resp(200, {"message": "Appointment updated"})
    except Exception as e:
        logger.error("update_appointment error: %s", e)
        return _resp(500, {"error": "Failed to update appointment"})


def cancel_appointment(event, claims, appt_id):
    try:
        result = _get_table().query(
            KeyConditionExpression=Key("appointment_id").eq(appt_id), Limit=1
        )
        items = result.get("Items", [])
        if not items:
            return _resp(404, {"error": "Appointment not found"})

        item = items[0]
        _get_table().update_item(
            Key={"appointment_id": appt_id, "appointment_date": item["appointment_date"]},
            UpdateExpression="SET #status = :s, updated_at = :ua",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":s": "CANCELLED",
                ":ua": datetime.now(timezone.utc).isoformat(),
            },
        )
        _audit(claims.get("email", "unknown"), "CANCEL_APPOINTMENT", appt_id)
        return _resp(200, {"message": "Appointment cancelled"})
    except Exception as e:
        logger.error("cancel_appointment error: %s", e)
        return _resp(500, {"error": "Failed to cancel appointment"})


def lambda_handler(event, context):
    if event.get("httpMethod") == "OPTIONS":
        return _resp(200, {})

    claims = _claims(event)
    method = event.get("httpMethod", "")
    path = event.get("path", "")
    parts = path.strip("/").split("/")
    appt_id = parts[1] if len(parts) > 1 else None

    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return _resp(400, {"error": "Invalid JSON body"})

    if method == "GET" and not appt_id:
        return list_appointments(event, claims)
    elif method == "POST" and not appt_id:
        return create_appointment(event, claims, body)
    elif method == "GET" and appt_id:
        return get_appointment(event, claims, appt_id)
    elif method == "PUT" and appt_id:
        return update_appointment(event, claims, appt_id, body)
    elif method == "DELETE" and appt_id:
        return cancel_appointment(event, claims, appt_id)
    else:
        return _resp(405, {"error": "Method not allowed"})
