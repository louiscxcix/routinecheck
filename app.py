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
    # Streamlit Cloud의 Secrets에서 API 키를 가져옵니다.
    api_key = st.secrets["GEMINI_API_KEY"]
except (KeyError, FileNotFoundError):
    # 로컬 환경이나 Secrets가 설정되지 않은 경우 사이드바에서 입력받습니다.
    st.sidebar.warning("GEMINI_API_KEY를 찾을 수 없습니다. 직접 입력해주세요.")
    api_key = st.sidebar.text_input(
        "여기에 Google AI API 키를 입력하세요.", type="password"
    )

if not api_key:
    st.info("앱을 사용하려면 Google AI API 키를 입력해주세요.")
    st.stop()

genai.configure(api_key=api_key)


# --- 3. 커스텀 CSS ---
def load_css():
    st.markdown(
        """
        <style>
            .stApp { background-color: #F1F2F5; font-family: 'Helvetica', sans-serif; }
            .main .block-container { padding: 2rem 1.5rem; }
            .header-icon {
                background-color: rgba(43, 167, 209, 0.1); border-radius: 50%; width: 52px; height: 52px;
                display: flex; align-items: center; justify-content: center; font-size: 28px; margin-bottom: 12px;
            }
            .title { color: #0D1628; font-size: 24px; font-weight: 700; }
            .subtitle { color: #8692A2; font-size: 14px; margin-bottom: 30px; line-height: 1.6;}
            .input-label { color: #0D1628; font-size: 18px; font-weight: 700; margin-bottom: 12px; }

            .stTextInput > div > div > input, .stTextArea > div > div > textarea, .stSelectbox > div[data-baseweb="select"] > div {
                background-color: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 12px;
                box-shadow: none; color: #0D1628;
            }
            .stSelectbox > div[data-baseweb="select"] > div { height: 48px; display: flex; align-items: center; }
            .stTextArea > div > div > textarea { height: 140px; }

            div[data-testid="stForm"] button[type="submit"] {
                width: 100%;
                padding: 16px 0 !important;
                font-size: 16px !important;
                font-weight: 600 !important;
                color: white !important;
                background: linear-gradient(135deg, #2BA7D1 0%, #1A8BB0 100%) !important;
                border: 2px solid #1A8BB0 !important;
                border-radius: 16px !important;
                box-shadow: 0px 4px 12px rgba(43, 167, 209, 0.3) !important;
                transition: all 0.3s ease !important;
                margin-top: 20px !important;
            }

            div[data-testid="stForm"] button[type="submit"]:hover {
                background: linear-gradient(135deg, #1A8BB0 0%, #147A9D 100%) !important;
                border: 2px solid #147A9D !important;
                box-shadow: 0px 6px 16px rgba(43, 167, 209, 0.4) !important;
                transform: translateY(-2px) !important;
            }

            /* --- 여기가 수정된 결과창 스타일 --- */
            #capture-area { border-radius: 16px; background-color: #F1F2F5; padding-top: 1px; }
            .result-card {
                background-color: #ffffff;
                padding: 24px;
                border-radius: 16px;
                border: 1px solid #EAEBF0;
                margin-bottom: 20px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            }
            .result-header {
                display: flex;
                align-items: center;
                color: #0D1628;
                font-size: 20px;
                font-weight: 700;
                padding-bottom: 14px;
                margin-bottom: 18px;
                border-bottom: 1px solid #F1F1F1;
            }
            .result-header-icon {
                font-size: 22px;
                margin-right: 10px;
            }
            .analysis-item {
                margin-bottom: 16px;
            }
            .analysis-item:last-child {
                margin-bottom: 0;
            }
            .item-title {
                color: #0D1628;
                font-size: 16px;
                font-weight: 600;
                margin-bottom: 8px;
            }
            .alert {
                padding: 12px 16px;
                border-radius: 10px;
                font-size: 14px;
                line-height: 1.6;
                display: flex;
                align-items: center;
            }
            .alert .icon {
                font-size: 18px;
                margin-right: 10px;
            }
            .alert.success { background-color: #E6F6EC; color: #1E854A; border-left: 4px solid #4CAF50; }
            .alert.warning { background-color: #FFF9E6; color: #B38600; border-left: 4px solid #FFC107; }
            .alert.error   { background-color: #FDEDED; color: #A82A2A; border-left: 4px solid #F44336; }

            .summary-box, .explanation-box {
                 color: #5A6472; font-size: 15px; line-height: 1.7; padding: 12px; border-radius: 8px; background-color: #F8F9FA;
            }
            .summary-box { margin-bottom: 16px; }
            .summary-box .item-title, .explanation-box .item-title {
                 font-size: 16px; font-weight: 700; color: #2BA7D1; margin-bottom: 6px;
            }

            .routine-v2-list {
                list-style: none;
                padding-left: 0;
                counter-reset: step-counter;
            }
            .routine-v2-list li {
                counter-increment: step-counter;
                margin-bottom: 16px;
                padding: 16px;
                background-color: #F8F9FA;
                border-radius: 12px;
                border: 1px solid #EAEBF0;
                position: relative;
                padding-left: 50px;
            }
            .routine-v2-list li::before {
                content: counter(step-counter);
                position: absolute;
                left: 16px;
                top: 50%;
                transform: translateY(-50%);
                width: 28px;
                height: 28px;
                border-radius: 50%;
                background-color: #2BA7D1;
                color: white;
                font-weight: 700;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 14px;
            }
            .routine-v2-list li .step-title {
                font-weight: 700;
                color: #0D1628;
                font-size: 16px;
                margin-bottom: 6px;
            }
            .routine-v2-list li .step-content {
                font-size: 15px;
                color: #5A6472;
                line-height: 1.6;
            }
        </style>
    """,
        unsafe_allow_html=True,
    )


load_css()


# --- 4. AI 모델 호출 및 결과 파싱 함수 ---
def generate_routine_analysis(sport, routine_type, current_routine):
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"""
    ### 과업 ###
    **매우 중요: 당신의 답변은 프로그램에 의해 자동으로 분석되므로, 반드시 아래 [출력 형식 예시]에 명시된 출력 형식과 구분자를 정확히 지켜야 합니다.**
    **분석 내용은 불필요한 설명을 제외하고, 핵심 위주로 간결하게 작성해주세요. 전체적인 길이를 기존보다 약 20% 짧게 요약합니다.**
    아래 선수 정보를 바탕으로, 다음 세 가지 내용을 **지정된 구분자(delimiter)를 사용하여** 생성하세요.
    **1. 루틴 분석표:** `원칙 항목 | 평가 (Y/N/▲) | 한 줄 이유` 형태로 5줄 생성
    **2. 종합 분석:** '한 줄 요약'과 '상세 설명' (3~4 문장으로 요약) 포함
    **3. 루틴 v2.0 제안:** 각 항목에 **타이틀**을 포함하여 구체적인 실행 방안 제시. 목록에는 Markdown의 `-`를 사용하세요. 예: `- **심호흡 및 준비 (에너지 컨트롤):** 테이블 뒤로 물러나...`
    ---
    **[출력 형식 예시]**
    :::ANALYSIS_TABLE_START:::
    [행동] 핵심 동작의 일관성 | ▲ | 공을 튀기는 시도는 좋으나, 횟수나 강도가 매번 달라 일관성이 부족합니다.
    [행동] 에너지 컨트롤 | N | 긴장을 조절하기 위한 의식적인 호흡이나 동작이 포함되어 있지 않습니다.
    [인지] 긍정적 자기암시 및 이미지 상상 | Y | 스스로에게 긍정적인 말을 하는 부분이 명확하게 포함되어 있습니다.
    [회복] 재집중 루틴 | N | 실수했거나 집중이 흐트러졌을 때 돌아올 수 있는 과정이 없습니다.
    [행동+인지] 자기 칭찬/세리머니 | ▲ | 작게 주먹을 쥐는 행동은 있으나, 성공을 내재화하는 의미있는 과정으로는 부족합니다.
    :::ANALYSIS_TABLE_END:::
    :::SUMMARY_START:::
    **한 줄 요약:** 긍정적 자기암시라는 좋은 인지적 기반을 가지고 있으나, 이를 뒷받침할 일관된 행동 루틴과 에너지 조절 전략이 시급합니다.
    **상세 설명:** 현재 루틴은 '마음'의 준비는 되어있으나 '몸'의 준비가 부족한 상태입니다. 신체적 긴장도를 조절하고 일관된 동작을 만들어주는 행동 루틴이 없다면 압박 상황에서 실수가 나올 확률이 높습니다. 행동 루틴을 추가하여 마음과 몸의 상태를 일치시키는 것이 중요합니다.
    :::SUMMARY_END:::
    :::ROUTINE_V2_START:::
    - **심호흡 및 준비 (에너지 컨트롤):** 테이블 뒤로 물러나 코로 3초간 숨을 들이마시고, 입으로 5초간 길게 내뱉어 심박수를 안정시킵니다.
    - **동작 루틴 (일관성):** 정해진 위치에서 공을 정확히 **두 번만** 튀깁니다. 이는 불필요한 생각을 차단하는 '앵커' 역할을 합니다.
    - **인지 루틴 (자기암시):** (기존의 장점 유지) 속으로 준비된 자기암시("나는 준비되었다")를 외칩니다.
    - **실행 및 세리머니 (자기 칭찬):** 성공 시 가볍게 주먹을 쥐며 "좋았어!"라고 인정해 성공 경험을 뇌에 각인시킵니다.
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


def format_results_to_html(result_text):
    try:
        # 오류 발생 시 처리
        if result_text.startswith("ERROR:::"):
            return f"<div class='result-card'><div class='alert error'>AI 호출 중 오류가 발생했습니다: {result_text.replace('ERROR:::', '')}</div></div>"

        # 각 섹션별 데이터 파싱
        analysis_table_str = re.search(r":::ANALYSIS_TABLE_START:::(.*?):::ANALYSIS_TABLE_END:::", result_text, re.DOTALL).group(1).strip()
        summary_full_str = re.search(r":::SUMMARY_START:::(.*?):::SUMMARY_END:::", result_text, re.DOTALL).group(1).strip()
        routine_v2_str = re.search(r":::ROUTINE_V2_START:::(.*?):::ROUTINE_V2_END:::", result_text, re.DOTALL).group(1).strip()

        # 상세 데이터 파싱
        summary_str = re.search(r"한 줄 요약:\s*(.*?)\n", summary_full_str).group(1).strip()
        explanation_str = re.search(r"상세 설명:\s*(.*)", summary_full_str, re.DOTALL).group(1).strip().replace("\n", "<br>")

        # --- 1. 루틴 분석표 HTML 생성 ---
        html = "<div class='result-card'><div class='result-header'><span class='result-header-icon'>📊</span>루틴 분석표</div>"
        table_data = [line.split("|") for line in analysis_table_str.strip().split("\n") if "|" in line]
        
        for item, rating, comment in table_data:
            item, rating, comment = item.strip(), rating.strip(), comment.strip()
            rating_class, icon = "", ""
            if "Y" in rating:
                rating_class, icon = "success", "✅"
            elif "▲" in rating:
                rating_class, icon = "warning", "⚠️"
            elif "N" in rating:
                rating_class, icon = "error", "❌"
            
            html += f"""
            <div class='analysis-item'>
                <div class='item-title'>{item}</div>
                <div class='alert {rating_class}'>
                    <span class='icon'>{icon}</span>
                    <span><strong>{rating}:</strong> {comment}</span>
                </div>
            </div>
            """
        html += "</div>"

        # --- 2. 종합 분석 HTML 생성 ---
        html += f"""
        <div class='result-card'>
            <div class='result-header'><span class='result-header-icon'>📝</span>종합 분석</div>
            <div class='summary-box'>
                <div class='item-title'>🎯 한 줄 요약</div>
                <p>{summary_str}</p>
            </div>
            <div class='explanation-box'>
                <div class='item-title'>💬 상세 설명</div>
                <p>{explanation_str}</p>
            </div>
        </div>
        """
        
        # --- 3. 루틴 v2.0 제안 HTML 생성 ---
        routine_items = [line.strip()[2:] for line in routine_v2_str.split("\n") if line.strip().startswith("- ")]
        routine_v2_html = "<ol class='routine-v2-list'>"
        
        for item in routine_items:
            # **텍스트** 부분을 step-title로, 나머지를 step-content로 분리
            match = re.match(r"\\*\\*(.*?)\\*\\*:\s*(.*)", item)
            if match:
                title, content = match.groups()
                routine_v2_html += f"<li><div class='step-title'>{title}</div><div class='step-content'>{content}</div></li>"
            else:
                # 매칭되는 패턴이 없으면 전체를 content로 처리
                routine_v2_html += f"<li><div class='step-content'>{item}</div></li>"
        
        routine_v2_html += "</ol>"

        html += f"""
        <div class='result-card'>
            <div class='result-header'><span class='result-header-icon'>💡</span>루틴 v2.0 제안</div>
            {routine_v2_html}
        </div>
        """
        return html

    # 파싱 실패 시 예외 처리
    except (AttributeError, IndexError):
        return f"<div class='result-card'><div class='alert error'>AI의 답변 형식이 예상과 달라 자동으로 분석할 수 없습니다. 아래 원본 답변을 확인해주세요.</div><pre style='white-space: pre-wrap; word-wrap: break-word; background-color: #f0f0f0; padding: 15px; border-radius: 8px;'>{result_text}</pre></div>"


# --- 5. 메인 UI 구성 ---
st.markdown('<div class="header-icon">✍️</div>', unsafe_allow_html=True)
st.markdown('<p class="title">AI 루틴 분석</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="subtitle">승부의 순간, 마음을 다잡는 루틴의 힘<br/>AI 루틴 코치가 도와 드립니다</p>',
    unsafe_allow_html=True,
)

with st.form("routine_form"):
    st.markdown(
        '<p class="input-label">어떤 종목의 선수이신가요?</p>', unsafe_allow_html=True
    )
    sport = st.selectbox(
        "Sport",
        ("탁구", "축구", "농구", "야구", "골프", "테니스", "양궁", "기타"),
        label_visibility="collapsed",
    )

    st.markdown(
        '<p class="input-label">루틴의 종류를 적어주세요</p>', unsafe_allow_html=True
    )
    routine_type = st.text_input(
        "Routine Type",
        placeholder="예: 서브, 자유투, 타석, 퍼팅 등",
        label_visibility="collapsed",
    )

    st.markdown(
        '<p class="input-label">현재 루틴 상세 내용</p>', unsafe_allow_html=True
    )
    current_routine = st.text_area(
        "Current Routine",
        placeholder="예: 공을 세번 튀기고, 심호흡을 깊게 한번 하고 바로 슛을 쏩니다.",
        height=140,
        label_visibility="collapsed",
    )

    st.write("")
    submitted = st.form_submit_button("AI 정밀 분석 시작하기", use_container_width=True)


if submitted:
    if not all([sport, routine_type, current_routine]):
        st.error("모든 항목을 정확하게 입력해주세요.")
    else:
        with st.spinner("AI 코치가 당신의 루틴을 정밀 분석하고 있습니다..."):
            st.session_state.analysis_result = generate_routine_analysis(
                sport, routine_type, current_routine
            )

if "analysis_result" in st.session_state and st.session_state.analysis_result:
    st.divider()
    result_html = format_results_to_html(st.session_state.analysis_result)

    # 이미지 저장 버튼 및 결과 출력
    html_with_button = f"""
    <style>
        #save-btn {{
            width: 100%;
            background: #2BA7D1;
            color: white;
            border-radius: 12px;
            padding: 16px 0;
            font-size: 16px;
            font-weight: bold;
            border: none;
            box-shadow: 0px 5px 10px rgba(43, 167, 209, 0.2);
            cursor: pointer;
            text-align: center;
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
        // 이미지 캡쳐 전 스크롤을 최상단으로 이동하여 전체 영역이 보이도록 함
        window.scrollTo(0, 0); 
        setTimeout(() => {{
            html2canvas(captureElement, {{
                scale: 2, // 해상도 2배로 높여 선명하게 저장
                backgroundColor: '#F1F2F5', // 배경색 지정
                useCORS: true
            }}).then(canvas => {{
                const image = canvas.toDataURL("image/png");
                const link = document.createElement("a");
                link.href = image;
                link.download = "ai-routine-analysis.png";
                link.click();
            }});
        }}, 200); // 렌더링을 위한 약간의 지연 시간
    }}
    </script>
    """
    st.components.v1.html(html_with_button, height=1200, scrolling=True)