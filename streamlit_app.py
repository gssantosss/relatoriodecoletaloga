import streamlit as st
import pandas as pd
import sqlite3

# Função pra conectar no banco
def get_connection():
    return sqlite3.connect("relatorios.db")

# Título do app
st.title("📊 Relatórios de Coleta")

# Upload do arquivo
uploaded_file = st.file_uploader("Suba o relatório em Excel", type=["xlsx"])

if uploaded_file is not None:
    # Ler o excel
    df = pd.read_excel(uploaded_file)

    # Mostrar preview
    st.write("Pré-visualização do arquivo:")
    st.dataframe(df.head())

    # Salvar no banco do zero
    conn = get_connection()
    cursor = conn.cursor()

    # Deleta tabela se já existir
    cursor.execute("DROP TABLE IF EXISTS relatorios")
    conn.commit()

    # Substitui a tabela completamente
    df.to_sql("relatorios", conn, if_exists="replace", index=False)
    conn.close()

    st.success("Relatório salvo no banco com sucesso ✅ (tabela recriada do zero)")

# Mostrar dados do banco
st.subheader("📂 Relatórios já armazenados")

conn = get_connection()
cursor = conn.cursor()

# Verifica se a tabela existe
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='relatorios'")
table_exists = cursor.fetchone()

if table_exists:
    df_banco = pd.read_sql("SELECT * FROM relatorios", conn)
    st.dataframe(df_banco)
else:
    st.info("Nenhum relatório foi carregado ainda.")

conn.close()

# --- Garantir coluna de mês ---
if table_exists:
    df = df_banco.copy()
    if 'Data' in df.columns:
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
        df['MesAno'] = df['Data'].dt.to_period("M").astype(str)
    else:
        st.stop()  # sem data não rola comparação

    # --- Usuário escolhe a coluna para FILTRAR ---
    col_filtro = st.selectbox("Escolha a coluna para o filtro:", [c for c in df.columns if c not in ["Data", "MesAno"]])
    val_filtro = st.selectbox(f"Escolha o valor em {col_filtro}:", df[col_filtro].dropna().unique())

    # --- Usuário escolhe a MÉTRICA ---
    colunas_numericas = df.select_dtypes(include="number").columns.tolist()
    col_metrica1 = st.selectbox("Escolha a primeira métrica:", colunas_numericas, index=0)
    col_metrica2 = st.selectbox("Escolha a segunda métrica (opcional):", ["Nenhuma"] + colunas_numericas, index=0)

    # --- Filtra o DataFrame ---
    df_filtrado = df[df[col_filtro] == val_filtro]

    # --- Agrupa por mês e soma ---
    resumo = df_filtrado.groupby("MesAno").agg({col_metrica1: "sum"}).reset_index()
    if col_metrica2 != "Nenhuma":
        resumo[col_metrica2] = df_filtrado.groupby("MesAno").agg({col_metrica2: "sum"}).values

    # --- Calcula variação mês a mês ---
    resumo['Delta_%_' + col_metrica1] = resumo[col_metrica1].pct_change() * 100

    # --- Mostrar resultados ---
    st.subheader(f"Comparativo de métricas para {val_filtro} ({col_filtro})")
    st.dataframe(resumo)

    # --- Visual bonitinho ---
    st.line_chart(resumo.set_index("MesAno")[[col_metrica1] + ([col_metrica2] if col_metrica2 != "Nenhuma" else [])])
