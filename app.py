import os
import re

import google.generativeai as genai
import streamlit as st

# --- 1. 페이지 기본 설정 및 뷰포트 추가 ---
st.set_page_config(
    page_title="AI 루틴 분석",
    page_icon="✍️",
    layout="centered",
)
st.markdown(
    '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
    unsafe_allow_html=True,
)

# --- 2. API 키 설정 ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except (KeyError, FileNotFoundError):
    st.sidebar.warning("GEMINI_API_KEY를 찾을 수 없습니다. 직접 입력해주세요.")
    api_key = st.sidebar.text_input(
        "여기에 Google AI API 키를 입력하세요.", type="password"
    )

if not api_key:
    st.info("앱을 사용하려면 Google AI API 키를 입력해주세요.")
    st.stop()

genai.configure(api_key=api_key)


# --- 3. 커스텀 CSS (결과 창 디자인만 수정) ---
def load_css():
    st.markdown(
        """
        <style>
            /* --- 기존 스타일 유지 --- */
            :root {
                --Colors-Black: #0D1628;
                --Colors-Secondary: #86929A;
                --Colors-Gray-GrayF1: #F1F1F1;
                --app-bg-color: #F1F2F5;
            }
            .stApp { background-color: var(--app-bg-color); font-family: 'Helvetica', sans-serif; }
            .main .block-container { padding: 2rem 1.5rem; }
            .header-icon {
                background-color: rgba(43, 167, 209, 0.1); border-radius: 50%; width: 52px; height: 52px;
                display: flex; align-items: center; justify-content: center; font-size: 28px; margin-bottom: 12px;
            }
            .title { color: var(--Colors-Black); font-size: 24px; font-weight: 700; }
            .subtitle { color: var(--Colors-Secondary); font-size: 14px; margin-bottom: 30px; line-height: 1.6;}
            .input-label { color: var(--Colors-Black); font-size: 18px; font-weight: 700; margin-bottom: 12px; }
            .stTextInput > div > div > input, .stTextArea > div > div > textarea, .stSelectbox > div[data-baseweb="select"] > div {
                background-color: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 12px;
                box-shadow: none; color: var(--Colors-Black);
            }
            div[data-testid="stForm"] button[type="submit"] {
                width: 100%; padding: 16px 0 !important; font-size: 16px !important; font-weight: 600 !important;
                color: white !important; background: linear-gradient(135deg, #2BA7D1 0%, #1A8BB0 100%) !important;
                border: 2px solid #1A8BB0 !important; border-radius: 16px !important;
                box-shadow: 0px 4px 12px rgba(43, 167, 209, 0.3) !important;
            }

            /* --- 여기부터 결과 창 스타일 수정 --- */
            #capture-area { background-color: var(--app-bg-color); }
            .results-container {
                background-color: #FFFFFF;
                padding: 24px;
                border-radius: 16px;
                border: 1px solid #EAEBF0;
                box-shadow: 0 4px 12px rgba(0,0,0,0.05);
                display: flex;
                flex-direction: column;
                gap: 10px; /* 각 섹션 간의 간격 */
            }
            .result-section {
                padding-bottom: 20px;
                border-bottom: 1px solid var(--Colors-Gray-GrayF1);
                display: flex;
                flex-direction: column;
                gap: 12px;
            }
            .result-section:last-child {
                border-bottom: none;
                padding-bottom: 0;
            }
            .result-section-header {
                color: var(--Colors-Black);
                font-size: 18px;
                font-family: Helvetica;
                font-weight: 700;
                line-height: 28px;
            }
            .result-section-content {
                color: var(--Colors-Secondary);
                font-size: 13px;
                font-family: Helvetica;
                font-weight: 400;
                line-height: 20px;
            }
            .analysis-item-title {
                color: var(--Colors-Black);
                font-size: 13px;
                font-family: 'Helvetica Neue', Helvetica, sans-serif;
                font-weight: 700;
                line-height: 20px;
                margin: 0;
            }
            .analysis-item-content {
                color: var(--Colors-Secondary);
                font-size: 13px;
                font-family: 'Helvetica Neue', Helvetica, sans-serif;
                font-weight: 400;
                line-height: 20px;
                margin: 0;
            }
            .summary-title {
                color: var(--Colors-Black);
                font-weight: 700;
            }
        </style>
    """,
        unsafe_allow_html=True,
    )

load_css()


# --- 4. AI 모델 호출 및 결과 파싱 함수 (새 디자인에 맞게 프롬프트 수정) ---
def generate_routine_analysis(sport, routine_type, current_routine):
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"""
    ### 과업 ###
    **매우 중요: 당신의 답변은 프로그램에 의해 자동으로 분석되므로, 반드시 아래 [출력 형식 예시]에 명시된 출력 형식과 구분자를 정확히 지켜야 합니다.**
    **1. 루틴 분석표:** `항목명 | 평가 (Y/N/▲) | 한 줄 이유` 형태로 4줄 생성. 마지막 줄에는 `한 줄 요약 | | 요약 내용` 형식으로 생성.
    **2. 상세 설명:** 2~3 문장의 간결한 설명 생성.
    **3. 루틴 v2.0 제안:** 각 항목을 `항목명: 설명` 형식으로 생성. 목록에는 Markdown의 `-`를 사용.
    ---
    **[출력 형식 예시]**
    :::ANALYSIS_TABLE_START:::
    심호흡 | Y | 심호흡을 통해 긴장을 다소 완화하려는 시도는 긍정적입니다.
    공 튀기기 | ▲ | 횟수와 강도가 일정치 않아 일관성이 부족합니다. 집중력 저하의 원인이 될 수 있습니다.
    감각 확인 | N | 주관적인 감각에 의존하는 것은 객관성과 일관성을 해칠 수 있습니다. 명확한 기준이 필요합니다.
    긍정적 자기암시 | N | 명시적으로 언급되지 않았으나, 추가가 필요합니다.
    한 줄 요약 | | ** 심호흡은 좋으나, 공 튀기기의 불규칙성과 실패 대처 전략 부재로 일관성과 집중력 유지에 어려움이 있습니다.
    :::ANALYSIS_TABLE_END:::
    :::EXPLANATION_START:::
    현재 루틴은 너무 주관적이고 일관성이 부족합니다. 객관적인 동작과 긍정적 자기암시를 통합하고, 실패 상황에 대한 대처 방안을 마련해야 합니다. 경기 중 압박감에 대한 대비책이 미흡합니다.
    :::EXPLANATION_END:::
    :::ROUTINE_V2_START:::
    - 심호흡: 코로 깊게 3번 들이쉬고, 입으로 천천히 5번 내쉬는 것을 2회 반복합니다.
    - 공 튀기기: 정확히 3회 일정한 강도로 튀긴 후, 서브 자세를 취합니다.
    - 자기암시: "나는 최고의 서브를 할 수 있다" 라고 속으로 세 번 되뇌입니다.
    - 실패 대처: 실패 시, 잠시 눈을 감고 심호흡을 한 후 다시 자기암시를 하고 동작 루틴을 반복합니다.
    :::ROUTINE_V2_END:::
    ---
    ### 선수 정보 ###
    - 종목: {sport}
    - 루틴 종류: {routine_type}
    - 현재 루틴: {current_routine}
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"ERROR:::{e}"

# --- HTML 생성 함수 (새 디자인에 맞게 수정) ---
def format_results_to_html(result_text):
    try:
        analysis_str = re.search(r":::ANALYSIS_TABLE_START:::(.*?):::ANALYSIS_TABLE_END:::", result_text, re.DOTALL).group(1).strip()
        explanation_str = re.search(r":::EXPLANATION_START:::(.*?):::EXPLANATION_END:::", result_text, re.DOTALL).group(1).strip()
        routine_v2_str = re.search(r":::ROUTINE_V2_START:::(.*?):::ROUTINE_V2_END:::", result_text, re.DOTALL).group(1).strip()

        # 분석표 HTML 생성
        analysis_html = ""
        summary_html = ""
        analysis_items = [line.split("|") for line in analysis_str.split("\n") if "|" in line]
        icon_map = {"Y": "✅", "▲": "⚠️", "N": "❌"}
        for item, rating, comment in analysis_items:
            item, rating, comment = item.strip(), rating.strip(), comment.strip()
            if "한 줄 요약" in item:
                summary_html = f"<p class='analysis-item-content' style='margin-top: 8px;'><span class='summary-title'>🎯 {item}</span><br/>{comment}</p>"
            else:
                icon = icon_map.get(rating, "")
                analysis_html += f"<p class='analysis-item-title'>{item}</p><p class='analysis-item-content'>{icon} {rating}: {comment}</p>"
        analysis_html += summary_html

        # 상세 설명 및 v2.0 제안 HTML 생성
        explanation_html = explanation_str.replace("\n", "<br/>")
        routine_items = [line.strip()[2:] for line in routine_v2_str.split("\n") if line.strip().startswith("- ")]
        routine_v2_html = "<br/>".join(routine_items)

        # 전체 HTML 결합
        return f"""
        <div class="results-container">
            <div class="result-section">
                <div class="result-section-header">📊 루틴 분석표</div>
                <div class="result-section-content">{analysis_html}</div>
            </div>
            <div class="result-section">
                <div class="result-section-header">💬 상세 설명</div>
                <div class="result-section-content">{explanation_html}</div>
            </div>
            <div class="result-section">
                <div class="result-section-header">💡 루틴 v2.0 제안</div>
                <div class="result-section-content">{routine_v2_html}</div>
            </div>
        </div>
        """
    except (AttributeError, IndexError):
        # 파싱 실패 시 원래 코드의 에러 메시지 스타일을 유지하면서 내용 개선
        return f"<div style='background-color: #f8d7da; color: #721c24; padding: 1rem; border-radius: 12px; border: 1px solid #f5c6cb;'>" \
               f"<strong>오류 발생</strong><br>AI의 답변 형식이 예상과 달라 분석할 수 없습니다. 잠시 후 다시 시도해주세요." \
               f"<details><summary>상세 정보 보기</summary><pre style='white-space: pre-wrap; word-wrap: break-word;'>{result_text}</pre></details></div>"

# --- 5. 메인 UI 구성 (기존과 동일) ---
st.markdown('<div class="header-icon">✍️</div>', unsafe_allow_html=True)
st.markdown('<p class="title">AI 루틴 분석</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="subtitle">승부의 순간, 마음을 다잡는 루틴의 힘<br/>AI 루틴 코치가 도와 드립니다</p>',
    unsafe_allow_html=True,
)

with st.form("routine_form"):
    st.markdown('<p class="input-label">어떤 종목의 선수이신가요?</p>', unsafe_allow_html=True)
    sport = st.selectbox("Sport", ("탁구", "축구", "농구", "야구", "골프", "테니스", "양궁", "기타"), label_visibility="collapsed")
    st.markdown('<p class="input-label">루틴의 종류를 적어주세요</p>', unsafe_allow_html=True)
    routine_type = st.text_input("Routine Type", placeholder="예: 서브, 자유투, 타석, 퍼팅 등", label_visibility="collapsed")
    st.markdown('<p class="input-label">현재 루틴 상세 내용</p>', unsafe_allow_html=True)
    current_routine = st.text_area("Current Routine", placeholder="예: 공을 세번 튀기고, 심호흡을 깊게 한번 하고 바로 슛을 쏩니다.", height=140, label_visibility="collapsed")
    st.write("")
    submitted = st.form_submit_button("AI 정밀 분석 시작하기", use_container_width=True)

if submitted:
    if not all([sport, routine_type, current_routine]):
        st.error("모든 항목을 정확하게 입력해주세요.")
    else:
        with st.spinner("AI 코치가 당신의 루틴을 정밀 분석하고 있습니다..."):
            st.session_state.analysis_result = generate_routine_analysis(sport, routine_type, current_routine)

if "analysis_result" in st.session_state and st.session_state.analysis_result:
    st.divider()
    result_html = format_results_to_html(st.session_state.analysis_result)

    # 이미지 저장 버튼 및 결과 출력 (기존과 동일)
    html_with_button = f"""
    <style>
        #save-btn {{
            width: 100%; background: #2BA7D1; color: white; border-radius: 12px; padding: 16px 0;
            font-size: 16px; font-weight: bold; border: none;
            box-shadow: 0px 5px 10px rgba(43, 167, 209, 0.2); cursor: pointer; text-align: center;
        }}
        #save-btn:hover {{ background: #2490b3; }}
    </style>
    <div id="capture-area">{result_html}</div>
    <div style="margin-top: 20px;">
        <div id="save-btn">분석 결과 이미지로 저장 📸</div>
    </div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
    <script>
    document.getElementById("save-btn").onclick = function() {{
        const captureElement = document.getElementById("capture-area");
        window.scrollTo(0, 0);
        setTimeout(() => {{
            html2canvas(captureElement, {{
                scale: 2,
                backgroundColor: getComputedStyle(document.documentElement).getPropertyValue('--app-bg-color').trim(),
                useCORS: true
            }}).then(canvas => {{
                const image = canvas.toDataURL("image/png");
                const link = document.createElement("a");
                link.href = image;
                link.download = "ai-routine-analysis.png";
                link.click();
            }});
        }}, 200);
    }}
    </script>
    """
    st.components.v1.html(html_with_button, height=800, scrolling=True)