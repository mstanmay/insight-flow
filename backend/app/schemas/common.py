from datetime import datetime
from typing import Generic, List, Optional, TypeVar, Dict, Any
from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationMeta(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(25, ge=1, le=500)
    total: int = Field(0, ge=0)
    total_pages: int = Field(0, ge=0)


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    page: int
    page_size: int
    total: int
    total_pages: int


class AvailabilityField(BaseModel):
    value: Any = None
    availability: str = "available"  # "available" | "unavailable"
    reason: Optional[str] = None


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"
    pipeline_version: str = "1.0.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ReadyCheckDetail(BaseModel):
    status: str
    message: Optional[str] = None


class ReadyResponse(BaseModel):
    status: str  # "ready" | "not_ready"
    checks: Dict[str, ReadyCheckDetail]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
