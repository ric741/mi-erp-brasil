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

def eliminar_registro(tabla_name, registro_id):
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {tabla_name} WHERE id = ?", (registro_id,))
    conn.commit()
    conn.close()

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

# --- PANTALLA PRINCIPAL DEL ERP ---
else:
    # --- MENÚ LATERAL ---
    st.sidebar.title(f"👤 Olá, {st.session_state['usuario'].capitalize()}")
    if st.sidebar.button("🔒 Sair / Log Out"):
        st.session_state["autenticado"] = False
        st.session_state["usuario"] = ""
        st.session_state["rol"] = ""
        st.rerun()
        
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎯 Filtros Generales")
    
    df_ventas_base = cargar_datos("ventas")
    df_trabajadores_base = cargar_datos("trabajadores")
    df_facturas_base = cargar_datos("facturas")
    
    # Filtros dinámicos
    lista_meses = ["Todos"]
    if not df_ventas_base.empty:
        lista_meses.extend(sorted(df_ventas_base["mes"].unique().tolist(), reverse=True))
    mes_seleccionado = st.sidebar.selectbox("Filtrar por Mes:", lista_meses)
    
    lista_trabajadores = ["Todos"]
    if not df_ventas_base.empty:
        lista_trabajadores.extend(sorted(df_ventas_base["trabajador"].unique().tolist()))
    trabajador_seleccionado = st.sidebar.selectbox("Filtrar por Trabajador:", lista_trabajadores)

    lista_productos = ["Todos"]
    if not df_ventas_base.empty:
        lista_productos.extend(sorted(df_ventas_base["producto_servicio"].unique().tolist()))
    producto_seleccionado = st.sidebar.selectbox("Filtrar por Producto/Servicio:", lista_productos)

    # Filtrado lógico
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
    
    # --- RESUMEN DE TOTALES ---
    st.subheader("💰 Resumen Financiero General")
    total_ventas = df_v_filtrado["total"].sum() if not df_v_filtrado.empty else 0.0
    total_facturas = df_facturas_base["monto"].sum() if not df_facturas_base.empty else 0.0
    saldo_restante = total_ventas - total_facturas

    col_v, col_f, col_s = st.columns(3)
    with col_v:
        st.metric(label="Total de Ventas", value=f"R$ {total_ventas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    with col_f:
        st.metric(label="Total a Pagar (Facturas)", value=f"R$ {total_facturas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    with col_s:
        st.metric(label="Valor Total Restante (Saldo)", value=f"R$ {saldo_restante:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    st.markdown("---")

    # --- ALERTAS DE FACTURAS ---
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

    # Pestañas principales
    tab_ventas, tab_trabajadores, tab_facturas = st.tabs(["💰 Ventas", "👥 Trabajadores", "📄 Facturas"])
    
    # --- VENTAS ---
    with tab_ventas:
        st.header("Gestión de Ventas")
        with st.expander("➕ Registrar Nueva Venta"):
            with st.form("form_ventas", clear_on_submit=True):
                col1, col2, col3 = st.columns(3)
                with col1:
                    f_fecha = st.date_input("Fecha de Venta", date.today(), key="nv_fecha")
                    f_trabajador = st.text_input("Nombre del Trabajador", key="nv_trab")
                with col2:
                    f_producto = st.text_input("Producto o Servicio", key="nv_prod")
                    f_cantidad = st.number_input("Cantidad", min_value=1, value=1, step=1, key="nv_cant")
                with col3:
                    f_precio = st.number_input("Precio Unitario (R$)", min_value=0.0, value=0.0, step=10.0, key="nv_prec")
                
                enviar_venta = st.form_submit_button("Guardar Venta")
                if enviar_venta and f_producto and f_trabajador:
                    f_mes = f_fecha.strftime("%Y-%m")
                    f_total = f_cantidad * f_precio
                    conn = obtener_conexion()
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO ventas (mes, fecha, producto_servicio, cantidad, precio, total, trabajador) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                                   (f_mes, str(f_fecha), f_producto, f_cantidad, f_precio, f_total, f_trabajador))
                    conn.commit()
                    conn.close()
                    st.success("✅ Venta registrada!")
                    st.rerun()

        st.subheader("Historial de Ventas")
        if not df_v_filtrado.empty:
            for idx, fila in df_v_filtrado.iterrows():
                col_texto, col_edit, col_btn = st.columns([8, 1, 1])
                with col_texto:
                    st.write(f"📅 {fila['fecha']} | 👤 {fila['trabajador']} | 📦 {fila['producto_servicio']} | {fila['cantidad']}x | **R$ {fila['total']:.2f}**")
                with col_edit:
                    exp_edit_v = st.expander("✏️")
                with col_btn:
                    if st.button("🗑️", key=f"del_v_{fila['id']}"):
                        eliminar_registro("ventas", fila["id"])
                        st.rerun()
                
                # Desplegable interno para editar el registro actual
                with exp_edit_v:
                    with st.form(f"edit_form_v_{fila['id']}"):
                        ev_fecha = st.date_input("Modificar Fecha", datetime.strptime(fila['fecha'], "%Y-%m-%d").date(), key=f"ef_{fila['id']}")
                        ev_trab = st.text_input("Trabajador", fila['trabajador'], key=f"et_{fila['id']}")
                        ev_prod = st.text_input("Producto", fila['producto_servicio'], key=f"ep_{fila['id']}")
                        ev_cant = st.number_input("Cantidad", min_value=1, value=int(fila['cantidad']), key=f"ec_{fila['id']}")
                        ev_prec = st.number_input("Precio (R$)", min_value=0.0, value=float(fila['precio']), key=f"epr_{fila['id']}")
                        
                        if st.form_submit_button("Actualizar Registro"):
                            ev_mes = ev_fecha.strftime("%Y-%m")
                            ev_total = ev_cant * ev_prec
                            conn = obtener_conexion()
                            cursor = conn.cursor()
                            cursor.execute("UPDATE ventas SET mes=?, fecha=?, producto_servicio=?, cantidad=?, precio=?, total=?, trabajador=? WHERE id=?",
                                           (ev_mes, str(ev_fecha), ev_prod, ev_cant, ev_prec, ev_total, ev_trab, fila['id']))
                            conn.commit()
                            conn.close()
                            st.success("¡Modificado!")
                            st.rerun()
        else:
            st.info("No hay ventas registradas.")

    # --- TRABAJADORES ---
    with tab_trabajadores:
        st.header("Gestión de Trabajadores y Pagos")
        with st.expander("➕ Registrar Pago a Trabajador"):
            with st.form("form_trabajadores", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    t_nombre = st.text_input("Nombre del Trabajador", key="nt_nomb")
                    t_producto = st.text_input("Producto/Servicio Vendido", key="nt_prod")
                with col2:
                    t_cantidad = st.number_input("Cantidad Vendida", min_value=1, value=1, step=1, key="nt_cant")
                    t_valor = st.number_input("Pago por Unidad (R$)", min_value=0.0, value=0.0, step=5.0, key="nt_val")
                
                enviar_trabajador = st.form_submit_button("Guardar Registro")
                if enviar_trabajador and t_nombre and t_producto:
                    t_mes = datetime.now().strftime("%Y-%m")
                    t_total = t_cantidad * t_valor
                    conn = obtener_conexion()
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO trabajadores (mes, trabajador, producto_vendido, quantity, valor_pago, total_pago) VALUES (?, ?, ?, ?, ?, ?)", 
                                   (t_mes, t_nombre, t_producto, t_cantidad, t_valor, t_total))
                    conn.commit()
                    conn.close()
                    st.success("✅ Pago registrado!")
                    st.rerun()

        st.subheader("Historial de Pagos")
        if not df_t_filtrado.empty:
            for idx, fila in df_t_filtrado.iterrows():
                col_texto, col_edit, col_btn = st.columns([8, 1, 1])
                with col_texto:
                    st.write(f"👤 {fila['trabajador']} | 📦 {fila['producto_vendido']} | {fila['cantidad']} uds | **Pago: R$ {fila['total_pago']:.2f}**")
                with col_edit:
                    exp_edit_t = st.expander("✏️")
                with col_btn:
                    if st.button("🗑️", key=f"del_t_{fila['id']}"):
                        eliminar_registro("trabajadores", fila["id"])
                        st.rerun()
                        
                with exp_edit_t:
                    with st.form(f"edit_form_t_{fila['id']}"):
                        et_nomb = st.text_input("Trabajador", fila['trabajador'], key=f"etn_{fila['id']}")
                        et_prod = st.text_input("Producto", fila['producto_vendido'], key=f"etp_{fila['id']}")
                        et_cant = st.number_input("Cantidad", min_value=1, value=int(fila['cantidad']), key=f"etc_{fila['id']}")
                        et_val = st.number_input("Valor (R$)", min_value=0.0, value=float(fila['valor_pago']), key=f"etv_{fila['id']}")
                        
                        if st.form_submit_button("Actualizar Registro"):
                            et_total = et_cant * et_val
                            conn = obtener_conexion()
                            cursor = conn.cursor()
                            cursor.execute("UPDATE trabajadores SET trabajador=?, producto_vendido=?, cantidad=?, valor_pago=?, total_pago=? WHERE id=?",
                                           (et_nomb, et_prod, et_cant, et_val, et_total, fila['id']))
                            conn.commit()
                            conn.close()
                            st.success("¡Modificado!")
                            st.rerun()
        else:
            st.info("No hay pagos registrados.")

    # --- FACTURAS ---
    with tab_facturas:
        st.header("Gestión de Facturas por Pagar")
        with st.expander("➕ Agregar Nueva Factura"):
            with st.form("form_facturas", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    fac_concepto = st.text_input("Concepto (Ej: Luz, Internet, Renta)", key="nf_con")
                with col2:
                    fac_monto = st.number_input("Monto de la Factura (R$)", min_value=0.0, value=0.0, step=10.0, key="nf_mon")
                    fac_vencimiento = st.date_input("Fecha de Vencimiento", date.today(), key="nf_ven")
                
                enviar_factura = st.form_submit_button("Guardar Factura")
                if enviar_factura and fac_concepto:
                    conn = obtener_conexion()
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO facturas (concepto, monto, fecha_vencimiento) VALUES (?, ?, ?)", 
                                   (fac_concepto, fac_monto, str(fac_vencimiento)))
                    conn.commit()
                    conn.close()
                    st.success("✅ Factura guardada!")
                    st.rerun()

        st.subheader("Lista de Facturas")
        if not df_facturas_base.empty:
            for idx, fila in df_facturas_base.iterrows():
                col_texto, col_edit, col_btn = st.columns([8, 1, 1])
                with col_texto:
                    st.write(f"📄 {fila['concepto']} | 💰 **R$ {fila['monto']:.2f}** | 📅 Vence: {fila['fecha_vencimiento']}")
                with col_edit:
                    exp_edit_f = st.expander("✏️")
                with col_btn:
                    if st.button("🗑️", key=f"del_f_{fila['id']}"):
                        eliminar_registro("facturas", fila["id"])
                        st.rerun()
                        
                with exp_edit_f:
                    with st.form(f"edit_form_f_{fila['id']}"):
                        ef_con = st.text_input("Concepto", fila['concepto'], key=f"efc_{fila['id']}")
                        ef_mon = st.number_input("Monto (R$)", min_value=0.0, value=float(fila['monto']), key=f"efm_{fila['id']}")
                        ef_ven = st.date_input("Vencimiento", datetime.strptime(fila['fecha_vencimiento'], "%Y-%m-%d").date(), key=f"efv_{fila['id']}")
                        
                        if st.form_submit_button("Actualizar Registro"):
                            conn = obtener_conexion()
                            cursor = conn.cursor()
                            cursor.execute("UPDATE facturas SET concepto=?, monto=?, fecha_vencimiento=? WHERE id=?",
                                           (ef_con, ef_mon, str(ef_ven), fila['id']))
                            conn.commit()
                            conn.close()
                            st.success("¡Modificado!")
                            st.rerun()
        else:
            st.info("No hay facturas registradas.")
