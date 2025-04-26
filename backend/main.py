from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from backend.gpt_service import analyze_user_message
from backend.resume_parser import extract_resume_text
from typing import Optional
import uvicorn
import os

app = FastAPI()

# 응답 모델
class AnalysisResult(BaseModel):
    result_json: dict

@app.post("/analyze", response_model=AnalysisResult)
async def analyze(
    user_message: str = Form(...),    # 자유 입력 텍스트
    resume: Optional[UploadFile] = File(None)  # 선택사항: 이력서 파일
):
    """
    사용자 자유 입력과 이력서 파일을 받아 GPT 분석 결과 반환
    """
    try:
        # 1. 이력서 파일 처리
        resume_text = ""
        if resume is not None and resume.filename != "":
            # 파일이 정상적으로 업로드된 경우만 처리
            file_location = f"temp_{resume.filename}"
            with open(file_location, "wb") as f:
                f.write(await resume.read())
            resume_text = extract_resume_text(file_location)
            os.remove(file_location)

        # 2. 자유 입력 + 이력서 텍스트 통합 → GPT 분석 요청
        result_json = await analyze_user_message(user_message, resume_text)

        return AnalysisResult(result_json=result_json)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8888, reload=True)
