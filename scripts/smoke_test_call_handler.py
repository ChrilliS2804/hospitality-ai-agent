"""Smoke test — invokes the call-handler Lambda directly and validates the response.

Used by the deploy-dev CI/CD pipeline after each deployment.
Requires: FUNCTION_NAME env var, AWS credentials in environment.
"""

from __future__ import annotations

import json
import os
import sys

import boto3

FUNCTION_NAME = os.environ["FUNCTION_NAME"]
REGION = os.environ.get("AWS_REGION", "eu-central-1")

# Minimal Connect-shaped event
TEST_EVENT = {
    "Name": "ContactFlowEvent",
    "Details": {"Parameters": {"userInput": ""}},
    "ContactData": {
        "ContactId": "smoke-test-contact-001",
        "InitialContactId": "smoke-test-contact-001",
        "Channel": "VOICE",
        "InstanceARN": "arn:aws:connect:eu-central-1:000000000000:instance/smoke",
        "Attributes": {"tenant_id": "smoke-test"},
        "CustomerEndpoint": {"Address": "+15550000000", "Type": "TELEPHONE_NUMBER"},
    },
}


def main() -> None:
    client = boto3.client("lambda", region_name=REGION)

    print(f"Invoking {FUNCTION_NAME}...")
    response = client.invoke(
        FunctionName=FUNCTION_NAME,
        InvocationType="RequestResponse",
        Payload=json.dumps(TEST_EVENT).encode(),
    )

    status_code = response["StatusCode"]
    payload = json.loads(response["Payload"].read())

    print(f"HTTP status: {status_code}")
    print(f"Payload: {json.dumps(payload, indent=2)}")

    # Assertions
    assert status_code == 200, f"Expected 200, got {status_code}"
    assert "response" in payload, "Missing 'response' field in Lambda output"
    assert "action" in payload, "Missing 'action' field in Lambda output"
    assert payload["action"] in ("continue", "transfer", "end"), \
        f"Unexpected action: {payload['action']}"
    assert len(payload["response"]) > 0, "Empty response text"

    print("✓ Smoke test passed")


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, KeyError) as exc:
        print(f"✗ Smoke test FAILED: {exc}", file=sys.stderr)
        sys.exit(1)
