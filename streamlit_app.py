import streamlit as st
import pandas as pd
import sqlite3
import unicodedata

# =========================
# Função para conectar no banco
# =========================
def get_connection():
    return sqlite3.connect("relatorios.db")

# =========================
# Função para padronizar nomes das colunas
# =========================
def padronizar_colunas(df):
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace("-", "_")
    )
    # Tirar acentos
    df.columns = [
        unicodedata.normalize("NFKD", col)
        .encode("ascii", errors="ignore")
        .decode("utf-8")
        for col in df.columns
    ]
    return df

# =========================
# Título
# =========================
st.title("📊 Relatórios de Coleta - LOGA")

# =========================
# Upload do arquivo
# =========================
uploaded_file = st.file_uploader("Suba o relatório em Excel", type=["xlsx"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)

    # Padronizar colunas
    df = padronizar_colunas(df)

    # Converter a coluna de Data
    if "data" in df.columns:
        df["data"] = pd.to_datetime(df["data"], errors="coerce", dayfirst=True)

    st.write("Pré-visualização do arquivo:")
    st.dataframe(df.head())

    # Salvar no banco (zera antes)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS relatorios")
    conn.commit()
    df.to_sql("relatorios", conn, if_exists="replace", index=False)
    conn.close()

    st.success("Relatório salvo no banco com sucesso ✅ (tabela recriada do zero)")

# =========================
# Mostrar dados já no banco
# =========================
st.subheader("📂 Relatórios já armazenados")

conn = get_connection()
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='relatorios'")
table_exists = cursor.fetchone()

if table_exists:
    df_banco = pd.read_sql("SELECT * FROM relatorios", conn)

    # Padronizar colunas de novo
    df_banco = padronizar_colunas(df_banco)

    # Garantir que Data é datetime
    if "data" in df_banco.columns:
        df_banco["data"] = pd.to_datetime(df_banco["data"], errors="coerce", dayfirst=True)
        df_banco["ano"] = df_banco["data"].dt.year
        df_banco["mesano"] = df_banco["data"].dt.strftime("%m/%Y")

    st.dataframe(df_banco.head())

    # =========================
    # Filtros globais
    # =========================
    st.sidebar.header("🔍 Filtros")

    f_sub = st.sidebar.multiselect("Subprefeitura", df_banco["subprefeitura"].dropna().unique() if "subprefeitura" in df_banco.columns else [])
    f_unidade = st.sidebar.multiselect("Unidade", df_banco["unidade"].dropna().unique() if "unidade" in df_banco.columns else [])
    f_tipo = st.sidebar.multiselect("Tipo de Operação", df_banco["tipo_de_operacao"].dropna().unique() if "tipo_de_operacao" in df_banco.columns else [])
    f_turno = st.sidebar.multiselect("Turno", df_banco["turno"].dropna().unique() if "turno" in df_banco.columns else [])

    # Filtro de Mês/Ano (formato BR)
    f_mesano = st.sidebar.multiselect("Mês/Ano", df_banco["mesano"].dropna().unique() if "mesano" in df_banco.columns else [])

    # =========================
    # Aplicar filtros
    # =========================
    df_filtered = df_banco.copy()

    if f_sub:
        df_filtered = df_filtered[df_filtered["subprefeitura"].isin(f_sub)]
    if f_unidade:
        df_filtered = df_filtered[df_filtered["unidade"].isin(f_unidade)]
    if f_tipo:
        df_filtered = df_filtered[df_filtered["tipo_de_operacao"].isin(f_tipo)]
    if f_turno:
        df_filtered = df_filtered[df_filtered["turno"].isin(f_turno)]
    if f_mesano:
        df_filtered = df_filtered[df_filtered["mesano"].isin(f_mesano)]

    # =========================
    # Abas
    # =========================
    tab1, tab2, tab3, tab4 = st.tabs(["🚛 Veículos", "🏙️ Operacional/Subsetores", "📏 Quilometragem", "⏱️ Horas"])

    with tab1:
        st.subheader("🚛 Análises de Veículos")
        st.dataframe(df_filtered)

    with tab2:
        st.subheader("🏙️ Análises Operacionais / Subsetores")
        st.dataframe(df_filtered)

    with tab3:
        st.subheader("📏 Análises de Quilometragem")
        st.dataframe(df_filtered)

    with tab4:
        st.subheader("⏱️ Análises de Horas")
        st.dataframe(df_filtered)

else:
    st.info("Nenhum relatório foi carregado ainda.")

conn.close()
