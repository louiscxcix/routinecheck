import streamlit as st
import google.generativeai as genai
import re

# --- 1. 페이지 기본 설정 ---
st.set_page_config(
    page_title="AI 루틴 코치 v5.0",
    page_icon="🏆",
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


# --- 3. AI 모델 호출 함수 ---
def generate_routine_analysis_v5(sport, routine_type, current_routine):
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

# --- 4. 결과 파싱 및 HTML 생성 함수 ---
def format_results_to_html(result_text):
    """AI 결과 텍스트를 파싱하여 이미지 저장이 가능한 단일 HTML 블록으로 생성"""
    try:
        # 각 섹션 내용 추출
        analysis_table_str = re.search(r":::ANALYSIS_TABLE_START:::(.*?):::ANALYSIS_TABLE_END:::", result_text, re.DOTALL).group(1).strip()
        summary_full_str = re.search(r":::SUMMARY_START:::(.*?):::SUMMARY_END:::", result_text, re.DOTALL).group(1).strip()
        routine_v2_str = re.search(r":::ROUTINE_V2_START:::(.*?):::ROUTINE_V2_END:::", result_text, re.DOTALL).group(1).strip()
        
        summary_str = re.search(r"한 줄 요약:\s*(.*?)\n", summary_full_str).group(1).strip()
        explanation_str = re.search(r"상세 설명:\s*(.*)", summary_full_str, re.DOTALL).group(1).strip()
        
        # HTML 컨텐츠 생성 시작
        html = "<h3>📊 루틴 분석표</h3>"
        table_data = [line.split('|') for line in analysis_table_str.strip().split('\n') if '|' in line]
        
        for item, rating, comment in table_data:
            item, rating, comment = item.strip(), rating.strip(), comment.strip()
            rating_class = ""
            icon = ""
            if "Y" in rating:
                rating_class = "success"
                icon = "✅"
            elif "▲" in rating:
                rating_class = "warning"
                icon = "⚠️"
            elif "N" in rating:
                rating_class = "error"
                icon = "❌"
            html += f"""
            <div class='analysis-item'>
                <strong>{item}</strong>
                <div class='alert {rating_class}'>{icon} <strong>{rating}:</strong> {comment}</div>
            </div>
            """

        html += f"""
        <hr>
        <h3>📝 종합 분석</h3>
        <div class='summary-box'>
            <strong>🎯 한 줄 요약</strong>
            <p>{summary_str}</p>
        </div>
        <div class='explanation-box'>
            <strong>💬 상세 설명</strong>
            <p>{explanation_str.replace('\\n', '<br>')}</p>
        </div>
        <hr>
        <h3>💡 루틴 v2.0 제안</h3>
        <div class='routine-box'>
            {routine_v2_str.replace('**', '<strong>').replace('**', '</strong>').replace('\\n', '<br>')}
        </div>
        """
        return html

    except (AttributeError, IndexError):
        return f"<div class='alert error'>AI의 답변 형식이 예상과 달라 자동으로 분석할 수 없습니다.</div><pre>{result_text}</pre>"

# --- 5. 메인 UI 구성 ---
st.title("🏆 AI 루틴 코치 v5.0")
st.write("하나의 결과창, 이미지 저장, 모바일 최적화로 더 편리해졌습니다. 당신의 루틴을 점검하고 확실한 개선안을 받아보세요.")
st.divider()

# --- 입력창 (세로 1단 구성) ---
with st.form("routine_form_v5"):
    st.header("Step 1: 당신의 루틴 알려주기")
    
    sport = st.selectbox('**1. 종목**', ('탁구', '축구', '농구', '야구', '골프', '테니스', '양궁', '기타'))
    routine_type = st.text_input('**2. 루틴 종류**', placeholder='예: 서브, 자유투, 타석')
    current_routine = st.text_area('**3. 현재 루틴 상세 내용**', placeholder='예: 공을 세 번 튀기고, 심호흡 한 번 하고 바로 슛을 쏩니다.', height=140)
    
    submitted = st.form_submit_button("AI 정밀 분석 시작하기", type="primary", use_container_width=True)

# --- 결과창 (통합 구성 및 이미지 저장) ---
if submitted:
    if not all([sport, routine_type, current_routine]):
        st.error("모든 항목을 정확하게 입력해주세요.")
    else:
        with st.spinner('AI 코치가 당신의 루틴을 정밀 분석하고 있습니다...'):
            analysis_result = generate_routine_analysis_v5(sport, routine_type, current_routine)
            st.session_state.analysis_result_v5 = analysis_result

if 'analysis_result_v5' in st.session_state and st.session_state.analysis_result_v5:
    st.divider()
    st.header("Step 2: AI 코칭 결과 확인하기")
    
    result_html = format_results_to_html(st.session_state.analysis_result_v5)

    # HTML과 자바스크립트를 포함한 최종 결과 컴포넌트
    html_with_button = f"""
    <div id="capture-area">
        {result_html}
    </div>
    
    <button id="save-btn">분석 결과 이미지로 저장 📸</button>

    <style>
        #capture-area {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji";
            padding: 20px;
            border: 1px solid #ddd;
            border-radius: 10px;
            background-color: #ffffff; /* 캡처 시 배경색 지정 */
        }}
        h3 {{ margin-top: 20px; border-bottom: 2px solid #ddd; padding-bottom: 5px;}}
        .analysis-item {{ margin-bottom: 15px; }}
        .alert {{
            padding: 10px;
            border-radius: 5px;
            margin-top: 5px;
        }}
        .alert.success {{ background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }}
        .alert.warning {{ background-color: #fff3cd; color: #856404; border: 1px solid #ffeeba; }}
        .alert.error {{ background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }}
        .summary-box, .explanation-box, .routine-box {{ margin-top: 10px; padding: 15px; border-radius: 5px; }}
        .summary-box {{ background-color: #e2e3e5; }}
        .explanation-box, .routine-box {{ background-color: #f8f9fa; }}
        #save-btn {{
            display: block;
            width: 100%;
            margin-top: 20px;
            padding: 15px;
            font-size: 18px;
            font-weight: bold;
            color: white;
            background-color: #007bff;
            border: none;
            border-radius: 10px;
            cursor: pointer;
        }}
        #save-btn:hover {{ background-color: #0056b3; }}
    </style>
    
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
    <script>
    document.getElementById("save-btn").onclick = function() {{
        const captureElement = document.getElementById("capture-area");
        html2canvas(captureElement, {{ scale: 2, backgroundColor: '#ffffff' }}).then(canvas => {{
            const image = canvas.toDataURL("image/png");
            const link = document.createElement("a");
            link.href = image;
            link.download = "ai-routine-analysis.png";
            link.click();
        }});
    }}
    </script>
    """
    
    st.components.v1.html(html_with_button, height=800, scrolling=True)