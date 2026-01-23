import streamlit as st
import pandas as pd
from PIL import Image
import pytesseract # Requer configuração de OCR

st.set_page_config(page_title="Expedição SPA1", layout="wide")

st.title("📲 Gerador de Status WhatsApp")

# --- INPUTS INICIAIS ---
col_header1, col_header2 = st.columns(2)
with col_header1:
    data_carregamento = st.text_input("Data", "22/01/2026")
    ciclo = st.text_input("Ciclo", "PM")
with col_header2:
    st.info("As placas e locais serão extraídos da imagem abaixo.")

# --- UPLOAD E OCR SIMPLIFICADO ---
uploaded_file = st.file_uploader("Upload do Print (Overview SPA1)", type=["jpg", "png"])

if uploaded_file:
    # Aqui simulamos a extração para o exemplo, 
    # mas o app terá campos para você confirmar os dados lidos
    st.success("Imagem carregada!")
    
    # Lista de Rotas para preencher letras e horários
    rotas = ["EPA4", "EPA5", "ETO4", "EPA7", "EPA3", "EPA8"]
    dados_rotas = {}

    for rota in rotas:
        with st.expander(f"Configurar {rota}"):
            c1, c2, c3 = st.columns(3)
            letra = c1.text_input(f"Letra {rota}", "V")
            janela = c2.text_input(f"Janela {rota}", "13:00 às 14:00")
            # Simulando extração de placas (No app real, o OCR preenche aqui)
            placas = c3.text_area(f"Placas {rota} (uma por linha)", "ABC1234\nXYZ5678")
            dados_rotas[rota] = {"letra": letra, "janela": janela, "placas": placas.split('\n')}

    # --- GERADOR DE TEXTO ---
    if st.button("GERAR TEXTO PARA WHATSAPP"):
        texto_final = f"*CARREGAMENTO {ciclo} {data_carregamento}*\n\n"
        
        for rota, info in dados_rotas.items():
            texto_final += f"*{rota}* (Local) ({info['janela']})\nLetra: *{info['letra']}*\n\n"
            for placa in info['placas']:
                if placa.strip():
                    texto_final += f"🚚 {placa} - Pendente\n"
            texto_final += "\n"
        
        st.text_area("Copie o texto abaixo:", texto_final, height=300)