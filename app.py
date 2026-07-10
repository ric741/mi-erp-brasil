import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date

# 1. CONFIGURACIÓN DE LA PÁGINA (Debe ser lo primero)
st.set_page_config(page_title="ERP Brasil Final", layout="wide")

# 2. CONEXIÓN Y CREACIÓN DE LA BASE DE DATOS (SQLite)
DB_NAME = "erp_brasil.db"

def inicializar_bd():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Crear tabla de ventas
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
    
    # Crear tabla de trabajadores
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
    
    # Crear tabla de facturas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS facturas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        concepto TEXT,
        monto REAL,
        fecha_vencimiento TEXT
    )
    """)
    
    # Insertar datos de prueba si las tablas están vacías
    cursor.execute("SELECT COUNT(*) FROM ventas")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO ventas (mes, fecha, producto_servicio, cantidad, precio, total, trabajador) VALUES ('2026-07', '2026-07-01', 'Web Design', 2, 50.0, 100.0, 'Joao Silva')")
        cursor.execute("INSERT INTO trabajadores (mes, trabajador, producto_vendido, cantidad, valor_pago, total_pago) VALUES ('2026-07', 'Joao Silva', 'Web Design', 2, 15.0, 30.0)")
        cursor.execute("INSERT INTO facturas (concepto, monto, fecha_vencimiento) VALUES ('Conta de Luz', 40.0, '2026-07-15')")
    
    conn.commit()
    conn.close()

# Ejecutar la creación de la base de datos
inicializar_bd()

# Funciones de ayuda para la base de datos
def obtener_conexion():
    return sqlite3.connect(DB_NAME)

def cargar_datos(tabla_name):
    conn = obtener_conexion()
    df = pd.read_sql_query(f"SELECT * FROM {tabla_name}", conn)
    conn.close()
    return df

# 3. SISTEMA DE CONTROL DE ACCESO (LOGIN)
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
    st.session_state["usuario"] = ""
    st.session_state["rol"] = ""

# --- CASO A: EL USUARIO NO ESTÁ LOGUEADO ---
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

# --- CASO B: EL USUARIO SÍ ESTÁ LOGUEADO ---
else:
    # Barra lateral con saludo y botón de salida corregido
    st.sidebar.title(f"👤 Olá, {st.session_state['usuario'].capitalize()}")
    st.sidebar.write(f"Rol: {st.session_state['rol']}")
    
    if st.sidebar.button("🔒 Sair / Log Out"):
        st.session_state["autenticado"] = False
        st.session_state["usuario"] = ""
        st.session_state["rol"] = ""
        st.rerun()

    # Título principal de la aplicación
    st.title("📊 Panel de Control - ERP Brasil")
    st.write("Bienvenido al sistema de gestión de tu empresa.")
    
    # Crear pestañas de navegación organizadas
    tab_ventas, tab_trabajadores, tab_facturas = st.tabs(["💰 Ventas", "👥 Trabajadores", "📄 Facturas"])
    
    # Contenido de la pestaña de Ventas
    with tab_ventas:
        st.header("Registro de Ventas")
        df_ventas = cargar_datos("ventas")
        st.dataframe(df_ventas, use_container_width=True)
        
    # Contenido de la pestaña de Trabajadores
    with tab_trabajadores:
        st.header("Control de Pagos a Trabajadores")
        df_trabajadores = cargar_datos("trabajadores")
        st.dataframe(df_trabajadores, use_container_width=True)
        
    # Contenido de la pestaña de Facturas
    with tab_facturas:
        st.header("Cuentas y Facturas por Pagar")
        df_facturas = cargar_datos("facturas")
        st.dataframe(df_facturas, use_container_width=True)
