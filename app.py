import streamlit as st
import google.generativeai as genai
import re

# --- 1. 페이지 기본 설정 ---
st.set_page_config(
    page_title="AI 루틴 코치 v4.2",
    page_icon="🎯",
    layout="wide",
)

# --- 2. API 키 설정 ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except (KeyError, FileNotFoundError):
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


# --- 3. AI 모델 호출 함수 (프롬프트 최종 수정) ---
def generate_routine_analysis_v4_2(sport, routine_type, current_routine):
    """안정성을 극대화한 'One-shot' 프롬프트로 AI 호출"""
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
### 페르소나 ###
당신은 세계 최고의 선수들을 지도하는 스포츠 심리학자이자 멘탈 코치입니다.

### 과업 ###
**매우 중요: 당신의 답변은 프로그램에 의해 자동으로 분석되므로, 반드시 아래 [출력 형식 예시]에 명시된 출력 형식과 구분자를 정확히 지켜야 합니다.**

아래 선수 정보를 바탕으로, 다음 세 가지 내용을 **지정된 구분자(delimiter)를 사용하여** 생성하세요.

**1. 루틴 분석표:** `원칙 항목 | 평가 (Y/N/▲) | 한 줄 이유` 형태로 5줄 생성
**2. 종합 분석:** '한 줄 요약'과 '상세 설명' 포함
**3. 루틴 v2.0 제안:** 구체적인 실행 방안 제시

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
**상세 설명:** 현재 루틴은 '마음'만 앞서고 '몸'의 준비가 부족한 상태입니다. 인지적 루틴은 훌륭하지만, 신체적 긴장도를 조절하고 일관된 동작을 만들어주는 행동 루틴이 없다면 압박 상황에서 실수가 나올 확률이 높습니다. 행동 루틴을 추가하여 마음과 몸의 상태를 일치시키는 것이 중요합니다.
:::SUMMARY_END:::

:::ROUTINE_V2_START:::
**1. 심호흡 및 준비 (에너지 컨트롤):**
   - 테이블 뒤로 한 걸음 물러나 코로 3초간 숨을 들이마시고, 입으로 5초간 길게 내뱉습니다.
   - 이 과정을 통해 심박수를 안정시키고 시야를 넓힙니다.

**2. 동작 루틴 (일관성):**
   - 정해진 위치에서 공을 정확히 **두 번만** 튀깁니다.
   - 라켓을 한 바퀴 돌리며 그립을 다시 잡습니다. 이는 불필요한 생각을 차단하는 '앵커' 역할을 합니다.

**3. 인지 루틴 (자기암시):**
   - (기존의 장점 유지) 속으로 준비된 자기암시("나는 준비되었다. 자신있게 하자.")를 외칩니다.

**4. 실행 및 세리머니 (자기 칭찬):**
   - 서브를 넣고, 성공 시 가볍게 주먹을 쥐며 "좋았어!"라고 인정해줍니다. 이는 성공 경험을 뇌에 각인시키는 중요한 과정입니다.
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
        st.error(f"AI 호출 중 오류가 발생했습니다: {e}")
        return None

# --- 4. 결과 파싱 및 UI 표시 함수 (안정성 최종 강화 버전) ---
def display_results(result_text):
    """AI 결과 텍스트를 새로운 구분자(delimiter) 기준으로 파싱하여 표시"""
    try:
        # 새로운 구분자를 기준으로 각 섹션의 내용을 추출
        analysis_table_str = re.search(r":::ANALYSIS_TABLE_START:::(.*?):::ANALYSIS_TABLE_END:::", result_text, re.DOTALL).group(1).strip()
        summary_full_str = re.search(r":::SUMMARY_START:::(.*?):::SUMMARY_END:::", result_text, re.DOTALL).group(1).strip()
        routine_v2_str = re.search(r":::ROUTINE_V2_START:::(.*?):::ROUTINE_V2_END:::", result_text, re.DOTALL).group(1).strip()
        
        # 종합 분석 내용을 '한 줄 요약'과 '상세 설명'으로 분리
        summary_str = re.search(r"한 줄 요약:\s*(.*?)\n", summary_full_str).group(1).strip()
        explanation_str = re.search(r"상세 설명:\s*(.*)", summary_full_str, re.DOTALL).group(1).strip()
        
        # 탭 UI 구성
        tab1, tab2, tab3 = st.tabs(["📊 **루틴 분석표**", "📝 **종합 분석**", "💡 **루틴 v2.0 제안**"])

        with tab1:
            st.subheader("체크리스트")
            table_data = [line.split('|') for line in analysis_table_str.strip().split('\n') if '|' in line]
            
            for item, rating, comment in table_data:
                st.markdown(f"**{item.strip()}**")
                rating = rating.strip()
                comment = comment.strip()
                
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

    except (AttributeError, IndexError):
        st.error("AI의 답변 형식이 예상과 달라 자동으로 분석할 수 없습니다. 아래 원본 답변을 확인해주세요.")
        st.text_area("AI 원본 답변:", result_text, height=400)
    except Exception as e:
        st.error(f"결과를 표시하는 중 예상치 못한 오류가 발생했습니다: {e}")


# --- 5. 메인 UI 구성 ---
st.title("🎯 AI 루틴 코치 v4.2 (안정성 최종 강화)")
st.write("Y/N 분석의 명확함과 심층 분석의 깊이를 모두 담았습니다. 당신의 루틴을 객관적으로 점검하고 확실한 개선안을 받아보세요.")
st.divider()

with st.form("routine_form_v4_2"):
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
            analysis_result = generate_routine_analysis_v4_2(sport, routine_type, current_routine)
            st.session_state.analysis_result_v4_2 = analysis_result

if 'analysis_result_v4_2' in st.session_state and st.session_state.analysis_result_v4_2:
    st.divider()
    st.header("Step 2: AI 코칭 결과 확인하기")
    display_results(st.session_state.analysis_result_v4_2)