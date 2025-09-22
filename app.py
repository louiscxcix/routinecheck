import os
import re

import google.generativeai as genai
import streamlit as st

# --- 1. Configuración básica de la página y adición de la ventana gráfica ---
st.set_page_config(
    page_title="Análisis de Rutina con IA",
    page_icon="✍️",
    layout="centered",
)
st.markdown(
    '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
    unsafe_allow_html=True,
)

# --- 2. Configuración de la clave de la API ---
try:
    # Obtiene la clave de la API desde los secretos de Streamlit Cloud.
    api_key = st.secrets["GEMINI_API_KEY"]
except (KeyError, FileNotFoundError):
    # Si estás en un entorno local o los secretos no están configurados, la solicita en la barra lateral.
    st.sidebar.warning("No se encontró la GEMINI_API_KEY. Por favor, introdúcela manualmente.")
    api_key = st.sidebar.text_input(
        "Introduce tu clave de la API de Google AI aquí.", type="password"
    )

if not api_key:
    st.info("Para usar la aplicación, por favor introduce tu clave de la API de Google AI.")
    st.stop()

genai.configure(api_key=api_key)


# --- 3. CSS personalizado ---
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
        </style>
    """,
        unsafe_allow_html=True,
    )


load_css()


# --- 4. Función para llamar al modelo de IA y analizar los resultados ---
def generate_routine_analysis(sport, routine_type, current_routine):
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"""
    ### Tarea ###
    **Muy importante: Tu respuesta será analizada automáticamente por un programa, por lo que debes seguir estrictamente el formato y los delimitadores especificados en el [Ejemplo de formato de salida] a continuación.**
    **El contenido del análisis debe ser conciso y centrarse en los puntos clave, omitiendo explicaciones innecesarias. Resume la longitud total aproximadamente un 20% más corta que antes.**
    Basándote en la información del atleta a continuación, genera los siguientes tres elementos **usando los delimitadores especificados**.
    **1. Tabla de análisis de la rutina:** Genera 5 líneas en el formato `Principio | Evaluación (Y/N/▲) | Razón en una línea`
    **2. Análisis general:** Incluye un 'Resumen de una línea' y una 'Explicación detallada' (resumida en 3-4 frases).
    **3. Propuesta de rutina v2.0:** Presenta un plan de acción concreto con un **título** para cada elemento. Usa `-` de Markdown para la lista. Ejemplo: `- **Respiración profunda y preparación (Control de energía):** Aléjate de la mesa...`
    ---
    **[Ejemplo de formato de salida]**
    :::ANALYSIS_TABLE_START:::
    [Acción] Consistencia del movimiento clave | ▲ | El intento de botar la pelota es bueno, pero el número de botes o la intensidad varían cada vez, faltando consistencia.
    [Acción] Control de energía | N | No se incluye una respiración consciente o un movimiento para controlar la tensión.
    [Cognitivo] Autoafirmación positiva e imaginería | Y | Se incluye claramente una parte donde se dicen palabras positivas a uno mismo.
    [Recuperación] Rutina de reenfoque | N | No hay un proceso para recuperarse después de un error o cuando la concentración se pierde.
    [Acción+Cognitivo] Autoelogio/Celebración | ▲ | Hay un pequeño gesto de apretar el puño, pero no es suficiente como un proceso significativo para internalizar el éxito.
    :::ANALYSIS_TABLE_END:::
    :::SUMMARY_START:::
    **Resumen de una línea:** Tiene una buena base cognitiva con autoafirmación positiva, pero necesita urgentemente una rutina de acción consistente y una estrategia de control de energía para respaldarla.
    **Explicación detallada:** La rutina actual está preparada 'mentalmente', pero le falta preparación 'física'. Sin una rutina de acción que controle la tensión física y cree movimientos consistentes, la probabilidad de cometer errores bajo presión es alta. Es crucial añadir una rutina de acción para alinear el estado mental y físico.
    :::SUMMARY_END:::
    :::ROUTINE_V2_START:::
    - **Respiración profunda y preparación (Control de energía):** Aléjate de la mesa, inhala por la nariz durante 3 segundos y exhala lentamente por la boca durante 5 segundos para estabilizar el ritmo cardíaco.
    - **Rutina de movimiento (Consistencia):** Desde una posición fija, bota la pelota exactamente **dos veces**. Esto actúa como un 'ancla' para bloquear pensamientos innecesarios.
    - **Rutina cognitiva (Autoafirmación):** (Manteniendo la fortaleza existente) Repite internamente la autoafirmación preparada ("Estoy listo").
    - **Ejecución y celebración (Autoelogio):** Tras un éxito, aprieta ligeramente el puño y di "¡Bien hecho!" para grabar la experiencia de éxito en el cerebro.
    :::ROUTINE_V2_END:::
    ---
    ### Información del atleta ###
    - Deporte: {sport}
    - Tipo de rutina: {routine_type}
    - Rutina actual: {current_routine}
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"ERROR:::{e}"


def format_results_to_html(result_text):
    # --- CSS para el nuevo diseño de la ventana de resultados ---
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
            error_message = result_text.replace('ERROR:::', '')
            return f"{new_style}<div id='capture-area'><div class='result-section'><div class='section-header'>❌ Error</div><div class='item-content'>Se produjo un error al contactar con la IA: {error_message}</div></div></div>"

        # Analiza las diferentes secciones
        analysis_table_str = re.search(r":::ANALYSIS_TABLE_START:::(.*?):::ANALYSIS_TABLE_END:::", result_text, re.DOTALL).group(1).strip()
        summary_full_str = re.search(r":::SUMMARY_START:::(.*?):::SUMMARY_END:::", result_text, re.DOTALL).group(1).strip()
        routine_v2_str = re.search(r":::ROUTINE_V2_START:::(.*?):::ROUTINE_V2_END:::", result_text, re.DOTALL).group(1).strip()

        # Analiza los datos en detalle
        summary_str = re.search(r"Resumen de una línea:\s*(.*?)\n", summary_full_str).group(1).strip()
        explanation_str = re.search(r"Explicación detallada:\s*(.*)", summary_full_str, re.DOTALL).group(1).strip()

        # --- 1. Genera el HTML para la tabla de análisis de la rutina ---
        html = f"{new_style}<div id='capture-area'>"
        html += "<div class='result-section'>"
        html += "<div class='section-header'>📊 Tabla de análisis de la rutina</div>"
        
        table_data = [line.split("|") for line in analysis_table_str.strip().split("\n") if "|" in line]
        
        for item, rating, comment in table_data:
            item, rating, comment = item.strip(), rating.strip(), comment.strip()
            icon = ""
            if "Y" in rating: icon = "✅"
            elif "▲" in rating: icon = "⚠️"
            elif "N" in rating: icon = "❌"
            
            html += f"""
            <div class='analysis-item'>
                <div class='item-title'>{item}</div>
                <div class='item-content'>{icon} <strong>{rating}:</strong> {comment}</div>
            </div>
            """
        html += "</div>"

        # --- 2. Genera el HTML para el análisis general ---
        html += f"""
        <div class='result-section'>
            <div class='section-header'>🎯 Resumen de una línea</div>
            <div class='item-content summary-line'>{summary_str}</div>
        </div>
        """
        html += f"""
        <div class='result-section'>
            <div class='section-header'>💬 Explicación detallada</div>
            <div class='item-content'>{explanation_str}</div>
        </div>
        """
        
        # --- 3. Genera el HTML para la propuesta de rutina v2.0 ---
        html += "<div class='result-section'>"
        html += "<div class='section-header'>💡 Propuesta de rutina v2.0</div>"
        
        routine_items = [line.strip()[2:] for line in routine_v2_str.split("\n") if line.strip().startswith("- ")]
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
        return f"{new_style}<div id='capture-area'><div class='result-section'><div class='section-header'>❌ Error de análisis</div><div class='item-content'>El formato de la respuesta de la IA no es el esperado y no se puede analizar automáticamente. Por favor, revisa la respuesta original a continuación.</div><pre style='white-space: pre-wrap; word-wrap: break-word; background-color: #f0f0f0; padding: 15px; border-radius: 8px;'>{result_text}</pre></div></div>"


# --- 5. Composición de la interfaz de usuario principal ---
st.markdown('<div class="header-icon">✍️</div>', unsafe_allow_html=True)
st.markdown('<p class="title">Análisis de Rutina con IA</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="subtitle">El poder de la rutina para dominar tu mente en el momento decisivo<br/>Tu entrenador de rutina con IA está aquí para ayudarte</p>',
    unsafe_allow_html=True,
)

with st.form("routine_form"):
    st.markdown(
        '<p class="input-label">¿Qué tipo de deportista eres?</p>', unsafe_allow_html=True
    )
    sport = st.selectbox(
        "Deporte",
        ("Tenis de mesa", "Fútbol", "Baloncesto", "Béisbol", "Golf", "Tenis", "Tiro con arco", "Otro"),
        label_visibility="collapsed",
    )

    st.markdown(
        '<p class="input-label">Describe el tipo de rutina</p>', unsafe_allow_html=True
    )
    routine_type = st.text_input(
        "Tipo de rutina",
        placeholder="Ej: Saque, tiro libre, bateo, putt, etc.",
        label_visibility="collapsed",
    )

    st.markdown(
        '<p class="input-label">Detalles de tu rutina actual</p>', unsafe_allow_html=True
    )
    current_routine = st.text_area(
        "Rutina actual",
        placeholder="Ej: Boto la pelota tres veces, respiro hondo una vez y luego lanzo.",
        height=140,
        label_visibility="collapsed",
    )

    st.write("")
    submitted = st.form_submit_button("Iniciar análisis detallado con IA", use_container_width=True)


if submitted:
    if not all([sport, routine_type, current_routine]):
        st.error("Por favor, completa todos los campos con precisión.")
    else:
        with st.spinner("El entrenador de IA está analizando tu rutina en detalle..."):
            st.session_state.analysis_result = generate_routine_analysis(
                sport, routine_type, current_routine
            )

if "analysis_result" in st.session_state and st.session_state.analysis_result:
    st.divider()
    result_html = format_results_to_html(st.session_state.analysis_result)

    # Botón para guardar la imagen y mostrar los resultados
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
        <div id="save-btn">Guardar resultados como imagen 📸</div>
    </div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
    <script>
    document.getElementById("save-btn").onclick = function() {{
        const captureElement = document.getElementById("capture-area");
        // Antes de capturar la imagen, desplázate a la parte superior para asegurar que toda el área sea visible
        window.scrollTo(0, 0); 
        setTimeout(() => {{
            html2canvas(captureElement, {{
                scale: 2, // Aumenta la resolución al doble para mayor nitidez
                backgroundColor: '#F1F2F5', // Especifica el color de fondo
                useCORS: true
            }}).then(canvas => {{
                const image = canvas.toDataURL("image/png");
                const link = document.createElement("a");
                link.href = image;
                link.download = "analisis-rutina-ia.png";
                link.click();
            }});
        }}, 200); // Un pequeño retardo para el renderizado
    }}
    </script>
    """
    st.components.v1.html(html_with_button, height=1200, scrolling=True)