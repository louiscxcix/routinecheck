import streamlit as st
import google.generativeai as genai
import re
import pandas as pd

# --- 1. 페이지 기본 설정 ---
st.set_page_config(
    page_title="AI 루틴 코치 v4.0",
    page_icon="🎯",
    layout="wide",
)

# --- 2. API 키 설정 ---
try:
    # Streamlit 클라우드 배포 시 st.secrets에서 키를 로드합니다.
    api_key = st.secrets["GEMINI_API_KEY"]
except (KeyError, FileNotFoundError):
    # 로컬 환경 테스트를 위해 사이드바에서 키를 입력받습니다.
    st.sidebar.warning("API 키를 찾을 수 없습니다.")
    api_key = st.sidebar.text_input(
        "여기에 Google AI API 키를 입력하세요.", type="password",
        help="[Google AI Studio](https://aistudio.google.com/app/apikey)에서 API 키를 발급받을 수 있습니다."
    )

if api_key:
    genai.configure(api_key=api_key)
else:
    st.info("앱을 사용하려면 사이드바에서 Google AI API 키를 입력해주세요.")
    st.stop()


# --- 3. AI 모델 호출 함수 ---
def generate_routine_analysis_v4(sport, routine_type, current_routine):
    """'Y/N/▲' 평가 및 구조화된 심층 분석을 위한 프롬프트로 AI 호출"""
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
### 페르소나 ###
당신은 세계 최고의 선수들을 지도하는 스포츠 심리학자이자 멘탈 코치입니다. 당신의 임무는 선수의 루틴을 명확한 기준으로 분석하고, 선수의 노력을 인정하면서도 성장을 위한 구체적인 방향을 제시하는 것입니다.

### 분석 기준: 좋은 루틴의 5가지 원칙 ###
1. [행동] 핵심 동작의 일관성
2. [행동] 에너지 컨트롤
3. [인지] 긍정적 자기암시 및 이미지 상상
4. [회복] 재집중 루틴
5. [행동+인지] 자기 칭찬/세리머니

### 과업 ###
아래 선수 정보를 바탕으로, 다음 세 가지를 **반드시 지정된 형식에 맞춰** 단계별로 수행하세요.

**1. 루틴 분석표:**
- '좋은 루틴의 5가지 원칙' 각각에 대해 아래 세 가지 중 하나로 평가하세요.
  - **Y (있음):** 해당 요소가 명확하고 일관되게 존재함.
  - **N (없음):** 해당 요소가 전혀 존재하지 않음.
  - **▲ (개선 중):** 시도는 있으나, 불규칙적이거나 구체적이지 않음.
- 각 평가에 대한 **한 줄짜리 건설적인 이유**를 덧붙여주세요.
- 출력 형식: `원칙 항목 | 평가 (Y/N/▲) | 한 줄 이유` 형태로 5줄을 생성하세요.

**2. 종합 분석:**
- **한 줄 요약:** 현재 루틴의 핵심적인 강점과 가장 시급한 개선점을 한 문장으로 요약하세요.
- **상세 설명:** 위 분석표와 요약을 바탕으로, 선수가 자신의 루틴을 심리적으로 왜 개선해야 하는지, 어떤 효과를 기대할 수 있는지 상세히 설명하세요.

**3. 루틴 v2.0 제안:**
- 분석표에서 'N' 또는 '▲'로 평가된 항목을 중심으로, 구체적이고 실행 가능한 새로운 루틴을 제안하세요.

### 선수 정보 ###
- 종목: {sport}
- 루틴 종류: {routine_type}
- 현재 루틴: {current_routine}
"""
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"AI 호출 중 오류가 발생했습니다: {e}")
        return None

# --- 4. 결과 파싱 및 UI 표시 함수 (UI 개선 버전) ---
def display_results(result_text):
    """AI 결과 텍스트를 파싱하여 직관적인 UI로 표시"""
    try:
        # 섹션별로 텍스트 분리 (정규식 강화)
        analysis_table_str = re.search(r"1\. 루틴 분석표\s*\n(.*?)(?=\n\n2\.|\Z)", result_text, re.DOTALL).group(1)
        summary_str = re.search(r"한 줄 요약:\s*(.*?)\n", result_text).group(1)
        explanation_str = re.search(r"상세 설명:\s*(.*?)(?=\n\n3\.|\Z)", result_text, re.DOTALL).group(1)
        routine_v2_str = re.search(r"3\. 루틴 v2\.0 제안\s*\n(.*?)$", result_text, re.DOTALL).group(1)

        # 탭 UI 구성
        tab1, tab2, tab3 = st.tabs(["📊 **루틴 분석표**", "📝 **종합 분석**", "💡 **루틴 v2.0 제안**"])

        with tab1:
            st.subheader("체크리스트")
            st.write("AI가 5가지 원칙에 따라 당신의 루틴을 분석했습니다. 각 항목의 강점과 개선점을 확인해보세요.")
            
            # 분석표 파싱
            table_data = []
            for line in analysis_table_str.strip().split('\n'):
                parts = [p.strip() for p in line.split('|')]
                if len(parts) == 3:
                    table_data.append(parts)
            
            # 각 항목을 순회하며 시각적 UI 생성
            for item, rating, comment in table_data:
                st.markdown(f"**{item}**")
                
                if "Y" in rating:
                    st.success(f"✅ **{rating}:** {comment}", icon="✅")
                elif "▲" in rating:
                    st.warning(f"⚠️ **{rating}:** {comment}", icon="⚠️")
                elif "N" in rating:
                    st.error(f"❌ **{rating}:** {comment}", icon="❌")
                st.divider()

        with tab2:
            st.subheader("🎯 한 줄 요약")
            st.info(summary_str)
            st.subheader("💬 상세 설명")
            st.markdown(explanation_str)

        with tab3:
            st.subheader("🚀 당신을 위한 루틴 v2.0")
            st.markdown(routine_v2_str)

    except Exception as e:
        st.error("결과를 분석하는 중 오류가 발생했습니다. AI가 생성한 답변 형식이 다를 수 있습니다.")
        st.code(f"오류 내용: {e}")
        st.text_area("AI 원본 답변:", result_text, height=300)

# --- 5. 메인 UI 구성 ---
st.title("🎯 AI 루틴 코치 v4.0")
st.write("Y/N 분석의 명확함과 심층 분석의 깊이를 모두 담았습니다. 당신의 루틴을 객관적으로 점검하고 확실한 개선안을 받아보세요.")
st.divider()

with st.form("routine_form_v4"):
    st.header("Step 1: 당신의 루틴 알려주기")
    col1, col2 = st.columns(2)
    with col1:
        sport = st.selectbox('**1. 종목**', ('탁구', '축구', '농구', '야구', '골프', '테니스', '양궁', '기타'))
        routine_type = st.text_input('**2. 루틴 종류**', placeholder='예: 서브, 자유투, 타석')
    with col2:
        current_routine = st.text_area('**3. 현재 루틴 상세 내용**', placeholder='예: 공을 세 번 튀기고, 심호흡 한 번 하고 바로 슛을 쏩니다.', height=140)
    
    submitted = st.form_submit_button("AI 정밀 분석 시작하기", type="primary", use_container_width=True)

if submitted:
    if not all([sport, routine_type, current_routine]):
        st.error("모든 항목을 정확하게 입력해주세요.")
    else:
        with st.spinner('AI 코치가 당신의 루틴을 정밀 분석하고 있습니다...'):
            analysis_result = generate_routine_analysis_v4(sport, routine_type, current_routine)
            st.session_state.analysis_result_v4 = analysis_result

if 'analysis_result_v4' in st.session_state and st.session_state.analysis_result_v4:
    st.divider()
    st.header("Step 2: AI 코칭 결과 확인하기")
    display_results(st.session_state.analysis_result_v4)