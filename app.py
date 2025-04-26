# app.py
import streamlit as st
import requests

# 페이지 설정
st.set_page_config(page_title="팩트폭격랩 퇴사진단기 🔥", page_icon="🔥", layout="centered")

# 제목, 부제
st.title("팩트폭격랩 퇴사진단기 🔥")
st.subheader("퇴사 고민? 팩트부터 조져보자.")

# 상태 저장
if "step" not in st.session_state:
    st.session_state.step = 1
    st.session_state.answers = {}

# 질문 플로우 함수
def ask_question(prompt, key):
    st.markdown(f"### {prompt}")
    answer = st.text_input("대답:", key=key)
    if answer:
        st.session_state.answers[key] = answer
        st.session_state.step += 1

# 단계별 질문
if st.session_state.step == 1:
    ask_question("퇴사 고민 있지? 왜 그렇게 빡쳤냐.", "concern")

elif st.session_state.step == 2:
    ask_question("오케이. 니 경력 몇 년 차.", "experience_years")

elif st.session_state.step == 3:
    ask_question("지금까지 무슨 일 했냐. 짧게.", "job_summary")

elif st.session_state.step == 4:
    ask_question("써본 툴, 기술 뭐 있냐.", "skills")

elif st.session_state.step == 5:
    ask_question("연봉은 얼마 받고 싶냐.", "expected_salary")

elif st.session_state.step == 6:
    st.markdown("### 이력서 파일 있으면 올려라. 없으면 걍 넘어가라.")
    uploaded_file = st.file_uploader("이력서 업로드 (pdf/docx)", type=["pdf", "docx"])

    if st.button("팩폭 분석 시작하기 ⚡"):
        if len(st.session_state.answers) < 5:
            st.error("답변 다 입력하고 다시 눌러라.")
        else:
            with st.spinner("팩폭 분석 중..."):
                try:
                    files = {"resume": uploaded_file} if uploaded_file else None
                    data = {"user_message": " ".join(st.session_state.answers.values())}

                    response = requests.post(
                        "http://127.0.0.1:8888/analyze",
                        files=files,
                        data=data
                    )

                    if response.status_code == 200:
                        result = response.json()["result_json"]
                        st.success("팩폭 완료 ✅")

                        # 결과 해석
                        st.markdown(f"## 결과 ⚡")

                        # ❗ 여기 수정됨: job_change_possibility
                        st.markdown(f"👉 이직 성공 확률: **{result['job_change_possibility']}**")

                        st.markdown("✅ 강점 요약:")
                        for s in result["strengths"]:
                            st.markdown(f"- {s}")

                        st.markdown("❌ 약점 요약:")
                        for w in result["weaknesses"]:
                            st.markdown(f"- {w}")

                        st.markdown("📆 Action Plan:")
                        st.markdown(f"**3개월:** {', '.join(result['action_plan']['3_months'])}")
                        st.markdown(f"**6개월:** {', '.join(result['action_plan']['6_months'])}")
                        st.markdown(f"**12개월:** {', '.join(result['action_plan']['12_months'])}")

                    else:
                        st.error("서버 오류. 잠시 후 다시 시도해라.")

                except Exception as e:
                    st.error(f"오류 발생: {e}")
