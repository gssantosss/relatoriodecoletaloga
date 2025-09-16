import streamlit as st
import pandas as pd
import sqlite3

# --- Conexão com SQLite ---
def get_connection():
    return sqlite3.connect("relatorios.db")

st.title("📊 Relatórios de Coleta")

# --- Upload de Excel ---
uploaded_file = st.file_uploader("Suba o relatório em Excel", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    
    # --- Padronização ---
    if 'Data' in df.columns:
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
    df = df.where(pd.notnull(df), None)  # substitui NaN por None
    
    # --- Salvar no banco ---
    conn = get_connection()
    try:
        df.to_sql("relatorios", conn, if_exists="append", index=False)
        st.success("Relatório salvo no banco com sucesso ✅")
    except Exception as e:
        st.error(f"Erro ao salvar no banco: {e}")
    finally:
        conn.close()
    
    st.write("Pré-visualização do arquivo:")
    st.dataframe(df.head())

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

# --- Garantir coluna de mês ---
if 'Data' not in df.columns:
    st.error("Coluna 'Data' não encontrada no banco.")
    st.stop()
df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
df['MesAno'] = df['Data'].dt.to_period("M").astype(str)

# --- Seleção de filtros ---
col_filtro = st.selectbox("Escolha a coluna para filtro:", [c for c in df.columns if c not in ["Data", "MesAno"]])
val_filtro = st.selectbox(f"Escolha o valor em {col_filtro}:", df[col_filtro].dropna().unique())

colunas_numericas = df.select_dtypes(include="number").columns.tolist()
if not colunas_numericas:
    st.error("Não há colunas numéricas para métricas.")
    st.stop()

col_metrica1 = st.selectbox("Escolha a primeira métrica:", colunas_numericas)
col_metrica2 = st.selectbox("Escolha a segunda métrica (opcional):", ["Nenhuma"] + colunas_numericas)

# --- Filtrar DataFrame ---
df_filtrado = df[df[col_filtro] == val_filtro]

# --- Agrupar por mês ---
resumo = df_filtrado.groupby("MesAno").agg({col_metrica1: "sum"}).reset_index()

if col_metrica2 != "Nenhuma":
    resumo2 = df_filtrado.groupby("MesAno").agg({col_metrica2: "sum"}).reset_index()
    resumo = resumo.merge(resumo2, on="MesAno")

# --- Delta percentual ---
resumo['Delta_%_' + col_metrica1] = resumo[col_metrica1].pct_change().fillna(0) * 100

# --- Mostrar resultados ---
st.subheader(f"Comparativo de métricas para {val_filtro} ({col_filtro})")
st.dataframe(resumo)

# --- Gráfico simples ---
cols_grafico = [col_metrica1] + ([col_metrica2] if col_metrica2 != "Nenhuma" else [])
st.line_chart(resumo.set_index("MesAno")[cols_grafico])
