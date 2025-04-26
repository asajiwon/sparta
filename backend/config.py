import os
from dotenv import load_dotenv

load_dotenv()  # .env 파일을 로드해서 환경변수로 등록

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
