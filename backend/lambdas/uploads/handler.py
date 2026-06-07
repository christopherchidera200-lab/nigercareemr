"""
NigerCare EMR – Uploads Lambda Handler
Routes:
  POST /uploads/presign   → generate presigned PUT URL for client-side upload
  GET  /uploads/presign   → generate presigned GET URL to view a file
  DELETE /uploads/{key}   → delete a document (admin only)
"""
import json
import os
import uuid
import boto3
import logging
from datetime import datetime, timezone
from urllib.parse import unquote_plus

logger = logging.getLogger()
logger.setLevel(logging.INFO)

_s3 = None
_audit_tbl = None


def _get_s3():
    global _s3
    if _s3 is None:
        _s3 = boto3.client("s3", region_name=os.environ.get("REGION", "us-east-1"))
    return _s3


def _get_audit():
    global _audit_tbl
    if _audit_tbl is None:
        db = boto3.resource("dynamodb", region_name=os.environ.get("REGION", "us-east-1"))
        _audit_tbl = db.Table(os.environ["AUDIT_LOGS_TABLE"])
    return _audit_tbl


def _get_bucket(): return os.environ["S3__get_bucket()"]


CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
    "Access-Control-Allow-Methods": "OPTIONS,GET,POST,DELETE",
    "Content-Type": "application/json",
}

ALLOWED_CONTENT_TYPES = {
    "image/jpeg", "image/png", "image/webp",
    "application/pdf",
    "image/dicom",
}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


def _resp(status, body):
    return {"statusCode": status, "headers": CORS_HEADERS, "body": json.dumps(body, default=str)}


def _claims(event):
    return event.get("requestContext", {}).get("authorizer", {}).get("claims", {})


def _groups(claims):
    g = claims.get("cognito:groups", "")
    return [g] if isinstance(g, str) else (g or [])


def _audit(uid, action, resource):
    try:
        _get_audit().put_item(Item={
            "log_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": uid, "action": action, "resource": resource,
            "expires_at": int(datetime.now(timezone.utc).timestamp()) + 7776000,
        })
    except Exception as e:
        logger.warning("Audit failed: %s", e)


def generate_upload_url(event, claims, body):
    """Generate a presigned PUT URL – file is uploaded directly from browser to S3."""
    patient_id = body.get("patient_id", "").strip()
    filename = body.get("filename", "").strip()
    content_type = body.get("content_type", "application/octet-stream").strip()
    file_size = body.get("file_size", 0)

    if not patient_id or not filename:
        return _resp(400, {"error": "patient_id and filename required"})

    if content_type not in ALLOWED_CONTENT_TYPES:
        return _resp(400, {"error": f"Content type not allowed. Allowed: {', '.join(ALLOWED_CONTENT_TYPES)}"})

    if file_size > MAX_FILE_SIZE_BYTES:
        return _resp(400, {"error": f"File too large. Max size: {MAX_FILE_SIZE_BYTES // 1024 // 1024}MB"})

    # Structured S3 key: uploads/{patient_id}/{uuid}/{filename}
    file_ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
    safe_name = f"{str(uuid.uuid4())}.{file_ext}"
    s3_key = f"uploads/{patient_id}/{safe_name}"

    try:
        presigned_url = _get_s3().generate_presigned_url(
            "put_object",
            Params={
                "Bucket": _get_bucket(),
                "Key": s3_key,
                "ContentType": content_type,
            },
            ExpiresIn=300,  # 5 minutes
        )
        _audit(claims.get("email", "unknown"), "GENERATE_UPLOAD_URL", s3_key)
        return _resp(200, {
            "upload_url": presigned_url,
            "s3_key": s3_key,
            "expires_in": 300,
        })
    except Exception as e:
        logger.error("generate_upload_url error: %s", e)
        return _resp(500, {"error": "Failed to generate upload URL"})


def generate_download_url(event, claims):
    """Generate a presigned GET URL for viewing a stored document."""
    params = event.get("queryStringParameters") or {}
    s3_key = params.get("key", "")
    groups = _groups(claims)

    if not s3_key:
        return _resp(400, {"error": "key query parameter required"})

    s3_key = unquote_plus(s3_key)

    # Patients can only access their own folder
    if "Patients" in groups:
        patient_id = claims.get("sub", "")
        if not s3_key.startswith(f"uploads/{patient_id}/"):
            return _resp(403, {"error": "Access denied"})

    try:
        # Verify object exists
        _get_s3().head_object(Bucket=_get_bucket(), Key=s3_key)

        presigned_url = _get_s3().generate_presigned_url(
            "get_object",
            Params={"Bucket": _get_bucket(), "Key": s3_key},
            ExpiresIn=900,  # 15 minutes
        )
        _audit(claims.get("email", "unknown"), "GENERATE_DOWNLOAD_URL", s3_key)
        return _resp(200, {"download_url": presigned_url, "expires_in": 900})
    except _get_s3().exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "404":
            return _resp(404, {"error": "File not found"})
        logger.error("head_object error: %s", e)
        return _resp(500, {"error": "Failed to generate download URL"})
    except Exception as e:
        logger.error("generate_download_url error: %s", e)
        return _resp(500, {"error": "Failed to generate download URL"})


def delete_document(event, claims, s3_key):
    groups = _groups(claims)
    if "Admins" not in groups and "Doctors" not in groups:
        return _resp(403, {"error": "Insufficient permissions"})

    s3_key = unquote_plus(s3_key)

    try:
        _get_s3().delete_object(Bucket=_get_bucket(), Key=s3_key)
        _audit(claims.get("email", "unknown"), "DELETE_DOCUMENT", s3_key)
        return _resp(200, {"message": "Document deleted"})
    except Exception as e:
        logger.error("delete_document error: %s", e)
        return _resp(500, {"error": "Failed to delete document"})


def lambda_handler(event, context):
    if event.get("httpMethod") == "OPTIONS":
        return _resp(200, {})

    claims = _claims(event)
    method = event.get("httpMethod", "")
    path = event.get("path", "")
    parts = path.strip("/").split("/")
    # parts: ["uploads", "presign"] or ["uploads", "key-value"]

    sub_path = parts[1] if len(parts) > 1 else ""

    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return _resp(400, {"error": "Invalid JSON"})

    if method == "POST" and sub_path == "presign":
        return generate_upload_url(event, claims, body)
    elif method == "GET" and sub_path == "presign":
        return generate_download_url(event, claims)
    elif method == "DELETE":
        # Remaining path is the S3 key
        s3_key = "/".join(parts[1:])
        return delete_document(event, claims, s3_key)
    else:
        return _resp(405, {"error": "Method not allowed"})
