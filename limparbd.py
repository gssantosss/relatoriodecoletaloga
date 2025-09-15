import sqlite3

# conecta no banco (tem que estar no mesmo diretório do script)
conn = sqlite3.connect("relatorios.db")
cursor = conn.cursor()

# apaga tudo da tabela relatorios
cursor.execute("DELETE FROM relatorios")

conn.commit()
conn.close()

print("Banco limpo com sucesso!")
