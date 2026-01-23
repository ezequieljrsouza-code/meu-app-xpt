import streamlit as st
import easyocr
import numpy as np
from PIL import Image

st.set_page_config(page_title="Expedição SPA1", layout="wide")

# Inicializa o leitor de OCR (armazenado em cache para ser rápido)
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['pt'])

reader = load_ocr()

st.title("📲 Gerador de Status WhatsApp")

# Configurações Iniciais
col_h1, col_h2 = st.columns(2)
with col_h1:
    data_carregamento = st.text_input("Data do Carregamento", "22/01/2026")
with col_h2:
    ciclo = st.text_input("Ciclo", "PM")

uploaded_file = st.file_uploader("Upload do Print (Overview SPA1)", type=["jpg", "png", "jpeg"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Imagem carregada", use_column_width=True)
    
    with st.spinner("Extraindo dados da imagem..."):
        # Converte imagem para array que o OCR entende
        img_array = np.array(image)
        results = reader.readtext(img_array)
        
        # Lógica simples de extração (busca padrões de placa e XPT)
        # Nota: Em um app real, aqui filtramos as coordenadas da tabela
        st.success("Dados extraídos! Ajuste abaixo:")

    # Dicionário para organizar os dados por XPT
    rotas_detectadas = ["EPA4", "EPA5", "ETO4", "EPA7", "EPA3", "EPA8"]
    form_dados = {}

    for rota in rotas_detectadas:
        with st.expander(f"Configurar {rota}", expanded=True):
            c1, c2, c3 = st.columns([1, 2, 3])
            letra = c1.text_input(f"Letra", value="V", key=f"letra_{rota}")
            janela = c2.text_input(f"Janela Horária", value="13:00 às 14:00", key=f"janela_{rota}")
            # Aqui você digita ou confirma as placas lidas
            placas = c3.text_area(f"Placas (uma por linha)", key=f"placas_{rota}")
            
            form_dados[rota] = {
                "letra": letra,
                "janela": janela,
                "placas": placas.split('\n')
            }

    if st.button("GERAR TEXTO PARA WHATSAPP"):
        texto_final = f"*{carregamento_nome} {ciclo} {data_carregamento}*\n\n"
        
        for rota, info in form_dados.items():
            if any(p.strip() for p in info['placas']): # Só add se tiver placa
                texto_final += f"*{rota}* (Local) ({info['janela']})\nLetra: *{info['letra']}*\n\n"
                for placa in info['placas']:
                    if placa.strip():
                        texto_final += f"🚚 {placa.upper()} - PENDENTE\n"
                texto_final += "\n"
        
        st.text_area("Copie para o WhatsApp:", texto_final, height=400)
        st.info("Dica: Você pode alterar 'PENDENTE' para 'FINALIZADO' ou 'CANCELADO' antes de copiar.")
