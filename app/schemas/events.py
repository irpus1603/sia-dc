from pydantic import BaseModel, Field
from typing import Optional, Any, Dict
from datetime import datetime

class ForwardItem(BaseModel):
    account: Optional[str] = None
    message_type: Optional[str] = Field(None, description="e.g., 'N' new, 'R' restore")
    code: Optional[str] = Field(None, description="SIA event code, e.g., BA")
    zone: Optional[str] = None
    partition: Optional[str] = None
    receiver: Optional[str] = None
    timestamp: Optional[datetime] = None
    raw: Optional[str] = Field(None, description="Original message text/frame")
    extras: Dict[str, Any] = Field(default_factory=dict)

class ReplayEvent(BaseModel):
    account: str = "AAA"
    message_type: str = "N"
    code: str = "BA"
    zone: Optional[str] = None
    timestamp: Optional[datetime] = None
    raw: Optional[str] = "TEST"
    extras: Dict[str, Any] = Field(default_factory=dict)
