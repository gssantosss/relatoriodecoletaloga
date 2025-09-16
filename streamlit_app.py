import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

# --- Conexão com banco e criação de tabela se não existir ---
def get_connection():
    conn = sqlite3.connect("relatorios.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS relatorios (
            Data TEXT,
            Coluna1 TEXT,
            Coluna2 REAL,
            Coluna3 REAL
            -- Adicione outras colunas que você espera receber
        )
    """)
    return conn

st.title("📊 Relatórios de Coleta")

# --- Upload de arquivo ---
uploaded_file = st.file_uploader("Suba o relatório em Excel", type=["xlsx"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    st.write("Pré-visualização do arquivo:")
    st.dataframe(df.head())

    # Salva no banco
    conn = get_connection()
    df.to_sql("relatorios", conn, if_exists="append", index=False)
    conn.close()
    st.success("Relatório salvo no banco com sucesso ✅")

# --- Ler dados do banco com segurança ---
conn = get_connection()
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='relatorios'")
if cursor.fetchone():
    df = pd.read_sql("SELECT * FROM relatorios", conn)
else:
    df = pd.DataFrame()
conn.close()

if df.empty:
    st.info("Nenhum relatório carregado ainda.")
    st.stop()

# --- Garantir coluna de data ---
if 'Data' in df.columns:
    df['Data'] = pd.to_datetime(df['Data'])
    df['MesAno'] = df['Data'].dt.to_period("M").astype(str)
else:
    st.error("Coluna 'Data' não encontrada no relatório.")
    st.stop()

# --- Seleção de filtros ---
col_filtro = st.selectbox("Escolha a coluna para o filtro:", [c for c in df.columns if c not in ["Data", "MesAno"]])
val_filtro = st.selectbox(f"Escolha o valor em {col_filtro}:", df[col_filtro].dropna().unique())

colunas_numericas = df.select_dtypes(include="number").columns.tolist()
col_metrica1 = st.selectbox("Escolha a primeira métrica:", colunas_numericas)
col_metrica2 = st.selectbox("Escolha a segunda métrica (opcional):", ["Nenhuma"] + colunas_numericas)

# --- Filtrar DataFrame ---
df_filtrado = df[df[col_filtro] == val_filtro]

# --- Agrupar por mês e somar ---
resumo = df_filtrado.groupby("MesAno").agg({col_metrica1: "sum"}).reset_index()

if col_metrica2 != "Nenhuma":
    resumo2 = df_filtrado.groupby("MesAno").agg({col_metrica2: "sum"}).reset_index()
    resumo = resumo.merge(resumo2, on="MesAno")

# --- Variação percentual ---
resumo['Delta_%_' + col_metrica1] = resumo[col_metrica1].pct_change().fillna(0) * 100

# --- Mostrar tabela ---
st.subheader(f"Comparativo de métricas para {val_filtro} ({col_filtro})")
st.dataframe(resumo)

# --- Gráfico interativo ---
cols_grafico = [col_metrica1] + ([col_metrica2] if col_metrica2 != "Nenhuma" else [])
fig = px.line(resumo, x="MesAno", y=cols_grafico, markers=True)
st.plotly_chart(fig)
