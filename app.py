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

# --- 2. ESTILIZAÇÃO CSS AVANÇADA (EXPANDERS COLORIDOS) ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .stDeployButton {display:none;}
    
    /* Estilização Geral dos Expanders */
    .stExpander {
        border: none !important;
        box-shadow: 0px 4px 6px rgba(0,0,0,0.2);
        margin-bottom: 15px !important;
    }
    
    /* Forçar a cor do texto do cabeçalho para branco quando colorido */
    .stExpander summary p {
        color: white !important;
        font-weight: bold !important;
        font-size: 1.1rem !important;
    }

    /* Estilo para os botões de status dentro das colunas */
    div[data-testid="stVerticalBlock"] > div:has(button.st-emotion-cache-12fmjuu) {
        background-color: rgba(255,255,255,0.05);
        padding: 10px;
        border-radius: 5px;
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

# --- 4. INICIALIZAÇÃO E CARREGAMENTO DE DADOS ---
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

# --- 5. BOTÕES DE CONTROLE ---
col_s, col_l, col_n = st.columns([1, 1, 1])
with col_s:
    if st.button("🔄 Sincronizar Nuvem", use_container_width=True, type="primary"):
        st.session_state.dados_controle = carregar_do_firebase()
        st.rerun()
with col_l:
    if st.button("🗑️ Limpar Placas", use_container_width=True):
        for r in st.session_state.dados_controle: st.session_state.dados_controle[r]["veiculos"] = []
        st.session_state.horario_inicio = ""; st.session_state.ciclo_finalizado = False
        salvar_no_firebase(); st.rerun()
with col_n:
    with st.popover("➕ Nova Rota", use_container_width=True):
        id_r = st.text_input("ID").upper()
        cid_r = st.text_input("Cidade").upper()
        if st.button("Adicionar"):
            st.session_state.dados_controle[id_r] = {"local": cid_r, "janela": "00:00 às 00:00", "letra": "?", "veiculos": []}
            salvar_no_firebase(); st.rerun()

# --- 6. EXIBIÇÃO DAS ROTAS COM EXPANDERS COLORIDOS ---
cores_config = {
    "EPA4": "#D00000", "EPA5": "#004B93", "ETO4": "#008F5A",
    "EPA7": "#D97706", "EPA3": "#6D28D9", "EPA8": "#2563EB"
}
cor_generica = "#475569"

for rota, info in st.session_state.dados_controle.items():
    cor = cores_config.get(rota, cor_generica)
    
    # CSS dinâmico para pintar apenas o cabeçalho deste expander específico
    st.markdown(f"""
        <style>
        div[data-testid="stExpander"]:has(p:contains("{rota}")) summary {{
            background-color: {cor} !important;
            border-radius: 8px 8px 0px 0px;
        }}
        div[data-testid="stExpander"]:has(p:contains("{rota}")) {{
            border: 2px solid {cor} !important;
            border-radius: 10px !important;
        }}
        </style>
    """, unsafe_allow_html=True)
    
    # Título do Expander (visível mesmo quando minimizado)
    titulo_expander = f"📍 {rota} | Ilha: {info['letra']} | {info['local']} ({info['janela']})"
    
    with st.expander(titulo_expander, expanded=True):
        c1, c2, c3 = st.columns([1, 2, 1])
        
        # Edição rápida da Rota
        nova_ilha = c1.text_input("Ilha", info['letra'], key=f"ilha_{rota}")
        if nova_ilha != info['letra']:
            info['letra'] = nova_ilha; salvar_no_firebase()
            
        nova_janela = c2.text_input("Janela", info['janela'], key=f"jan_{rota}")
        if nova_janela != info['janela']:
            info['janela'] = nova_janela; salvar_no_firebase()

        if c3.button("➕ Veículo", key=f"btn_{rota}", use_container_width=True):
            info['veiculos'].append({"placa": "", "status": "Pendente", "doca": ""})
            salvar_no_firebase(); st.rerun()

        # Tabela de Veículos
        for idx, v in enumerate(info['veiculos']):
            col_p, col_d, col_s, col_x = st.columns([2, 1, 2, 0.5])
            
            v['placa'] = col_p.text_input("Placa", v['placa'], key=f"p_{rota}_{idx}").upper()
            v['doca'] = col_d.text_input("Doca", v.get('doca', ''), key=f"d_{rota}_{idx}").upper()
            
            opcoes = ["Pendente", "Em Carregamento", "Finalizado", "Aguardando Carregamento", "Cancelado"]
            v['status'] = col_s.selectbox("Status", opcoes, index=opcoes.index(v['status']) if v['status'] in opcoes else 0, key=f"s_{rota}_{idx}")
            
            if col_x.button("❌", key=f"del_{rota}_{idx}"):
                info['veiculos'].pop(idx)
                salvar_no_firebase(); st.rerun()
            st.divider()

# --- 7. RELATÓRIO WHATSAPP ---
st.divider()
st.subheader("📲 Relatório para WhatsApp")
col_bt1, col_bt2, col_bt3 = st.columns(3)

fuso = pytz.timezone('America/Sao_Paulo')
if col_bt1.button("▶️ Registrar Início"):
    st.session_state.horario_inicio = datetime.now(fuso).strftime('%H:%M'); st.rerun()
if col_bt2.button("🏁 Registrar Fim"):
    st.session_state.ciclo_finalizado = True; st.rerun()
if col_bt3.button("🔄 Resetar Ciclo"):
    st.session_state.horario_inicio = ""; st.session_state.ciclo_finalizado = False; st.rerun()

# Construção do Texto
texto_final = f"*CARREGAMENTO PM/MM - {datetime.now(fuso).strftime('%d/%m/%Y')}*\n"
if st.session_state.horario_inicio: texto_final += f"INICIO: {st.session_state.horario_inicio}\n"
texto_final += "\n"

for rota, info in st.session_state.dados_controle.items():
    if info['veiculos']:
        texto_final += f"*{rota}* ({info['local']}) - Ilha: {info['letra']}\n"
        for v in info['veiculos']:
            emj = "✅" if v['status'] == "Finalizado" else "🟡"
            dc = f" [Doca {v['doca']}]" if v['doca'] else ""
            texto_final += f"🚚 {v['placa']}{dc} - {v['status']} {emj}\n"
        texto_final += "\n"

if st.session_state.ciclo_finalizado: texto_final += "CICLO FINALIZADO ✅"

st.text_area("Prévia do Texto", texto_final, height=800)

js_code = f"""
<script>
function copiar() {{
    navigator.clipboard.writeText(`{texto_final}`);
    alert("Relatório copiado para a área de transferência!");
}}
</script>
<button onclick="copiar()" style="width:100%; padding:15px; background:#25D366; color:white; border:none; border-radius:10px; cursor:pointer; font-weight:bold; font-size:16px;">
    COPIAR PARA WHATSAPP
</button>
"""
components.html(js_code, height=80)
