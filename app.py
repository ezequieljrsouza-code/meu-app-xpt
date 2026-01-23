import streamlit as st
import easyocr
import numpy as np
from PIL import Image
import re
import streamlit.components.v1 as components

st.set_page_config(page_title="Expedição SPA1", layout="wide")

# --- ESCONDER MENU E LINKS DO GITHUB ---
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            .stDeployButton {display:none;}
            #stDecoration {display:none;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# --- NOME NO TOPO ---
st.markdown('<div style="text-align: right; color: grey; font-weight: bold;">Ezequiel Miranda</div>', unsafe_allow_html=True)

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['pt'])

reader = load_ocr()

st.title("📦 Controle de Carregamento XPT SPA1 - PM")
st.write(f"Autor: **Ezequiel Miranda**")

# --- PERSISTÊNCIA DE DADOS ---
if 'dados_controle' not in st.session_state:
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
    data_carregamento = st.text_input("Data", "22/01/2026")

with col_h2:
    with st.expander("➕ Adicionar Nova Rota"):
        c_id, c_loc, c_b = st.columns([1, 1, 1])
        n_id = c_id.text_input("ID").upper()
        n_loc = c_loc.text_input("Local")
        if c_b.button("Salvar Rota"):
            if n_id and n_id not in st.session_state.dados_controle:
                st.session_state.dados_controle[n_id] = {"local": n_loc, "janela": "00:00", "letra": "?", "veiculos": []}
                st.rerun()

uploaded_file = st.file_uploader("Upload do Print", type=["jpg", "png", "jpeg"])

if uploaded_file:
    img = Image.open(uploaded_file)
    if st.button("🔍 EXTRAIR PLACAS"):
        with st.spinner("Lendo imagem..."):
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
        st.rerun()

# --- EDIÇÃO ---
for rota in list(st.session_state.dados_controle.keys()):
    info = st.session_state.dados_controle[rota]
    with st.expander(f"📍 {rota} - {info['local']}", expanded=True):
        cl, ch, ca, cr = st.columns([1, 2, 1, 0.5])
        info['letra'] = cl.text_input(f"Letra", value=info['letra'], key=f"l_{rota}")
        info['janela'] = ch.text_input(f"Hora", value=info['janela'], key=f"h_{rota}")
        if ca.button(f"➕ Placa", key=f"av_{rota}"):
            info['veiculos'].append({"placa": "", "status": "PENDENTE"})
            st.rerun()
        if cr.button("🗑️", key=f"dr_{rota}"):
            del st.session_state.dados_controle[rota]
            st.rerun()
        
        for idx, v in enumerate(info['veiculos']):
            # Proporção otimizada para alinhar ícones no PC e Celular
            c1, c2, c_move, c3 = st.columns([2.5, 2.5, 0.6, 0.5])
            
            v['placa'] = c1.text_input("Placa", value=v['placa'], key=f"p_{rota}_{idx}").upper()
            v['status'] = c2.selectbox("Status", ["PENDENTE", "FINALIZADO", "EM CARREGAMENTO", "CANCELADO", "AGUARDANDO CARREGAMENTO"], 
                                      index=["PENDENTE", "FINALIZADO", "EM CARREGAMENTO", "CANCELADO", "AGUARDANDO CARREGAMENTO"].index(v['status']),
                                      key=f"s_{rota}_{idx}")
            
            # --- LÓGICA DE MOVER VEÍCULO ---
            with c_move:
                st.markdown('<div style="margin-top: 28px;"></div>', unsafe_allow_html=True)
                with st.popover("🔄"):
                    st.write("Mover para:")
                    for destino in st.session_state.dados_controle.keys():
                        if destino != rota:
                            if st.button(destino, key=f"move_{rota}_{destino}_{idx}"):
                                st.session_state.dados_controle[destino]["veiculos"].append(v)
                                info['veiculos'].pop(idx)
                                st.rerun()

            with c3:
                st.markdown('<div style="margin-top: 28px;"></div>', unsafe_allow_html=True)
                if st.button("❌", key=f"dv_{rota}_{idx}"):
                    info['veiculos'].pop(idx)
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
            # Seleção do emoji de status para o final da placa
            status_emoji = "✅" if "FINALIZADO" in v['status'] else "❌" if "CANCELADO" in v['status'] else "⏳" if "CARREGAMENTO" in v['status'] else "🟡"
            
            # Formatação solicitada: Caminhão na frente + Placa + Status + Emoji de Status
            res_texto += f"🚚 {v['placa']} - {v['status']} {status_emoji}\n"
        res_texto += "\n"

st.divider()
if tem_placa:
    st.subheader("📋 Resultado Final")
    st.text_area("Texto pronto para WhatsApp:", value=res_texto, height=300)
    
    # --- BOTÃO DE COPIAR VIA JAVASCRIPT ---
    copy_code = f"""
    <button style="width: 100%; background-color: #25D366; color: white; border: none; padding: 15px; font-size: 16px; border-radius: 10px; cursor: pointer; font-weight: bold;" 
    onclick="navigator.clipboard.writeText(`{res_texto}`)">
    📋 COPIAR PARA WHATSAPP
    </button>
    """
    components.html(copy_code, height=70)

