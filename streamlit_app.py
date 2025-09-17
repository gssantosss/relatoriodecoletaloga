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
# Filtros globais unificados
# =========================

# Filtrar apenas linhas com datas válidas
if "data" in df_banco.columns:
    df_banco["data"] = pd.to_datetime(df_banco["data"], dayfirst=True, errors="coerce")
    df_banco = df_banco[df_banco["data"].notna()]  # remove datas inválidas
    df_banco["mesano"] = df_banco["data"].dt.strftime("%m/%Y")


# Granularidade
granularidade = st.sidebar.radio("Filtrar por:", ["Mês/Ano", "Período de Dias"])

if granularidade == "Mês/Ano":
    f_mesano = st.sidebar.multiselect(
        "Mês/Ano",
        sorted(df_banco["mesano"].unique())
    )
    f_periodo = None
else:
    min_date = df_banco["data"].min()
    max_date = df_banco["data"].max()
    f_periodo = st.sidebar.date_input(
        "Período (dd/mm/aaaa)",
        [min_date, max_date],
        min_value=min_date,
        max_value=max_date,
        format="DD/MM/YYYY"
    )
    f_mesano = None

# =========================
# Abas (fora do if/else)
# =========================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Visão Geral","🗂️ Setores", "🚛 Veículos", "📐 Quilometragem", "⏱️ Horas"
])

    with tab1:
        st.subheader("Análise Geral")
            st.subheader("Análise Geral")
        
            # Garantir que as colunas numéricas estão no formato certo
            if "total_de_kms" in df_filtered.columns:
                df_filtered["total_de_kms"] = pd.to_numeric(df_filtered["total_de_kms"], errors="coerce")
        
            if "%_realizado" in df_filtered.columns:
                df_filtered["%_realizado"] = pd.to_numeric(df_filtered["%_realizado"], errors="coerce")
        
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
            media_realizado = df_filtered["%_realizado"].mean() if "%_realizado" in df_filtered.columns else 0
            total_horas = df_filtered["horas_operacao_num"].sum() if "horas_operacao_num" in df_filtered.columns else 0
        
            col1, col2, col3 = st.columns(3)
            col1.metric("Total de KM", f"{total_km:,.0f} km")
            col2.metric("% Médio Realizado", f"{media_realizado:.1f}%")
            col3.metric("Total de Horas", f"{total_horas:.1f} h")
        
            # Gráfico de KM por subprefeitura
            if "subprefeitura" in df_filtered.columns and "total_de_kms" in df_filtered.columns:
                km_por_sub = df_filtered.groupby("subprefeitura")["total_de_kms"].sum().reset_index()
                fig_km = px.bar(
                    km_por_sub,
                    x="total_de_kms",
                    y="subprefeitura",
                    orientation='h',
                    text="total_de_kms",
                    title="🚛 Quilometragem por Subprefeitura"
                )
                fig_km.update_traces(
                    texttemplate='%{text:.0f}', 
                    textposition='outside',
                    hovertemplate="<b>%{y}</b><br>KMs: %{x:,}"
                )
                fig_km.update_layout(
                    xaxis_title="Total de KM",
                    yaxis_title="Subprefeitura",
                    showlegend=False
                )
                st.plotly_chart(fig_km, use_container_width=True)
    
        
            # Gráfico da evolução do % realizado ao longo do tempo
            if "mesano" in df_filtered.columns and "%_realizado" in df_filtered.columns:
                evolucao = df_filtered.groupby("mesano")["%_realizado"].mean().reset_index()
                fig_realizado = px.line(
                    evolucao,
                    x="mesano",
                    y="%_realizado",
                    markers=True,
                    title="📈 Evolução do % Realizado"
                )
                # Adicionar rótulo de dados
                fig_realizado.update_traces(
                    text=evolucao["%_realizado"].round(1),
                    textposition="top center"
                )
            
                fig_realizado.update_layout(
                    xaxis_title="Mês/Ano",
                    yaxis_title="% Realizado",
                    hovermode="x unified"
                )
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
