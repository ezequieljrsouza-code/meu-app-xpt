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

# Configuração da Página
st.set_page_config(page_title="Expedição SPA1", page_icon="🚚", layout="wide")

# --- NOME NO TOPO ---
st.markdown('<div style="text-align: right; color: grey; font-weight: bold;">Ezequiel Miranda</div>', unsafe_allow_html=True)

# --- ESTADOS PARA O WHATSAPP ---
if 'horario_inicio' not in st.session_state:
    st.session_state.horario_inicio = ""
if 'ciclo_finalizado' not in st.session_state:
    st.session_state.ciclo_finalizado = False

# --- 1. CONEXÃO COM FIREBASE ---
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

# --- 2. ESTILIZAÇÃO CSS (CORREÇÃO DOS CABEÇALHOS) ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .stDeployButton {display:none;}
    
    /* Estilização Geral dos Expanders */
    .stExpander {
        border-radius: 10px !important;
        margin-bottom: 15px !important;
        overflow: hidden;
    }
    
    /* Garante que o texto do cabeçalho seja sempre legível */
    .stExpander summary span, .stExpander summary p {
        color: white !important;
        font-weight: bold !important;
    }
    
    /* Ajuste para o ícone de seta do expander ficar branco */
    .stExpander summary svg {
        fill: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. TÍTULO PRINCIPAL ---
st.title("📦 Controle de Carregamento XPT SPA1")

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['pt'])
reader = load_ocr()

# --- 4. DADOS ---
if 'dados_controle' not in st.session_state:
    dados_nuvem = carregar_do_firebase()
    if dados_nuvem:
        st.session_state.dados_controle = dados_nuvem
    else:
        st.session_state.dados_controle = {
            "EPA4": {"local": "MARABA", "janela": "12:00 às 14:00", "letra": "?", "veiculos": []},
            "EPA5": {"local": "GOIANESIA", "janela": "12:00 às 14:00", "letra": "?", "veiculos": []},
            "ETO4": {"local": "PARAUAPEBAS", "janela": "13:30 às 15:30", "letra": "?", "veiculos": []},
            "EPA7": {"local": "CANAA", "janela": "13:30 às 15:30", "letra": "?", "veiculos": []},
            "EPA3": {"local": "PARAGOMINAS", "janela": "14:30 às 16:30", "letra": "?", "veiculos": []},
            "EPA8": {"local": "MAE DO RIO", "janela": "14:30 às 16:30", "letra": "?", "veiculos": []},
        }

# --- 5. EXIBIÇÃO DAS ROTAS ---
cores_config = {
    "EPA4": "#D00000", "EPA5": "#004B93", "ETO4": "#008F5A",
    "EPA7": "#D97706", "EPA3": "#6D28D9", "EPA8": "#2563EB"
}
cor_generica = "#475569"

for rota, info in st.session_state.dados_controle.items():
    cor = cores_config.get(rota, cor_generica)
    
    # CSS dinâmico que busca o texto da rota dentro do expander para pintar o fundo
    st.markdown(f"""
        <style>
        div[data-testid="stExpander"]:has(p:contains("{rota}")) summary {{
            background-color: {cor} !important;
            border: 1px solid {cor} !important;
        }}
        div[data-testid="stExpander"]:has(p:contains("{rota}")) {{
            border: 1px solid {cor} !important;
        }}
        </style>
    """, unsafe_allow_html=True)
    
    # Título que será buscado pelo CSS acima
    titulo_expander = f"📍 {rota} | {info['local']} | Ilha: {info['letra']}"
    
    with st.expander(titulo_expander, expanded=True):
        c1, c2, c3 = st.columns([1, 2, 1])
        
        info['letra'] = c1.text_input("Ilha", info['letra'], key=f"ilha_{rota}")
        info['janela'] = c2.text_input("Janela", info['janela'], key=f"jan_{rota}")

        if c3.button("➕ Veículo", key=f"btn_{rota}", use_container_width=True):
            info['veiculos'].append({"placa": "", "status": "Pendente", "doca": ""})
            salvar_no_firebase(); st.rerun()

        for idx, v in enumerate(info['veiculos']):
            col_p, col_d, col_s, col_x = st.columns([2, 1, 2, 0.5])
            v['placa'] = col_p.text_input("Placa", v['placa'], key=f"p_{rota}_{idx}").upper()
            v['doca'] = col_d.text_input("Doca", v.get('doca', ''), key=f"d_{rota}_{idx}").upper()
            
            opcoes = ["Pendente", "Em Carregamento", "Finalizado", "Aguardando Carregamento", "Cancelado"]
            v['status'] = col_s.selectbox("Status", opcoes, index=opcoes.index(v['status']) if v['status'] in opcoes else 0, key=f"s_{rota}_{idx}")
            
            if col_x.button("❌", key=f"del_{rota}_{idx}"):
                info['veiculos'].pop(idx); salvar_no_firebase(); st.rerun()
            st.divider()

# --- 6. WHATSAPP ---
st.divider()
fuso = pytz.timezone('America/Sao_Paulo')
texto_wa = f"*CARREGAMENTO - {datetime.now(fuso).strftime('%d/%m/%Y')}*\n\n"

for rota, info in st.session_state.dados_controle.items():
    if info['veiculos']:
        texto_wa += f"*{rota}* ({info['local']}) - Ilha: {info['letra']}\n"
        for v in info['veiculos']:
            texto_wa += f"🚚 {v['placa']} - {v['status']}\n"
        texto_wa += "\n"

js_code = f"""
<script>
function copiar() {{
    navigator.clipboard.writeText(`{texto_wa}`);
    alert("Copiado!");
}}
</script>
<button onclick="copiar()" style="width:100%; padding:15px; background:#25D366; color:white; border:none; border-radius:10px; cursor:pointer; font-weight:bold;">
    COPIAR PARA WHATSAPP
</button>
"""
components.html(js_code, height=800)
