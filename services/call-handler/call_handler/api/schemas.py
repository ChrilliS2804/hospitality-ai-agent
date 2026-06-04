"""Request/response schemas for the call handler Lambda.

Amazon Connect invokes the Lambda with a specific event structure.
The actual Connect event places ContactData INSIDE Details:
{
  "Name": "ContactFlowEvent",
  "Details": {
    "ContactData": { ... },
    "Parameters": { ... }
  }
}

Connect event reference:
https://docs.aws.amazon.com/connect/latest/adminguide/connect-lambda-functions.html
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, model_validator


class ConnectContactData(BaseModel):
    """Subset of the Amazon Connect ContactData block we care about."""

    ContactId: str
    InitialContactId: str = ""
    Channel: str = "VOICE"
    InstanceARN: str = ""
    Attributes: dict[str, str] = Field(default_factory=dict)
    CustomerEndpoint: dict[str, str] | None = None

    model_config = {"extra": "allow"}

    @property
    def caller_phone(self) -> str:
        """Extract caller phone from CustomerEndpoint, or empty string."""
        if self.CustomerEndpoint:
            return self.CustomerEndpoint.get("Address", "")
        return ""


class ConnectDetails(BaseModel):
    """The Details block from the Connect event."""

    ContactData: ConnectContactData
    Parameters: dict[str, str] = Field(default_factory=dict)

    model_config = {"extra": "allow"}


class ConnectEvent(BaseModel):
    """Top-level Amazon Connect Lambda invocation event.

    Handles both the real Connect format (ContactData inside Details)
    and our smoke test format (ContactData at top level) for backward
    compatibility.
    """

    Name: str = "ContactFlowEvent"
    Details: dict[str, Any] = Field(default_factory=dict)
    ContactData: ConnectContactData | None = None

    model_config = {"extra": "allow"}

    @model_validator(mode="before")
    @classmethod
    def normalize_event(cls, values: dict[str, Any]) -> dict[str, Any]:
        """Handle both Connect format and smoke test format.

        Real Connect: ContactData is inside Details.
        Smoke test:   ContactData is at top level.
        """
        details = values.get("Details", {})

        # Real Connect format: ContactData inside Details
        if "ContactData" in details and "ContactData" not in values:
            values["ContactData"] = details["ContactData"]

        # If ContactData is still missing, check if it's nested
        if values.get("ContactData") is None and "ContactData" in details:
            values["ContactData"] = details["ContactData"]

        return values

    @property
    def contact_data(self) -> ConnectContactData:
        """Return ContactData regardless of where it was in the original event."""
        if self.ContactData is not None:
            return self.ContactData
        # Fallback: try to parse from Details
        cd = self.Details.get("ContactData", {})
        return ConnectContactData(**cd)

    @property
    def session_id(self) -> str:
        return self.contact_data.ContactId

    @property
    def tenant_id(self) -> str:
        """Tenant ID is passed as a Contact Attribute set in the Contact Flow."""
        return self.contact_data.Attributes.get("tenant_id", "default")

    @property
    def user_input(self) -> str:
        """The caller's spoken input, transcribed by Connect."""
        # Real Connect: Parameters is inside Details
        params = self.Details.get("Parameters", {})
        return params.get("userInput", "")


class ConnectResponse(BaseModel):
    """Response returned to Amazon Connect from the Lambda.

    Connect reads the 'response' field and speaks it to the caller.
    """

    response: str
    action: str = "continue"
    transfer_queue_arn: str | None = None
    session_attributes: dict[str, str] = Field(default_factory=dict)

    def to_dict(self) -> dict[str, str]:
        """Return flat string key-value map as required by Amazon Connect."""
        result: dict[str, str] = {
            "response": self.response,
            "action": self.action,
        }
        if self.transfer_queue_arn:
            result["transferQueueArn"] = self.transfer_queue_arn
        # Flatten session attributes into the response map
        for key, value in self.session_attributes.items():
            result[key] = value
        return result
