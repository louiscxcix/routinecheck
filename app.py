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
    api_key = os.environ["GEMINI_API_KEY"]
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
            @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600;700&display=swap');

            .stApp {
                background: linear-gradient(135deg, #F8F9FC 0%, #F1F2F5 100%);
                font-family: 'Noto Sans KR', 'Inter', 'Helvetica', sans-serif;
            }
            .main .block-container { padding: 2rem 1.5rem; }
            .header-icon {
                background: linear-gradient(135deg, rgba(43, 167, 209, 0.15) 0%, rgba(98, 120, 246, 0.1) 100%);
                border-radius: 50%; width: 52px; height: 52px;
                display: flex; align-items: center; justify-content: center;
                font-size: 28px; margin-bottom: 12px;
                box-shadow: 0px 4px 12px rgba(43, 167, 209, 0.15);
            }
            .title { color: #0D1628; font-size: 24px; font-weight: 700; }
            .subtitle { color: #8692A2; font-size: 14px; margin-bottom: 30px; line-height: 1.6;}
            .input-label { color: #0D1628; font-size: 18px; font-weight: 700; margin-bottom: 12px; }

            .stTextInput > div > div > input, .stTextArea > div > div > textarea, .stSelectbox > div[data-baseweb="select"] > div {
                background-color: #FFFFFF;
                border: 1.5px solid #E5E7EB;
                border-radius: 12px;
                box-shadow: 0px 2px 8px rgba(0, 0, 0, 0.04);
                color: #0D1628;
                font-family: 'Noto Sans KR', sans-serif;
                transition: all 0.2s ease;
            }
            .stTextInput > div > div > input:focus, .stTextArea > div > div > textarea:focus {
                border-color: #2BA7D1;
                box-shadow: 0px 0px 0px 3px rgba(43, 167, 209, 0.1);
            }
            .stSelectbox > div[data-baseweb="select"] > div { height: 48px; display: flex; align-items: center; }
            .stTextArea > div > div > textarea { height: 140px; }

            div[data-testid="stForm"] button[type="submit"] {
                width: 100%;
                padding: 16px 0 !important;
                font-size: 16px !important;
                font-weight: 600 !important;
                color: white !important;
                background-color: #2BA7D1 !important;
                background-image: linear-gradient(135deg, rgba(98, 120.20, 246, 0.20) 0%, rgba(29, 48, 78, 0) 100%) !important;
                background: linear-gradient(135deg, rgba(98, 120.20, 246, 0.20) 0%, rgba(29, 48, 78, 0) 100%), #2BA7D1 !important;
                border: none !important;
                border-radius: 12px !important;
                box-shadow: 0px 5px 10px rgba(26, 26, 26, 0.10) !important;
                transition: all 0.3s ease !important;
                margin-top: 20px !important;
                font-family: 'Noto Sans KR', sans-serif !important;
                letter-spacing: -0.2px !important;
            }

            div[data-testid="stForm"] button[type="submit"]:hover,
            div[data-testid="stForm"] button[kind="primaryFormSubmit"]:hover,
            .stForm button[type="submit"]:hover,
            button[kind="primaryFormSubmit"]:hover {
                background-color: #1A8BB0 !important;
                background-image: linear-gradient(135deg, rgba(98, 120.20, 246, 0.30) 0%, rgba(29, 48, 78, 0) 100%) !important;
                background: linear-gradient(135deg, rgba(98, 120.20, 246, 0.30) 0%, rgba(29, 48, 78, 0) 100%), #1A8BB0 !important;
                border: none !important;
                box-shadow: 0px 6px 14px rgba(26, 26, 26, 0.15) !important;
                transform: translateY(-2px) !important;
            }
        </style>
    """,
        unsafe_allow_html=True,
    )


load_css()


# --- 4. AI 모델 호출 및 결과 파싱 함수 ---
def generate_routine_analysis(sport, routine_type, current_routine):
    model = genai.GenerativeModel("gemini-2.0-flash")
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
    # --- 새로운 결과창 디자인을 위한 CSS ---
    new_style = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Helvetica+Neue:wght@400;700&display=swap');
        
        #capture-area {
            font-family: 'Helvetica Neue', Helvetica, sans-serif;
            background: linear-gradient(315deg, rgba(77, 0, 200, 0.03) 0%, rgba(29, 48, 78, 0.03) 100%), white;
            border-radius: 24px;
            padding: 40px 16px;
            border: 1px solid rgba(33, 64, 131, 0.08);
        }
        .result-section {
            margin-bottom: 20px;
            padding-bottom: 20px;
            border-bottom: 1px solid #F1F1F1;
        }
        .result-section:last-child {
            margin-bottom: 0;
            padding-bottom: 0;
            border-bottom: none;
        }
        .section-header {
            color: #0D1628;
            font-size: 18px;
            font-weight: 700;
            line-height: 28px;
            margin-bottom: 12px;
        }
        .analysis-item {
            margin-bottom: 12px;
        }
        .item-title {
            color: #0D1628;
            font-size: 14px;
            font-weight: 700;
            line-height: 20px;
            margin-bottom: 4px;
        }
        .item-content {
            color: #86929A;
            font-size: 14px;
            font-weight: 400;
            line-height: 20px;
        }
        .item-content strong {
            color: #5A6472;
        }
        .summary-line {
            font-weight: bold;
            color: #5A6472;
        }
        .routine-v2-item {
             margin-bottom: 8px;
        }
    </style>
    """
    try:
        if result_text.startswith("ERROR:::"):
            error_message = result_text.replace("ERROR:::", "")
            return f"{new_style}<div id='capture-area'><div class='result-section'><div class='section-header'>❌ 오류</div><div class='item-content'>AI 호출 중 오류가 발생했습니다: {error_message}</div></div></div>"

        # 각 섹션별 데이터 파싱
        analysis_table_str = (
            re.search(
                r":::ANALYSIS_TABLE_START:::(.*?):::ANALYSIS_TABLE_END:::",
                result_text,
                re.DOTALL,
            )
            .group(1)
            .strip()
        )
        summary_full_str = (
            re.search(
                r":::SUMMARY_START:::(.*?):::SUMMARY_END:::", result_text, re.DOTALL
            )
            .group(1)
            .strip()
        )
        routine_v2_str = (
            re.search(
                r":::ROUTINE_V2_START:::(.*?):::ROUTINE_V2_END:::",
                result_text,
                re.DOTALL,
            )
            .group(1)
            .strip()
        )

        # 상세 데이터 파싱
        summary_str = (
            re.search(r"한 줄 요약:\s*(.*?)\n", summary_full_str).group(1).strip()
        )
        explanation_str = (
            re.search(r"상세 설명:\s*(.*)", summary_full_str, re.DOTALL)
            .group(1)
            .strip()
        )

        # --- 1. 루틴 분석표 HTML 생성 ---
        html = f"{new_style}<div id='capture-area'>"
        html += "<div class='result-section'>"
        html += "<div class='section-header'>📊 루틴 분석표</div>"

        table_data = [
            line.split("|")
            for line in analysis_table_str.strip().split("\n")
            if "|" in line
        ]

        for item, rating, comment in table_data:
            item, rating, comment = item.strip(), rating.strip(), comment.strip()
            icon = ""
            if "Y" in rating:
                icon = "✅"
            elif "▲" in rating:
                icon = "⚠️"
            elif "N" in rating:
                icon = "❌"

            html += f"""
            <div class='analysis-item'>
                <div class='item-title'>{item}</div>
                <div class='item-content'>{icon} <strong>{rating}:</strong> {comment}</div>
            </div>
            """
        html += "</div>"

        # --- 2. 종합 분석 HTML 생성 ---
        html += f"""
        <div class='result-section'>
            <div class='section-header'>🎯 한 줄 요약</div>
            <div class='item-content summary-line'>{summary_str}</div>
        </div>
        """
        html += f"""
        <div class='result-section'>
            <div class='section-header'>💬 상세 설명</div>
            <div class='item-content'>{explanation_str}</div>
        </div>
        """

        # --- 3. 루틴 v2.0 제안 HTML 생성 ---
        html += "<div class='result-section'>"
        html += "<div class='section-header'>💡 루틴 v2.0 제안</div>"

        routine_items = [
            line.strip()[2:]
            for line in routine_v2_str.split("\n")
            if line.strip().startswith("- ")
        ]
        for item in routine_items:
            match = re.match(r"\*\*(.*?)\*\*:\s*(.*)", item)
            if match:
                title, content = match.groups()
                html += f"<div class='routine-v2-item'><strong class='item-title'>{title}:</strong><span class='item-content'> {content}</span></div>"
            else:
                html += f"<div class='routine-v2-item item-content'>{item}</div>"

        html += "</div>"
        html += "</div>"
        return html

    except (AttributeError, IndexError):
        return f"{new_style}<div id='capture-area'><div class='result-section'><div class='section-header'>❌ 파싱 오류</div><div class='item-content'>AI의 답변 형식이 예상과 달라 자동으로 분석할 수 없습니다. 아래 원본 답변을 확인해주세요.</div><pre style='white-space: pre-wrap; word-wrap: break-word; background-color: #f0f0f0; padding: 15px; border-radius: 8px;'>{result_text}</pre></div></div>"


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
    {result_html}
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
