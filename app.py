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

st.set_page_config(page_title="Expedição SPA1", layout="wide")

# --- NOME NO TOPO ---
st.markdown('<div style="text-align: right; color: grey; font-weight: bold;">Ezequiel Miranda</div>', unsafe_allow_html=True)

# --- 1. NOTIFICAÇÃO PÓS-SYNC ---
if st.session_state.get('sync_ok'):
    st.toast("Sincronizado com a nuvem com sucesso! ☁️✅", icon="🔄")
    st.session_state['sync_ok'] = False

# --- 2. DATA AUTOMÁTICA (Brasília) ---
fuso_br = pytz.timezone('America/Sao_Paulo')
data_hoje = datetime.now(fuso_br).strftime('%d/%m/%Y')

# --- 3. CONEXÃO COM FIREBASE ---
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

# --- 4. FUNÇÕES DE CALLBACK (UPDATE RÁPIDO) ---
def atualizar_ilha(rota):
    novo_valor = st.session_state[f"l_{rota}"]
    st.session_state.dados_controle[rota]['letra'] = novo_valor
    salvar_no_firebase()

def atualizar_hora(rota):
    novo_valor = st.session_state[f"h_{rota}"]
    st.session_state.dados_controle[rota]['janela'] = novo_valor
    salvar_no_firebase()

# --- 5. ESTILIZAÇÃO CSS ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .stDeployButton {display:none;}
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) button[kind="secondary"] {
        background-color: #ff4b4b !important; color: white !important; border: none !important;
    }
    div.stButton > button:first-child[kind="primary"] {
        background-color: #007bff !important; border: none;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 6. TÍTULO PRINCIPAL ---
st.title("📦 Controle de Carregamento XPT SPA1 - PM")
st.write(f"Autor: **Ezequiel Miranda**")

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['pt'])

reader = load_ocr()

# --- 7. INICIALIZAÇÃO DE DADOS ---
if 'dados_controle' not in st.session_state:
    dados_nuvem = carregar_do_firebase()
    if dados_nuvem:
        ordem_desejada = ["EPA4", "EPA5", "ETO4", "EPA7", "EPA3", "EPA8"]
        extras = [r for r in dados_nuvem.keys() if r not in ordem_desejada]
        st.session_state.dados_controle = {rota: dados_nuvem[rota] for rota in (ordem_desejada + extras) if rota in dados_nuvem}
    else:
        st.session_state.dados_controle = {
            "EPA4": {"local": "Marabá", "janela": "12:00 às 14:00", "letra": "?", "veiculos": []},
            "EPA5": {"local": "Goianésia", "janela": "12:00 às 14:00", "letra": "?", "veiculos": []},
            "ETO4": {"local": "Parauapebas", "janela": "13:30 às 15:30", "letra": "?", "veiculos": []},
            "EPA7": {"local": "Canaã", "janela": "13:30 às 15:30", "letra": "?", "veiculos": []},
            "EPA3": {"local": "Paragominas", "janela": "14:30 às 16:30", "letra": "?", "veiculos": []},
            "EPA8": {"local": "Mãe do Rio", "janela": "14:30 às 16:30", "letra": "?", "veiculos": []},
        }

# --- 8. BOTÕES DE AÇÃO ---
col_sync, col_clear, col_add = st.columns([1, 1, 1])
with col_sync:
    if st.button("🔄 Sincronizar", use_container_width=True, type="primary"):
        st.cache_data.clear()
        dados_novos = carregar_do_firebase()
        if dados_novos:
            st.session_state.dados_controle = dados_novos
            st.session_state['sync_ok'] = True
            st.rerun()

with col_clear:
    if st.button("🗑️ Limpar Tudo", use_container_width=True, type="secondary"):
        for rota in st.session_state.dados_controle:
            st.session_state.dados_controle[rota]["veiculos"] = []
        salvar_no_firebase()
        st.rerun()

with col_add:
    with st.popover("➕ Nova Rota", use_container_width=True):
        nova_id = st.text_input("ID da Rota (ex: EPA9)").upper()
        nova_cid = st.text_input("Cidade")
        if st.button("Confirmar Adição"):
            if nova_id and nova_cid:
                st.session_state.dados_controle[nova_id] = {"local": nova_cid, "janela": "00:00 às 00:00", "letra": "?", "veiculos": []}
                salvar_no_firebase()
                st.rerun()

# --- 9. CABEÇALHO ---
col_h1, col_h2 = st.columns(2)
with col_h1:
    titulo_geral = st.text_input("Título", "CARREGAMENTO PM")
with col_h2:
    data_carregamento = st.text_input("Data", data_hoje)

# --- 10. EXTRAÇÃO ---
uploaded_file = st.file_uploader("Upload do Print", type=["jpg", "png", "jpeg"])
if uploaded_file:
    img = Image.open(uploaded_file)
    if st.button("🔍 EXTRAIR DADOS"):
