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

    # Salvar no banco
    conn = get_connection()
    df.to_sql("relatorios", conn, if_exists="append", index=False)
    conn.close()

    st.success("Relatório salvo no banco com sucesso ✅")

# Mostrar dados do banco
st.subheader("📂 Relatórios já armazenados")

conn = get_connection()
cursor = conn.cursor()

# Verifica se a tabela já existe
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='relatorios'")
table_exists = cursor.fetchone()

if table_exists:
    df_banco = pd.read_sql("SELECT * FROM relatorios", conn)
    st.dataframe(df_banco)
else:
    st.info("Nenhum relatório foi carregado ainda.")


# --- Garantir coluna de mês ---
if 'Data' in df.columns:
    df['Data'] = pd.to_datetime(df['Data'])
    df['MesAno'] = df['Data'].dt.to_period("M").astype(str)
else:
    st.stop()  # sem data não rola comparação

# --- Escolha do usuário ---
col_filtro = st.selectbox("Escolha a coluna para filtrar:", [c for c in df.columns if c not in ["Data", "MesAno"]])
val_filtro = st.selectbox(f"Escolha o valor de {col_filtro}:", df[col_filtro].unique())

col_metrica = st.selectbox("Escolha a métrica para comparar:", ["KM_Planejado", "Horas_Operacao"])

# --- Filtra o DataFrame ---
df_filtrado = df[df[col_filtro] == val_filtro]

# --- Agrupa por mês ---
resumo = df_filtrado.groupby("MesAno").agg({col_metrica: "sum"}).reset_index()

# --- Calcula variação mês a mês ---
resumo['Delta_%'] = resumo[col_metrica].pct_change() * 100

# --- Mostra resultados ---
st.subheader(f"📊 Comparativo de {col_metrica} para {val_filtro} ({col_filtro})")
st.dataframe(resumo)

# --- Dica visual extra ---
st.line_chart(resumo.set_index("MesAno")[[col_metrica]])
