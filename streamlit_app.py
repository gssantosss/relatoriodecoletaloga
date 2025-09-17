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
