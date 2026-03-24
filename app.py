import streamlit as st
import easyocr
import numpy as np
from PIL import Image
import re
import streamlit.components.v1 as components
from google.cloud import firestore
from google.oauth2 import service_account
import json
from datetime import datetime
import pytz

# ─────────────────────────────────────────────
# CONFIGURAÇÃO DA PÁGINA
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Expedição SPA1",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
# CSS RESPONSIVO — MOBILE FIRST
# ─────────────────────────────────────────────
st.markdown("""
<style>
/* ── Imports ── */
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@400;500;700&display=swap');

/* ── Reset & Base ── */
#MainMenu, footer, header, .stDeployButton { visibility: hidden; display: none !important; }
html, body, [data-testid="stAppViewContainer"] { background: #0d0f14 !important; }
[data-testid="stAppViewContainer"] > .main { background: #0d0f14 !important; }
[data-testid="block-container"] { padding: 1rem 0.75rem 3rem !important; max-width: 900px !important; margin: 0 auto; }

/* ── Typography ── */
*, .stMarkdown, .stText, label, .stTextInput label, .stSelectbox label {
    font-family: 'IBM Plex Sans', sans-serif !important;
    color: #e2e8f0;
}

/* ── Topo / Header ── */
.xpt-header {
    background: linear-gradient(135deg, #111827 0%, #1a1f2e 100%);
    border: 1px solid #f97316;
    border-radius: 10px;
    padding: 1rem 1.25rem 0.75rem;
    margin-bottom: 1.25rem;
    position: relative;
    overflow: hidden;
}
.xpt-header::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, #f97316, #fb923c, #f59e0b);
}
.xpt-header-title {
    font-family: 'Bebas Neue', sans-serif !important;
    font-size: clamp(1.6rem, 5vw, 2.4rem) !important;
    letter-spacing: 2px;
    color: #f97316 !important;
    line-height: 1;
    margin: 0;
}
.xpt-header-sub {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.7rem !important;
    color: #94a3b8 !important;
    margin-top: 0.25rem;
    letter-spacing: 1px;
}
.xpt-badge {
    display: inline-block;
    background: rgba(249,115,22,0.15);
    border: 1px solid rgba(249,115,22,0.4);
    color: #fb923c !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.65rem;
    padding: 2px 8px;
    border-radius: 4px;
    letter-spacing: 1px;
    margin-top: 0.4rem;
}

/* ── Action Buttons ── */
div.stButton > button {
    font-family: 'IBM Plex Mono', monospace !important;
    font-weight: 600 !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.5px;
    border-radius: 6px !important;
    border: 1px solid #334155 !important;
    background: #1e2533 !important;
    color: #cbd5e1 !important;
    transition: all 0.15s ease !important;
    width: 100%;
    padding: 0.45rem 0.5rem !important;
    height: auto !important;
    min-height: 2.4rem !important;
}
div.stButton > button:hover {
    background: #293347 !important;
    border-color: #f97316 !important;
    color: #fb923c !important;
    transform: translateY(-1px);
}
div.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #ea580c, #f97316) !important;
    border-color: #f97316 !important;
    color: white !important;
}
div.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #c2410c, #ea580c) !important;
    color: white !important;
}
div.stButton > button[kind="secondary"] {
    background: rgba(239,68,68,0.12) !important;
    border-color: #ef4444 !important;
    color: #f87171 !important;
}
div.stButton > button[kind="secondary"]:hover {
    background: rgba(239,68,68,0.25) !important;
    color: #fca5a5 !important;
}

/* ── Inputs ── */
input[type="text"], textarea, [data-testid="stTextInput"] input {
    background: #161b27 !important;
    border: 1px solid #2d3748 !important;
    border-radius: 6px !important;
    color: #e2e8f0 !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.82rem !important;
    padding: 0.4rem 0.6rem !important;
    transition: border-color 0.15s;
}
input[type="text"]:focus, [data-testid="stTextInput"] input:focus {
    border-color: #f97316 !important;
    box-shadow: 0 0 0 2px rgba(249,115,22,0.15) !important;
}
[data-testid="stTextInput"] label, [data-testid="stSelectbox"] label {
    font-size: 0.68rem !important;
    font-weight: 600 !important;
    letter-spacing: 1px !important;
    text-transform: uppercase !important;
    color: #64748b !important;
    margin-bottom: 2px !important;
}
textarea {
    background: #161b27 !important;
    border: 1px solid #2d3748 !important;
    border-radius: 6px !important;
    color: #94a3b8 !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.75rem !important;
}
[data-testid="stTextArea"] label {
    font-size: 0.68rem !important;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: #64748b !important;
}

/* ── Selectbox ── */
[data-testid="stSelectbox"] > div > div {
    background: #161b27 !important;
    border: 1px solid #2d3748 !important;
    border-radius: 6px !important;
    color: #e2e8f0 !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.8rem !important;
}
[data-testid="stSelectbox"] svg { color: #64748b !important; }

/* ── Expander (Rota Card) ── */
[data-testid="stExpander"] {
    background: #111827 !important;
    border: 1px solid #1e293b !important;
    border-radius: 10px !important;
    margin-bottom: 0.75rem !important;
    overflow: hidden;
    transition: border-color 0.2s;
}
[data-testid="stExpander"]:hover {
    border-color: rgba(249,115,22,0.3) !important;
}
[data-testid="stExpander"] summary {
    background: #161b27 !important;
    padding: 0.7rem 1rem !important;
    border-radius: 10px 10px 0 0 !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    color: #cbd5e1 !important;
    letter-spacing: 0.5px;
    border-bottom: 1px solid #1e293b !important;
}
[data-testid="stExpander"] summary:hover {
    color: #f97316 !important;
    background: #1a2132 !important;
}
[data-testid="stExpander"] summary svg { color: #f97316 !important; }
[data-testid="stExpander"] > div > div { padding: 0.75rem 0.75rem 0.5rem !important; }

/* ── Divider ── */
hr { border-color: #1e293b !important; margin: 0.5rem 0 !important; }

/* ── File Uploader ── */
[data-testid="stFileUploader"] {
    background: #111827 !important;
    border: 1px dashed #334155 !important;
    border-radius: 8px !important;
    padding: 0.75rem !important;
}
[data-testid="stFileUploader"] label {
    color: #94a3b8 !important;
    font-size: 0.8rem !important;
}

/* ── Popover ── */
[data-testid="stPopover"] button {
    font-size: 0.75rem !important;
    padding: 0.35rem 0.5rem !important;
}

/* ── Spinner ── */
[data-testid="stSpinner"] { color: #f97316 !important; }

/* ── Section separator labels ── */
.section-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.62rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #475569;
    margin: 1.25rem 0 0.5rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.section-label::after {
    content: '';
    flex: 1;
    height: 1px;
    background: #1e293b;
}

/* ── Status chips ── */
.chip-pendente   { color: #fbbf24; font-weight: 600; }
.chip-finalizado { color: #34d399; font-weight: 600; }
.chip-cancel     { color: #f87171; font-weight: 600; }
.chip-em         { color: #60a5fa; font-weight: 600; }

/* ── WhatsApp button ── */
.wa-btn {
    width: 100%; background: #25D366; color: white;
    border: none; padding: 13px; border-radius: 8px;
    font-weight: 700; cursor: pointer; font-size: 0.9rem;
    letter-spacing: 0.5px; font-family: 'IBM Plex Mono', monospace;
    transition: background 0.2s;
}
.wa-btn:hover { background: #1ebe57; }

/* ── Responsive tweaks ── */
@media (max-width: 640px) {
    [data-testid="block-container"] { padding: 0.5rem 0.4rem 3rem !important; }
    .xpt-header { padding: 0.75rem 0.9rem 0.6rem; }
    [data-testid="stExpander"] summary { font-size: 0.75rem !important; }
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: #0d0f14; }
::-webkit-scrollbar-thumb { background: #334155; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #f97316; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# NOTIFICAÇÃO PÓS-SYNC
# ─────────────────────────────────────────────
if st.session_state.get('sync_ok'):
    st.toast("Sincronizado com a nuvem! ☁️✅", icon="🔄")
    st.session_state['sync_ok'] = False

# ─────────────────────────────────────────────
# DATA / TIMEZONE
# ─────────────────────────────────────────────
fuso_br = pytz.timezone('America/Sao_Paulo')
data_hoje = datetime.now(fuso_br).strftime('%d/%m/%Y')

# ─────────────────────────────────────────────
# FIREBASE
# ─────────────────────────────────────────────
@st.cache_resource
def get_db():
    key_dict = json.loads(st.secrets["firestore_key"])
    creds = service_account.Credentials.from_service_account_info(key_dict)
    return firestore.Client(credentials=creds, project=key_dict['project_id'])

db = get_db()

def salvar_no_firebase():
    db.collection("expedicao").document("config").set(st.session_state.dados_controle)

def carregar_do_firebase():
    doc = db.collection("expedicao").document("config").get()
    return doc.to_dict() if doc.exists else None

# ─────────────────────────────────────────────
# CALLBACKS
# ─────────────────────────────────────────────
def atualizar_ilha(rota):
    st.session_state.dados_controle[rota]['letra'] = st.session_state[f"l_{rota}"]
    salvar_no_firebase()

def atualizar_hora(rota):
    st.session_state.dados_controle[rota]['janela'] = st.session_state[f"h_{rota}"]
    salvar_no_firebase()

# ─────────────────────────────────────────────
# OCR
# ─────────────────────────────────────────────
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['pt'])

reader = load_ocr()

# ─────────────────────────────────────────────
# DADOS INICIAIS
# ─────────────────────────────────────────────
def organizar_dados(dados_brutos):
    ordem_fixa = ["EPA4", "EPA5", "ETO4", "EPA7", "EPA3", "EPA8"]
    dados_ordenados = {}
    for rota in ordem_fixa:
        if rota in dados_brutos:
            dados_ordenados[rota] = dados_brutos[rota]
    for rota in dados_brutos:
        if rota not in dados_ordenados:
            dados_ordenados[rota] = dados_brutos[rota]
    return dados_ordenados

if 'dados_controle' not in st.session_state:
    dados_nuvem = carregar_do_firebase()
    if dados_nuvem:
        st.session_state.dados_controle = organizar_dados(dados_nuvem)
    else:
        st.session_state.dados_controle = {
            "EPA4": {"local": "MARABA",       "janela": "12:00 às 14:00", "letra": "?", "veiculos": []},
            "EPA5": {"local": "GOIANESIA",    "janela": "12:00 às 14:00", "letra": "?", "veiculos": []},
            "ETO4": {"local": "PARAUAPEBAS",  "janela": "13:30 às 15:30", "letra": "?", "veiculos": []},
            "EPA7": {"local": "CANAA",        "janela": "13:30 às 15:30", "letra": "?", "veiculos": []},
            "EPA3": {"local": "PARAGOMINAS",  "janela": "14:30 às 16:30", "letra": "?", "veiculos": []},
            "EPA8": {"local": "MAE DO RIO",   "janela": "14:30 às 16:30", "letra": "?", "veiculos": []},
        }

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown(f"""
<div class="xpt-header">
    <div class="xpt-header-title">📦 XPT SPA1</div>
    <div class="xpt-header-sub">CONTROLE DE CARREGAMENTO · PM/MM</div>
    <span class="xpt-badge">EZEQUIEL MIRANDA</span>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# AÇÕES PRINCIPAIS
# ─────────────────────────────────────────────
st.markdown('<div class="section-label">Ações</div>', unsafe_allow_html=True)

col_sync, col_clear, col_add = st.columns([1, 1, 1], gap="small")

with col_sync:
    if st.button("🔄 Sincronizar", use_container_width=True, type="primary"):
        st.cache_data.clear()
        dados_novos = carregar_do_firebase()
        if dados_novos:
            st.session_state.dados_controle = organizar_dados(dados_novos)
            st.session_state['sync_ok'] = True
            st.rerun()

with col_clear:
    if st.button("🗑️ Limpar Tudo", use_container_width=True, type="secondary"):
        for rota in st.session_state.dados_controle:
            st.session_state.dados_controle[rota]["veiculos"] = []
            st.session_state.dados_controle[rota]["letra"] = "?"
            if "doca" in st.session_state.dados_controle[rota]:
                del st.session_state.dados_controle[rota]["doca"]
        salvar_no_firebase()
        st.toast("Dados limpos! 🗑️", icon="✅")
        st.rerun()

with col_add:
    with st.popover("➕ Nova Rota", use_container_width=True):
        nova_id  = st.text_input("ID da Rota (ex: EPA9)").upper()
        nova_cid = st.text_input("Cidade").upper()
        if st.button("Confirmar Adição"):
            if nova_id and nova_cid:
                st.session_state.dados_controle[nova_id] = {
                    "local": nova_cid, "janela": "00:00 às 00:00",
                    "letra": "?", "veiculos": []
                }
                salvar_no_firebase()
                st.rerun()

# ─────────────────────────────────────────────
# CABEÇALHO DO CARREGAMENTO
# ─────────────────────────────────────────────
st.markdown('<div class="section-label">Identificação</div>', unsafe_allow_html=True)
col_h1, col_h2 = st.columns([2, 1], gap="small")
with col_h1:
    titulo_geral = st.text_input("Título", "CARREGAMENTO PM", label_visibility="visible")
with col_h2:
    data_carregamento = st.text_input("Data", data_hoje)

# ─────────────────────────────────────────────
# UPLOAD + OCR
# ─────────────────────────────────────────────
st.markdown('<div class="section-label">Leitura de Print (OCR)</div>', unsafe_allow_html=True)
uploaded_file = st.file_uploader("Upload do Print", type=["jpg", "png", "jpeg"], label_visibility="collapsed")
if uploaded_file:
    img = Image.open(uploaded_file)
    if st.button("🔍 EXTRAIR DADOS", use_container_width=True, type="primary"):
        with st.spinner("Lendo print por destinos…"):
            resultados = reader.readtext(np.array(img), paragraph=False)

            def get_y_center(bbox):
                return (bbox[0][1] + bbox[2][1]) / 2

            linhas = []
            if resultados:
                resultados.sort(key=lambda x: get_y_center(x[0]))
                current_row = [resultados[0]]
                last_y = get_y_center(resultados[0][0])
                for res in resultados[1:]:
                    curr_y = get_y_center(res[0])
                    if abs(curr_y - last_y) < 25:
                        current_row.append(res)
                    else:
                        linhas.append(current_row)
                        current_row = [res]
                        last_y = curr_y
                linhas.append(current_row)

            padrao_placa = re.compile(r'[A-Z]{3}[0-9][A-Z0-9][0-9]{2}')

            for linha in linhas:
                linha.sort(key=lambda x: x[0][0][0])
                textos_linha = [item[1].strip().upper() for item in linha]
                texto_completo_linha = " ".join(textos_linha)

                rota_vinculada = None
                for id_rota, info in st.session_state.dados_controle.items():
                    destino = info['local'].upper()
                    if id_rota in texto_completo_linha or destino in texto_completo_linha:
                        rota_vinculada = id_rota
                        break

                if rota_vinculada:
                    for txt in textos_linha:
                        letra_limpa = re.sub(r'[^A-Z]', '', txt.replace("XPT", ""))
                        if 1 <= len(letra_limpa) <= 2:
                            st.session_state.dados_controle[rota_vinculada]["letra"] = letra_limpa
                            break
                    for txt in textos_linha:
                        clean_txt = txt.replace(" ", "").replace("-", "")
                        match = padrao_placa.search(clean_txt)
                        if match:
                            placa = match.group(0)
                            ja_existe = any(v['placa'] == placa for v in st.session_state.dados_controle[rota_vinculada]["veiculos"])
                            if not ja_existe:
                                st.session_state.dados_controle[rota_vinculada]["veiculos"].append(
                                    {"placa": placa, "status": "Pendente", "doca": ""}
                                )
                            break

            salvar_no_firebase()
            st.rerun()

# ─────────────────────────────────────────────
# ROTAS
# ─────────────────────────────────────────────
st.markdown('<div class="section-label">Rotas</div>', unsafe_allow_html=True)

STATUS_OPCOES = ["Pendente", "Finalizado", "Em Carregamento", "Cancelado", "Aguardando Carregamento"]

for rota, info in st.session_state.dados_controle.items():
    n_veic = len(info['veiculos'])
    n_ok   = sum(1 for v in info['veiculos'] if v['status'] == "Finalizado")
    label  = f"📍 {rota}  ·  Ilha {info['letra']}  ·  {info['local']}  ·  {n_ok}/{n_veic} ✔"

    with st.expander(label, expanded=True):

        # ── Cabeçalho da rota ──────────────────────
        c_l, c_h, c_a = st.columns([1, 2, 1], gap="small")
        c_l.text_input("Ilha", value=info['letra'],  key=f"l_{rota}", on_change=atualizar_ilha, args=(rota,))
        c_h.text_input("Hora", value=info['janela'], key=f"h_{rota}", on_change=atualizar_hora, args=(rota,))

        if c_a.button("➕ Placa", key=f"add_{rota}"):
            st.session_state.dados_controle[rota]['veiculos'].append(
                {"placa": "", "status": "Pendente", "doca": ""}
            )
            salvar_no_firebase()
            st.rerun()

        # ── Veículos ────────────────────────────────
        for idx, v in enumerate(info['veiculos']):

            # Mobile: 2 linhas. Desktop: 1 linha.
            # Linha 1: Placa | Doca | Status
            col_p, col_d, col_s = st.columns([2, 1, 2], gap="small")

            nova_p = col_p.text_input("Placa", v['placa'], key=f"p_{rota}_{idx}").upper()
            if nova_p != v['placa']:
                v['placa'] = nova_p
                salvar_no_firebase()

            if "doca" not in v:
                v["doca"] = ""
            nova_d = col_d.text_input("Doca", v['doca'], key=f"d_{rota}_{idx}").upper()
            if nova_d != v['doca']:
                v['doca'] = nova_d
                salvar_no_firebase()

            novo_s = col_s.selectbox(
                "Status", STATUS_OPCOES,
                index=STATUS_OPCOES.index(v['status']) if v['status'] in STATUS_OPCOES else 0,
                key=f"s_{rota}_{idx}"
            )
            if novo_s != v['status']:
                v['status'] = novo_s
                if novo_s == "Finalizado":
                    v['hora_finalizacao'] = datetime.now(fuso_br).strftime('%H:%M')
                elif "hora_finalizacao" in v:
                    del v['hora_finalizacao']
                salvar_no_firebase()

            # Linha 2: Mover | Excluir
            col_mv, col_ex, col_space = st.columns([1, 1, 3], gap="small")

            with col_mv:
                with st.popover("🔄 Mover", use_container_width=True):
                    for dest in st.session_state.dados_controle.keys():
                        if dest != rota:
                            if st.button(dest, key=f"mv_{rota}_{dest}_{idx}"):
                                st.session_state.dados_controle[dest]["veiculos"].append(v.copy())
                                info['veiculos'].pop(idx)
                                salvar_no_firebase()
                                st.rerun()

            with col_ex:
                if st.button("❌ Excluir", key=f"x_{rota}_{idx}", use_container_width=True):
                    info['veiculos'].pop(idx)
                    salvar_no_firebase()
                    st.rerun()

            st.divider()

# ─────────────────────────────────────────────
# WHATSAPP
# ─────────────────────────────────────────────
res_texto = f"*{titulo_geral} {data_carregamento}*\n\n"
tem_placa = False

for rota, info in st.session_state.dados_controle.items():
    v_validos = [v for v in info['veiculos'] if v['placa'].strip()]
    if v_validos:
        tem_placa = True
        res_texto += (
            f"*{rota}* ({info['local']}) ({info['janela']})\n"
            f"Letra: *{info['letra']}*\n"
        )
        for v in v_validos:
            status_emoji = {
                "Pendente":                "🟡",
                "Finalizado":              f"✅ {v.get('hora_finalizacao', '')}",
                "Cancelado":               "❌",
                "Aguardando Carregamento": "🕑",
                "Em Carregamento":         "⏳",
            }.get(v['status'], "🟡")

            texto_doca = f" [Doca: {v.get('doca', '')}]" if v.get('doca') else ""
            res_texto += f"🚚 {v['placa']}{texto_doca} - {v['status']} {status_emoji}\n"
        res_texto += "\n"

if tem_placa:
    st.markdown('<div class="section-label">Resumo WhatsApp</div>', unsafe_allow_html=True)
    st.text_area("Texto para copiar", res_texto, height=300, label_visibility="collapsed")

    js_code = f"""
    <script>
    function copiarTexto() {{
        const t = `{res_texto.replace("`", "\\`")}`;
        navigator.clipboard.writeText(t).then(() => {{
            const b = document.getElementById('wabtn');
            b.textContent = '✅ COPIADO!';
            setTimeout(() => b.textContent = '📋 COPIAR PARA WHATSAPP', 2000);
        }});
    }}
    </script>
    <button id="wabtn" class="wa-btn" onclick="copiarTexto()">📋 COPIAR PARA WHATSAPP</button>
    """
    components.html(f"<style>.wa-btn{{width:100%;background:#25D366;color:white;border:none;padding:13px;border-radius:8px;font-weight:700;cursor:pointer;font-size:0.9rem;letter-spacing:0.5px;font-family:monospace;transition:background 0.2s}}.wa-btn:hover{{background:#1ebe57}}</style>{js_code}", height=70)
