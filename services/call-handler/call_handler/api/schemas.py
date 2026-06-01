"""Request/response schemas for the call handler Lambda.

Amazon Connect invokes the Lambda with a specific event structure.
These Pydantic models validate and document that contract.

Connect event reference:
https://docs.aws.amazon.com/connect/latest/adminguide/connect-lambda-functions.html
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ConnectContactData(BaseModel):
    """Subset of the Amazon Connect ContactData block we care about."""

    ContactId: str
    InitialContactId: str
    Channel: str = "VOICE"
    InstanceARN: str = ""
    Attributes: dict[str, str] = Field(default_factory=dict)
    CustomerEndpoint: dict[str, str] | None = None

    @property
    def caller_phone(self) -> str:
        """Extract caller phone from CustomerEndpoint, or empty string."""
        if self.CustomerEndpoint:
            return self.CustomerEndpoint.get("Address", "")
        return ""


class ConnectEvent(BaseModel):
    """Top-level Amazon Connect Lambda invocation event."""

    Name: str = "ContactFlowEvent"
    Details: dict[str, Any] = Field(default_factory=dict)
    ContactData: ConnectContactData

    @property
    def session_id(self) -> str:
        return self.ContactData.ContactId

    @property
    def tenant_id(self) -> str:
        """Tenant ID is passed as a Contact Attribute set in the Contact Flow."""
        return self.ContactData.Attributes.get("tenant_id", "default")

    @property
    def user_input(self) -> str:
        """The caller's spoken input, transcribed by Connect."""
        return self.Details.get("Parameters", {}).get("userInput", "")


class ConnectResponse(BaseModel):
    """Response returned to Amazon Connect from the Lambda.

    Connect reads the 'response' field and speaks it to the caller.
    """

    response: str                          # Text/SSML to speak to caller
    action: str = "continue"              # continue | transfer | end
    transfer_queue_arn: str | None = None  # Set when action=transfer
    session_attributes: dict[str, str] = Field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "response": self.response,
            "action": self.action,
            "sessionAttributes": self.session_attributes,
        }
        if self.transfer_queue_arn:
            result["transferQueueArn"] = self.transfer_queue_arn
        return result
