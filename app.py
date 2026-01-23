import streamlit as st
import easyocr
import numpy as np
from PIL import Image
import re

# Configuração da página
st.set_page_config(page_title="Expedição SPA1", layout="wide")

# --- ESTILO PARA O NOME NO CANTO SUPERIOR DIREITO ---
st.markdown(
    """
    <style>
    .user-name {
        position: absolute;
        top: -50px;
        right: 0px;
        font-weight: bold;
        color: #555;
    }
    </style>
    <div class="user-name">Ezequiel Miranda</div>
    """,
    unsafe_allow_html=True
)

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['pt'])

reader = load_ocr()

st.title("📦 Controle de Carregamento SPA1")
st.write(f"Usuário: **Ezequiel Miranda**")

# --- PERSISTÊNCIA DE DADOS ---
# Nota: No Streamlit Cloud, o session_state limpa no refresh. 
# Para persistência real entre sessões, os dados são mantidos enquanto a aba estiver aberta.
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

uploaded_file = st.file_uploader("Upload do Print SPA1", type=["jpg", "png", "jpeg"])

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
        c_letra, c_hora, c_add, c_del_r = st.columns([1, 2, 1, 0.5])
        info['letra'] = c_letra.text_input(f"Letra", value=info['letra'], key=f"letra_{rota}")
        info['janela'] = c_hora.text_input(f"Horário", value=info['janela'], key=f"horario_{rota}")
        
        if c_add.button(f"➕ Placa", key=f"add_v_{rota}"):
            info['veiculos'].append({"placa": "", "status": "PENDENTE"})
            st.rerun()
        
        if c_del_r.button("🗑️", key=f"del_rota_{rota}"):
            del st.session_state.dados_controle[rota]
            st.rerun()
        
        for idx, veiculo in enumerate(info['veiculos']):
            r_col1, r_col2, r_col3 = st.columns([2, 2, 0.5])
            veiculo['placa'] = r_col1.text_input("Placa", value=veiculo['placa'], key=f"p_{rota}_{idx}").upper()
            veiculo['status'] = r_col2.selectbox("Status", ["PENDENTE", "FINALIZADO", "EM CARREGAMENTO", "CANCELADO", "AGUARDANDO CARREGAMENTO"], 
                                                index=["PENDENTE", "FINALIZADO", "EM CARREGAMENTO", "CANCELADO", "AGUARDANDO CARREGAMENTO"].index(veiculo['status']),
                                                key=f"s_{rota}_{idx}")
            if r_col3.button("❌", key=f"del_v_{rota}_{idx}"):
                info['veiculos'].pop(idx)
                st.rerun()

# --- GERAÇÃO DO TEXTO ---
res_texto = f"*CARREGAMENTO PM {data_carregamento}*\n\n"
tem_placa = False
for rota, info in st.session_state.dados_controle.items():
    v_validos = [v for v in info['veiculos'] if v['placa'].strip()]
    if v_validos:
        tem_placa = True
        res_texto += f"*{rota}* ({info['local']}) ({info['janela']})\nLetra: *{info['letra']}*\n\n"
        for v in v_validos:
            emoji = "✅" if "FINALIZADO" in v['status'] else "❌" if "CANCELADO" in v['status'] else "⏳" if "CARREGAMENTO" in v['status'] else "🚚"
            res_texto += f"{emoji} {v['placa']} - {v['status']}\n"
        res_texto += "\n"

st.divider()
if tem_placa:
    st.subheader("📋 Resultado Final")
    st.text_area("Copiável:", value=res_texto, height=400)
    if st.button("📋 COPIAR PARA WHATSAPP"):
        st.copy_to_clipboard(res_texto)
        st.toast("Copiado!")
