import os

from typing import List
from bs4 import BeautifulSoup
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI

class InteractiveElement(BaseModel):
    text: str = Field(description="사용자가 볼 수 있는 버튼 또는 링크의 텍스트")
    action_type: str = Field(description="예상되는 행동 (예: '페이지 이동', '로그인', '검색 실행')")


class PageSection(BaseModel):
    section_name: str = Field(description="콘텐츠 영역의 의미론적 이름 (예: '주요 뉴스', '쇼핑 바로가기', '로그인 영역')")
    elements: List[InteractiveElement] = Field(description="해당 영역에 포함된 상호작용 요소 목록")


class PageStructure(BaseModel):
    page_title: str = Field(description="웹페이지의 전체 제목")
    sections: List[PageSection] = Field(description="페이지를 구성하는 주요 섹션 목록")

def clean_html_with_soup(html_content: str) -> str:
    soup = BeautifulSoup(html_content, "html.parser")

    tags_to_remove = ['script', 'style', 'header', 'footer', 'nav', 'aside', 'form', 'iframe', 'link', 'meta']
    for tag in tags_to_remove:
        for s in soup.select(tag):
            s.decompose()

    if soup.body:
        body_text = soup.body.get_text(separator=' ', strip=True)
    else:
        body_text = soup.get_text(separator=' ', strip=True)

    return ' '.join(body_text.split())

async def structure_html_with_langchain(cleaned_html_text: str, url: str) -> PageStructure:

    model = ChatOpenAI(temperature=0, model="gpt-4o", openai_api_key=os.getenv("OPENAI_API_KEY"))

    parser = PydanticOutputParser(pydantic_object=PageStructure)

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are an expert web accessibility analyst. Your task is to analyze the text content of a webpage and identify the main interactive sections and elements for a user with motor disabilities. Respond ONLY in the requested JSON format."),
        ("human", """
        Analyze the following text content from the URL '{url}'. 
        Group the main interactive elements (links, buttons) into logical sections that a user would understand.

        {format_instructions}

        Webpage Text Content:
        ---
        {html_text}
        ---
        """),
    ])

    chain = prompt | model | parser

    # 체인 실행 및 결과 반환
    # 텍스트가 너무 길 경우를 대비해 앞부분만 잘라서 사용 (토큰 제한)
    result = await chain.ainvoke({
        "url": url,
        "html_text": cleaned_html_text[:4000],
        "format_instructions": parser.get_format_instructions()
    })

    return result
