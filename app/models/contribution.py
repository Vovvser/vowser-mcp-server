from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class ContributionStep(BaseModel):
    """기여모드 단계 데이터 모델"""
    url: str
    title: str
    action: str
    selector: Optional[str] = None
    htmlAttributes: Optional[Dict[str, str]] = None
    timestamp: int

class ContributionPathData(BaseModel):
    """기여모드 경로 데이터 모델"""
    sessionId: str
    task: str
    steps: List[ContributionStep]
    isPartial: bool = False
    isComplete: bool = False
    totalSteps: int = 0

class ContributionResponse(BaseModel):
    """기여모드 응답 모델"""
    type: str = "contribution_save_result"
    status: str  # success or error
    data: Dict[str, Any]