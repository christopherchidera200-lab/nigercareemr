"""
NigerCare EMR – Unit Tests (lazy-init aware)
Run: cd backend && python3 -m pytest tests/ -v --tb=short
"""
import json
import os
import importlib.util
import types
import pytest
from unittest.mock import patch, MagicMock

# env vars are set by conftest.py before any import


def load_handler(name: str) -> types.ModuleType:
    path = os.path.join(os.path.dirname(__file__), f"../lambdas/{name}/handler.py")
    spec = importlib.util.spec_from_file_location(f"{name}_h", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def make_event(method="GET", path="/", body=None, claims=None, qsp=None):
    return {
        "httpMethod": method,
        "path": path,
        "pathParameters": {},
        "queryStringParameters": qsp,
        "body": json.dumps(body) if body else None,
        "requestContext": {
            "authorizer": {
                "claims": claims or {
                    "sub": "user-123",
                    "email": "admin@test.com",
                    "cognito:groups": "Admins",
                    "name": "Test Admin",
                }
            }
        },
    }

# ── Auth ──────────────────────────────────────────────────────────────────────


class TestAuth:
    @pytest.fixture(autouse=True)
    def setup(self): self.mod = load_handler("auth")

    def _patch(self):
        mc = MagicMock()
        mc.exceptions.NotAuthorizedException = type("E", (Exception,), {})
        mc.exceptions.UserNotConfirmedException = type("E", (Exception,), {})
        mc.exceptions.UserNotFoundException = type("E", (Exception,), {})
        mc.exceptions.UsernameExistsException = type("E", (Exception,), {})
        mc.exceptions.InvalidPasswordException = type("E", (Exception,), {})
        mc.exceptions.CodeMismatchException = type("E", (Exception,), {})
        mc.exceptions.ExpiredCodeException = type("E", (Exception,), {})
        return mc

    def test_options_200(self):
        resp = self.mod.lambda_handler(make_event("OPTIONS", "/auth/login"), {})
        assert resp["statusCode"] == 200

    def test_login_missing_fields(self):
        with patch.object(self.mod, "_get_cognito", return_value=self._patch()), \
                patch.object(self.mod, "_get_audit_table", return_value=MagicMock()):
            resp = self.mod.lambda_handler(make_event("POST", "/auth/login", {"email": ""}), {})
        assert resp["statusCode"] == 400

    def test_login_success(self):
        mc = self._patch()
        mc.initiate_auth.return_value = {"AuthenticationResult": {
            "AccessToken": "a", "IdToken": "i", "RefreshToken": "r", "ExpiresIn": 3600}}
        with patch.object(self.mod, "_get_cognito", return_value=mc), \
                patch.object(self.mod, "_get_audit_table", return_value=MagicMock()):
            resp = self.mod.lambda_handler(
                make_event("POST", "/auth/login", {"email": "doc@t.com", "password": "Pass1!"}), {})
        assert resp["statusCode"] == 200
        assert "accessToken" in json.loads(resp["body"])

    def test_unknown_route_404(self):
        resp = self.mod.lambda_handler(make_event("POST", "/auth/nope"), {})
        assert resp["statusCode"] == 404

    def test_register_missing_fields(self):
        with patch.object(self.mod, "_get_cognito", return_value=self._patch()), \
                patch.object(self.mod, "_get_audit_table", return_value=MagicMock()):
            resp = self.mod.lambda_handler(
                make_event("POST", "/auth/register", {"email": "x@x.com"}), {})
        assert resp["statusCode"] == 400

    def test_forgot_password_missing_email(self):
        with patch.object(self.mod, "_get_cognito", return_value=self._patch()), \
                patch.object(self.mod, "_get_audit_table", return_value=MagicMock()):
            resp = self.mod.lambda_handler(
                make_event("POST", "/auth/forgot-password", {}), {})
        assert resp["statusCode"] == 400

# ── Patients ──────────────────────────────────────────────────────────────────


class TestPatients:
    @pytest.fixture(autouse=True)
    def setup(self): self.mod = load_handler("patients")

    def test_options_200(self):
        with patch.object(self.mod, "_get_table", return_value=MagicMock()), \
                patch.object(self.mod, "_get_audit", return_value=MagicMock()):
            resp = self.mod.lambda_handler(make_event("OPTIONS", "/patients"), {})
        assert resp["statusCode"] == 200

    def test_patient_role_blocked_from_list(self):
        with patch.object(self.mod, "_get_table", return_value=MagicMock()), \
                patch.object(self.mod, "_get_audit", return_value=MagicMock()):
            resp = self.mod.lambda_handler(
                make_event("GET", "/patients", claims={
                    "sub": "p1", "email": "p@t.com", "cognito:groups": "Patients"}), {})
        assert resp["statusCode"] == 403

    def test_create_missing_fields(self):
        with patch.object(self.mod, "_get_table", return_value=MagicMock()), \
                patch.object(self.mod, "_get_audit", return_value=MagicMock()):
            resp = self.mod.lambda_handler(
                make_event("POST", "/patients", {"firstName": "John"},
                           claims={"sub": "a1", "email": "a@t.com", "cognito:groups": "Admins"}), {})
        assert resp["statusCode"] == 400

    def test_admin_list_patients(self):
        mt = MagicMock()
        mt.scan.return_value = {"Items": [], "Count": 0}
        with patch.object(self.mod, "_get_table", return_value=mt), \
                patch.object(self.mod, "_get_audit", return_value=MagicMock()):
            resp = self.mod.lambda_handler(
                make_event("GET", "/patients",
                           claims={"sub": "a1", "email": "a@t.com", "cognito:groups": "Admins"}), {})
        assert resp["statusCode"] == 200

# ── Appointments ──────────────────────────────────────────────────────────────


class TestAppointments:
    @pytest.fixture(autouse=True)
    def setup(self): self.mod = load_handler("appointments")

    def test_options_200(self):
        with patch.object(self.mod, "_get_table", return_value=MagicMock()), \
                patch.object(self.mod, "_get_audit", return_value=MagicMock()):
            resp = self.mod.lambda_handler(make_event("OPTIONS", "/appointments"), {})
        assert resp["statusCode"] == 200

    def test_create_missing_fields(self):
        with patch.object(self.mod, "_get_table", return_value=MagicMock()), \
                patch.object(self.mod, "_get_audit", return_value=MagicMock()):
            resp = self.mod.lambda_handler(
                make_event("POST", "/appointments", {"patient_id": "p1"}), {})
        assert resp["statusCode"] == 400

# ── Uploads ───────────────────────────────────────────────────────────────────


class TestUploads:
    @pytest.fixture(autouse=True)
    def setup(self): self.mod = load_handler("uploads")

    def test_options_200(self):
        with patch.object(self.mod, "_get_s3", return_value=MagicMock()), \
                patch.object(self.mod, "_get_audit", return_value=MagicMock()), \
                patch.object(self.mod, "_get_bucket", return_value="test-bucket"):
            resp = self.mod.lambda_handler(make_event("OPTIONS", "/uploads/presign"), {})
        assert resp["statusCode"] == 200

    def test_blocked_content_type(self):
        with patch.object(self.mod, "_get_s3", return_value=MagicMock()), \
                patch.object(self.mod, "_get_audit", return_value=MagicMock()), \
                patch.object(self.mod, "_get_bucket", return_value="test-bucket"):
            resp = self.mod.lambda_handler(
                make_event("POST", "/uploads/presign", {
                    "patient_id": "p1", "filename": "x.exe", "content_type": "application/exe"}), {})
        assert resp["statusCode"] == 400

    def test_file_too_large(self):
        with patch.object(self.mod, "_get_s3", return_value=MagicMock()), \
                patch.object(self.mod, "_get_audit", return_value=MagicMock()), \
                patch.object(self.mod, "_get_bucket", return_value="test-bucket"):
            resp = self.mod.lambda_handler(
                make_event("POST", "/uploads/presign", {
                    "patient_id": "p1", "filename": "scan.pdf",
                    "content_type": "application/pdf", "file_size": 20 * 1024 * 1024}), {})
        assert resp["statusCode"] == 400

# ── CORS ──────────────────────────────────────────────────────────────────────


class TestCORS:
    def test_all_have_cors(self):
        for name in ["auth", "patients", "appointments", "records", "uploads", "admin", "notifications"]:
            mod = load_handler(name)
            assert hasattr(mod, "CORS_HEADERS"), f"{name} missing CORS_HEADERS"
            assert "Access-Control-Allow-Origin" in mod.CORS_HEADERS

# ── Response format ───────────────────────────────────────────────────────────


class TestResponse:
    def test_structure(self):
        mod = load_handler("auth")
        resp = mod._resp(201, {"k": "v"})
        assert resp["statusCode"] == 201
        assert "headers" in resp
        assert json.loads(resp["body"]) == {"k": "v"}

    def test_cors_in_response(self):
        mod = load_handler("patients")
        resp = mod._resp(200, {})
        assert "Access-Control-Allow-Origin" in resp["headers"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
