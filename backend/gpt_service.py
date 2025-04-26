import openai
import json
from backend.prompts import build_gpt_prompt, build_strategy_prompt
from backend.config import OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY

async def analyze_user_message(user_message, resume_text):
    """
    자유 입력 + 이력서 텍스트를 기반으로 GPT 분석 (1차 분석 + 2차 전략 생성)
    """
    # 1차 분석: 사용자 입력과 이력서를 바탕으로 JSON 추출
    primary_prompt = build_gpt_prompt(user_message, resume_text)

    primary_response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "너는 현실적인 커리어 분석 전문가야."},
            {"role": "user", "content": primary_prompt}
        ],
        temperature=0.2,
        max_tokens=1500,
    )

    primary_result_text = primary_response['choices'][0]['message']['content']

    # 코드블록(```json) 제거
    cleaned_primary_text = (
        primary_result_text
        .replace("```json", "")
        .replace("```", "")
        .strip()
    )

    try:
        primary_result_json = json.loads(cleaned_primary_text)
    except Exception as e:
        raise ValueError(f"GPT 1차 응답을 JSON으로 변환할 수 없습니다. GPT 응답 내용: {primary_result_text}")

    # 2차 분석: 1차 JSON을 기반으로 전략 생성
    secondary_prompt = build_strategy_prompt(primary_result_json)

    secondary_response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "너는 현실적인 커리어 분석 전문가야."},
            {"role": "user", "content": secondary_prompt}
        ],
        temperature=0.2,
        max_tokens=1500,
    )

    secondary_result_text = secondary_response['choices'][0]['message']['content']

    # 코드블록(```json) 제거
    cleaned_secondary_text = (
        secondary_result_text
        .replace("```json", "")
        .replace("```", "")
        .strip()
    )

    try:
        secondary_result_json = json.loads(cleaned_secondary_text)
    except Exception as e:
        raise ValueError(f"GPT 2차 전략 응답을 JSON으로 변환할 수 없습니다. GPT 응답 내용: {secondary_result_text}")

    return secondary_result_json
