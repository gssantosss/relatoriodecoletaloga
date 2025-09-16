import streamlit as st
import pandas as pd
import sqlite3

# Conexão com o banco
def get_connection():
    return sqlite3.connect("relatorios.db")

st.title("📊 Relatórios de Coleta")

# --- Upload de arquivos ---
uploaded_file = st.file_uploader("Suba o relatório em Excel", type=["xlsx"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)

    # Preview
    st.write("Pré-visualização do arquivo:")
    st.dataframe(df.head())

    # Salva no banco
    conn = get_connection()
    df.to_sql("relatorios", conn, if_exists="append", index=False)
    conn.close()
    st.success("Relatório salvo no banco com sucesso ✅")

# --- Mostrar dados do banco ---
st.subheader("📂 Relatórios já armazenados")
conn = get_connection()
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='relatorios'")
table_exists = cursor.fetchone()

if table_exists:
    df = pd.read_sql("SELECT * FROM relatorios", conn)
    conn.close()

    # Garantir coluna de mês
    if 'Data' in df.columns:
        df['Data'] = pd.to_datetime(df['Data'])
        df['MesAno'] = df['Data'].dt.to_period("M").astype(str)
    else:
        st.stop()

    # --- Filtros ---
    col_filtro = st.selectbox("Escolha a coluna para o filtro:", [c for c in df.columns if c not in ["Data","MesAno"]])
    val_filtro = st.selectbox(f"Escolha o valor em {col_filtro}:", df[col_filtro].dropna().unique())

    # --- Métricas ---
    colunas_numericas = df.select_dtypes(include="number").columns.tolist()
    col_metrica1 = st.selectbox("Escolha a primeira métrica:", colunas_numericas, index=0)
    col_metrica2 = st.selectbox("Escolha a segunda métrica (opcional):", ["Nenhuma"] + colunas_numericas, index=0)

    # --- Filtrar ---
    df_filtrado = df[df[col_filtro] == val_filtro]

    # --- Agrupar ---
    resumo = df_filtrado.groupby("MesAno").agg({col_metrica1: "sum"}).reset_index()
    if col_metrica2 != "Nenhuma":
        resumo[col_metrica2] = df_filtrado.groupby("MesAno").agg({col_metrica2: "sum"}).values

    resumo['Variação_%_' + col_metrica1] = resumo[col_metrica1].pct_change() * 100

    # --- Exibir ---
    st.subheader(f"Comparativo de métricas para {val_filtro} ({col_filtro})")
    st.dataframe(resumo)
    st.line_chart(resumo.set_index("MesAno")[[col_metrica1] + ([col_metrica2] if col_metrica2 != "Nenhuma" else [])])

else:
    st.info("Nenhum relatório foi carregado ainda.")
