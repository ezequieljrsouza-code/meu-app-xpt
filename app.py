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

# --- 2. ESTILIZAÇÃO CSS (FOCO NOS CABEÇALHOS) ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .stDeployButton {display:none;}
    
    /* Estilo para os cards das rotas */
    .rota-card {
        border-radius: 10px;
        margin-bottom: 20px;
        border: 1px solid rgba(255,255,255,0.1);
        overflow: hidden;
    }
    
    /* Estilo do Cabeçalho da Rota */
    .rota-header {
        padding: 10px 15px;
        color: white;
        font-weight: bold;
        font-size: 1.1rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-radius: 10px 10px 0 0;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. TÍTULO PRINCIPAL ---
st.title("📦 Controle de Carregamento XPT SPA1")
st.write(f"Analista: **Ezequiel Miranda**")

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['pt'])
reader = load_ocr()

# --- 4. INICIALIZAÇÃO DE DADOS ---
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

# --- 5. BOTÕES DE AÇÃO ---
col_sync, col_clear = st.columns([1, 1])
with col_sync:
    if st.button("🔄 Sincronizar Nuvem", use_container_width=True, type="primary"):
        dados_novos = carregar_do_firebase()
        if dados_novos:
            st.session_state.dados_controle = dados_novos
            st.rerun()

with col_clear:
    if st.button("🗑️ Limpar Tudo", use_container_width=True):
        for r in st.session_state.dados_controle:
            st.session_state.dados_controle[r]["veiculos"] = []
        st.session_state.horario_inicio = ""
        st.session_state.ciclo_finalizado = False
        salvar_no_firebase()
        st.rerun()

# --- 6. EXIBIÇÃO DAS ROTAS COM CORES NOS CABEÇALHOS ---
cores_rotas = {
    "EPA4": "#E63946", "EPA5": "#1D3557", "ETO4": "#06D6A0",
    "EPA7": "#F4A261", "EPA3": "#8338EC", "EPA8": "#3A86FF"
}
cor_padrao = "#457B9D"

for rota, info in st.session_state.dados_controle.items():
    cor = cores_rotas.get(rota, cor_padrao)
    
    # Criando o cabeçalho personalizado
    st.markdown(f"""
        <div class="rota-header" style="background-color: {cor};">
            <span>📍 {rota} | {info['local']}</span>
            <span style="font-size: 0.9rem; opacity: 0.9;">Ilha: {info['letra']} | {info['janela']}</span>
        </div>
    """, unsafe_allow_html=True)
    
    # Conteúdo da rota dentro de um container com borda da mesma cor
    with st.container(border=True):
        c_l, c_h, c_a = st.columns([1, 2, 1])
        
        # Inputs que salvam automaticamente
        nova_ilha = c_l.text_input("Ilha", info['letra'], key=f"l_{rota}")
        if nova_ilha != info['letra']:
            info['letra'] = nova_ilha
            salvar_no_firebase()
            
        nova_janela = c_h.text_input("Janela", info['janela'], key=f"h_{rota}")
        if nova_janela != info['janela']:
            info['janela'] = nova_janela
            salvar_no_firebase()

        if c_a.button("➕ Veículo", key=f"add_{rota}", use_container_width=True):
            info['veiculos'].append({"placa": "", "status": "Pendente", "doca": ""})
            salvar_no_firebase()
            st.rerun()

        # Listagem de Veículos
        for idx_v, v in enumerate(info['veiculos']):
            col_p, col_d, col_s, col_x = st.columns([2, 1, 2, 0.5])
            
            v['placa'] = col_p.text_input("Placa", v['placa'], key=f"p_{rota}_{idx_v}").upper()
            v['doca'] = col_d.text_input("Doca", v.get('doca', ''), key=f"d_{rota}_{idx_v}").upper()
            
            status_opcoes = ["Pendente", "Em Carregamento", "Finalizado", "Aguardando Carregamento", "Cancelado"]
            v['status'] = col_s.selectbox("Status", status_opcoes, index=status_opcoes.index(v['status']) if v['status'] in status_opcoes else 0, key=f"s_{rota}_{idx_v}")
            
            if col_x.button("❌", key=f"x_{rota}_{idx_v}"):
                info['veiculos'].pop(idx_v)
                salvar_no_firebase()
                st.rerun()
    st.markdown("<br>", unsafe_allow_html=True)

# --- 7. WHATSAPP ---
st.divider()
st.subheader("📲 Relatório WhatsApp")
col_in, col_fim, col_res = st.columns(3)

fuso = pytz.timezone('America/Sao_Paulo')
if col_in.button("▶️ Início"):
    st.session_state.horario_inicio = datetime.now(fuso).strftime('%H:%M')
    st.rerun()
if col_fim.button("🏁 Fim"):
    st.session_state.ciclo_finalizado = True
    st.rerun()
if col_res.button("🔄 Reset"):
    st.session_state.horario_inicio = ""
    st.session_state.ciclo_finalizado = False
    st.rerun()

# Montagem do Texto
txt_wa = f"*CARREGAMENTO PM/MM - {datetime.now(fuso).strftime('%d/%m/%Y')}*\n"
if st.session_state.horario_inicio: txt_wa += f"INICIO: {st.session_state.horario_inicio}\n"
txt_wa += "\n"

for rota, info in st.session_state.dados_controle.items():
    if info['veiculos']:
        txt_wa += f"*{rota}* ({info['local']}) - Ilha: {info['letra']}\n"
        for v in info['veiculos']:
            emoji = "🟡" if v['status'] != "Finalizado" else "✅"
            doca_txt = f" [Doca {v['doca']}]" if v['doca'] else ""
            txt_wa += f"🚚 {v['placa']}{doca_txt} - {v['status']} {emoji}\n"
        txt_wa += "\n"

if st.session_state.ciclo_finalizado: txt_wa += "CICLO FINALIZADO ✅"

st.text_area("Texto para Copiar", txt_wa, height=800)

js_copiar = f"""
<script>
function copiar() {{
    navigator.clipboard.writeText(`{txt_wa}`);
    alert("Copiado!");
}}
</script>
<button onclick="copiar()" style="width:100%; padding:10px; background:#25D366; color:white; border:none; border-radius:5px; cursor:pointer; font-weight:bold;">
    COPIAR PARA WHATSAPP
</button>
"""
components.html(js_copiar, height=60)
