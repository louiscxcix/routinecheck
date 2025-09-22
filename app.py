import os
import re
from PIL import Image

import google.generativeai as genai
import streamlit as st

# --- 1. 페이지 기본 설정 ---
try:
    page_icon = Image.open("icon.png")
except FileNotFoundError:
    page_icon = "✍️"

st.set_page_config(
    page_title="AI 루틴 분석",
    page_icon=page_icon,
    layout="centered",
)
st.markdown(
    '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
    unsafe_allow_html=True,
)
st.markdown( # 기본 Streamlit UI 요소들 숨기기
    """<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {padding-top: 2rem;}
    </style>""",
    unsafe_allow_html=True
)

# --- 2. API 키 설정 ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except (KeyError, FileNotFoundError):
    st.sidebar.warning("GEMINI_API_KEY를 찾을 수 없습니다. 직접 입력해주세요.")
    api_key = st.sidebar.text_input("여기에 Google AI API 키를 입력하세요.", type="password")

if not api_key:
    st.info("앱을 사용하려면 Google AI API 키를 입력해주세요.")
    st.stop()
genai.configure(api_key=api_key)


# --- 3. 커스텀 CSS (제공된 HTML 기반) ---
def load_css():
    st.markdown(
        """
        <style>
            :root {
                --Colors-Black: #0D1628;
                --Colors-Secondary: #86929A;
                --Colors-Gray-GrayF1: #F1F1F1;
                --Colors-Input-filed: rgba(12.55, 124.74, 162.74, 0.04);
            }
            .stApp, body {
                font-family: 'Helvetica', sans-serif;
                background-color: #FFFFFF; /* 배경 흰색으로 변경 */
            }
            .main .block-container {
                padding: 1.5rem;
            }

            /* 입력 UI 스타일 (기존 스타일 유지) */
            .input-label { color: var(--Colors-Black); font-size: 18px; font-weight: 700; margin-bottom: 12px; }
            .stTextInput > div > div > input, .stTextArea > div > div > textarea, .stSelectbox > div[data-baseweb="select"] > div {
                background-color: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 12px;
                box-shadow: none; color: var(--Colors-Black);
            }
            div[data-testid="stForm"] button[type="submit"] {
                width: 100%; padding: 16px 0 !important; font-size: 16px !important; font-weight: 600 !important;
                color: white !important; background: linear-gradient(135deg, #2BA7D1 0%, #1A8BB0 100%) !important;
                border: 2px solid #1A8BB0 !important; border-radius: 16px !important;
            }

            /* --- 결과창 스타일 (제공된 HTML 기반) --- */
            .results-container {
                display: flex;
                flex-direction: column;
                gap: 20px;
                margin-top: 30px;
            }
            .result-section {
                padding-bottom: 20px;
                border-bottom: 1px solid var(--Colors-Gray-GrayF1);
                display: flex;
                flex-direction: column;
                gap: 12px;
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
            
            /* 분석표 전용 스타일 */
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
                display: inline-block; /* 너비만큼만 배경색 적용되도록 */
                color: var(--Colors-Black);
                font-size: 13px;
                font-weight: 700;
                line-height: 20px;
                margin-top: 8px; /* 위 항목과 간격 */
            }
        </style>
    """, unsafe_allow_html=True)

load_css()


# --- 4. AI 모델 호출 및 결과 파싱 함수 ---
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

# --- HTML 생성 함수 (제공된 HTML 기반) ---
def format_results_to_html(result_text):
    try:
        # 데이터 파싱
        analysis_str = re.search(r":::ANALYSIS_TABLE_START:::(.*?):::ANALYSIS_TABLE_END:::", result_text, re.DOTALL).group(1).strip()
        explanation_str = re.search(r":::EXPLANATION_START:::(.*?):::EXPLANATION_END:::", result_text, re.DOTALL).group(1).strip()
        routine_v2_str = re.search(r":::ROUTINE_V2_START:::(.*?):::ROUTINE_V2_END:::", result_text, re.DOTALL).group(1).strip()

        # --- 1. 루틴 분석표 HTML ---
        analysis_html = ""
        summary_html = ""
        analysis_items = [line.split("|") for line in analysis_str.split("\n") if "|" in line]
        
        icon_map = {"Y": "✅", "▲": "⚠️", "N": "❌"}
        
        for item, rating, comment in analysis_items:
            item, rating, comment = item.strip(), rating.strip(), comment.strip()
            if "한 줄 요약" in item:
                summary_html = f"<p class='analysis-item-content'><span class='summary-title'>🎯 {item}</span><br/>{comment}</p>"
            else:
                icon = icon_map.get(rating, "")
                analysis_html += f"<p class='analysis-item-title'>{item}</p><p class='analysis-item-content'>{icon} {rating}: {comment}</p>"
        
        analysis_html += summary_html

        # --- 2. 상세 설명 HTML ---
        explanation_html = explanation_str.replace("\n", "<br/>")

        # --- 3. 루틴 v2.0 제안 HTML ---
        routine_items = [line.strip()[2:] for line in routine_v2_str.split("\n") if line.strip().startswith("- ")]
        routine_v2_html = "<br/>".join(routine_items)

        # --- 전체 HTML 결합 ---
        html = f"""
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
        return html
    except (AttributeError, IndexError) as e:
        return f"<div style='color:red;'>오류: AI 응답을 파싱할 수 없습니다. 형식을 확인해주세요.<br><pre>{result_text}</pre></div>"

# --- 5. 메인 UI 구성 ---
# 입력 부분 UI (HTML 직접 작성)
st.markdown("""
    <div style="display: flex; flex-direction: column; gap: 8px;">
        <div style="color: var(--Colors-Black, #0D1628); font-size: 20px; font-weight: 700; line-height: 32px;">AI 루틴 코치</div>
        <div style="color: var(--Colors-Secondary, #86929A); font-size: 13px; font-weight: 400; line-height: 20px;">승부의 순간, 마음을 다잡는 루틴의 힘<br/>AI 루틴 코치가 도와 드립니다</div>
    </div>
""", unsafe_allow_html=True)

# Streamlit 입력 폼
with st.form("routine_form"):
    st.markdown('<p class="input-label" style="margin-top: 20px;">어떤 종목의 선수이신가요?</p>', unsafe_allow_html=True)
    sport = st.selectbox("Sport", ("탁구", "축구", "농구", "야구", "골프", "테니스", "양궁", "기타"), label_visibility="collapsed")
    
    st.markdown('<p class="input-label">루틴의 종류를 적어주세요</p>', unsafe_allow_html=True)
    routine_type = st.text_input("Routine Type", placeholder="예: 서브, 자유투, 타석, 퍼팅 등", label_visibility="collapsed")
    
    st.markdown('<p class="input-label">현재 루틴 상세 내용</p>', unsafe_allow_html=True)
    current_routine = st.text_area("Current Routine", placeholder="예: 공을 세번 튀기고 심호흡 한번 후 슛", height=140, label_visibility="collapsed")
    
    submitted = st.form_submit_button("AI 정밀 분석 시작하기", use_container_width=True)

# 결과 출력
if submitted:
    if not all([sport, routine_type, current_routine]):
        st.error("모든 항목을 정확하게 입력해주세요.")
    else:
        with st.spinner("AI 코치가 당신의 루틴을 정밀 분석하고 있습니다..."):
            st.session_state.analysis_result = generate_routine_analysis(sport, routine_type, current_routine)

if "analysis_result" in st.session_state and st.session_state.analysis_result:
    result_html = format_results_to_html(st.session_state.analysis_result)
    st.markdown(result_html, unsafe_allow_html=True)