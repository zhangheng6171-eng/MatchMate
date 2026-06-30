"""通话相关 Pydantic 模型"""
from datetime import datetime
from pydantic import BaseModel


class CallInitiate(BaseModel):
    callee_id: str
    call_type: str = "video"  # voice / video


class CallUpdate(BaseModel):
    status: str | None = None  # in_progress / ended / rejected / busy
    duration_seconds: int | None = None
    quality_score: int | None = None


class CallResponse(BaseModel):
    id: str
    caller_id: str
    callee_id: str
    call_type: str
    status: str
    duration_seconds: int | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
