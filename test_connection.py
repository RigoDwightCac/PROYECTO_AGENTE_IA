# test_connection.py
import os
from dotenv import load_dotenv
import mysql.connector

# Cargar variables del archivo .env
load_dotenv()

print("DEBUG:", os.getenv("MYSQL_HOST"), os.getenv("MYSQL_PORT"))

# Leer las variables correctamente
host = os.getenv("MYSQL_HOST")
port = int(os.getenv("MYSQL_PORT"))
user = os.getenv("MYSQL_USER")
pwd  = os.getenv("MYSQL_PASS")
db   = os.getenv("MYSQL_DB")

print(f"Conectando a MySQL en {host}:{port} como {user}...")

try:
    conn = mysql.connector.connect(
        host=host,
        port=port,
        user=user,
        password=pwd,
        database=db,
        charset='utf8mb4'
    )
    print("✅ Conexión exitosa a la base de datos:", db)
    cur = conn.cursor()
    cur.execute("SHOW TABLES;")
    print("\n📋 Tablas encontradas:")
    for (table,) in cur.fetchall():
        print(" -", table)
    cur.close()
    conn.close()

except mysql.connector.Error as err:
    print("❌ Error al conectar:", err)

