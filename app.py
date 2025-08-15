import streamlit as st
import google.generativeai as genai

# --- 1. 페이지 기본 설정 ---
st.set_page_config(
    page_title="AI 루틴 코치 (심층분석 Ver.)",
    page_icon="💡",
    layout="wide",
    initial_sidebar_state="auto",
)

# --- 2. API 키 설정 (st.secrets 활용) ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except (KeyError, FileNotFoundError):
    st.sidebar.warning("API 키를 찾을 수 없습니다. 로컬 테스트를 위해 키를 직접 입력해주세요.")
    api_key = st.sidebar.text_input(
        "여기에 Google AI API 키를 입력하세요.", type="password",
        help="[Google AI Studio](https://aistudio.google.com/app/apikey)에서 API 키를 발급받을 수 있습니다."
    )

if api_key:
    genai.configure(api_key=api_key)
else:
    st.info("앱을 사용하려면 사이드바에서 Google AI API 키를 입력해주세요.")
    st.stop()


# --- 3. AI 모델 호출 함수 (프롬프트 전면 수정) ---
def generate_routine_analysis(sport, routine_type, current_routine):
    """Gemini API를 호출하여 루틴에 대한 심층 분석 및 개선안을 생성하는 함수"""
    model = genai.GenerativeModel('gemini-1.5-flash')

    # '강점 & 성장 기회' 분석 모델을 적용한 새로운 프롬프트
    prompt = f"""
### 페르소나 ###
당신은 세계 최고의 선수들을 지도하는 스포츠 심리학자이자 멘탈 코치입니다. 당신의 임무는 선수의 루틴을 분석하고, 심리학적 원리와 세계적인 선수들의 성공 사례를 바탕으로 최적의 루틴을 설계하는 것입니다. 당신의 코칭 스타일은 선수의 자신감을 북돋아 주는 **긍정적이고 건설적인 방식**입니다.

### 분석 기준: 좋은 루틴의 5가지 원칙 ###
1. [행동] 핵심 동작의 일관성 (순서, 시간)
2. [행동] 에너지 컨트롤 (심호흡, 긴장 완화 동작)
3. [인지] 긍정적 자기암시 및 이미지 상상
4. [회복] 재집중 루틴 (실수 후 마음을 다잡는 전략)
5. [행동+인지] 자기 칭찬/세리머니 (성공 경험 내재화)

### 참고 원칙: 세계적 선수들의 루틴 활용 ###
당신은 세계적인 선수들의 훈련법과 심리적 습관에 대한 방대한 지식을 가지고 있습니다. 사용자가 입력한 **'{sport}'** 종목과 관련된 유명 선수의 실제 루틴 사례를 **스스로 탐색하고 떠올려보세요.** 그들이 루틴을 통해 어떻게 집중력을 유지하고, 압박감을 이겨내는지 그 **핵심적인 심리 원칙**을 분석하여 코칭에 녹여내세요.

### 과업 ###
아래 선수 정보를 바탕으로, 다음 두 가지를 단계별로 명확하게 수행하세요.

1.  **심층 분석 (Strength & Opportunity Analysis):**
    * **절대 단순한 Y/N 평가를 사용하지 마세요.**
    * 대신, '좋은 루틴의 5가지 원칙' 각각에 대해 아래 형식으로 심층 분석을 제공하세요.
    * **강점 (Strength):** 선수의 현재 루틴에서 해당 원칙과 관련된 **긍정적인 요소**를 먼저 찾아 칭찬하고 인정해주세요. (예: "심호흡을 통해 긴장을 조절하려는 시도는 매우 좋은 출발점입니다.")
    * **성장 기회 (Opportunity):** 발견한 강점을 바탕으로, 루틴을 한 단계 더 발전시킬 수 있는 **구체적이고 실용적인 방법**을 제안하세요. (예: "여기에 '어깨 돌리기'를 추가하여 신체적 긴장을 완전히 해소하는 단계를 더하면 더욱 효과적일 것입니다.")

2.  **루틴 v2.0 제안:**
    * 위의 심층 분석을 종합하여, 선수를 위한 새롭고 강력한 **'루틴 v2.0'**을 완성된 형태로 제안해주세요. 각 단계가 왜 중요한지, 어떤 심리적 효과를 목표로 하는지 간략히 설명하여 선수가 완전히 이해하고 실행할 수 있도록 도와주세요.

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

# --- 4. 웹 앱 UI 구성 ---
st.title("💡 AI 루틴 코치 v3.0 (심층분석)")
st.write("당신의 루틴에 숨겨진 강점을 발견하고, 세계적인 선수들처럼 최고의 퍼포먼스를 발휘하기 위한 성장 기회를 찾아보세요.")
st.divider()

with st.form("routine_form_v3"):
    st.header("Step 1: 당신의 루틴 알려주기")

    col1, col2 = st.columns(2)
    with col1:
        sport = st.selectbox(
            '**1. 어떤 종목의 선수이신가요?**',
            ('탁구', '축구', '농구', '야구', '골프', '테니스', '양궁', '수영', '육상', '격투기', 'e스포츠', '기타')
        )
        routine_type = st.text_input(
            '**2. 어떤 상황의 루틴인가요?**',
            placeholder='예: 서브, 자유투, 타석, 페널티킥'
        )

    with col2:
        current_routine = st.text_area(
            '**3. 현재 루틴을 상세하게 알려주세요.**',
            placeholder='예: 공을 세 번 튀기고, 심호흡 한 번 하고, \'제발 들어가라\'고 생각하며 바로 슛을 쏩니다.',
            height=155
        )

    submitted = st.form_submit_button("AI 심층 분석 및 코칭 시작하기", type="primary", use_container_width=True)


if submitted:
    if not all([sport, routine_type, current_routine]):
        st.error("모든 항목을 정확하게 입력해주세요.")
    else:
        with st.spinner('AI 코치가 당신의 루틴에 숨겨진 강점을 분석하고 성장 기회를 찾고 있습니다...'):
            analysis_result = generate_routine_analysis(sport, routine_type, current_routine)
            st.session_state.analysis_result = analysis_result

if 'analysis_result' in st.session_state and st.session_state.analysis_result:
    st.divider()
    st.header("Step 2: AI 코칭 결과 확인하기")
    st.markdown(st.session_state.analysis_result)
    st.success("코칭이 완료되었습니다! 당신의 강점을 믿고, 제안된 성장 기회를 훈련에 적용해 보세요.")