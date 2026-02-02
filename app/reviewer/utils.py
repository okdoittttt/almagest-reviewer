"""
Reviewer 유틸리티 함수
"""
import json
from typing import Any
from loguru import logger


def parse_llm_json_response(response_text: str) -> dict[str, Any]:
    """
    LLM 응답에서 JSON 추출 및 파싱

    LLM이 반환하는 응답에서 JSON 블록을 찾아 파싱합니다.
    응답이 ```json ... ``` 형식으로 감싸져 있으면 추출하고,
    그렇지 않으면 전체 텍스트를 JSON으로 파싱합니다.

    Args:
        response_text: LLM 응답 텍스트

    Returns:
        파싱된 JSON 딕셔너리

    Raises:
        json.JSONDecodeError: JSON 파싱 실패 시
    """
    try:
        # JSON 블록 추출 (```json ... ``` 형식)
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            # 마지막 ``` 찾기 (응답 내용에 ``` 문자열이 포함될 수 있으므로)
            json_end = response_text.rfind("```")

            # 유효한 범위인지 확인
            if json_end > json_start:
                json_text = response_text[json_start:json_end].strip()
            else:
                # 닫는 태그가 없으면 시작점부터 끝까지
                logger.warning("JSON 블록의 닫는 태그(```)를 찾을 수 없습니다. 시작점부터 끝까지 파싱을 시도합니다.")
                json_text = response_text[json_start:].strip()
        else:
            json_text = response_text.strip()

        return json.loads(json_text)

    except json.JSONDecodeError as e:
        logger.error(f"JSON 파싱 실패: {e}")
        logger.debug(f"파싱 실패한 텍스트: {response_text[:200]}...")
        raise
