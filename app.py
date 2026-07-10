import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date, timedelta

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="ERP Brasil Profesional", layout="wide")

# 2. CONEXIÓN Y FUNCIONES DE LA BASE DE DATOS
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
    conn.commit()
    conn.close()

inicializar_bd()

def obtener_conexion():
    return sqlite3.connect(DB_NAME)

def cargar_datos(tabla_name):
    conn = obtener_conexion()
    df = pd.read_sql_query(f"SELECT * FROM {tabla_name} ORDER BY id DESC", conn)
    conn.close()
    return df

# 3. CONTROL DE ACCESO (LOGIN)
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
    st.session_state["usuario"] = ""
    st.session_state["rol"] = ""

# --- PANTALLA DE LOGIN ---
if not st.session_state["autenticado"]:
    st.title("🔑 Login - ERP Brasil")
    usuario_input = st.text_input("Usuário", key="login_user")
    contrasena_input = st.text_input("Senha", type="password", key="login_pass")
    
    if st.button("Entrar"):
        if usuario_input == "admin" and contrasena_input == "admin2017":
            st.session_state["autenticado"] = True
            st.session_state["usuario"] = usuario_input
            st.session_state["rol"] = "admin"
            st.rerun()
        elif usuario_input == "trabajador" and contrasena_input == "trabaja2017":
            st.session_state["autenticado"] = True
            st.session_state["usuario"] = usuario_input
            st.session_state["rol"] = "trabajador"
            st.rerun()
        else:
            st.error("❌ Usuário ou senha incorretos.")

# --- PANTALLA PRINCIPAL DEL ERP (LOGUEADO) ---
else:
    # --- MENÚ LATERAL (SALUDO, CERRAR SESIÓN Y FILTROS) ---
    st.sidebar.title(f"👤 Olá, {st.session_state['usuario'].capitalize()}")
    
    if st.sidebar.button("🔒 Sair / Log Out"):
        st.session_state["autenticado"] = False
        st.session_state["usuario"] = ""
        st.session_state["rol"] = ""
        st.rerun()
        
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎯 Filtros Generales")
    
    # Cargar datos base para los filtros
    df_ventas_base = cargar_datos("ventas")
    df_trabajadores_base = cargar_datos("trabajadores")
    df_facturas_base = cargar_datos("facturas")
    
    # Filtro de Mes
    lista_meses = ["Todos"]
    if not df_ventas_base.empty:
        lista_meses.extend(sorted(df_ventas_base["mes"].unique().tolist(), reverse=True))
    mes_seleccionado = st.sidebar.selectbox("Filtrar por Mes:", lista_meses)
    
    # Filtro de Trabajador
    lista_trabajadores = ["Todos"]
    if not df_ventas_base.empty:
        lista_trabajadores.extend(sorted(df_ventas_base["trabajador"].unique().tolist()))
    trabajador_seleccionado = st.sidebar.selectbox("Filtrar por Trabajador:", lista_trabajadores)

    # Filtro de Producto / Servicio
    lista_productos = ["Todos"]
    if not df_ventas_base.empty:
        lista_productos.extend(sorted(df_ventas_base["producto_servicio"].unique().tolist()))
    producto_seleccionado = st.sidebar.selectbox("Filtrar por Producto/Servicio:", lista_productos)

    # --- APLICAR FILTROS A LOS DATOS ---
    df_v_filtrado = df_ventas_base.copy()
    df_t_filtrado = df_trabajadores_base.copy()

    if mes_seleccionado != "Todos":
        df_v_filtrado = df_v_filtrado[df_v_filtrado["mes"] == mes_seleccionado]
        df_t_filtrado = df_t_filtrado[df_t_filtrado["mes"] == mes_seleccionado]
        
    if trabajador_seleccionado != "Todos":
        df_v_filtrado = df_v_filtrado[df_v_filtrado["trabajador"] == trabajador_seleccionado]
        df_t_filtrado = df_t_filtrado[df_t_filtrado["trabajador"] == trabajador_seleccionado]

    if producto_seleccionado != "Todos":
        df_v_filtrado = df_v_filtrado[df_v_filtrado["producto_servicio"] == producto_seleccionado]
        df_t_filtrado = df_t_filtrado[df_t_filtrado["producto_vendido"] == producto_seleccionado]

    # --- CONTENIDO PRINCIPAL ---
    st.title("📊 Sistema de Gestión - ERP Brasil")
    
    # --- RESUMEN DE TOTALES (A PRIMERA HORA) ---
    st.subheader("💰 Resumen Financiero General")
    
    total_ventas = df_v_filtrado["total"].sum() if not df_v_filtrado.empty else 0.0
    total_facturas = df_facturas_base["monto"].sum() if not df_facturas_base.empty else 0.0
    saldo_restante = total_ventas - total_facturas

    col_v, col_f, col_s = st.columns(3)
    with col_v:
        st.metric(label="Total de Ventas", value=f"R$ {total_ventas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    with col_f:
        st.metric(label="Total a Pagar (Facturas)", value=f"R$ {total_facturas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), delta_color="inverse")
    with col_s:
        # Muestra en verde si es positivo, en rojo si es negativo
        st.metric(label="Valor Total Restante (Saldo)", value=f"R$ {saldo_restante:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    st.markdown("---")

    # --- SECCIÓN AUTOMÁTICA DE ALERTAS DE FACTURAS ---
    if not df_facturas_base.empty:
        st.subheader("🔔 Alertas de Facturas")
        hoy = date.today()
        limite_proximo = hoy + timedelta(days=7)
        
        for _, fila in df_facturas_base.iterrows():
            try:
                fecha_venc = datetime.strptime(fila["fecha_vencimiento"], "%Y-%m-%d").date()
                if fecha_venc < hoy:
                    st.error(f"🚨 **¡FACTURA VENCIDA!** {fila['concepto']} por R$ {fila['monto']:.2f} (Venció el {fila['fecha_vencimiento']})")
                elif hoy <= fecha_venc <= limite_proximo:
                    st.warning(f"⚠️ **Factura próxima a vencer:** {fila['concepto']} por R$ {fila['monto']:.2f} (Vence el {fila['fecha_vencimiento']})")
            except ValueError:
                pass

    # Pestañas de la aplicación
    tab_ventas, tab_trabajadores, tab_facturas = st.tabs(["💰 Ventas", "👥 Trabajadores", "📄 Facturas"])
    
    # --- SECCIÓN DE VENTAS ---
    with tab_ventas:
        st.header("Gestión de Ventas")
        
        with st.expander("➕ Registrar Nueva Venta"):
            with st.form("form_ventas", clear_on_submit=True):
                col1, col2, col3 = st.columns(3)
                with col1:
                    f_fecha = st.date_input("Fecha de Venta", date.today())
                    f_trabajador = st.text_input("Nombre del Trabajador")
                with col2:
                    f_producto = st.text_input("Producto o Servicio")
                    f_cantidad = st.number_input("Cantidad", min_value=1, value=1, step=1)
                with col3:
                    f_precio = st.number_input("Precio Unitario (R$)", min_value=0.0, value=0.0, step=10.0)
                
                enviar_venta = st.form_submit_button("Guardar Venta")
                
                if enviar_venta:
                    if f_producto and f_trabajador:
                        f_mes = f_fecha.strftime("%Y-%m")
                        f_total = f_cantidad * f_precio
                        
                        conn = obtener_conexion()
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO ventas (mes, fecha, producto_servicio, cantidad, precio, total, trabajador)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (f_mes, str(f_fecha), f_producto, f_cantidad, f_precio, f_total, f_trabajador))
                        conn.commit()
                        conn.close()
                        st.success("✅ Venta registrada con éxito!")
                        st.rerun()
                    else:
                        st.error("⚠️ Por favor rellena todos los campos.")
        
        st.subheader("Historial de Ventas")
        st.dataframe(df_v_filtrado, use_container_width=True)

    # --- SECCIÓN DE TRABAJADORES ---
    with tab_trabajadores:
        st.header("Gestión de Trabajadores y Pagos")
        
        with st.expander("➕ Registrar Pago a Trabajador"):
            with st.form("form_trabajadores", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    t_nombre = st.text_input("Nombre del Trabajador")
                    t_producto = st.text_input("Producto/Servicio Vendido")
                with col2:
                    t_cantidad = st.number_input("Cantidad Vendida", min_value=1, value=1, step=1)
                    t_valor = st.number_input("Pago por Unidad (R$)", min_value=0.0, value=0.0, step=5.0)
                
                enviar_trabajador = st.form_submit_button("Guardar Registro")
                
                if enviar_trabajador:
                    if t_nombre and t_producto:
                        t_mes = datetime.now().strftime("%Y-%m")
                        t_total = t_cantidad * t_valor
                        
                        conn = obtener_conexion()
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO trabajadores (mes, trabajador, producto_vendido, cantidad, valor_pago, total_pago)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (t_mes, t_nombre, t_producto, t_cantidad, t_valor, t_total))
                        conn.commit()
                        conn.close()
                        st.success("✅ Pago registrado con éxito!")
                        st.rerun()
                    else:
                        st.error("⚠️ Por favor rellena todos los campos.")

        st.subheader("Historial de Pagos")
        st.dataframe(df_t_filtrado, use_container_width=True)

    # --- SECCIÓN DE FACTURAS ---
    with tab_facturas:
        st.header("Gestión de Facturas por Pagar")
        
        with st.expander("➕ Agregar Nueva Factura"):
            with st.form("form_facturas", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    fac_concepto = st.text_input("Concepto (Ej: Luz, Internet, Renta)")
                with col2:
                    fac_monto = st.number_input("Monto de la Factura (R$)", min_value=0.0, value=0.0, step=10.0)
                    fac_vencimiento = st.date_input("Fecha de Vencimiento", date.today())
                
                enviar_factura = st.form_submit_button("Guardar Factura")
                
                if enviar_factura:
                    if fac_concepto:
                        conn = obtener_conexion()
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO facturas (concepto, monto, fecha_vencimiento)
                            VALUES (?, ?, ?)
                        """, (fac_concepto, fac_monto, str(fac_vencimiento)))
                        conn.commit()
                        conn.close()
                        st.success("✅ Factura guardada con éxito!")
                        st.rerun()
                    else:
                        st.error("⚠️ El concepto de la factura no puede estar vacío.")

        st.subheader("Lista de Facturas")
        st.dataframe(df_facturas_base, use_container_width=True)
