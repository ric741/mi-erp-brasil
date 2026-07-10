import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date

# Configuración de la página
st.set_page_config(page_title="ERP Brasil Final", layout="wide")

# --- CONEXIÓN Y CREACIÓN DE LA BASE DE DATOS (SQLite) ---
DB_NAME = "erp_brasil.db"

def inicializar_bd():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ventas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mes TEXT,
        fecha TEXT,
        producto_servicio TEXT,
        cantidad INTEGER,
        precio REAL,
        total REAL,
        trabajador TEXT
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS trabajadores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mes TEXT,
        trabajador TEXT,
        producto_vendido TEXT,
        cantidad INTEGER,
        valor_pago REAL,
        total_pago REAL
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS facturas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        concepto TEXT,
        monto REAL,
        fecha_vencimiento TEXT
    )
    """)
    
    cursor.execute("SELECT COUNT(*) FROM ventas")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO ventas (mes, fecha, producto_servicio, cantidad, precio, total, trabajador) VALUES ('2026-07', '2026-07-01', 'Web Design', 2, 50.0, 100.0, 'Joao Silva')")
        cursor.execute("INSERT INTO trabajadores (mes, trabajador, producto_vendido, cantidad, valor_pago, total_pago) VALUES ('2026-07', 'Joao Silva', 'Web Design', 2, 15.0, 30.0)")
        cursor.execute("INSERT INTO facturas (concepto, monto, fecha_vencimiento) VALUES ('Conta de Luz', 40.0, '2026-07-15')")
    
    conn.commit()
    conn.close()

inicializar_bd()

def obtener_conexion():
    return sqlite3.connect(DB_NAME)

def cargar_datos(tabla_name):
    conn = obtener_conexion()
    df = pd.read_sql_query(f"SELECT * FROM {tabla_name}", conn)
    conn.close()
    return df

def guardar_dataframe_seguro(df, tabla_name):
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {tabla_name}")
    df.to_sql(tabla_name, conn, if_exists="append", index=False)
    conn.commit()
    conn.close()

# --- SISTEMA DE CONTROL DE ACCESO (LOGIN) ---
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
    st.session_state["usuario"] = ""
    st.session_state["rol"] = ""

# Si no está autenticado, muestra el formulario de login de forma directa
if not st.session_state["autenticado"]:
    st.title("🔑 Login - ERP Brasil")
    usuario_input = st.text_input("Usuário", key="login_user")
    contrasena_input = st.text_input("Senha", type="password", key="login_pass")
    
    if st.button("Entrar"):
        if usuario_input == "admin" and contrasena_input == "admin123":
            st.session_state["autenticado"] = True
            st.session_state["usuario"] = usuario_input
            st.session_state["rol"] = "admin"
            st.rerun()
        elif usuario_input == "trabajador" and contrasena_input == "trabaja321":
            st.session_state["autenticado"] = True
            st.session_state["usuario"] = usuario_input
            st.session_state["rol"] = "trabajador"
            st.rerun()
        else:
            st.error("❌ Usuário ou senha incorretos.")

# Si está autenticado, carga toda la aplicación de manera normal
else:
    # --- MENU LATERAL Y FILTROS GENERALES ---
    st.sidebar.title(f"👤 Olá, {st.session_state['usuario'].capitalize()}")
    if st.sidebar.button("🔒 Sair / Log Out"):
        st.session_state["autenticado"] = False
        st.session_state["usuario"] = ""
        st.session_state

