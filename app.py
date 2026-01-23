import streamlit as st
import easyocr
import numpy as np
from PIL import Image
import re

st.set_page_config(page_title="Expedição SPA1", layout="wide")

# Inicializa o OCR (Cache para não carregar toda hora)
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['pt'])

reader = load_ocr()

st.title("📦 Gerador de Status - Mercado Envios")

# --- INPUTS CABEÇALHO ---
col_h1, col_h2, col_h3 = st.columns(3)
with col_h1:
    titulo_geral = st.text_input("Título", "CARREGAMENTO PM")
with col_h2:
    data_carregamento = st.text_input("Data", "22/01/2026")
with col_h3:
    st.write("") # Espaçador

uploaded_file = st.file_uploader("Upload do Print SPA1", type=["jpg", "png", "jpeg"])

# Dicionário padrão para organizar os dados
dados_extraidos = {
    "EPA4": {"local": "Marabá", "placas": []},
    "EPA5": {"local": "Goianésia", "placas": []},
    "ETO4": {"local": "Parauapebas", "placas": []},
    "EPA7": {"local": "Canaã", "placas": []},
    "EPA3": {"local": "Paragominas", "placas": []},
    "EPA8": {"local": "Mãe do Rio", "placas": []},
}

if uploaded_file:
    img = Image.open(uploaded_file)
    img_np = np.array(img)
    
    with st.spinner("Lendo placas e rotas..."):
        # O OCR lê tudo na imagem
        resultados = reader.readtext(img_np)
        
        texto_completo = " ".join([res[1].upper() for res in resultados])
        
        # Regex para identificar placas (Padrão Mercosul e Antigo)
        padrao_placa = re.compile(r'[A-Z]{3}[0-9][A-Z0-9][0-9]{2}')
        
        # Lógica de extração por proximidade (Simplificada)
        current_xpt = None
        for res in resultados:
            texto = res[1].upper().strip()
            
            # Identifica a Rota (XPT)
            for rota in dados_extraidos.keys():
                if rota in texto:
                    current_xpt = rota
            
            # Identifica a Placa e associa à última rota lida
            if padrao_placa.match(texto) and current_xpt:
                if texto not in dados_extraidos[current_xpt]["placas"]:
                    dados_extraidos[current_xpt]["placas"].append(texto)

    st.success("Leitura concluída!")

    # --- ÁREA DE EDIÇÃO ---
    form_final = {}
    
    for rota, info in dados_extraidos.items():
        with st.expander(f"Configurar {rota} - {info['local']}", expanded=True):
            c1, c2, c3 = st.columns([1, 2, 4])
            letra = c1.text_input("Letra", value="V", key=f"L_{rota}")
            janela = c2.text_input("Horário", value="13:00 às 14:00", key=f"H_{rota}")
            
            # Transforma a lista de placas extraídas em texto editável
            placas_iniciais = "\n".join(info["placas"])
            placas_editadas = c3.text_area("Placas extraídas (edite se necessário)", value=placas_iniciais, key=f"P_{rota}")
            
            form_final[rota] = {
                "local": info["local"],
                "letra": letra,
                "janela": janela,
                "placas": placas_editadas.split("\n")
            }

    # --- GERAÇÃO DO TEXTO WHATSAPP ---
    if st.button("GERAR TEXTO PARA WHATSAPP"):
        texto_zap = f"*{titulo_geral} {data_carregamento}*\n\n"
        
        for rota, info in form_final.items():
            # Só adiciona a rota se houver placas digitadas
            placas_limpas = [p.strip() for p in info["placas"] if p.strip()]
            if placas_limpas:
                texto_zap += f"*{rota}* ({info['local']}) ({info['janela']})\n"
                texto_zap += f"Letra: *{info['letra']}*\n\n"
                for p in placas_limpas:
                    texto_zap += f"🚚 {p} - PENDENTE\n"
                texto_zap += "\n"
        
        st.subheader("📋 Pronto para copiar:")
        st.text_area("Copiável:", texto_zap, height=400)
        st.info("Dica: No celular, clique e segure no texto acima para selecionar tudo.")
