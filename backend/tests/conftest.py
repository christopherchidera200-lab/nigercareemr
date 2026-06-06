"""Pytest configuration – sets up AWS env vars before any test imports."""
import os
import pytest

# Required by all Lambda handlers
os.environ.setdefault("AWS_DEFAULT_REGION",  "us-east-1")
os.environ.setdefault("AWS_ACCESS_KEY_ID",   "testing")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY","testing")
os.environ.setdefault("AWS_SECURITY_TOKEN",  "testing")
os.environ.setdefault("REGION",              "us-east-1")
os.environ.setdefault("PATIENTS_TABLE",        "test-patients")
os.environ.setdefault("DOCTORS_TABLE",         "test-doctors")
os.environ.setdefault("APPOINTMENTS_TABLE",    "test-appointments")
os.environ.setdefault("MEDICAL_RECORDS_TABLE", "test-medical-records")
os.environ.setdefault("AUDIT_LOGS_TABLE",      "test-audit-logs")
os.environ.setdefault("NOTIFICATIONS_TABLE",   "test-notifications")
os.environ.setdefault("S3_BUCKET",             "test-bucket")
os.environ.setdefault("COGNITO_USER_POOL_ID",  "us-east-1_testpool")
os.environ.setdefault("COGNITO_CLIENT_ID",     "testclientid")
os.environ.setdefault("SNS_TOPIC_ARN",         "arn:aws:sns:us-east-1:123456789012:test-topic")
os.environ.setdefault("AWS_ACCOUNT_ID",        "123456789012")
