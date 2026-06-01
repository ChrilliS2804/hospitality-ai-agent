"""Pytest configuration for call-handler tests."""

import os

import pytest

# Ensure AWS SDK calls don't hit real AWS during tests
os.environ.setdefault("AWS_DEFAULT_REGION", "eu-central-1")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")
os.environ.setdefault("AWS_SECURITY_TOKEN", "testing")
os.environ.setdefault("AWS_SESSION_TOKEN", "testing")
os.environ.setdefault("DYNAMODB_TABLE_NAME", "hospitality-ai-test-table")
os.environ.setdefault("XRAY_ENABLED", "false")
