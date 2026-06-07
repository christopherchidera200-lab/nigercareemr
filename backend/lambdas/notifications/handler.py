"""
NigerCare EMR – Notifications Lambda Handler
Routes:
  GET  /notifications          → list user's notifications
  POST /notifications          → send notification (internal/admin)
  PUT  /notifications/{id}/read → mark as read
"""
import json
import os
import uuid
import boto3
import logging
from datetime import datetime, timezone

logger = logging.getLogger()
logger.setLevel(logging.INFO)

_table = None
_sns = None


def _get_table():
    global _table
    if _table is None:
        db = boto3.resource("dynamodb", region_name=os.environ.get("REGION", "us-east-1"))
        _table = db.Table(os.environ["NOTIFICATIONS_TABLE"])
    return _table


def _get_sns():
    global _sns
    if _sns is None:
        _sns = boto3.client("sns", region_name=os.environ.get("REGION", "us-east-1"))
    return _sns


def _get_sns_topic(): return os.environ.get("_get_sns_topic()", "")


CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
    "Access-Control-Allow-Methods": "OPTIONS,GET,POST,PUT",
    "Content-Type": "application/json",
}


def _resp(status, body):
    return {"statusCode": status, "headers": CORS_HEADERS, "body": json.dumps(body, default=str)}


def _claims(event):
    return event.get("requestContext", {}).get("authorizer", {}).get("claims", {})


def _groups(claims):
    g = claims.get("cognito:groups", "")
    return [g] if isinstance(g, str) else (g or [])


def list_notifications(event, claims):
    from boto3.dynamodb.conditions import Key
    user_id = claims.get("sub", "")
    if not user_id:
        return _resp(401, {"error": "Unauthorized"})

    try:
        result = _get_table().query(
            IndexName="recipient-index",
            KeyConditionExpression=Key("recipient_id").eq(user_id),
            ScanIndexForward=False,
            Limit=50,
        )
        return _resp(200, {"notifications": result.get("Items", []), "count": result.get("Count", 0)})
    except Exception as e:
        logger.error("list_notifications error: %s", e)
        return _resp(500, {"error": "Failed to retrieve notifications"})


def send_notification(event, claims, body):
    groups = _groups(claims)
    if "Admins" not in groups and "Doctors" not in groups:
        return _resp(403, {"error": "Insufficient permissions"})

    required = ["recipient_id", "title", "message", "type"]
    missing = [f for f in required if not body.get(f)]
    if missing:
        return _resp(400, {"error": f"Missing: {', '.join(missing)}"})

    valid_types = {"APPOINTMENT", "REMINDER", "RESULT", "ALERT", "GENERAL"}
    if body["type"] not in valid_types:
        return _resp(400, {"error": f"Invalid type. Valid: {', '.join(valid_types)}"})

    notif_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    expires_at = int(datetime.now(timezone.utc).timestamp()) + 2592000  # 30 days

    item = {
        "notification_id": notif_id,
        "created_at": now,
        "recipient_id": body["recipient_id"],
        "title": body["title"].strip(),
        "message": body["message"].strip(),
        "type": body["type"],
        "is_read": False,
        "sent_by": claims.get("email", "system"),
        "expires_at": expires_at,
    }

    try:
        _get_table().put_item(Item=item)

        # Optionally publish to SNS for email/SMS delivery
        if _get_sns_topic() and body.get("send_sns", False):
            _get_sns().publish(
                TopicArn=_get_sns_topic(),
                Subject=body["title"],
                Message=body["message"],
            )

        return _resp(201, {"notification_id": notif_id, "message": "Notification sent"})
    except Exception as e:
        logger.error("send_notification error: %s", e)
        return _resp(500, {"error": "Failed to send notification"})


def mark_read(event, claims, notif_id):
    user_id = claims.get("sub", "")

    try:
        # Query to get the created_at sort key
        from boto3.dynamodb.conditions import Key
        result = _get_table().query(
            KeyConditionExpression=Key("notification_id").eq(notif_id),
            Limit=1,
        )
        items = result.get("Items", [])
        if not items:
            return _resp(404, {"error": "Notification not found"})

        item = items[0]
        if item.get("recipient_id") != user_id:
            return _resp(403, {"error": "Access denied"})

        _get_table().update_item(
            Key={"notification_id": notif_id, "created_at": item["created_at"]},
            UpdateExpression="SET is_read = :r, read_at = :ra",
            ExpressionAttributeValues={
                ":r": True,
                ":ra": datetime.now(timezone.utc).isoformat(),
            },
        )
        return _resp(200, {"message": "Notification marked as read"})
    except Exception as e:
        logger.error("mark_read error: %s", e)
        return _resp(500, {"error": "Failed to mark notification as read"})


def lambda_handler(event, context):
    if event.get("httpMethod") == "OPTIONS":
        return _resp(200, {})

    claims = _claims(event)
    method = event.get("httpMethod", "")
    path = event.get("path", "")
    parts = path.strip("/").split("/")

    sub1 = parts[1] if len(parts) > 1 else ""
    sub2 = parts[2] if len(parts) > 2 else ""

    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return _resp(400, {"error": "Invalid JSON"})

    if method == "GET" and not sub1:
        return list_notifications(event, claims)
    elif method == "POST" and not sub1:
        return send_notification(event, claims, body)
    elif method == "PUT" and sub1 and sub2 == "read":
        return mark_read(event, claims, sub1)
    else:
        return _resp(405, {"error": "Method not allowed"})
