import streamlit as st
import pandas as pd
import sqlite3

# =========================
# Função para conectar no banco
# =========================
def get_connection():
    return sqlite3.connect("relatorios.db")

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

    # Converter a coluna de Data
    if "Data" in df.columns:
        df["Data"] = pd.to_datetime(df["Data"], errors="coerce", dayfirst=True)

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

    # Garantir que Data é datetime
    if "Data" in df_banco.columns:
        df_banco["Data"] = pd.to_datetime(df_banco["Data"], errors="coerce", dayfirst=True)
        # Criar colunas de Ano e Mês/Ano
        df_banco["Ano"] = df_banco["Data"].dt.year
        df_banco["MesAno"] = df_banco["Data"].dt.strftime("%m/%Y")

    st.dataframe(df_banco.head())

    # =========================
    # Filtros globais
    # =========================
    st.sidebar.header("🔍 Filtros")

    f_sub = st.sidebar.multiselect("Subprefeitura", df_banco["Subprefeitura"].dropna().unique())
    f_unidade = st.sidebar.multiselect("Unidade", df_banco["Unidade"].dropna().unique())
    f_tipo = st.sidebar.multiselect("Tipo de Operação", df_banco["Tipo de Operacao"].dropna().unique())
    f_turno = st.sidebar.multiselect("Turno", df_banco["Turno"].dropna().unique())

    # Filtro de Mês/Ano (formato BR)
    if "MesAno" in df_banco.columns:
        f_mesano = st.sidebar.multiselect("Mês/Ano", df_banco["MesAno"].dropna().unique())
    else:
        f_mesano = None

    # =========================
    # Aplicar filtros
    # =========================
    df_filtered = df_banco.copy()

    if f_sub:
        df_filtered = df_filtered[df_filtered["Subprefeitura"].isin(f_sub)]
    if f_unidade:
        df_filtered = df_filtered[df_filtered["Unidade"].isin(f_unidade)]
    if f_tipo:
        df_filtered = df_filtered[df_filtered["Tipo de Operacao"].isin(f_tipo)]
    if f_turno:
        df_filtered = df_filtered[df_filtered["Turno"].isin(f_turno)]
    if f_mesano:
        df_filtered = df_filtered[df_filtered["MesAno"].isin(f_mesano)]

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
