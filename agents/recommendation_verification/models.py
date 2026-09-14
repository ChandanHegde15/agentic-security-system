"""Models emitted by Agent 5."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class VerificationStatus(str, Enum):
    VERIFIED = "verified"
    REJECTED = "rejected"
    REQUIRES_REVIEW = "requires_review"


class VerificationResult(BaseModel):
    """A merge gate result; Agent 5 never performs the merge itself."""

    model_config = ConfigDict(extra="forbid")
    project_id: str = Field(min_length=1)
    branch_name: Optional[str] = None
    status: VerificationStatus
    tests_available: bool
    tests_passed: Optional[bool]
    candidate_valid: bool
    merge_allowed: bool
    details: list[str]
