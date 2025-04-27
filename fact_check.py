import streamlit as st
import openai
import os
import sys
import json
import pdfplumber
import docx
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import uvicorn
from dotenv import load_dotenv

# ====== 환경 설정 ======
sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# ====== 이력서 파싱 ======
def extract_text_from_pdf(file_path):
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return clean_text(text)

def extract_text_from_docx(file_path):
    doc = docx.Document(file_path)
    text = "\n".join([para.text.strip() for para in doc.paragraphs if para.text.strip()])
    return clean_text(text)

def extract_resume_text(file_path):
    ext = os.path.splitext(file_path)[-1].lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext == ".docx":
        return extract_text_from_docx(file_path)
    else:
        raise ValueError(f"Unsupported file format: {ext}")

def clean_text(text):
    lines = text.split("\n")
    cleaned_lines = [line.strip() for line in lines if line.strip()]
    return "\n".join(cleaned_lines)

# ====== GPT 프롬프트 빌더 ======
def build_gpt_prompt(user_message, resume_text):
    prompt = f"""...
[사용자 자유 입력]
{user_message}

[이력서 텍스트]
{resume_text}
"""
    return prompt

def build_strategy_prompt(primary_json):
    return f"""...
"""

async def analyze_user_message(user_message, resume_text):
    primary_prompt = build_gpt_prompt(user_message, resume_text)

    primary_response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "너는 현실적인 커리어 분석 전문가야."},
            {"role": "user", "content": primary_prompt}
        ],
        temperature=0.2,
        max_tokens=1500,
    )
    primary_result_text = primary_response.choices[0].message.content
    cleaned_primary_text = primary_result_text.replace("```json", "").replace("```", "").strip()
    primary_result_json = json.loads(cleaned_primary_text)

    secondary_prompt = build_strategy_prompt(primary_result_json)
    secondary_response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "너는 현실적인 커리어 분석 전문가야."},
            {"role": "user", "content": secondary_prompt}
        ],
        temperature=0.2,
        max_tokens=1500,
    )
    secondary_result_text = secondary_response.choices[0].message.content
    cleaned_secondary_text = secondary_result_text.replace("```json", "").replace("```", "").strip()
    secondary_result_json = json.loads(cleaned_secondary_text)

    return secondary_result_json

# ====== FastAPI 서버 설정 ======
app = FastAPI()

class AnalysisResult(BaseModel):
    result_json: dict

@app.post("/analyze", response_model=AnalysisResult)
async def analyze(user_message: str = Form(...), resume: Optional[UploadFile] = File(None)):
    try:
        resume_text = ""
        if resume is not None and resume.filename != "":
            file_location = f"temp_{resume.filename}"
            with open(file_location, "wb") as f:
                f.write(await resume.read())
            resume_text = extract_resume_text(file_location)
            os.remove(file_location)

        result_json = await analyze_user_message(user_message, resume_text)
        return AnalysisResult(result_json=result_json)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ====== Streamlit 앱 ======
st.set_page_config(page_title="팩트폭격랩 퇴사진단기 🔥", page_icon="🔥", layout="centered")
st.title("팩트폭격랩 퇴사진단기 🔥")
st.subheader("퇴사 고민? 팩트부터 조져보자.")

if "step" not in st.session_state:
    st.session_state.step = 1
if "user_answers" not in st.session_state:
    st.session_state.user_answers = []

def ask_question(prompt, key):
    st.write(prompt)
    return st.text_input("대답:", key=key)

if st.session_state.step == 1:
    answer = ask_question("퇴사 고민 있지? 왜 그렇게 빡쳤냐.", "first_answer")
    if answer:
        st.session_state.user_answers.append(answer)
        st.session_state.step = 2
elif st.session_state.step == 2:
    answer = ask_question("오케이. 니 경력 몇 년 차.", "second_answer")
    if answer:
        st.session_state.user_answers.append(answer)
        st.session_state.step = 3
elif st.session_state.step == 3:
    answer = ask_question("지금까지 무슨 일 했냐. 짧게.", "third_answer")
    if answer:
        st.session_state.user_answers.append(answer)
        st.session_state.step = 4
elif st.session_state.step == 4:
    answer = ask_question("써본 툴, 기술 뭐 있냐.", "forth_answer")
    if answer:
        st.session_state.user_answers.append(answer)
        st.session_state.step = 5
elif st.session_state.step == 5:
    answer = ask_question("연봉은 얼마 받고 싶냐.", "fifth_answer")
    if answer:
        st.session_state.user_answers.append(answer)
        st.session_state.step = 6
elif st.session_state.step == 6:
    if st.button("팩폭 분석 시작하기 ⚡"):
        with st.spinner("팩폭 분석 중..."):
            try:
                user_message = "\n".join(st.session_state.user_answers)
                prompt = f"""
[지침]
- '1. 2. 3.' 같은 목록 나열 절대 금지.
- 사람 말투처럼 자연스럽게 이어가되, 짧게 끊는 문장으로 팩트폭격해.
- 감정 위로나 착한 말투 절대 쓰지 마라. 친절 ❌, 싸늘하게 ❌, 무심하게 팩트만 말해.
- 이모티콘 금지.
- 현실 직격: 경력과 스킬을 냉정하게 평가하고, 시장 상황을 깔끔하게 박살내고, 끝에 현실 조언 한 줄로 정리해.
- 가능하면 확률(%)이나 예상 기간(개월) 같은 숫자도 자연스럽게 섞어줘.

[참고 예시 스타일]
“프로그래머로 5년 일했다고? 코드 퀄리티 보니까 유지보수 걱정 생긴다. 대충 넘길 스펙 아님.
지금 개발자 시장? 공고 하나에 지원자 수백 명 몰린다. 니 스킬셋으론 그냥 묻힌다.
신규 프로젝트 들어가고 싶으면, 코드부터 다시 닦고 최신 트렌드 따라잡아. 할 자신 없으면 그냥 현상유지나 해."

[분석할 유저 정보]
{user_message}
"""
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "유저 이력을 바탕으로 냉철한 피드백을 작성해"},
                        {"role": "user", "content": prompt}
                    ]
                )
                llm_answer = response.choices[0].message.content
                st.write(llm_answer)

            except Exception as e:
                st.error(f"오류 발생: {e}")

# ====== FastAPI 실행 ======
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8888, reload=True)
