import streamlit as st
import pandas as pd
import sqlite3
import unicodedata
import plotly.express as px

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
        st.subheader("Análise Geral")
    
        # Garantir que as colunas numéricas estão no formato certo
        if "total_de_kms" in df_filtered.columns:
            df_filtered["total_de_kms"] = pd.to_numeric(df_filtered["total_de_kms"], errors="coerce")
    
        if "percentual_realizado" in df_filtered.columns:
            df_filtered["percentual_realizado"] = pd.to_numeric(df_filtered["percentual_realizado"], errors="coerce")
    
        # Conversão da coluna de horas se existir
        if "horas_operacao" in df_filtered.columns:
            def parse_horas(x):
                if pd.isna(x):
                    return 0
                try:
                    h, m = 0, 0
                    if "h" in str(x):
                        h = int(str(x).split("h")[0].strip())
                    if "m" in str(x):
                        m = int(str(x).split("h")[-1].replace("m", "").strip())
                    return h + m/60
                except:
                    return 0
    
            df_filtered["horas_operacao_num"] = df_filtered["horas_operacao"].apply(parse_horas)
    
        # KPIs
        total_km = df_filtered["total_de_kms"].sum() if "total_de_kms" in df_filtered.columns else 0
        media_realizado = df_filtered["percentual_realizado"].mean() if "percentual_realizado" in df_filtered.columns else 0
        total_horas = df_filtered["horas_operacao_num"].sum() if "horas_operacao_num" in df_filtered.columns else 0
    
        col1, col2, col3 = st.columns(3)
        col1.metric("Total de KM", f"{total_km:,.0f} km")
        col2.metric("% Médio Realizado", f"{media_realizado:.1f}%")
        col3.metric("Total de Horas", f"{total_horas:.1f} h")
    
        # Gráfico de KM por subprefeitura
        if "subprefeitura" in df_filtered.columns and "total_de_kms" in df_filtered.columns:
            km_por_sub = df_filtered.groupby("subprefeitura")["total_de_kms"].sum().reset_index()
            fig_km = px.bar(km_por_sub, x="total_de_kms", y="subprefeitura",
                            orientation='h', text="total_de_kms")
            fig_km.update_traces(texttemplate='%{text:.0f}', textposition='outside')
            st.plotly_chart(fig_km, use_container_width=True)
    
        # Gráfico da evolução do % realizado ao longo do tempo
        if "data" in df_filtered.columns and "percentual_realizado" in df_filtered.columns:
            evolucao = df_filtered.groupby("data")["percentual_realizado"].mean().reset_index()
            fig_realizado = px.line(evolucao, x="data", y="percentual_realizado", markers=True)
            st.plotly_chart(fig_realizado, use_container_width=True)





    
        
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
