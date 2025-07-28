from pydantic import BaseModel
from typing import List, Dict, Any, Optional

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