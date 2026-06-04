# Amazon Connect Contact Flow Setup

The Contact Flow is created manually in the AWS Console.
The Connect instance and Lambda association are managed by Terraform.

---

## Prerequisites

- Terraform apply completed successfully
- Lambda function `hospitality-ai-dev-call-handler` deployed and working
- Amazon Connect instance `hospitality-ai-dev-instance` created by Terraform

---

## Step 1 — Open your Connect instance

1. Go to **AWS Console → Amazon Connect**
2. Click on **hospitality-ai-dev-instance**
3. Click **Log in for emergency access** or open the instance URL

---

## Step 2 — Create the Contact Flow

1. In the Connect console go to **Routing → Contact flows**
2. Click **Create contact flow**
3. Name it: `hospitality-ai-dev-inbound-flow`
4. Click the **down arrow** next to Save → **Import flow**
5. Upload the file: `docs/connect/inbound-flow.json`

Or build it manually with these blocks in order:

```
[Set contact attributes]
  - Key: tenant_id  Value: default
  - Connects to → [Invoke AWS Lambda function]

[Invoke AWS Lambda function]
  - Function: hospitality-ai-dev-call-handler
  - Timeout: 8 seconds
  - Attribute: userInput = $.Attributes.userInput
  - On success → [Play prompt]
  - On error → [Play prompt: error message]

[Play prompt]
  - Text to speech: $.External.response
  - Connects to → [Get customer input]

[Get customer input]
  - Text to speech: (leave blank)
  - Timeout: 8 seconds
  - On timeout → [Invoke AWS Lambda function]
  - On speech → [Set contact attributes: userInput = $.CustomerInput.SpeechResult]
                → [Invoke AWS Lambda function]

[Play prompt: error message]
  - Text: "I am sorry, something went wrong. Please call back."
  - Connects to → [Disconnect]

[Disconnect]
```

6. Click **Save** then **Publish**

---

## Step 3 — Claim a phone number

1. Go to **Channels → Phone numbers**
2. Click **Claim a number**
3. Select **DID**, country **Germany (+49)**
4. Assign contact flow: `hospitality-ai-dev-inbound-flow`
5. Click **Save**

---

## Step 4 — Test

Call the number. You should hear:

> "Hello, thank you for calling. I'm your AI assistant..."

Check **CloudWatch → Log Groups → /aws/lambda/hospitality-ai-dev-call-handler**
for the structured JSON log entry confirming the invocation.
