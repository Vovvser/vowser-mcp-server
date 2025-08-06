from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class LocationData(BaseModel):
    primarySelector: str
    fallbackSelectors: List[str]
    anchorPoint: str
    relativePathFromAnchor: str
    elementSnapshot: Dict[str, Any]

class SemanticData(BaseModel):
    textLabels: List[str]
    contextText: Dict[str, Any]
    pageInfo: Dict[str, Any]
    actionType: str

class PathStep(BaseModel):
    order: int
    url: str
    locationData: Optional[LocationData] = None
    semanticData: Optional[SemanticData] = None

class PathData(BaseModel):
    sessionId: str
    startCommand: str
    completePath: List[PathStep]

# 새로운 검색 관련 모델들
class SearchPathRequest(BaseModel):
    query: str
    limit: int = 3
    domain_hint: Optional[str] = None

class PathStepResponse(BaseModel):
    order: int
    type: str  # ROOT or PAGE
    title: str
    pageId: Optional[str] = None
    domain: Optional[str] = None
    url: str
    selector: Optional[str] = None
    anchorPoint: Optional[str] = None
    action: str
    textLabels: Optional[List[str]] = None

class MatchedPath(BaseModel):
    pathId: str
    relevance_score: float
    total_weight: int
    last_used: Optional[datetime] = None
    estimated_time: Optional[float] = None
    steps: List[PathStepResponse]

class SearchMetadata(BaseModel):
    total_found: int
    search_time_ms: int
    vector_search_used: bool
    min_score_threshold: float = 0.7

class SearchPathResponse(BaseModel):
    query: str
    matched_paths: List[MatchedPath]
    search_metadata: SearchMetadata