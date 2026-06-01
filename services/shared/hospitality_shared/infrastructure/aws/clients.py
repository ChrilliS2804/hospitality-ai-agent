"""AWS SDK client factories.

Clients are module-level singletons so boto3 connections are reused
across Lambda invocations (warm starts). Each factory is called once
and the result cached.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

import boto3
from botocore.config import Config


def _region() -> str:
    return os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "eu-central-1"))


_RETRY_CONFIG = Config(
    retries={"max_attempts": 3, "mode": "adaptive"},
    connect_timeout=5,
    read_timeout=30,
)


@lru_cache(maxsize=1)
def get_dynamodb_client() -> Any:
    """Return a cached DynamoDB client."""
    return boto3.client("dynamodb", region_name=_region(), config=_RETRY_CONFIG)


@lru_cache(maxsize=1)
def get_dynamodb_resource() -> Any:
    """Return a cached DynamoDB resource (higher-level API)."""
    return boto3.resource("dynamodb", region_name=_region(), config=_RETRY_CONFIG)


@lru_cache(maxsize=1)
def get_lambda_client() -> Any:
    """Return a cached Lambda client."""
    return boto3.client("lambda", region_name=_region(), config=_RETRY_CONFIG)


@lru_cache(maxsize=1)
def get_bedrock_runtime_client() -> Any:
    """Return a cached Bedrock Runtime client."""
    return boto3.client(
        "bedrock-runtime",
        region_name=_region(),
        config=Config(
            retries={"max_attempts": 3, "mode": "adaptive"},
            connect_timeout=5,
            read_timeout=60,  # Bedrock can be slow on first token
        ),
    )


@lru_cache(maxsize=1)
def get_bedrock_agent_runtime_client() -> Any:
    """Return a cached Bedrock Agent Runtime client (for Knowledge Bases)."""
    return boto3.client(
        "bedrock-agent-runtime",
        region_name=_region(),
        config=Config(
            retries={"max_attempts": 3, "mode": "adaptive"},
            connect_timeout=5,
            read_timeout=60,
        ),
    )


@lru_cache(maxsize=1)
def get_sns_client() -> Any:
    """Return a cached SNS client."""
    return boto3.client("sns", region_name=_region(), config=_RETRY_CONFIG)


@lru_cache(maxsize=1)
def get_ses_client() -> Any:
    """Return a cached SES client."""
    return boto3.client("ses", region_name=_region(), config=_RETRY_CONFIG)


@lru_cache(maxsize=1)
def get_events_client() -> Any:
    """Return a cached EventBridge client."""
    return boto3.client("events", region_name=_region(), config=_RETRY_CONFIG)


@lru_cache(maxsize=1)
def get_secretsmanager_client() -> Any:
    """Return a cached Secrets Manager client."""
    return boto3.client("secretsmanager", region_name=_region(), config=_RETRY_CONFIG)
