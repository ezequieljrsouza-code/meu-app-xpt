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

# --- 1. DATA AUTOMÁTICA (Brasília) ---
fuso_br = pytz.timezone('America/Sao_Paulo')
data_hoje = datetime.now(fuso_br).strftime('%d/%m/%Y')

# --- 2. CONEXÃO COM FIREBASE ---
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

# --- 3. ESTILIZAÇÃO CSS ---
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

# --- 4. TÍTULOS RESTAURADOS ---
st.title("📦 Controle de Carregamento XPT SPA1 - PM")
st.write(f"Autor: **Ezequiel Miranda**")

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['pt'])

reader = load_ocr()

# --- 5. INICIALIZAÇÃO DE DADOS ---
if 'dados_controle' not in st.session_state:
    dados_nuvem = carregar_do_firebase()
    if dados_nuvem:
        st.session_state.dados_controle = dados_nuvem
    else:
        st.session_state.dados_controle = {
            "EPA4": {"local": "Marabá", "janela": "12:00 às 14:00", "letra": "?", "veiculos": []},
            "EPA5": {"local": "Goianésia", "janela": "12:00 às 14:00", "letra": "?", "veiculos": []},
            "EPA7": {"local": "Canaã", "janela": "13:30 às 15:30", "letra": "?", "veiculos": []},
            "ETO4": {"local": "Parauapebas", "janela": "13:30 às 15:30", "letra": "?", "veiculos": []},
            "EPA3": {"local": "Paragominas", "janela": "14:30 às 16:30", "letra": "?", "veiculos": []},
            "EPA8": {"local": "Mãe do Rio", "janela": "14:30 às 16:30", "letra": "?", "veiculos": []},
        }

# --- 6. BOTÕES DE AÇÃO ---
col_sync, col_clear = st.columns([1, 1])
with col_sync:
    if st.button("🔄 Sincronizar", use_container_width=True, type="primary"):
        dados_novos = carregar_do_firebase()
        if dados_novos:
            st.session_state.dados_controle = dados_novos
            st.rerun()

with col_clear:
    if st.button("🗑️ Limpar Tudo", use_container_width=True, type="secondary"):
        for rota in st.session_state.dados_controle:
            st.session_state.dados_controle[rota]["veiculos"] = []
        salvar_no_firebase()
        st.rerun()

# --- 7. CABEÇALHO ---
col_h1, col_h2 = st.columns(2)
with col_h1:
    titulo_geral = st.text_input("Título", "CARREGAMENTO PM")
with col_h2:
    data_carregamento = st.text_input("Data", data_hoje)

# --- 8. EXTRAÇÃO ---
uploaded_file = st.file_uploader("Upload do Print", type=["jpg", "png", "jpeg"])
if uploaded_file:
    img = Image.open(uploaded_file)
    if st.button("🔍 EXTRAIR DADOS"):
        with st.spinner("Extraindo..."):
            resultados = reader.readtext(np.array(img))
            bruto = [res[1].upper().strip() for res in resultados]
            padrao_placa = re.compile(r'[A-Z]{3}[0-9][A-Z0-9][0-9]{2}')
            
            for i, texto in enumerate(bruto):
                for rota_id in st.session_state.dados_controle.keys():
                    if rota_id in texto:
                        for busca in range(1, 4):
                            if i - busca >= 0:
                                cand = bruto[i-busca].replace(" ", "")
                                if 1 <= len(cand) <= 3 and "XPT" not in cand:
                                    st.session_state.dados_controle[rota_id]["letra"] = cand
                                    break
            
            curr_xpt = None
            for texto in bruto:
                txt_limpo = texto.replace(" ", "")
                for rota in st.session_state.dados_controle.keys():
                    if rota in txt_limpo: curr_xpt = rota
                if padrao_placa.match(txt_limpo) and curr_xpt:
                    if not any(v['placa'] == txt_limpo for v in st.session_state.dados_controle[curr_xpt]["veiculos"]):
                        st.session_state.dados_controle[curr_xpt]["veiculos"].append({"placa": txt_limpo, "status": "PENDENTE"})
            
            salvar_no_firebase()
            st.rerun()

# --- 9. EDIÇÃO INSTANTÂNEA ---
for rota, info in st.session_state.dados_controle.items():
    with st.expander(f"📍 {rota} | Ilha: {info['letra']} | {info['local']}", expanded=True):
        c_l, c_h, c_a = st.columns([1, 2, 1])
        
        nova_ilha = c_l.text_input("Ilha", info['letra'], key=f"l_{rota}")
        if nova_ilha != info['letra']:
            st.session_state.dados_controle[rota]['letra'] = nova_ilha
            salvar_no_firebase()
            st.rerun()

        nova_hora = c_h.text_input("Hora", info['janela'], key=f"h_{rota}")
        if nova_hora != info['janela']:
            st.session_state.dados_controle[rota]['janela'] = nova_hora
            salvar_no_firebase()
            st.rerun()
        
        if c_a.button("➕ Placa", key=f"add_{rota}"):
            st.session_state.dados_controle[rota]['veiculos'].append({"placa": "", "status": "PENDENTE"})
            salvar_no_firebase()
            st.rerun()

        for idx, v in enumerate(info['veiculos']):
            c1, c2, c_move, c3 = st.columns([2.5, 2.5, 0.6, 0.5])
            
            nova_p = c1.text_input("Placa", v['placa'], key=f"p_{rota}_{idx}").upper()
            if nova_p != v['placa']:
                v['placa'] = nova_p
                salvar_no_firebase()

            novo_s = c2.selectbox("Status", ["PENDENTE", "FINALIZADO", "EM CARREGAMENTO", "CANCELADO", "AGUARDANDO CHEGAR"], 
                                  index=["PENDENTE", "FINALIZADO", "EM CARREGAMENTO", "CANCELADO", "AGUARDANDO CHEGAR"].index(v['status']), 
                                  key=f"s_{rota}_{idx}")
            if novo_s != v['status']:
                v['status'] = novo_s
                salvar_no_firebase()
            
            with c_move:
                st.markdown('<div style="margin-top: 28px;"></div>', unsafe_allow_html=True)
                with st.popover("🔄"):
                    for dest in st.session_state.dados_controle.keys():
                        if dest != rota:
                            if st.button(dest, key=f"mv_{rota}_{dest}_{idx}"):
                                st.session_state.dados_controle[dest]["veiculos"].append(v.copy())
                                info['veiculos'].pop(idx)
                                salvar_no_firebase()
                                st.rerun()

            if c3.button("❌", key=f"x_{rota}_{idx}"):
                info['veiculos'].pop(idx)
                salvar_no_firebase()
                st.rerun()

# --- 10. WHATSAPP ---
res_texto = f"*{titulo_geral} {data_carregamento}*\n\n"
tem_dados = False
for rota, info in st.session_state.dados_controle.items():
    if info['veiculos']:
        tem_dados = True
        res_texto += f"*{rota}* - Ilha: *{info['letra']}*\n"
        for v in info['veiculos']:
            res_texto += f"🚚 {v['placa']} - {v['status']}\n"
        res_texto += "\n"

if tem_dados:
    st.divider()
    st.text_area("Texto para Copiar", res_texto, height=150)
    components.html(f'<button style="width:100%; background:#25D366; color:white; border:none; padding:12px; border-radius:8px; font-weight:bold; cursor:pointer;" onclick="navigator.clipboard.writeText(`{res_texto}`)">COPIAR WHATSAPP</button>', height=50)

