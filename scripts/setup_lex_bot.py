"""Create the Lex V2 passthrough bot for speech-to-text in Connect.

This bot has NO custom intents. All speech is caught by FallbackIntent,
which invokes our call-handler Lambda with the transcribed text.

Run once:
    py scripts/setup_lex_bot.py

Requires: AWS credentials with Lex and IAM permissions.
"""

from __future__ import annotations

import json
import os
import sys
import time

import boto3

REGION = os.environ.get("AWS_REGION", "eu-central-1")
ACCOUNT_ID = os.environ.get("AWS_ACCOUNT_ID", "799379601618")
BOT_NAME = "hospitality-ai-dev-speech-bot"
LAMBDA_ARN = f"arn:aws:lambda:{REGION}:{ACCOUNT_ID}:function:hospitality-ai-dev-call-handler"
LOCALE = "de_DE"


def main() -> None:
    lex = boto3.client("lexv2-models", region_name=REGION)
    lambda_client = boto3.client("lambda", region_name=REGION)
    iam = boto3.client("iam")

    # Step 1: Create IAM role for Lex bot
    print("Creating Lex bot IAM role...")
    role_name = "hospitality-ai-dev-lex-bot-role"
    try:
        role = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps({
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Principal": {"Service": "lexv2.amazonaws.com"},
                    "Action": "sts:AssumeRole",
                }],
            }),
            Tags=[{"Key": "Application", "Value": "AIHospitalityAgent"}],
        )
        role_arn = role["Role"]["Arn"]
        iam.attach_role_policy(
            RoleName=role_name,
            PolicyArn="arn:aws:iam::aws:policy/AmazonLexFullAccess",
        )
        print(f"  Role created: {role_arn}")
        time.sleep(10)  # Wait for IAM propagation
    except iam.exceptions.EntityAlreadyExistsException:
        role_arn = f"arn:aws:iam::{ACCOUNT_ID}:role/{role_name}"
        print(f"  Role already exists: {role_arn}")

    # Step 2: Create the bot
    print("Creating Lex V2 bot...")
    try:
        bot = lex.create_bot(
            botName=BOT_NAME,
            roleArn=role_arn,
            dataPrivacy={"childDirected": False},
            idleSessionTTLInSeconds=300,
            botTags={"Application": "AIHospitalityAgent"},
        )
        bot_id = bot["botId"]
        print(f"  Bot created: {bot_id}")
        time.sleep(15)  # Wait for bot to become Available
    except (lex.exceptions.ConflictException, lex.exceptions.PreconditionFailedException):
        # Bot already exists, find it
        bots = lex.list_bots(filters=[{"name": "BotName", "values": [BOT_NAME], "operator": "EQ"}])
        bot_id = bots["botSummaries"][0]["botId"]
        print(f"  Bot already exists: {bot_id}")

    # Step 3: Create German locale
    print("Creating de_DE locale...")
    try:
        lex.create_bot_locale(
            botId=bot_id,
            botVersion="DRAFT",
            localeId=LOCALE,
            nluIntentConfidenceThreshold=0.4,
            voiceSettings={"voiceId": "Vicki", "engine": "neural"},
        )
        print("  Locale created")
    except (lex.exceptions.ConflictException, lex.exceptions.PreconditionFailedException,
            lex.exceptions.ServiceQuotaExceededException):
        print("  Locale already exists or bot not ready, continuing...")
    except Exception as e:
        if "ValidationException" in str(type(e).__name__):
            print("  Bot still creating, waiting 15s...")
            time.sleep(15)
            try:
                lex.create_bot_locale(
                    botId=bot_id,
                    botVersion="DRAFT",
                    localeId=LOCALE,
                    nluIntentConfidenceThreshold=0.4,
                    voiceSettings={"voiceId": "Vicki", "engine": "neural"},
                )
                print("  Locale created (retry)")
            except Exception:
                print("  Locale may already exist, continuing...")

    # Step 4: Wait for locale to be ready
    print("Waiting for locale to be ready...")
    for _ in range(30):
        status = lex.describe_bot_locale(botId=bot_id, botVersion="DRAFT", localeId=LOCALE)
        if status["botLocaleStatus"] in ("Built", "NotBuilt", "ReadyExpressTesting"):
            break
        time.sleep(2)
    print(f"  Locale status: {status['botLocaleStatus']}")

    # Step 5: Update FallbackIntent with fulfillment Lambda
    print("Configuring FallbackIntent with Lambda fulfillment...")
    intents = lex.list_intents(botId=bot_id, botVersion="DRAFT", localeId=LOCALE)
    fallback_id = None
    for intent in intents.get("intentSummaries", []):
        if intent["intentName"] == "FallbackIntent":
            fallback_id = intent["intentId"]
            break

    if fallback_id:
        lex.update_intent(
            botId=bot_id,
            botVersion="DRAFT",
            localeId=LOCALE,
            intentId=fallback_id,
            intentName="FallbackIntent",
            parentIntentSignature="AMAZON.FallbackIntent",
            fulfillmentCodeHook={"enabled": True},
        )
        print(f"  FallbackIntent updated: {fallback_id}")

    # Step 5b: Create a dummy intent (Lex requires at least one custom intent with utterances)
    print("Creating dummy CatchAll intent...")
    try:
        dummy = lex.create_intent(
            botId=bot_id,
            botVersion="DRAFT",
            localeId=LOCALE,
            intentName="CatchAllIntent",
            sampleUtterances=[
                {"utterance": "xyzzy_placeholder_never_match"},
            ],
        )
        print(f"  CatchAll intent created: {dummy['intentId']}")
    except Exception as e:
        if "already exists" in str(e) or "Conflict" in str(type(e).__name__):
            print("  CatchAll intent already exists")
        else:
            print(f"  CatchAll intent issue (continuing): {e}")

    # Step 6: Build the locale
    print("Building bot locale...")
    lex.build_bot_locale(botId=bot_id, botVersion="DRAFT", localeId=LOCALE)

    print("Waiting for build...")
    for _ in range(60):
        status = lex.describe_bot_locale(botId=bot_id, botVersion="DRAFT", localeId=LOCALE)
        if status["botLocaleStatus"] == "Built":
            break
        time.sleep(3)
    print(f"  Build status: {status['botLocaleStatus']}")

    if status["botLocaleStatus"] != "Built":
        print("ERROR: Bot locale did not build successfully")
        sys.exit(1)

    # Step 7: Create bot version
    print("Creating bot version...")
    try:
        version = lex.create_bot_version(
            botId=bot_id,
            botVersionLocaleSpecification={
                LOCALE: {"sourceBotVersion": "DRAFT"}
            },
        )
        bot_version = version["botVersion"]
        print(f"  Version created: {bot_version}")
    except Exception as e:
        print(f"  Version creation issue: {e}")
        # Use version 1 as fallback
        bot_version = "1"
        print(f"  Using version: {bot_version}")

    # Wait for version to be available
    print("Waiting for version to be available...")
    time.sleep(5)
    for _ in range(30):
        try:
            v = lex.describe_bot_version(botId=bot_id, botVersion=bot_version)
            if v["botStatus"] == "Available":
                print(f"  Version {bot_version} is available")
                break
        except Exception:
            pass
        time.sleep(3)
    else:
        print("  WARNING: Version may not be ready yet, continuing anyway...")

    # Step 8: Create bot alias with Lambda
    print("Creating bot alias 'live'...")
    try:
        alias = lex.create_bot_alias(
            botId=bot_id,
            botAliasName="live",
            botVersion=bot_version,
            botAliasLocaleSettings={
                LOCALE: {
                    "enabled": True,
                    "codeHookSpecification": {
                        "lambdaCodeHook": {
                            "lambdaARN": LAMBDA_ARN,
                            "codeHookInterfaceVersion": "1.0",
                        }
                    },
                }
            },
            tags={"Application": "AIHospitalityAgent"},
        )
        alias_id = alias["botAliasId"]
        print(f"  Alias created: {alias_id}")
    except lex.exceptions.ConflictException:
        aliases = lex.list_bot_aliases(botId=bot_id)
        alias_id = [a for a in aliases["botAliasSummaries"] if a["botAliasName"] == "live"][0]["botAliasId"]
        print(f"  Alias already exists: {alias_id}")

    # Step 9: Add Lambda permission for Lex
    print("Adding Lambda permission for Lex...")
    try:
        lambda_client.add_permission(
            FunctionName=LAMBDA_ARN,
            StatementId="AllowLexV2Invoke",
            Action="lambda:InvokeFunction",
            Principal="lexv2.amazonaws.com",
            SourceArn=f"arn:aws:lex:{REGION}:{ACCOUNT_ID}:bot-alias/{bot_id}/{alias_id}",
        )
        print("  Permission added")
    except lambda_client.exceptions.ResourceConflictException:
        print("  Permission already exists")

    # Step 10: Associate bot with Connect instance
    print("Associating bot with Connect instance...")
    connect = boto3.client("connect", region_name=REGION)
    connect_instance_id = "5ea3934f-ac57-48d5-abf9-d16e845e345e"
    try:
        connect.associate_bot(
            InstanceId=connect_instance_id,
            LexV2Bot={
                "AliasArn": f"arn:aws:lex:{REGION}:{ACCOUNT_ID}:bot-alias/{bot_id}/{alias_id}",
            },
        )
        print("  Bot associated with Connect")
    except Exception as e:
        print(f"  Associate bot result: {e}")

    print("\n" + "=" * 60)
    print("DONE! Lex bot setup complete.")
    print(f"  Bot ID:    {bot_id}")
    print(f"  Alias ID:  {alias_id}")
    print(f"  Bot Name:  {BOT_NAME}")
    print(f"  Lambda:    {LAMBDA_ARN}")
    print("\nNext: Update the Connect Contact Flow to use this bot")
    print("  in the 'Get customer input' block (Amazon Lex tab).")
    print("=" * 60)


if __name__ == "__main__":
    main()
