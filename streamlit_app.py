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
df_banco = pd.read_sql("SELECT * FROM relatorios", conn)
conn.close()

st.dataframe(df_banco)
