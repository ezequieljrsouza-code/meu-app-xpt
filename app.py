import streamlit as st
import easyocr
import numpy as np
from PIL import Image
import re

st.set_page_config(page_title="Expedição SPA1", layout="wide")

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['pt'])

reader = load_ocr()

st.title("📦 Controle de Carregamento SPA1")

# --- CABEÇALHO ---
col_h1, col_h2 = st.columns(2)
with col_h1:
    titulo_geral = st.text_input("Título do Relatório", "CARREGAMENTO PM")
    data_carregamento = st.text_input("Data", "22/01/2026")

uploaded_file = st.file_uploader("Upload do Print SPA1", type=["jpg", "png", "jpeg"])

# Inicialização do estado
if 'dados_controle' not in st.session_state:
    st.session_state.dados_controle = {
        "EPA4": {"local": "Marabá", "janela": "13:00 às 14:00", "letra": "V", "veiculos": []},
        "EPA5": {"local": "Goianésia", "janela": "14:00 às 15:00", "letra": "X", "veiculos": []},
        "ETO4": {"local": "Parauapebas", "janela": "14:30 às 16:30", "letra": "U", "veiculos": []},
        "EPA7": {"local": "Canaã", "janela": "14:30 às 16:30", "letra": "Y", "veiculos": []},
        "EPA3": {"local": "Paragominas", "janela": "15:30 às 17:30", "letra": "T", "veiculos": []},
        "EPA8": {"local": "Mãe do Rio", "janela": "15:30 às 17:30", "letra": "W", "veiculos": []},
    }

if uploaded_file:
    img = Image.open(uploaded_file)
    img_np = np.array(img)
    
    if st.button("🔍 EXTRAIR PLACAS DA IMAGEM"):
        with st.spinner("Lendo imagem..."):
            resultados = reader.readtext(img_np)
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
        st.success("Placas extraídas!")

# --- ÁREA DE EDIÇÃO DINÂMICA ---
st.divider()
for rota, info in st.session_state.dados_controle.items():
    with st.expander(f"📍 {rota} - {info['local']}", expanded=True):
        c_letra, c_hora, c_add = st.columns([1, 2, 1])
        info['letra'] = c_letra.text_input(f"Letra", value=info['letra'], key=f"letra_{rota}")
        info['janela'] = c_hora.text_input(f"Horário", value=info['janela'], key=f"horario_{rota}")
        
        if c_add.button(f"➕ Add", key=f"add_{rota}"):
            info['veiculos'].append({"placa": "", "status": "PENDENTE"})
            st.rerun()
        
        for idx, veiculo in enumerate(info['veiculos']):
            r_col1, r_col2, r_col3 = st.columns([2, 2, 0.5])
            veiculo['placa'] = r_col1.text_input("Placa", value=veiculo['placa'], key=f"p_{rota}_{idx}").upper()
            veiculo['status'] = r_col2.selectbox("Status", ["PENDENTE", "FINALIZADO", "EM CARREGAMENTO", "CANCELADO", "AGUARDANDO CARREGAMENTO"], 
                                                index=0, key=f"s_{rota}_{idx}")
            if r_col3.button("🗑️", key=f"del_{rota}_{idx}"):
                info['veiculos'].pop(idx)
                st.rerun()

# --- GERAÇÃO AUTOMÁTICA DO TEXTO ---
res_texto = f"*{titulo_geral} {data_carregamento}*\n\n"
tem_conteudo = False

for rota, info in st.session_state.dados_controle.items():
    placas_validas = [v for v in info['veiculos'] if v['placa'].strip()]
    if placas_validas:
        tem_conteudo = True
        res_texto += f"*{rota}* ({info['local']}) ({info['janela']})\n"
        res_texto += f"Letra: *{info['letra']}*\n\n"
        for v in placas_validas:
            # Emoji dinâmico baseado no status
            if "FINALIZADO" in v['status']: emoji = "✅"
            elif "CANCELADO" in v['status']: emoji = "❌"
            elif "EM CARREGAMENTO" in v['status']: emoji = "⏳"
            else: emoji = "🚚"
            
            res_texto += f"{emoji} {v['placa']} - {v['status']}\n"
        res_texto += "\n"

# --- ÁREA DE COPIAR (FIXA NO FINAL) ---
st.divider()
if tem_conteudo:
    st.subheader("📋 Resultado Final (Atualizado em tempo real)")
    # O texto aqui dentro muda sozinho sempre que você mexe em algo acima
    st.text_area("Copie o texto abaixo:", res_texto, height=400, key="output_text")
    
    if st.button("📋 COPIAR PARA WHATSAPP"):
        st.copy_to_clipboard(res_texto)
        st.toast("Copiado com sucesso!")
else:
    st.info("O resultado aparecerá aqui assim que houver placas cadastradas.")
