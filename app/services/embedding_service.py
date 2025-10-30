import os
import hashlib

from typing import List, Optional
from openai import OpenAI
from app.models.path import PathStep
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

def get_openai_client():
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("환경변수에 OPENAI_API_KEY가 없습니다!")
            return None
        return OpenAI(api_key=api_key)
    except Exception as e:
        print(f"OpenAI client 초기화 실패. Error: {e}")
        return None

client = None

# 임베딩 캐시 (메모리 기반)
_embedding_cache = {}
_CACHE_MAX_SIZE = 1000  # 최대 캐시 크기

def _get_cache_key(text: str) -> str:
    """텍스트의 캐시 키 생성 (해시 기반)"""
    return hashlib.md5(text.strip().encode()).hexdigest()

def _clean_cache_if_needed():
    """캐시 크기가 최대치를 초과하면 가장 오래된 항목 삭제"""
    global _embedding_cache
    if len(_embedding_cache) > _CACHE_MAX_SIZE:
        # 간단하게 전체 캐시의 절반 삭제 (FIFO)
        keys_to_remove = list(_embedding_cache.keys())[:_CACHE_MAX_SIZE // 2]
        for key in keys_to_remove:
            del _embedding_cache[key]
        print(f"🧹 임베딩 캐시 정리: {len(keys_to_remove)}개 항목 삭제")

def generate_embedding(text: str) -> Optional[List[float]]:
    """
    텍스트를 임베딩 벡터로 변환 (캐싱 지원)
    
    Args:
        text (str): 임베딩할 텍스트
        
    Returns:
        List[float] | None: 임베딩 벡터 또는 None (실패 시)
    """
    global _embedding_cache
    
    if not text or not text.strip():
        print("Warning: 임베딩 생성 건너뜀: 빈 텍스트가 제공되었습니다.")
        return None
    
    # 캐시 키 생성
    cache_key = _get_cache_key(text)
    
    # 캐시에서 확인
    if cache_key in _embedding_cache:
        print(f"💾 임베딩 캐시 히트: '{text[:30]}...'")
        return _embedding_cache[cache_key]
    
    # 캐시 미스 - 새로 생성
    client = get_openai_client()
    if not client:
        print("Warning: 임베딩 생성 건너뜀: OpenAI 클라이언트를 사용할 수 없습니다.")
        return None
    
    try:
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=text.strip()
        )
        embedding = response.data[0].embedding
        
        # 캐시에 저장
        _embedding_cache[cache_key] = embedding
        _clean_cache_if_needed()
        
        print(f"📝 임베딩 생성 및 캐싱: '{text[:30]}...'")
        return embedding
    except Exception as e:
        print(f"Error: 임베딩 생성 실패: {e}")
        return None

def create_embedding_text(step: PathStep) -> str:
    """
    PathStep 객체에서 PAGE 임베딩용 텍스트 생성
    
    Args:
        step (PathStep): 경로 단계 데이터
        
    Returns:
        str: 임베딩용으로 조합된 텍스트
    """
    if not step.semanticData:
        return ""
    
    texts = []
    
    # textLabels 추가
    if step.semanticData.textLabels:
        texts.extend(step.semanticData.textLabels)
    
    # contextText 추가
    if step.semanticData.contextText:
        context = step.semanticData.contextText
        
        # immediate context
        if context.get('immediate'):
            texts.append(context['immediate'])
        
        # section context
        if context.get('section'):
            texts.append(context['section'])
        
        # neighbor context
        if context.get('neighbor') and isinstance(context['neighbor'], list):
            texts.extend(context['neighbor'])
    
    # pageInfo 추가
    if step.semanticData.pageInfo and step.semanticData.pageInfo.get('title'):
        texts.append(step.semanticData.pageInfo['title'])
    
    filtered_texts = [text for text in texts if text and text.strip()]
    return ' '.join(filtered_texts)
