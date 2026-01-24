import streamlit as st
import easyocr
import numpy as np
from PIL import Image
import re
import streamlit.components.v1 as components
from google.cloud import firestore
from google.oauth2 import service_account
import json

st.set_page_config(page_title="Expedição SPA1", layout="wide")

# --- CONEXÃO COM FIREBASE (FIRESTORE) ---
@st.cache_resource
def get_db():
    # No Streamlit Cloud, você colocará o JSON da chave em Settings > Secrets
    # Com o nome: firestore_key
    key_dict = json.loads(st.secrets["firestore_key"])
    creds = service_account.Credentials.from_service_account_info(key_dict)
    return firestore.Client(credentials=creds, project=key_dict['project_id'])

db = get_db()

# --- FUNÇÕES DE BANCO DE DADOS ---
def salvar_no_firebase(dados):
    # Salva o dicionário inteiro em um documento chamado 'config' na coleção 'expedicao'
    db.collection("expedicao").document("config").set(dados)

def carregar_do_firebase():
    doc = db.collection("expedicao").document("config").get()
    if doc.exists:
        return doc.to_dict()
    return None

# --- ESCONDER MENU E LINKS DO GITHUB ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div style="text-align: right; color: grey; font-weight: bold;">Ezequiel Miranda</div>', unsafe_allow_html=True)

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['pt'])

reader = load_ocr()

st.title("📦 Controle de Carregamento XPT SPA1 (Sincronizado)")
st.write(f"Autor: **Ezequiel Miranda**")

# --- BOTÃO DE SINCRONIZAÇÃO MANUAL ---
# Colocamos no topo para fácil acesso no celular
if st.button("🔄 Sincronizar Agora"):
    with st.spinner("Buscando dados na nuvem..."):
        dados_novos = carregar_do_firebase()
        if dados_novos:
            st.session_state.dados_controle = dados_novos
            st.rerun()

# --- INICIALIZAÇÃO / CARREGAMENTO ---
if 'dados_controle' not in st.session_state:
    dados_nuvem = carregar_do_firebase()
    if dados_nuvem:
        st.session_state.dados_controle = dados_nuvem
    else:
        # Suas rotas padrão caso o banco esteja vazio
        st.session_state.dados_controle = {
            "EPA4": {"local": "Marabá", "janela": "13:00 às 14:00", "letra": "V", "veiculos": []},
            "EPA5": {"local": "Goianésia", "janela": "14:00 às 15:00", "letra": "X", "veiculos": []},
            "ETO4": {"local": "Parauapebas", "janela": "14:30 às 16:30", "letra": "U", "veiculos": []},
            "EPA7": {"local": "Canaã", "janela": "14:30 às 16:30", "letra": "Y", "veiculos": []},
            "EPA3": {"local": "Paragominas", "janela": "15:30 às 17:30", "letra": "T", "veiculos": []},
            "EPA8": {"local": "Mãe do Rio", "janela": "15:30 às 17:30", "letra": "W", "veiculos": []},
        }

# --- CABEÇALHO ---
col_h1, col_h2 = st.columns(2)
with col_h1:
    titulo_geral = st.text_input("Título", "CARREGAMENTO PM")
    data_carregamento = st.text_input("Data", "23/01/2026")

with col_h2:
    with st.expander("➕ Adicionar/Gerenciar Rotas"):
        c_id, c_loc, c_b = st.columns([1, 1, 1])
        n_id = c_id.text_input("ID").upper()
        n_loc = c_loc.text_input("Local")
        if c_b.button("Salvar Rota"):
            if n_id and n_id not in st.session_state.dados_controle:
                st.session_state.dados_controle[n_id] = {"local": n_loc, "janela": "00:00", "letra": "?", "veiculos": []}
                salvar_no_firebase(st.session_state.dados_controle)
                st.rerun()

uploaded_file = st.file_uploader("Upload do Print", type=["jpg", "png", "jpeg"])

if uploaded_file:
    img = Image.open(uploaded_file)
    if st.button("🔍 EXTRAIR E SINCRONIZAR"):
        with st.spinner("Lendo e salvando na nuvem..."):
            resultados = reader.readtext(np.array(img))
            padrao_placa = re.compile(r'[A-Z]{3}[0-9][A-Z0-9][0-9]{2}')
            for r in st.session_state.dados_controle:
                st.session_state.dados_controle[r]["veiculos"] = []
            
            current_xpt = None
            for res in resultados:
                texto = res[1].upper().strip().replace(" ", "")
                for rota in st.session_state.dados_controle.keys():
                    if rota in texto: current_xpt = rota
                if padrao_placa.match(texto) and current_xpt:
                    if not any(v['placa'] == texto for v in st.session_state.dados_controle[current_xpt]["veiculos"]):
                        st.session_state.dados_controle[current_xpt]["veiculos"].append({"placa": texto, "status": "PENDENTE"})
            
            salvar_no_firebase(st.session_state.dados_controle)
        st.rerun()

# --- ÁREA DE EDIÇÃO ---
for rota in list(st.session_state.dados_controle.keys()):
    info = st.session_state.dados_controle[rota]
    with st.expander(f"📍 {rota} - {info['local']}", expanded=True):
        cl, ch, ca, cr = st.columns([1, 2, 1, 0.5])
        
        # Atualiza banco ao mudar letra ou hora
        info['letra'] = cl.text_input(f"Letra", value=info['letra'], key=f"l_{rota}", on_change=salvar_no_firebase, args=(st.session_state.dados_controle,))
        info['janela'] = ch.text_input(f"Hora", value=info['janela'], key=f"h_{rota}", on_change=salvar_no_firebase, args=(st.session_state.dados_controle,))
        
        if ca.button(f"➕ Placa", key=f"av_{rota}"):
            info['veiculos'].append({"placa": "", "status": "PENDENTE"})
            salvar_no_firebase(st.session_state.dados_controle)
            st.rerun()

        if cr.button("🗑️", key=f"dr_{rota}"):
            del st.session_state.dados_controle[rota]
            salvar_no_firebase(st.session_state.dados_controle)
            st.rerun()
        
        for idx, v in enumerate(info['veiculos']):
            c1, c2, c_move, c3 = st.columns([2.5, 2.5, 0.6, 0.5])
            
            v['placa'] = c1.text_input("Placa", value=v['placa'], key=f"p_{rota}_{idx}", on_change=salvar_no_firebase, args=(st.session_state.dados_controle,)).upper()
            
            # Selectbox que salva automaticamente ao mudar
            v['status'] = c2.selectbox("Status", ["PENDENTE", "FINALIZADO", "EM CARREGAMENTO", "CANCELADO", "AGUARDANDO CARREGAMENTO"], 
                                      index=["PENDENTE", "FINALIZADO", "EM CARREGAMENTO", "CANCELADO", "AGUARDANDO CARREGAMENTO"].index(v['status']),
                                      key=f"s_{rota}_{idx}", on_change=salvar_no_firebase, args=(st.session_state.dados_controle,))
            
            with c_move:
                st.markdown('<div style="margin-top: 28px;"></div>', unsafe_allow_html=True)
                with st.popover("🔄"):
                    for destino in st.session_state.dados_controle.keys():
                        if destino != rota:
                            if st.button(destino, key=f"move_{rota}_{destino}_{idx}"):
                                st.session_state.dados_controle[destino]["veiculos"].append(v)
                                info['veiculos'].pop(idx)
                                salvar_no_firebase(st.session_state.dados_controle)
                                st.rerun()

            with c3:
                st.markdown('<div style="margin-top: 28px;"></div>', unsafe_allow_html=True)
                if st.button("❌", key=f"dv_{rota}_{idx}"):
                    info['veiculos'].pop(idx)
                    salvar_no_firebase(st.session_state.dados_controle)
                    st.rerun()

# --- GERAÇÃO DO TEXTO ---
res_texto = f"*{titulo_geral} {data_carregamento}*\n\n"
tem_placa = False
for rota, info in st.session_state.dados_controle.items():
    v_validos = [v for v in info['veiculos'] if v['placa'].strip()]
    if v_validos:
        tem_placa = True
        res_texto += f"*{rota}* ({info['local']}) ({info['janela']})\nLetra: *{info['letra']}*\n\n"
        for v in v_validos:
            e = "✅" if "FINALIZADO" in v['status'] else "❌" if "CANCELADO" in v['status'] else "⏳" if "CARREGAMENTO" in v['status'] else "🚚"
            res_texto += f"🚚 {v['placa']} - {v['status']} {e}\n"
        res_texto += "\n"

st.divider()
if tem_placa:
    st.subheader("📋 Resultado Final")
    st.text_area("Copiável:", value=res_texto, height=300)
    
    copy_code = f"""
    <button style="width: 100%; background-color: #25D366; color: white; border: none; padding: 15px; font-size: 16px; border-radius: 10px; cursor: pointer; font-weight: bold;" 
    onclick="navigator.clipboard.writeText(`{res_texto}`)">
    📋 COPIAR PARA WHATSAPP
    </button>
    """
    components.html(copy_code, height=70)


