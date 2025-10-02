from pydantic import BaseModel
from typing import List


class RootData(BaseModel):
    """
    ROOT 노드 데이터

    도메인 정보와 메타데이터를 담는 모델
    """
    domain: str  # 예: "naver.com"
    baseURL: str  # 예: "https://naver.com"
    displayName: str  # 예: "네이버"
    keywords: List[str] = []  # 예: ["네이버", "포털", "검색"]
