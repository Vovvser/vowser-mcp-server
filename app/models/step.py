from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class StepData(BaseModel):
    """
    단일 STEP 노드 데이터 (기존 PAGE 노드 개념 확장)

    사용자의 웹 액션을 표현하는 개별 단계
    """
    stepId: Optional[str] = None  # 자동 생성 (MD5 해시)
    url: str
    domain: str

    # 선택자 정보
    selectors: List[str] = Field(default_factory=list)  # [primary, fallback1, fallback2, ...]
    anchorPoint: Optional[str] = None
    relativePathFromAnchor: Optional[str] = None

    # 액션 타입
    action: str  # "click" | "input" | "wait"

    # 입력 관련 (action = "input"일 때)
    isInput: bool = False
    inputType: Optional[str] = None  # "email" | "id" | "password" | "search" | "text"
    inputPlaceholder: Optional[str] = None

    # 대기 관련 (action = "wait"일 때)
    shouldWait: bool = False
    waitMessage: Optional[str] = None  # "카카오 간편인증을 기다리고 있습니다"
    maxWaitTime: Optional[int] = None  # 최대 대기 시간 (초)

    # 시맨틱 정보
    description: str  # "로그인 버튼 클릭"
    textLabels: List[str] = Field(default_factory=list)  # 요소의 텍스트들
    contextText: Optional[str] = None  # 주변 텍스트

    # 메타데이터
    successRate: float = 1.0  # 0.0 ~ 1.0


class PathSubmission(BaseModel):
    """
    사용자가 제출하는 완전한 경로 데이터

    클라이언트에서 서버로 전송되는 경로 정보
    """
    sessionId: str
    taskIntent: str  # "날씨 보기", "로그인" 등 - 사용자 의도
    domain: str  # 시작 도메인
    steps: List[StepData]  # 순차적 단계 목록
