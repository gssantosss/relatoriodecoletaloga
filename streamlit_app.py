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
    
        if not df_filtered.empty:
    
            # -------------------------
            # Normalizar coluna de horas
            # -------------------------
            def horas_para_decimal(hora_str):
                """
                Converte '9h 10m' ou número em horas decimais.
                """
                if pd.isna(hora_str):
                    return 0
                if isinstance(hora_str, (int, float)):
                    return hora_str
                partes = hora_str.split("h")
                try:
                    horas = int(partes[0].strip())
                    minutos = int(partes[1].replace("m", "").strip()) if len(partes) > 1 else 0
                    return horas + minutos / 60
                except:
                    return 0
    
            if "horas_operacao" in df_filtered.columns:
                df_filtered["horas_operacao_decimal"] = df_filtered["horas_operacao"].apply(horas_para_decimal)
            else:
                df_filtered["horas_operacao_decimal"] = 0
    
            # -------------------------
            # Cards principais
            # -------------------------
            total_km = df_filtered["total_de_kms"].sum() if "total_de_kms" in df_filtered.columns else 0
            total_horas = df_filtered["horas_operacao_decimal"].sum()
            pct_realizado = int(df_filtered["%_realizado"].mean()) if "%_realizado" in df_filtered.columns else 0
    
            # Top setor por KM
            if "subprefeitura" in df_filtered.columns and "km" in df_filtered.columns:
                top_setor_km = df_filtered.groupby("subprefeitura")["km"].sum().sort_values(ascending=False).index[0]
            else:
                top_setor_km = "N/A"
    
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("📈 % Realizado", f"{pct_realizado}%")
            col2.metric("🛣 Total KM", f"{total_km} km")
            col3.metric("⏱ Total Horas", f"{round(total_horas,1)} h")
            col4.metric("🏆 Setor com maior KM", top_setor_km)
    
            # -------------------------
            # Gráfico de barras: KM por setor
            # -------------------------
            if "subprefeitura" in df_filtered.columns and "km" in df_filtered.columns:
                km_por_setor = df_filtered.groupby("subprefeitura")["km"].sum().reset_index()
                km_por_setor = km_por_setor.sort_values("km", ascending=True)
                fig_km = px.bar(km_por_setor, x="km", y="subprefeitura", orientation='h', text="km")
                st.plotly_chart(fig_km, use_container_width=True)
    
            # -------------------------
            # Gráfico de linha: evolução diária do % realizado
            # -------------------------
            if "data" in df_filtered.columns and "pct_realizado" in df_filtered.columns:
                evolucao = df_filtered.groupby("data")["pct_realizado"].mean().reset_index()
                fig_evol = px.line(evolucao, x="data", y="pct_realizado", markers=True)
                st.plotly_chart(fig_evol, use_container_width=True)
    
            # -------------------------
            # Tabela rápida: top 5 setores por % realizado
            # -------------------------
            if "subprefeitura" in df_filtered.columns and "%_realizado" in df_filtered.columns:
                top_setores_% = df_filtered.groupby("subprefeitura")["pct_realizado"].mean().sort_values(ascending=False).head(5).reset_index()
                st.subheader("Top 5 setores por % realizado")
                st.dataframe(top_setores_%)
    
        else:
            st.info("Nenhum dado disponível para os filtros selecionados.")




    
        
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
