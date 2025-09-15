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
    
conn.close()

import streamlit as st
import pandas as pd
import sqlite3

# Função para conectar no banco
def get_connection():
    return sqlite3.connect("relatorios.db")

# Conecta e puxa todos os dados
conn = get_connection()
df = pd.read_sql("SELECT * FROM relatorios", conn)
conn.close()

# --- EXPLORAÇÃO BÁSICA ---
st.subheader("👀 Preview do banco")
st.dataframe(df.head())  # mostra as primeiras linhas

st.subheader("📊 Estatísticas básicas")
st.write(df.describe())  # estatísticas básicas das colunas numéricas

# --- FILTRAR VIAGENS ACIMA DE 8 HORAS ---
if 'Horas Operação' in df.columns:
    st.subheader("🚛 Viagens acima de 8 horas")
    viagens_longas = df[df['Horas Operação'] > 8]
    st.write(f"Total de viagens acima de 8h: {viagens_longas.shape[0]}")
    st.dataframe(viagens_longas)
