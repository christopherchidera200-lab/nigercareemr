"""
NigerCare EMR – Auth Lambda Handler
Routes: POST /auth/login | POST /auth/register | POST /auth/refresh
        POST /auth/forgot-password | POST /auth/confirm-password
"""
import json
import os
import boto3
import logging
from datetime import datetime, timezone

logger = logging.getLogger()
logger.setLevel(logging.INFO)

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
    "Access-Control-Allow-Methods": "OPTIONS,POST,GET",
    "Content-Type": "application/json",
}

# ── Lazy clients (initialised on first invocation, not at import) ────────────
_cognito = None
_audit_tbl = None


def _get_cognito():
    global _cognito
    if _cognito is None:
        _cognito = boto3.client("cognito-idp",
                                region_name=os.environ.get("REGION", "us-east-1"))
    return _cognito


def _get_audit_table():
    global _audit_tbl
    if _audit_tbl is None:
        dynamodb = boto3.resource("dynamodb",
                                  region_name=os.environ.get("REGION", "us-east-1"))
        _audit_tbl = dynamodb.Table(os.environ["AUDIT_LOGS_TABLE"])
    return _audit_tbl


def _get_pool_id(): return os.environ["COGNITO_USER_POOL_ID"]
def _get_client_id(): return os.environ["COGNITO_CLIENT_ID"]


def _resp(status: int, body: dict) -> dict:
    return {"statusCode": status, "headers": CORS_HEADERS, "body": json.dumps(body)}


def _log_audit(action: str, user_id: str, details: dict = None):
    import uuid
    try:
        _get_audit_table().put_item(Item={
            "log_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": user_id,
            "action": action,
            "details": json.dumps(details or {}),
            "expires_at": int(datetime.now(timezone.utc).timestamp()) + 7776000,
        })
    except Exception as e:
        logger.warning("Audit log failed: %s", e)


def handle_login(body: dict) -> dict:
    email = body.get("email", "").strip().lower()
    password = body.get("password", "")
    if not email or not password:
        return _resp(400, {"error": "email and password required"})
    cognito = _get_cognito()
    try:
        resp = cognito.initiate_auth(
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={"USERNAME": email, "PASSWORD": password},
            ClientId=_get_client_id(),
        )
        auth = resp.get("AuthenticationResult", {})
        _log_audit("LOGIN_SUCCESS", email)
        return _resp(200, {
            "accessToken": auth.get("AccessToken"),
            "idToken": auth.get("IdToken"),
            "refreshToken": auth.get("RefreshToken"),
            "expiresIn": auth.get("ExpiresIn", 3600),
        })
    except cognito.exceptions.NotAuthorizedException:
        _log_audit("LOGIN_FAILED", email, {"reason": "invalid_credentials"})
        return _resp(401, {"error": "Invalid email or password"})
    except cognito.exceptions.UserNotConfirmedException:
        return _resp(403, {"error": "Account not confirmed. Check your email."})
    except cognito.exceptions.UserNotFoundException:
        _log_audit("LOGIN_FAILED", email, {"reason": "user_not_found"})
        return _resp(401, {"error": "Invalid email or password"})
    except Exception as e:
        logger.error("Login error: %s", e)
        return _resp(500, {"error": "Authentication service unavailable"})


def handle_register(body: dict) -> dict:
    email = body.get("email", "").strip().lower()
    password = body.get("password", "")
    name = body.get("name", "").strip()
    role = body.get("role", "patients").lower()
    if role not in ("patients", "doctors"):
        role = "patients"
    if not email or not password or not name:
        return _resp(400, {"error": "email, password, and name are required"})
    cognito = _get_cognito()
    try:
        cognito.sign_up(
            ClientId=_get_client_id(),
            Username=email,
            Password=password,
            UserAttributes=[
                {"Name": "email", "Value": email},
                {"Name": "name", "Value": name},
                {"Name": "custom:role", "Value": role},
            ],
        )
        _log_audit("REGISTER_SUCCESS", email, {"role": role})
        return _resp(201, {"message": "Registration successful. Please verify your email."})
    except cognito.exceptions.UsernameExistsException:
        return _resp(409, {"error": "An account with this email already exists"})
    except cognito.exceptions.InvalidPasswordException as e:
        return _resp(400, {"error": str(e)})
    except Exception as e:
        logger.error("Register error: %s", e)
        return _resp(500, {"error": "Registration service unavailable"})


def handle_refresh(body: dict) -> dict:
    refresh_token = body.get("refreshToken", "")
    if not refresh_token:
        return _resp(400, {"error": "refreshToken required"})
    cognito = _get_cognito()
    try:
        resp = cognito.initiate_auth(
            AuthFlow="REFRESH_TOKEN_AUTH",
            AuthParameters={"REFRESH_TOKEN": refresh_token},
            ClientId=_get_client_id(),
        )
        auth = resp.get("AuthenticationResult", {})
        return _resp(200, {
            "accessToken": auth.get("AccessToken"),
            "idToken": auth.get("IdToken"),
            "expiresIn": auth.get("ExpiresIn", 3600),
        })
    except cognito.exceptions.NotAuthorizedException:
        return _resp(401, {"error": "Refresh token expired or invalid"})
    except Exception as e:
        logger.error("Refresh error: %s", e)
        return _resp(500, {"error": "Token refresh failed"})


def handle_forgot_password(body: dict) -> dict:
    email = body.get("email", "").strip().lower()
    if not email:
        return _resp(400, {"error": "email required"})
    cognito = _get_cognito()
    try:
        cognito.forgot_password(ClientId=_get_client_id(), Username=email)
        _log_audit("FORGOT_PASSWORD", email)
        return _resp(200, {"message": "Password reset code sent to your email"})
    except cognito.exceptions.UserNotFoundException:
        return _resp(200, {"message": "If your email is registered, you will receive a reset code"})
    except Exception as e:
        logger.error("Forgot password error: %s", e)
        return _resp(500, {"error": "Password reset service unavailable"})


def handle_confirm_password(body: dict) -> dict:
    email = body.get("email", "").strip().lower()
    code = body.get("code", "")
    new_password = body.get("newPassword", "")
    if not email or not code or not new_password:
        return _resp(400, {"error": "email, code, and newPassword required"})
    cognito = _get_cognito()
    try:
        cognito.confirm_forgot_password(
            ClientId=_get_client_id(),
            Username=email,
            ConfirmationCode=code,
            Password=new_password,
        )
        _log_audit("PASSWORD_RESET_SUCCESS", email)
        return _resp(200, {"message": "Password reset successful"})
    except cognito.exceptions.CodeMismatchException:
        return _resp(400, {"error": "Invalid confirmation code"})
    except cognito.exceptions.ExpiredCodeException:
        return _resp(400, {"error": "Confirmation code has expired"})
    except Exception as e:
        logger.error("Confirm password error: %s", e)
        return _resp(500, {"error": "Password confirmation failed"})



def handle_confirm(body: dict) -> dict:
    email = body.get("email", "").strip().lower()
    code  = body.get("code", "").strip()
    if not email or not code:
        return _resp(400, {"error": "email and code required"})
    cognito = _get_cognito()
    try:
        cognito.confirm_sign_up(
            ClientId=_get_client_id(),
            Username=email,
            ConfirmationCode=code,
        )
        _log_audit("EMAIL_CONFIRMED", email)
        return _resp(200, {"message": "Email confirmed successfully. You can now log in."})
    except cognito.exceptions.CodeMismatchException:
        return _resp(400, {"error": "Invalid verification code"})
    except cognito.exceptions.ExpiredCodeException:
        return _resp(400, {"error": "Code has expired. Request a new one."})
    except cognito.exceptions.NotAuthorizedException:
        return _resp(400, {"error": "Account is already confirmed"})
    except Exception as e:
        logger.error("Confirm error: %s", e)
        return _resp(500, {"error": "Confirmation failed"})


def handle_resend_code(body: dict) -> dict:
    email = body.get("email", "").strip().lower()
    if not email:
        return _resp(400, {"error": "email required"})
    cognito = _get_cognito()
    try:
        cognito.resend_confirmation_code(
            ClientId=_get_client_id(),
            Username=email,
        )
        return _resp(200, {"message": "Verification code resent. Check your inbox and spam folder."})
    except cognito.exceptions.UserNotFoundException:
        return _resp(404, {"error": "No account found with this email"})
    except cognito.exceptions.InvalidParameterException:
        return _resp(400, {"error": "Account is already confirmed"})
    except Exception as e:
        logger.error("Resend code error: %s", e)
        return _resp(500, {"error": "Failed to resend code"})


ROUTE_MAP = {
    "POST /auth/login": handle_login,
    "POST /auth/register": handle_register,
    "POST /auth/refresh": handle_refresh,
    "POST /auth/forgot-password": handle_forgot_password,
    "POST /auth/confirm-password": handle_confirm_password,
}


def lambda_handler(event, context):
    if event.get("httpMethod") == "OPTIONS":
        return _resp(200, {})
    method = event.get("httpMethod", "")
    path = event.get("path", "").rstrip("/")
    key = f"{method} {path}"
    handler = ROUTE_MAP.get(key)
    if not handler:
        return _resp(404, {"error": f"Route {key} not found"})
    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return _resp(400, {"error": "Invalid JSON body"})
    return handler(body)
