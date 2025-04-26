import openai, json
from backend.config import OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY

def build_gpt_prompt(user_message, resume_text):
    prompt = f"""
너는 냉정하고 현실적인 커리어 분석 전문가야.

아래 사용자 자유 입력과 이력서 텍스트를 기반으로 다음을 분석해줘:

1. 직무 (Job)
2. 산업군 (Industry)
3. 경력 연차 (Experience Years)
4. 주요 스킬 (Skills)
5. 자격증 (Certifications)
6. 마지막 회사 규모 (Company Size)
7. 경력 단절 여부 (Career Gap 여부)
8. 기대 연봉 (Expected Salary)
9. 고민 (Concern)
10. 목표 (Goal)

**응답은 반드시 순수 JSON 형식으로만 출력해. 자연어 문장 추가 없이, JSON만.**

추출한 결과를 다음 JSON 포맷으로 정확히 맞춰 작성해:

{{
    "job": "",
    "industry": "",
    "experience_years": 0,
    "skills": [],
    "certifications": [],
    "last_company_size": "",
    "career_gap": true,
    "expected_salary": 0,
    "concern": "",
    "goal": ""
}}

[사용자 자유 입력]
{user_message}

[이력서 텍스트]
{resume_text}
    """
    return prompt


def build_strategy_prompt(primary_json):
    """
    1차 분석 JSON 결과를 기반으로 전략 분석용 프롬프트 생성
    """
    return f"""
아래는 사용자의 현재 커리어 분석 결과야.

{json.dumps(primary_json, ensure_ascii=False)}

이걸 바탕으로,

1. 이직 가능성을 '높음', '보통', '낮음' 중 하나로 평가해줘.
2. 강점(Strength)을 간단히 요약해줘.
3. 약점(Weakness)을 간단히 요약해줘.
4. 향후 3개월/6개월/12개월 관점으로 Action Plan을 제안해줘.

- 응답은 반드시 순수 JSON 포맷으로 작성
- 문장 설명 없이 바로 JSON만 작성
    """



async def analyze_user_message(user_message, resume_text):
    """
    자유 입력 + 이력서 텍스트를 기반으로 GPT 분석
    """
    prompt = build_gpt_prompt(user_message, resume_text)

    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "너는 현실적인 커리어 분석 전문가야."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        max_tokens=1500,
    )

    result_text = response['choices'][0]['message']['content']

    # JSON 형태로 파싱 시도
    try:
        result_json = eval(result_text)  # (주의: 운영 시에는 json.loads()로 교체 추천)
    except:
        raise ValueError("GPT 응답을 JSON으로 변환할 수 없습니다.")

    return result_json
