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

# --- INICIALIZAÇÃO DE ESTADOS PARA O WHATSAPP ---
if 'horario_inicio' not in st.session_state:
    st.session_state.horario_inicio = ""
if 'ciclo_finalizado' not in st.session_state:
    st.session_state.ciclo_finalizado = False

# --- 1. NOTIFICAÇÃO PÓS-SYNC ---
if st.session_state.get('sync_ok'):
    st.toast("Sincronizado com a nuvem com sucesso! ☁️✅", icon="🔄")
    st.session_state['sync_ok'] = False

# --- 2. DATA AUTOMÁTICA (Brasília) ---
fuso_br = pytz.timezone('America/Sao_Paulo')
data_hoje = datetime.now(fuso_br).strftime('%d/%m/%Y')

# --- 3. CONEXÃO COM FIREBASE ---
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

# --- 4. FUNÇÕES DE CALLBACK ---
def atualizar_ilha(rota):
    novo_valor = st.session_state[f"l_{rota}"]
    st.session_state.dados_controle[rota]['letra'] = novo_valor
    salvar_no_firebase()

def atualizar_hora(rota):
    novo_valor = st.session_state[f"h_{rota}"]
    st.session_state.dados_controle[rota]['janela'] = novo_valor
    salvar_no_firebase()

# --- 5. ESTILIZAÇÃO CSS ---
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
    
    /* Estilo reforçado para separação das rotas */
    .rota-container {
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 25px;
        border: 1px solid rgba(255,255,255,0.1);
        border-left: 15px solid;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.3);
    }

    /* MOBILE: collapsa expanders por padrão e reduz padding */
    @media (max-width: 768px) {
        .rota-container {
            padding: 8px;
            margin-bottom: 12px;
            border-left-width: 8px;
        }
        /* Reduz espaçamento interno dos blocos no mobile */
        section[data-testid="stExpander"] > div {
            padding: 6px !important;
        }
        /* Botões de ação mais compactos no mobile */
        div[data-testid="stHorizontalBlock"] {
            gap: 4px !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# --- 6. TÍTULO PRINCIPAL ---
st.title("📦 Controle de Carregamento XPT SPA1 - PM/MM")
st.write(f"Analista: **Ezequiel Miranda**")

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['pt'])

reader = load_ocr()

# --- 7. INICIALIZAÇÃO DE DADOS ---
def organizar_dados(dados_brutos):
    ordem_fixa = ["EPA4", "EPA5", "ETO4", "EPA7", "EPA3", "EPA8"]
    dados_ordenados = {}
    for rota in ordem_fixa:
        if rota in dados_brutos:
            dados_ordenados[rota] = dados_brutos[rota]
    for rota in dados_brutos:
        if rota not in dados_ordenados:
            dados_ordenados[rota] = dados_brutos[rota]
    return dados_ordenados

if 'dados_controle' not in st.session_state:
    dados_nuvem = carregar_do_firebase()
    if dados_nuvem:
        st.session_state.dados_controle = organizar_dados(dados_nuvem)
    else:
        st.session_state.dados_controle = {
            "EPA4": {"local": "MARABA", "janela": "12:00 às 14:00", "letra": "?", "veiculos": []},
            "EPA5": {"local": "GOIANESIA", "janela": "12:00 às 14:00", "letra": "?", "veiculos": []},
            "ETO4": {"local": "PARAUAPEBAS", "janela": "13:30 às 15:30", "letra": "?", "veiculos": []},
            "EPA7": {"local": "CANAA", "janela": "13:30 às 15:30", "letra": "?", "veiculos": []},
            "EPA3": {"local": "PARAGOMINAS", "janela": "14:30 às 16:30", "letra": "?", "veiculos": []},
            "EPA8": {"local": "MAE DO RIO", "janela": "14:30 às 16:30", "letra": "?", "veiculos": []},
        }

# --- 8. BOTÕES DE AÇÃO ---
col_sync, col_clear, col_add = st.columns([1, 1, 1])
with col_sync:
    if st.button("🔄 Sincronizar", use_container_width=True, type="primary"):
        st.cache_data.clear()
        dados_novos = carregar_do_firebase()
        if dados_novos:
            st.session_state.dados_controle = organizar_dados(dados_novos)
            st.session_state['sync_ok'] = True
            st.rerun()

with col_clear:
    if st.button("🗑️ Limpar Tudo", use_container_width=True, type="secondary"):
        for rota in st.session_state.dados_controle:
            st.session_state.dados_controle[rota]["veiculos"] = []
            st.session_state.dados_controle[rota]["letra"] = "?"
        st.session_state.horario_inicio = ""
        st.session_state.ciclo_finalizado = False
        salvar_no_firebase()
        st.toast("Dados e ciclo limpos com sucesso! 🗑️", icon="✅")
        st.rerun()

with col_add:
    with st.popover("➕ Nova Rota", use_container_width=True):
        nova_id = st.text_input("ID da Rota").upper()
        nova_cid = st.text_input("Cidade").upper()
        if st.button("Confirmar Adição"):
            if nova_id and nova_cid:
                st.session_state.dados_controle[nova_id] = {"local": nova_cid, "janela": "00:00 às 00:00", "letra": "?", "veiculos": []}
                salvar_no_firebase()
                st.rerun()

# --- 9. CABEÇALHO ---
col_h1, col_h2 = st.columns(2)
with col_h1:
    titulo_geral = st.text_input("Título", "CARREGAMENTO PM")
with col_h2:
    data_carregamento = st.text_input("Data", data_hoje)

# --- 10. EXTRAÇÃO INTELIGENTE ---
# Mapeamento fixo: rota → letras de ilha esperadas (da tabela da imagem)
# Padrão da imagem: "XPT - EPA3" na coluna Tipos de serviço, "Q" ou "Z" na coluna ilha
uploaded_file = st.file_uploader("Upload do Print", type=["jpg", "png", "jpeg"])
if uploaded_file:
    img = Image.open(uploaded_file)
    if st.button("🔍 EXTRAIR DADOS"):
        with st.spinner("Lendo print..."):
            resultados = reader.readtext(np.array(img), paragraph=False)
            
            def get_y_center(bbox): return (bbox[0][1] + bbox[2][1]) / 2
            def get_x_center(bbox): return (bbox[0][0] + bbox[2][0]) / 2

            # Agrupa por linha (mesma altura Y)
            linhas = []
            if resultados:
                resultados.sort(key=lambda x: get_y_center(x[0]))
                current_row = [resultados[0]]
                last_y = get_y_center(resultados[0][0])
                for res in resultados[1:]:
                    curr_y = get_y_center(res[0])
                    if abs(curr_y - last_y) < 25:
                        current_row.append(res)
                    else:
                        linhas.append(current_row)
                        current_row = [res]
                        last_y = curr_y
                linhas.append(current_row)

            padrao_placa = re.compile(r'[A-Z]{3}[0-9][A-Z0-9][0-9]{2}')
            # Padrão para detectar linha de tabela tipo imagem: "XPT - ROTA" ou "XPT ROTA"
            # e extrair a ilha da coluna mais à esquerda da mesma linha
            padrao_xpt_rota = re.compile(r'XPT[\s\-]+([A-Z]{3}[0-9])', re.IGNORECASE)

            for linha in linhas:
                linha.sort(key=lambda x: x[0][0][0])  # ordena da esquerda p/ direita
                textos_linha = [item[1].strip().upper() for item in linha]
                texto_completo_linha = " ".join(textos_linha)

                # --- NOVA LÓGICA: extração de ilha pelo modelo da tabela da imagem ---
                # Detecta se a linha contém "XPT - ROTA" (ex: "XPT - EPA3")
                match_xpt = padrao_xpt_rota.search(texto_completo_linha)
                if match_xpt:
                    rota_detectada = match_xpt.group(1)  # ex: "EPA3"
                    if rota_detectada in st.session_state.dados_controle:
                        # A letra da ilha é o 1º token da linha (coluna mais à esquerda)
                        # Filtra tokens que sejam apenas 1 letra maiúscula (A-Z)
                        for item in linha:
                            txt = item[1].strip().upper()
                            txt_limpo = re.sub(r'[^A-Z]', '', txt)
                            if len(txt_limpo) == 1 and txt_limpo.isalpha():
                                st.session_state.dados_controle[rota_detectada]["letra"] = txt_limpo
                                break
                    continue  # linha processada pelo novo modelo, pula lógica antiga

                # --- LÓGICA ANTIGA: vinculação por nome de rota ou cidade ---
                rota_vinculada = None
                for id_rota, info in st.session_state.dados_controle.items():
                    destino = info['local'].upper()
                    if id_rota in texto_completo_linha or destino in texto_completo_linha:
                        rota_vinculada = id_rota
                        break
                
                if rota_vinculada:
                    for txt in textos_linha:
                        letra_limpa = re.sub(r'[^A-Z]', '', txt.replace("XPT", ""))
                        if 1 <= len(letra_limpa) <= 2:
                            st.session_state.dados_controle[rota_vinculada]["letra"] = letra_limpa
                            break
                    for txt in textos_linha:
                        clean_txt = txt.replace(" ", "").replace("-", "")
                        match = padrao_placa.search(clean_txt)
                        if match:
                            placa = match.group(0)
                            if not any(v['placa'] == placa for v in st.session_state.dados_controle[rota_vinculada]["veiculos"]):
                                st.session_state.dados_controle[rota_vinculada]["veiculos"].append({"placa": placa, "status": "Pendente", "doca": ""})
                            break
            salvar_no_firebase()
            st.rerun()

# --- 11. EDIÇÃO COM DESTAQUE VISUAL REFORÇADO ---
cores_vibrantes = ["#FF0000", "#007BFF", "#28A745", "#FF8C00", "#A100FF", "#00CED1", "#FF1493", "#FFD700"]

# Injeta CSS para colorir o header de cada expander pelo índice (nth-of-type)
_total_rotas = len(st.session_state.dados_controle)
_css_expanders = ""
for _i in range(_total_rotas):
    _cor = cores_vibrantes[_i % len(cores_vibrantes)]
    # Seleciona o (n+1)-ésimo details element (expander) na página
    _css_expanders += f"""
    details:nth-of-type({_i + 1}) > summary {{
        background-color: {_cor} !important;
        border-radius: 8px !important;
        color: white !important;
        font-weight: bold !important;
        padding: 10px 14px !important;
    }}
    details:nth-of-type({_i + 1}) > summary svg {{
        fill: white !important;
        stroke: white !important;
    }}
    details:nth-of-type({_i + 1}) {{
        border: 2px solid {_cor} !important;
        border-radius: 10px !important;
        margin-bottom: 16px !important;
    }}
    """
st.markdown(f"<style>{_css_expanders}</style>", unsafe_allow_html=True)

for idx, (rota, info) in enumerate(st.session_state.dados_controle.items()):
    cor_atual = cores_vibrantes[idx % len(cores_vibrantes)]
    
    st.markdown(f'''
        <div class="rota-container" style="border-left-color: {cor_atual}; background-color: {cor_atual}25;">
    ''', unsafe_allow_html=True)
    
    with st.expander(f"📍 {rota} | Ilha: {info['letra']} | {info['local']}", expanded=False):
        # FIX: botão ➕ Placa alinhado com campo Hora (3 colunas: Ilha | Hora | ➕Placa)
        c_l, c_h, c_a = st.columns([1, 2, 1])
        c_l.text_input("Ilha", value=info['letra'], key=f"l_{rota}", on_change=atualizar_ilha, args=(rota,))
        c_h.text_input("Hora", value=info['janela'], key=f"h_{rota}", on_change=atualizar_hora, args=(rota,))
        
        with c_a:
            # Alinha verticalmente com o campo de texto usando margin
            st.markdown('<div style="margin-top: 28px;"></div>', unsafe_allow_html=True)
            if st.button("➕ Placa", key=f"add_{rota}", use_container_width=True):
                st.session_state.dados_controle[rota]['veiculos'].append({"placa": "", "status": "Pendente", "doca": ""})
                salvar_no_firebase()
                st.rerun()

        for idx_v, v in enumerate(info['veiculos']):
            c1, c_doca, c2, c_move, c3 = st.columns([2, 1, 2, 0.5, 0.5])
            v['placa'] = c1.text_input("Placa", v['placa'], key=f"p_{rota}_{idx_v}").upper()
            if "doca" not in v: v["doca"] = ""
            v['doca'] = c_doca.text_input("Doca", v['doca'], key=f"d_{rota}_{idx_v}").upper()

            status_opcoes = ["Pendente", "Finalizado", "Em Carregamento", "Cancelado", "Aguardando Carregamento"]
            novo_s = c2.selectbox("Status", status_opcoes, index=status_opcoes.index(v['status']) if v['status'] in status_opcoes else 0, key=f"s_{rota}_{idx_v}")
            
            if novo_s != v['status']:
                v['status'] = novo_s
                if novo_s == "Finalizado": v['hora_finalizacao'] = datetime.now(fuso_br).strftime('%H:%M')
                elif "hora_finalizacao" in v: del v['hora_finalizacao']
                salvar_no_firebase()
            
            with c_move:
                st.markdown('<div style="margin-top: 28px;"></div>', unsafe_allow_html=True)
                with st.popover("🔄", use_container_width=True):
                    for dest in st.session_state.dados_controle.keys():
                        if dest != rota:
                            if st.button(dest, key=f"mv_{rota}_{dest}_{idx_v}"):
                                st.session_state.dados_controle[dest]["veiculos"].append(v.copy())
                                info['veiculos'].pop(idx_v)
                                salvar_no_firebase(); st.rerun()
            with c3:
                st.markdown('<div style="margin-top: 28px;"></div>', unsafe_allow_html=True)
                if st.button("❌", key=f"x_{rota}_{idx_v}", use_container_width=True):
                    info['veiculos'].pop(idx_v); salvar_no_firebase(); st.rerun()
            st.divider()
    st.markdown('</div>', unsafe_allow_html=True)

# --- 12. WHATSAPP ---
st.divider()
st.subheader("📲 Configuração do Texto WhatsApp")
col_bt1, col_bt2, col_bt3 = st.columns([1, 1, 2])
with col_bt1:
    if st.button("▶️ Marcar INICIO", use_container_width=True):
        st.session_state.horario_inicio = datetime.now(fuso_br).strftime('%H:%M'); st.rerun()
with col_bt2:
    if st.button("🏁 Marcar FIM", use_container_width=True):
        st.session_state.ciclo_finalizado = True; st.rerun()
with col_bt3:
    if st.button("🔄 Resetar Status Ciclo", use_container_width=True):
        st.session_state.horario_inicio = ""; st.session_state.ciclo_finalizado = False; st.rerun()

res_texto = f"*{titulo_geral} {data_carregamento}*\n"
if st.session_state.horario_inicio: res_texto += f"INICIO: {st.session_state.horario_inicio}\n"
res_texto += "\n"

tem_placa = False
for rota, info in st.session_state.dados_controle.items():
    v_validos = [v for v in info['veiculos'] if v['placa'].strip()]
    if v_validos:
        tem_placa = True
        res_texto += f"*{rota}* ({info['local']}) ({info['janela']})\nLetra: *{info['letra']}*\n"
        for v in v_validos:
            status_emoji = {"Pendente": "🟡", "Finalizado": f"✅ {v.get('hora_finalizacao', '')}", "Cancelado": "❌", "Aguardando Carregamento": "🕑", "Em Carregamento": "⏳"}.get(v['status'], "🟡")
            texto_doca = f" [Doca: {v.get('doca', '')}]" if v.get('doca') else ""
            res_texto += f"🚚 {v['placa']}{texto_doca} - {v['status']} {status_emoji}\n"
        res_texto += "\n"

if st.session_state.ciclo_finalizado: res_texto += "CICLO PM_MM FINALIZADO ✅\n"

if tem_placa:
    st.text_area("Texto para Copiar", res_texto, height=800)
    js_code = f"""<script>function copiarTexto() {{ const textToCopy = `{res_texto}`; navigator.clipboard.writeText(textToCopy).then(() => {{ alert("Texto copiado para o WhatsApp! ✅"); }}); }}</script><button style="width:100%; background:#25D366; color:white; border:none; padding:12px; border-radius:8px; font-weight:bold; cursor:pointer;" onclick="copiarTexto()">COPIAR PARA WHATSAPP</button>"""
    components.html(js_code, height=70)
