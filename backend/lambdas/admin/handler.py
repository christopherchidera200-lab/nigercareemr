"""
NigerCare EMR – Admin Lambda Handler
Routes:
  GET  /admin/stats           → dashboard stats
  GET  /admin/users           → list Cognito users
  POST /admin/users/{id}/role → assign user to Cognito group
  GET  /admin/audit           → fetch audit logs
  GET  /admin/doctors         → list doctors
  POST /admin/doctors         → create doctor profile
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

_cognito = None
_patients_tbl = None
_doctors_tbl = None
_appts_tbl = None
_audit_tbl = None


def _get_cognito():
    global _cognito
    if _cognito is None:
        _cognito = boto3.client("cognito-idp", region_name=os.environ.get("REGION", "us-east-1"))
    return _cognito


def _get_db(attr, table_env):
    tbl = globals().get(attr)
    if tbl is None:
        db = boto3.resource("dynamodb", region_name=os.environ.get("REGION", "us-east-1"))
        tbl = db.Table(os.environ[table_env])
        globals()[attr] = tbl
    return tbl


def _get_patients_tbl(): return _get_db("_patients_tbl", "PATIENTS_TABLE")
def _get_doctors_tbl(): return _get_db("_doctors_tbl", "DOCTORS_TABLE")
def _get_appts_tbl(): return _get_db("_appts_tbl", "APPOINTMENTS_TABLE")
def _get_audit(): return _get_db("_audit_tbl", "AUDIT_LOGS_TABLE")
def _get_pool_id(): return os.environ["COGNITO_USER_POOL_ID"]


CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
    "Access-Control-Allow-Methods": "OPTIONS,GET,POST,PUT,DELETE",
    "Content-Type": "application/json",
}


def _resp(status, body):
    return {"statusCode": status, "headers": CORS_HEADERS, "body": json.dumps(body, default=str)}


def _claims(event):
    return event.get("requestContext", {}).get("authorizer", {}).get("claims", {})


def _groups(claims):
    g = claims.get("cognito:groups", "")
    return [g] if isinstance(g, str) else (g or [])


def _require_admin(claims):
    return "Admins" in _groups(claims)


def get_stats(event, claims):
    if not _require_admin(claims):
        return _resp(403, {"error": "Admin only"})

    try:
        patient_count = _get_patients_tbl().scan(
            Select="COUNT",
            FilterExpression="#s = :active",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={":active": "ACTIVE"},
        )["Count"]

        doctor_count = _get_doctors_tbl().scan(Select="COUNT")["Count"]

        today = datetime.now(timezone.utc).date().isoformat()
        appt_today = _get_appts_tbl().scan(
            Select="COUNT",
            FilterExpression="begins_with(appointment_date, :today)",
            ExpressionAttributeValues={":today": today},
        )["Count"]

        pending_appts = _get_appts_tbl().scan(
            Select="COUNT",
            FilterExpression="#s = :pending",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={":pending": "PENDING"},
        )["Count"]

        return _resp(200, {
            "active_patients": patient_count,
            "total_doctors": doctor_count,
            "appointments_today": appt_today,
            "pending_approvals": pending_appts,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        })
    except Exception as e:
        logger.error("get_stats error: %s", e)
        return _resp(500, {"error": "Failed to retrieve stats"})


def list_users(event, claims):
    if not _require_admin(claims):
        return _resp(403, {"error": "Admin only"})

    try:
        resp = _get_cognito().list_users(UserPoolId=_get_pool_id(), Limit=60)
        users = []
        for u in resp.get("Users", []):
            attrs = {a["Name"]: a["Value"] for a in u.get("Attributes", [])}
            users.append(
                {
                    "username": u.get("Username"), "email": attrs.get(
                        "email", ""), "name": attrs.get(
                        "name", ""), "role": attrs.get(
                        "custom:role", ""), "status": u.get("UserStatus"), "created_at": u.get(
                        "UserCreateDate", "").isoformat() if hasattr(
                            u.get(
                                "UserCreateDate", ""), "isoformat") else str(
                                    u.get(
                                        "UserCreateDate", "")), })
        return _resp(200, {"users": users, "count": len(users)})
    except Exception as e:
        logger.error("list_users error: %s", e)
        return _resp(500, {"error": "Failed to list users"})


def assign_role(event, claims, user_id, body):
    if not _require_admin(claims):
        return _resp(403, {"error": "Admin only"})

    group = body.get("group", "")
    valid_groups = ["Admins", "Doctors", "Patients"]
    if group not in valid_groups:
        return _resp(400, {"error": f"Invalid group. Valid: {', '.join(valid_groups)}"})

    try:
        _get_cognito().admin_add_user_to_group(
            UserPoolId=_get_pool_id(),
            Username=user_id,
            GroupName=group,
        )
        _get_audit().put_item(Item={
            "log_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": claims.get("email", "unknown"),
            "action": f"ASSIGN_ROLE_{group.upper()}",
            "resource": user_id,
            "expires_at": int(datetime.now(timezone.utc).timestamp()) + 7776000,
        })
        return _resp(200, {"message": f"User assigned to {group}"})
    except _get_cognito().exceptions.UserNotFoundException:
        return _resp(404, {"error": "User not found"})
    except Exception as e:
        logger.error("assign_role error: %s", e)
        return _resp(500, {"error": "Failed to assign role"})


def get_audit_logs(event, claims):
    if not _require_admin(claims):
        return _resp(403, {"error": "Admin only"})

    params = event.get("queryStringParameters") or {}
    user_id = params.get("user_id")

    try:
        if user_id:
            result = _get_audit().query(
                IndexName="user-activity-index",
                KeyConditionExpression=Key("user_id").eq(user_id),
                ScanIndexForward=False,
                Limit=100,
            )
        else:
            result = _get_audit().scan(Limit=100)

        return _resp(200, {"logs": result.get("Items", []), "count": result.get("Count", 0)})
    except Exception as e:
        logger.error("get_audit_logs error: %s", e)
        return _resp(500, {"error": "Failed to retrieve audit logs"})


def list_doctors(event, claims):
    if not _require_admin(claims):
        return _resp(403, {"error": "Admin only"})

    try:
        result = _get_doctors_tbl().scan(Limit=100)
        return _resp(200, {"doctors": result.get("Items", []), "count": result.get("Count", 0)})
    except Exception as e:
        logger.error("list_doctors error: %s", e)
        return _resp(500, {"error": "Failed to retrieve doctors"})


def create_doctor(event, claims, body):
    if not _require_admin(claims):
        return _resp(403, {"error": "Admin only"})

    required = ["name", "specialty", "email", "phone", "license_number"]
    missing = [f for f in required if not body.get(f)]
    if missing:
        return _resp(400, {"error": f"Missing: {', '.join(missing)}"})

    doctor_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    item = {
        "doctor_id": doctor_id,
        "record_type": "PROFILE",
        "name": body["name"].strip(),
        "specialty": body["specialty"].strip(),
        "email": body["email"].strip().lower(),
        "phone": body["phone"].strip(),
        "license_number": body["license_number"].strip(),
        "qualifications": body.get("qualifications", []),
        "availability": body.get("availability", {}),
        "status": "ACTIVE",
        "created_by": claims.get("email", "unknown"),
        "created_at": now,
        "updated_at": now,
    }

    try:
        _get_doctors_tbl().put_item(Item=item)
        return _resp(201, {"doctor_id": doctor_id, "message": "Doctor profile created"})
    except Exception as e:
        logger.error("create_doctor error: %s", e)
        return _resp(500, {"error": "Failed to create doctor profile"})


def delete_user(event, claims, username):
    if not _require_admin(claims):
        return _resp(403, {"error": "Admin only"})
    if not username:
        return _resp(400, {"error": "username required"})
    try:
        _get_cognito().admin_delete_user(
            UserPoolId=_get_pool_id(),
            Username=username,
        )
        _get_audit().put_item(Item={
            "log_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": claims.get("email", "unknown"),
            "action": "DELETE_USER",
            "resource": username,
            "expires_at": int(datetime.now(timezone.utc).timestamp()) + 7776000,
        })
        return _resp(200, {"message": f"User {username} deleted"})
    except _get_cognito().exceptions.UserNotFoundException:
        return _resp(404, {"error": "User not found"})
    except Exception as e:
        logger.error("delete_user error: %s", e)
        return _resp(500, {"error": "Failed to delete user"})


def lambda_handler(event, context):
    if event.get("httpMethod") == "OPTIONS":
        return _resp(200, {})

    claims = _claims(event)
    method = event.get("httpMethod", "")
    path = event.get("path", "")
    parts = path.strip("/").split("/")
    # parts: ["admin", "stats"|"users"|"audit"|"doctors", optional_id, optional_sub]

    sub1 = parts[1] if len(parts) > 1 else ""
    sub2 = parts[2] if len(parts) > 2 else ""
    sub3 = parts[3] if len(parts) > 3 else ""

    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return _resp(400, {"error": "Invalid JSON"})

    if method == "GET" and sub1 == "stats":
        return get_stats(event, claims)
    elif method == "GET" and sub1 == "users":
        return list_users(event, claims)
    elif method == "POST" and sub1 == "users" and sub2 and sub3 == "role":
        return assign_role(event, claims, sub2, body)
    elif method == "GET" and sub1 == "audit":
        return get_audit_logs(event, claims)
    elif method == "GET" and sub1 == "doctors":
        return list_doctors(event, claims)
    elif method == "POST" and sub1 == "doctors":
        return create_doctor(event, claims, body)
    elif method == "DELETE" and sub1 == "users" and sub2:
        return delete_user(event, claims, sub2)
    else:
        return _resp(404, {"error": "Route not found"})
