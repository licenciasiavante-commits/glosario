import streamlit as st
import json
import google.generativeai as genai
import re

# =====================================================================
# Aplicación Web: Generador de Glosarios Interactivos (Streamlit)
# Arquitectura: Cliente-Servidor (Serverless / Cloud Deployable)
# =====================================================================

st.set_page_config(page_title="Generador de Glosarios IA", page_icon="📚", layout="centered")

# --- PLANTILLA MAESTRA INCRUSTADA (Basada en tu glosario.html) ---
PLANTILLA_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{TITULO_DEL_GLOSARIO}}</title>
    
    <!-- Bootstrap 5.3 CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- Bootstrap Icons -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    <!-- Google Fonts: Inter -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">

    <style>
        :root {
            --custom-bg: #D4E0E4;           /* Fondo gris azulado suave */
            --custom-primary: #2A4A6A;      /* Azul petróleo oscuro corporativo */
            --custom-primary-light: #eaf0f3;
            --font-main: 'Inter', sans-serif;
            --feedback-success: #198754;
            --feedback-error: #dc3545;
        }

        body { background-color: var(--custom-bg); font-family: var(--font-main); color: #333; min-height: 100vh; }
        h1, h2, h3, .navbar-brand { color: var(--custom-primary); font-weight: 700; }
        .text-primary-custom { color: var(--custom-primary); }
        .nav-pills .nav-link { color: var(--custom-primary); background-color: rgba(255,255,255,0.5); margin: 0 5px; border-radius: 8px; font-weight: 600; transition: all 0.3s ease; }
        .nav-pills .nav-link.active { background-color: var(--custom-primary); color: white; box-shadow: 0 4px 6px rgba(42, 74, 106, 0.2); }
        .term-card { background: white; border: none; border-left: 4px solid var(--custom-primary); border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); transition: transform 0.2s; height: 100%; }
        .term-card:hover { transform: translateY(-2px); box-shadow: 0 6px 15px rgba(0,0,0,0.1); }
        .category-badge { background-color: var(--custom-primary-light); color: var(--custom-primary); font-size: 0.8rem; padding: 4px 8px; border-radius: 4px; font-weight: 600; display: inline-block; margin-bottom: 8px; }
        .flashcard-container { perspective: 1000px; height: 400px; width: 100%; max-width: 700px; margin: 0 auto; }
        .flashcard { position: relative; width: 100%; height: 100%; text-align: center; transition: transform 0.6s; transform-style: preserve-3d; cursor: pointer; display: grid; grid-template-columns: 1fr; }
        .flashcard.flipped { transform: rotateY(180deg); }
        .flashcard-front, .flashcard-back { grid-area: 1 / 1; width: 100%; height: 100%; backface-visibility: hidden; border-radius: 12px; box-shadow: 0 8px 20px rgba(0,0,0,0.1); background-color: white; padding: 2rem; display: flex; flex-direction: column; justify-content: center; align-items: center; overflow-y: auto; border: 1px solid rgba(42, 74, 106, 0.1); }
        .flashcard-front { border-bottom: 4px solid var(--custom-primary); }
        .flashcard-back { background-color: #fafbfd; transform: rotateY(180deg); border-top: 4px solid var(--custom-primary); text-align: left; align-items: flex-start; }
        .btn-primary-custom { background-color: var(--custom-primary); color: white; border: none; }
        .btn-primary-custom:hover { background-color: #1e364d; color: white; }
        .btn-outline-custom { color: var(--custom-primary); border-color: var(--custom-primary); }
        .btn-outline-custom:hover, .btn-outline-custom.active { background-color: var(--custom-primary); color: white; }
        .quiz-option { cursor: pointer; transition: all 0.2s; border: 2px solid #e9ecef; background: white; }
        .quiz-option:hover { border-color: var(--custom-primary); background-color: var(--custom-primary-light); }
        .quiz-option.correct { background-color: #d1e7dd !important; border-color: var(--feedback-success) !important; color: var(--feedback-success); }
        .quiz-option.incorrect { background-color: #f8d7da !important; border-color: var(--feedback-error) !important; color: var(--feedback-error); }
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: #f1f1f1; }
        ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
    </style>
</head>
<body class="p-3 p-md-4">

<div class="container mw-100">
    <!-- Header Dinámico -->
    <header class="d-flex flex-column flex-md-row justify-content-between align-items-center mb-4 pb-3 border-bottom border-dark-subtle">
        <div class="d-flex align-items-center gap-3">
            <i class="bi bi-journal-medical fs-1 text-primary-custom"></i>
            <div>
                <h1 class="h3 mb-0">{{TITULO_DEL_GLOSARIO}}</h1>
                <small class="text-muted">{{SUBTITULO_DEL_GLOSARIO}}</small>
            </div>
        </div>
        
        <ul class="nav nav-pills mt-3 mt-md-0" id="mainTab" role="tablist">
            <li class="nav-item" role="presentation"><button class="nav-link active" id="glossary-tab" data-bs-toggle="pill" data-bs-target="#glossary" type="button" role="tab"><i class="bi bi-list-columns me-1"></i> Glosario</button></li>
            <li class="nav-item" role="presentation"><button class="nav-link" id="flashcards-tab" data-bs-toggle="pill" data-bs-target="#flashcards" type="button" role="tab"><i class="bi bi-card-text me-1"></i> Flashcards</button></li>
            <li class="nav-item" role="presentation"><button class="nav-link" id="quiz-tab" data-bs-toggle="pill" data-bs-target="#quiz" type="button" role="tab"><i class="bi bi-check2-circle me-1"></i> Autoevaluación</button></li>
        </ul>
    </header>

    <!-- Contenido Principal -->
    <div class="tab-content" id="mainTabContent">
        
        <!-- PESTAÑA 1: GLOSARIO -->
        <div class="tab-pane fade show active" id="glossary" role="tabpanel">
            <div class="row mb-4">
                <div class="col-md-6 mb-2">
                    <div class="input-group">
                        <span class="input-group-text bg-white text-primary-custom border-end-0"><i class="bi bi-search"></i></span>
                        <input type="text" id="searchInput" class="form-control border-start-0" placeholder="Buscar término, definición...">
                    </div>
                </div>
                <div class="col-md-6">
                    <div id="categoryFilters" class="d-flex flex-wrap gap-2 justify-content-md-end">
                        <button class="btn btn-sm btn-primary-custom active" onclick="filterCategory('all')">Todos</button>
                    </div>
                </div>
            </div>
            <div id="termsGrid" class="row g-4"></div>
            <div id="noResults" class="text-center py-5 d-none">
                <i class="bi bi-emoji-frown fs-1 text-muted"></i>
                <p class="text-muted mt-2">No se encontraron conceptos que coincidan con tu búsqueda.</p>
            </div>
        </div>

        <!-- PESTAÑA 2: FLASHCARDS -->
        <div class="tab-pane fade" id="flashcards" role="tabpanel">
            <div class="d-flex flex-column align-items-center justify-content-center py-4">
                <div class="flashcard-container mb-4">
                    <div class="flashcard" id="flashcardElement" onclick="flipCard()">
                        <div class="flashcard-front">
                            <span class="badge bg-light text-dark mb-3" id="fcCategory">Categoría</span>
                            <h2 class="display-6 fw-bold text-primary-custom" id="fcTerm">Término</h2>
                            <p class="text-muted mt-3 small"><i class="bi bi-hand-index-thumb"></i> Toca para ver definición</p>
                        </div>
                        <div class="flashcard-back">
                            <h4 class="h5 text-primary-custom mb-3 border-bottom pb-2 w-100">Definición</h4>
                            <p id="fcDefinition" class="mb-3">Definición del término...</p>
                            <h4 class="h6 text-primary-custom mb-2 fw-bold"><i class="bi bi-star-fill text-warning me-1"></i> Importancia</h4>
                            <p id="fcImportance" class="small fst-italic mb-0">Importancia clínica...</p>
                        </div>
                    </div>
                </div>
                <div class="controls d-flex gap-3 align-items-center">
                    <button class="btn btn-outline-custom rounded-circle p-3" onclick="prevCard()"><i class="bi bi-arrow-left fs-4"></i></button>
                    <span class="fw-bold text-muted user-select-none" id="cardCounter">1 / X</span>
                    <button class="btn btn-outline-custom rounded-circle p-3" onclick="nextCard()"><i class="bi bi-arrow-right fs-4"></i></button>
                </div>
                <button class="btn btn-sm btn-link text-muted mt-3 text-decoration-none" onclick="shuffleCards()"><i class="bi bi-shuffle"></i> Barajar tarjetas</button>
            </div>
        </div>

        <!-- PESTAÑA 3: AUTOEVALUACIÓN -->
        <div class="tab-pane fade" id="quiz" role="tabpanel">
            <div class="row justify-content-center">
                <div class="col-lg-8">
                    <div id="quizStart" class="text-center py-5">
                        <i class="bi bi-clipboard-check fs-1 text-primary-custom mb-3"></i>
                        <h3 class="mb-3">Autoevaluación</h3>
                        <p class="text-muted mb-4">Pon a prueba tus conocimientos con hasta 10 preguntas aleatorias basadas en el glosario.</p>
                        <button class="btn btn-primary-custom btn-lg px-5" onclick="startQuiz()">Comenzar Test</button>
                    </div>
                    <div id="quizError" class="text-center py-5 d-none">
                        <div class="alert alert-warning">Insuficientes datos para generar el test. Se requieren al menos 4 términos en el glosario.</div>
                    </div>
                    <div id="quizContainer" class="d-none">
                        <div class="d-flex justify-content-between align-items-center mb-4">
                            <span class="badge bg-secondary" id="questionCounter">Pregunta 1</span>
                            <span class="fw-bold text-primary-custom">Puntuación: <span id="currentScore">0</span></span>
                        </div>
                        <div class="card border-0 shadow-sm p-4 mb-4">
                            <p class="text-muted small mb-2 text-uppercase fw-bold">Identifica el concepto</p>
                            <p class="lead mb-0" id="questionText">Texto de la definición...</p>
                        </div>
                        <div class="d-grid gap-3" id="answerOptions"></div>
                        <div id="feedbackArea" class="mt-4 text-center d-none">
                            <button class="btn btn-primary-custom px-4" onclick="nextQuestion()">Siguiente Pregunta <i class="bi bi-arrow-right"></i></button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Modal Resultados -->
<div class="modal fade" id="resultModal" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
            <div class="modal-header border-0"><h5 class="modal-title">Resultados del Test</h5><button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button></div>
            <div class="modal-body text-center py-4">
                <div class="display-1 fw-bold mb-3" id="finalScoreDisplay">0</div>
                <p class="lead mb-4" id="finalMessage">¡Buen trabajo!</p>
                <div class="d-grid gap-2">
                    <button class="btn btn-primary-custom" onclick="location.reload()">Reiniciar Aplicación</button>
                    <button class="btn btn-outline-custom" data-bs-dismiss="modal" onclick="startQuiz()">Repetir Test</button>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- INYECCIÓN SEGURA DE DATOS -->
<script id="glosario-data" type="application/json">
{{JSON_DATA_AQUI}}
</script>

<script>
    // -------------------------------------------------------------------------
    // 1. CARGA DE DATOS SEGUROS INYECTADOS POR PYTHON
    // -------------------------------------------------------------------------
    let terms = [];
    try {
        const dataNode = document.getElementById('glosario-data');
        if(dataNode && !dataNode.textContent.includes("JSON_DATA_AQUI")) {
            terms = JSON.parse(dataNode.textContent);
        } else {
            console.warn("Modo demo: Datos no inyectados por el servidor.");
        }
    } catch(e) {
        console.error("Error crítico de parseo del JSON inyectado.", e);
        alert("Hubo un error cargando los datos del glosario.");
    }

    // -------------------------------------------------------------------------
    // 2. LÓGICA DEL GLOSARIO
    // -------------------------------------------------------------------------
    const categories = [...new Set(terms.map(t => t.category))];
    
    function initGlossary() {
        if(terms.length === 0) return;
        const catContainer = document.getElementById('categoryFilters');
        categories.forEach(cat => {
            const btn = document.createElement('button');
            btn.className = 'btn btn-sm btn-outline-custom';
            btn.textContent = cat;
            btn.onclick = () => filterCategory(cat);
            catContainer.appendChild(btn);
        });
        renderTerms(terms);
        document.getElementById('searchInput').addEventListener('input', (e) => filterTerms(e.target.value));
    }

    function renderTerms(data) {
        const grid = document.getElementById('termsGrid');
        const noResults = document.getElementById('noResults');
        grid.innerHTML = '';
        if (data.length === 0) { noResults.classList.remove('d-none'); } 
        else {
            noResults.classList.add('d-none');
            data.forEach(item => {
                const col = document.createElement('div');
                col.className = 'col-md-6 col-lg-4';
                col.innerHTML = `
                    <div class="card term-card h-100 p-3">
                        <div><span class="category-badge">${item.category}</span><h5 class="fw-bold text-primary-custom">${item.term}</h5></div>
                        <p class="small text-muted mb-2">${item.definition}</p>
                        <p class="small border-top pt-2 mt-auto fst-italic text-secondary"><i class="bi bi-info-circle me-1"></i> ${item.importance}</p>
                    </div>`;
                grid.appendChild(col);
            });
        }
    }

    let currentCategory = 'all';
    function filterCategory(cat) {
        currentCategory = cat;
        const buttons = document.getElementById('categoryFilters').querySelectorAll('button');
        buttons.forEach(btn => {
            if ((cat === 'all' && btn.textContent === 'Todos') || btn.textContent === cat) {
                btn.classList.add('active', 'btn-primary-custom'); btn.classList.remove('btn-outline-custom');
            } else {
                btn.classList.remove('active', 'btn-primary-custom'); btn.classList.add('btn-outline-custom');
            }
        });
        filterTerms(document.getElementById('searchInput').value);
    }

    function filterTerms(text) {
        const lowerText = text.toLowerCase();
        const filtered = terms.filter(item => {
            const matchesCategory = currentCategory === 'all' || item.category === currentCategory;
            const matchesSearch = item.term.toLowerCase().includes(lowerText) || item.definition.toLowerCase().includes(lowerText) || item.importance.toLowerCase().includes(lowerText);
            return matchesCategory && matchesSearch;
        });
        renderTerms(filtered);
    }

    // -------------------------------------------------------------------------
    // 3. LÓGICA FLASHCARDS
    // -------------------------------------------------------------------------
    let fcIndex = 0;
    let fcList = [...terms];

    function initFlashcards() { if(fcList.length > 0) updateFlashcardUI(); }

    function updateFlashcardUI() {
        if(fcList.length === 0) return;
        const card = document.getElementById('flashcardElement');
        card.classList.remove('flipped');
        const item = fcList[fcIndex];
        document.getElementById('fcTerm').textContent = item.term;
        document.getElementById('fcDefinition').textContent = item.definition;
        document.getElementById('fcImportance').textContent = item.importance;
        document.getElementById('fcCategory').textContent = item.category;
        document.getElementById('cardCounter').textContent = `${fcIndex + 1} / ${fcList.length}`;
    }

    function flipCard() { document.getElementById('flashcardElement').classList.toggle('flipped'); }
    function nextCard() { fcIndex = (fcIndex < fcList.length - 1) ? fcIndex + 1 : 0; updateFlashcardUI(); }
    function prevCard() { fcIndex = (fcIndex > 0) ? fcIndex - 1 : fcList.length - 1; updateFlashcardUI(); }
    function shuffleCards() {
        for (let i = fcList.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [fcList[i], fcList[j]] = [fcList[j], fcList[i]]; }
        fcIndex = 0; updateFlashcardUI();
    }

    // -------------------------------------------------------------------------
    // 4. LÓGICA AUTOEVALUACIÓN (QUIZ)
    // -------------------------------------------------------------------------
    let currentQuestionIndex = 0, score = 0, quizQuestions = [];
    const MAX_QUESTIONS = 10;

    function initQuiz() {
        if (terms.length < 4) { // Cambiado a 4 para permitir 1 correcta + 3 distractores
            document.getElementById('quizStart').classList.add('d-none');
            document.getElementById('quizError').classList.remove('d-none');
        }
    }

    function startQuiz() {
        const availableIndices = Array.from({length: terms.length}, (_, i) => i);
        for (let i = availableIndices.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [availableIndices[i], availableIndices[j]] = [availableIndices[j], availableIndices[i]];
        }
        
        const numQuestions = Math.min(MAX_QUESTIONS, terms.length);
        const selectedIndices = availableIndices.slice(0, numQuestions);
        
        quizQuestions = selectedIndices.map(idx => {
            const correctTerm = terms[idx];
            let distractors = [];
            while(distractors.length < 3 && distractors.length < (terms.length - 1)) {
                const randIdx = Math.floor(Math.random() * terms.length);
                if (randIdx !== idx && !distractors.includes(terms[randIdx].term)) {
                    distractors.push(terms[randIdx].term);
                }
            }
            const options = [...distractors, correctTerm.term];
            for (let i = options.length - 1; i > 0; i--) {
                const j = Math.floor(Math.random() * (i + 1));
                [options[i], options[j]] = [options[j], options[i]];
            }
            return { question: correctTerm.definition, correctAnswer: correctTerm.term, options: options };
        });

        currentQuestionIndex = 0; score = 0;
        document.getElementById('quizStart').classList.add('d-none');
        document.getElementById('quizContainer').classList.remove('d-none');
        document.getElementById('currentScore').textContent = '0';
        showQuestion();
    }

    function showQuestion() {
        const q = quizQuestions[currentQuestionIndex];
        document.getElementById('questionCounter').textContent = `Pregunta ${currentQuestionIndex + 1}/${quizQuestions.length}`;
        document.getElementById('questionText').textContent = q.question;
        document.getElementById('feedbackArea').classList.add('d-none');
        
        const optsContainer = document.getElementById('answerOptions');
        optsContainer.innerHTML = '';
        q.options.forEach(opt => {
            const btn = document.createElement('div');
            btn.className = 'p-3 rounded quiz-option fw-semibold text-center';
            btn.textContent = opt;
            btn.onclick = () => handleAnswer(btn, opt, q.correctAnswer);
            optsContainer.appendChild(btn);
        });
    }

    function handleAnswer(element, selected, correct) {
        const allOpts = document.querySelectorAll('.quiz-option');
        allOpts.forEach(el => el.onclick = null);

        if (selected === correct) {
            element.classList.add('correct'); element.innerHTML += ' <i class="bi bi-check-circle-fill"></i>';
            score++; document.getElementById('currentScore').textContent = score;
        } else {
            element.classList.add('incorrect'); element.innerHTML += ' <i class="bi bi-x-circle-fill"></i>';
            allOpts.forEach(el => { if (el.textContent === correct) { el.classList.add('correct'); el.innerHTML += ' <i class="bi bi-check-circle-fill"></i>'; } });
        }

        document.getElementById('feedbackArea').classList.remove('d-none');
        const nextBtn = document.querySelector('#feedbackArea button');
        if (currentQuestionIndex === quizQuestions.length - 1) {
            nextBtn.innerHTML = 'Ver Resultados <i class="bi bi-trophy"></i>'; nextBtn.onclick = finishQuiz;
        } else {
            nextBtn.innerHTML = 'Siguiente Pregunta <i class="bi bi-arrow-right"></i>'; nextBtn.onclick = nextQuestion;
        }
    }

    function nextQuestion() { currentQuestionIndex++; showQuestion(); }

    function finishQuiz() {
        const modal = new bootstrap.Modal(document.getElementById('resultModal'));
        document.getElementById('finalScoreDisplay').textContent = `${score}/${quizQuestions.length}`;
        let msg = "";
        if (score === quizQuestions.length) msg = "¡Excelente! Dominas el tema a la perfección.";
        else if (score >= (quizQuestions.length * 0.7)) msg = "¡Muy bien! Tienes conocimientos sólidos.";
        else if (score >= (quizQuestions.length * 0.5)) msg = "Bien, pero repasa algunos conceptos en las flashcards.";
        else msg = "Sigue estudiando, ¡puedes mejorar!";
        document.getElementById('finalMessage').textContent = msg;
        modal.show();
    }

    document.addEventListener('DOMContentLoaded', () => { initGlossary(); initFlashcards(); initQuiz(); });

</script>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>"""

def extraer_glosario_con_ia(api_key, texto_apuntes):
    """
    Motor de extracción. Obliga al modelo a generar las 4 claves exactas 
    que requiere la arquitectura del glosario.html
    """
    genai.configure(api_key=api_key)
    modelo = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = f"""
    Eres un experto lexicógrafo médico y estructurador de datos educativos.
    Extrae los conceptos clave del siguiente texto y devuelve EXCLUSIVAMENTE un objeto JSON válido.
    
    Estructura OBLIGATORIA:
    {{
        "titulo_glosario": "Título general representativo (String)",
        "subtitulo_glosario": "Subtítulo descriptivo o área de estudio (String)",
        "terminos": [
            {{ 
                "category": "Categoría general (ej: Anatomía, Procedimientos) (String)", 
                "term": "El concepto clave o término (String)", 
                "definition": "Definición clara, académica y rigurosa (String)", 
                "importance": "Por qué es importante en la práctica clínica o su relevancia (String)" 
            }}
        ]
    }}
    
    Asegúrate de extraer la mayor cantidad de conceptos útiles posibles.
    Texto a analizar:
    {texto_apuntes}
    """
    
    response = modelo.generate_content(prompt)
    raw_text = response.text.strip()
    
    # Sanitización de seguridad (Remover marcas de markdown)
    if raw_text.startswith("```json"):
        raw_text = raw_text[7:-3].strip()
    elif raw_text.startswith("```"):
        raw_text = raw_text[3:-3].strip()
        
    # Extracción por Regex
    json_match = re.search(r'(\{.*\})', raw_text, re.DOTALL)
    if json_match:
        raw_text = json_match.group(1)
        
    return json.loads(raw_text)

# --- INTERFAZ DE USUARIO (STREAMLIT) ---

st.title("📚 Generador de Glosarios Interactivos")
st.markdown("Transforma textos, protocolos o temarios en una web de estudio con Glosario, Flashcards y Autoevaluación incorporada.")

with st.sidebar:
    st.header("⚙️ Configuración")
    st.info("Introduce tu API Key para activar el motor de extracción de Gemini.")
    api_key_input = st.text_input("Ingresa tu Google Gemini API Key", type="password")

st.subheader("Sube el contenido teórico")
uploaded_file = st.file_uploader("Selecciona un archivo .txt con temario o protocolos", type="txt")

if uploaded_file and api_key_input:
    texto = uploaded_file.getvalue().decode("utf-8")
    
    if st.button("🚀 Crear Glosario Interactivo", type="primary"):
        with st.spinner("Extrayendo conceptos anatómicos y clínicos..."):
            try:
                # 1. Extracción Estructurada IA
                datos_ia = extraer_glosario_con_ia(api_key_input, texto)
                
                titulo = datos_ia.get("titulo_glosario", "Glosario Médico")
                subtitulo = datos_ia.get("subtitulo_glosario", "Herramienta de Estudio")
                terminos_array = datos_ia.get("terminos", [])
                
                if not terminos_array:
                    st.error("La IA no pudo extraer términos del texto.")
                    st.stop()
                
                # 2. Inyección Determinista en el Servidor
                json_string_seguro = json.dumps(terminos_array, ensure_ascii=False)
                
                html_final = PLANTILLA_HTML.replace("{{TITULO_DEL_GLOSARIO}}", titulo)
                html_final = html_final.replace("{{SUBTITULO_DEL_GLOSARIO}}", subtitulo)
                html_final = html_final.replace("{{JSON_DATA_AQUI}}", json_string_seguro)
                
                st.success(f"¡Éxito! Se han extraído {len(terminos_array)} conceptos del tema: **{titulo}**.")
                
                # 3. Descarga del Artefacto
                nombre_archivo = f"glosario_{titulo.replace(' ', '_').lower()}.html"
                st.download_button(
                    label="📥 Descargar Glosario HTML (Para Moodle)",
                    data=html_final,
                    file_name=nombre_archivo,
                    mime="text/html"
                )
                
                with st.expander("🔍 Ver estructura JSON extraída (Debug)"):
                    st.json(datos_ia)
                    
            except Exception as e:
                st.error(f"Error durante el procesamiento. Detalle técnico: {str(e)}")
                
elif not api_key_input:
    st.warning("👈 Por favor, introduce tu API Key en la barra lateral.")