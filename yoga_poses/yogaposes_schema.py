from pydantic import BaseModel ,Field,HttpUrl,computed_field
from typing import Literal,List,Optional
from uuid import uuid4
class YogaPoses(BaseModel):
    video_id: str = Field(default_factory=lambda: str(uuid4()))

    name: str = Field(..., description="Name of the yoga pose")

    benefits: List[str] = Field(
        ..., description="Health benefits of the pose"
    )

    difficulty: str = Field(
        ..., description="beginner / intermediate / advanced"
    )

    duration: int = Field(
        ..., description="Duration in minutes"
    )

    category: str = Field(
        ..., description="warmup / main / relaxation"
    )

    focus: List[str] = Field(
        ..., description="pcos / pcod / stress / weight_loss"
    )

    contraindications: Optional[List[str]] = Field(
        default=[], description="Who should avoid this pose"
    )

    best_time: Optional[str] = Field(
        default="morning", description="Best time to perform"
    )

    video_url: HttpUrl = Field(...)

    tags: List[str] = Field(
        ..., description="search tags like pcos, hormones"
    )