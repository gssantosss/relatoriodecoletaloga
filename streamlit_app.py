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
st.title("Análise - Relatórios de Coleta")

# =========================
# Upload do arquivo
# =========================
uploaded_file = st.file_uploader("Suba o relatório de coleta em Excel (xlsx.)", type=["xlsx"])

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

    st.success("Relatório salvo no banco com sucesso ✅")

# =========================
# Mostrar dados já no banco
# =========================
st.subheader("📂 Preview do Relatório")

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
    st.sidebar.header("Filtros de Pesquisa")

    f_sub = st.sidebar.multiselect("Subprefeitura", df_banco["subprefeitura"].dropna().unique() if "subprefeitura" in df_banco.columns else [])
    f_unidade = st.sidebar.multiselect("Unidade", df_banco["unidade"].dropna().unique() if "unidade" in df_banco.columns else [])
    f_tipo = st.sidebar.multiselect("Tipo de Operação", df_banco["tipo_operacao"].dropna().unique() if "tipo_operacao" in df_banco.columns else [])
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
        df_filtered = df_filtered[df_filtered["tipo_operacao"].isin(f_tipo)]
    if f_turno:
        df_filtered = df_filtered[df_filtered["turno"].isin(f_turno)]
    if f_mesano:
        df_filtered = df_filtered[df_filtered["mesano"].isin(f_mesano)]



    
    # =========================
    # Abas
    # =========================
    tab1, tab2, tab3, tab4, tab5= st.tabs(["📊 Visão Geral","🗂️ Setores", "🚛 Veículos", "📐 Quilometragem", "⏱️ Horas"])

    with tab1:
        st.subheader("📊 Visão Geral")
    
        # Cards rápidos
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            total_pontos = df_filtered["total_pontos"].sum() if "total_pontos" in df_filtered.columns else 0
            coletados = df_filtered["coletados"].sum() if "coletados" in df_filtered.columns else 0
            st.metric("Total de Pontos", f"{total_pontos} / {coletados}")
        with col2:
            percentual_realizado = (coletados / total_pontos * 100) if total_pontos > 0 else 0
            st.metric("Percentual Realizado", f"{percentual_realizado:.2f}%")
        with col3:
            km_total = df_filtered["km_total"].sum() if "km_total" in df_filtered.columns else 0
            st.metric("KM Rodado", f"{km_total} km")
        with col4:
            horas_totais = df_filtered["horas_totais"].sum() if "horas_totais" in df_filtered.columns else 0
            st.metric("Horas de Operação", f"{horas_totais} h")
    
        # Gráfico de KM por Subprefeitura
        km_por_sub = df_filtered.groupby("subprefeitura")["km_total"].sum().reset_index()
        km_por_sub = km_por_sub.sort_values("km_total", ascending=False)
        fig_km = px.bar(km_por_sub, x="km_total", y="subprefeitura", orientation='h', text="km_total")
        st.plotly_chart(fig_km)
    
        # Gráfico de Horas por Subprefeitura
        horas_por_sub = df_filtered.groupby("subprefeitura")["horas_totais"].sum().reset_index()
        horas_por_sub = horas_por_sub.sort_values("horas_totais", ascending=False)
        fig_horas = px.bar(horas_por_sub, x="horas_totais", y="subprefeitura", orientation='h', text="horas_totais")
        st.plotly_chart(fig_horas)




    
        
    with tab2:
        st.subheader("Análise de Setores")
        st.dataframe(df_filtered)

    with tab3:
        st.subheader("Análise de Veículos")
        st.dataframe(df_filtered)

    with tab4:
        st.subheader("Análise de KM")
        st.dataframe(df_filtered)

    with tab5:
        st.subheader("Análise de Horas")
        st.dataframe(df_filtered)

else:
    st.info("Nenhum relatório foi carregado.")

conn.close()
