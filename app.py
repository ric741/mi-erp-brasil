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
    
    # Se añade la columna 'fecha' a la tabla de trabajadores
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS trabajadores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mes TEXT,
        fecha TEXT,
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
    
    # Script de migración automática por si la tabla ya existía sin la columna 'fecha'
    try:
        cursor.execute("ALTER TABLE trabajadores ADD COLUMN fecha TEXT")
    except sqlite3.OperationalError:
        pass # La columna ya existe
        
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

# --- PANTALLA PRINCIPAL ---
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
                fecha_venc = datetime.strptime(str(fila["fecha_vencimiento"]), "%Y-%m-%d").date()
                if fecha_venc < hoy:
                    st.error(f"🚨 **¡FACTURA VENCIDA!** {fila['concepto']} por R$ {fila['monto']:.2f} (Venció el {fila['fecha_vencimiento']})")
                elif hoy <= fecha_venc <= limite_proximo:
                    st.warning(f"⚠️ **Factura próxima a vencer:** {fila['concepto']} por R$ {fila['monto']:.2f} (Vence el {fila['fecha_vencimiento']})")
            except ValueError:
                pass
        st.markdown("---")

    # Pestañas principales
    tab_ventas, tab_trabajadores, tab_facturas = st.tabs(["💰 Ventas", "👥 Trabajadores", "📄 Facturas"])
    
    # --- TAB VENTAS ---
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

        st.subheader("📝 Historial Editable de Ventas")
        if not df_v_filtrado.empty:
            st.info("💡 Haz doble clic sobre cualquier celda para corregirla directamente. Al terminar, presiona el botón 'Guardar Cambios'.")
            
            ventas_editadas = st.data_editor(
                df_v_filtrado,
                column_config={
                    "id": st.column_config.NumberColumn("ID", disabled=True),
                    "mes": st.column_config.TextColumn("Mes", disabled=True),
                    "fecha": st.column_config.TextColumn("Fecha (AAAA-MM-DD)"),
                    "producto_servicio": st.column_config.TextColumn("Producto/Servicio"),
                    "cantidad": st.column_config.NumberColumn("Cantidad", min_value=1),
                    "precio": st.column_config.NumberColumn("Precio (R$)", format="R$ %.2f"),
                    "total": st.column_config.NumberColumn("Total Calculado", disabled=True, format="R$ %.2f"),
                    "trabajador": st.column_config.TextColumn("Trabajador")
                },
                num_rows="dynamic",
                hide_index=True,
                key="editor_ventas"
            )
            
            if st.button("💾 Guardar Cambios en Ventas"):
                conn = obtener_conexion()
                cursor = conn.cursor()
                for _, fila in ventas_editadas.iterrows():
                    nuevo_total = int(fila['cantidad']) * float(fila['precio'])
                    try:
                        fecha_dt = datetime.strptime(str(fila['fecha']), "%Y-%m-%d")
                        nuevo_mes = fecha_dt.strftime("%Y-%m")
                    except:
                        nuevo_mes = fila['mes']

                    cursor.execute("""
                        UPDATE ventas 
                        SET mes=?, fecha=?, producto_servicio=?, cantidad=?, precio=?, total=?, trabajador=? 
                        WHERE id=?
                    """, (nuevo_mes, str(fila['fecha']), fila['producto_servicio'], int(fila['cantidad']), float(fila['precio']), nuevo_total, fila['trabajador'], int(fila['id'])))
                conn.commit()
                conn.close()
                st.success("🎉 ¡Todos los cambios han sido guardados con éxito!")
                st.rerun()
        else:
            st.info("No hay ventas registradas.")

    # --- TAB TRABAJADORES ---
    with tab_trabajadores:
        st.header("Gestión de Trabajadores y Pagos")
        with st.expander("➕ Registrar Pago a Trabajador"):
            with st.form("form_trabajadores", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    t_fecha = st.date_input("Fecha de Registro/Pago", date.today(), key="nt_fecha")
                    t_nombre = st.text_input("Nombre del Trabajador")
                with col2:
                    t_producto = st.text_input("Producto/Servicio Vendido")
                    t_cantidad = st.number_input("Cantidad Vendida", min_value=1, value=1, step=1)
                    t_valor = st.number_input("Pago por Unidad (R$)", min_value=0.0, value=0.0, step=5.0)
                
                enviar_trabajador = st.form_submit_button("Guardar Registro")
                if enviar_trabajador and t_nombre and t_producto:
                    t_mes = t_fecha.strftime("%Y-%m")
                    t_total = t_cantidad * t_valor
                    conn = obtener_conexion()
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO trabajadores (mes, fecha, trabajador, producto_vendido, cantidad, valor_pago, total_pago) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                                   (t_mes, str(t_fecha), t_nombre, t_producto, t_cantidad, t_valor, t_total))
                    conn.commit()
                    conn.close()
                    st.success("✅ Pago registrado!")
                    st.rerun()

        st.subheader("📝 Historial Editable de Pagos")
        if not df_t_filtrado.empty:
            pagos_editados = st.data_editor(
                df_t_filtrado,
                column_config={
                    "id": st.column_config.NumberColumn("ID", disabled=True),
                    "mes": st.column_config.TextColumn("Mes", disabled=True),
                    "fecha": st.column_config.TextColumn("Fecha (AAAA-MM-DD)"),
                    "trabajador": st.column_config.TextColumn("Trabajador"),
                    "producto_vendido": st.column_config.TextColumn("Producto Vendido"),
                    "cantidad": st.column_config.NumberColumn("Cantidad"),
                    "valor_pago": st.column_config.NumberColumn("Pago x Unidad", format="R$ %.2f"),
                    "total_pago": st.column_config.NumberColumn("Total Pago", disabled=True, format="R$ %.2f")
                },
                num_rows="dynamic",
                hide_index=True,
                key="editor_trabajadores"
            )
            
            if st.button("💾 Guardar Cambios en Pagos"):
                conn = obtener_conexion()
                cursor = conn.cursor()
                for _, fila in pagos_editados.iterrows():
                    nuevo_total_pago = int(fila['cantidad']) * float(fila['valor_pago'])
                    try:
                        fecha_dt = datetime.strptime(str(fila['fecha']), "%Y-%m-%d")
                        nuevo_mes = fecha_dt.strftime("%Y-%m")
                    except:
                        nuevo_mes = fila['mes']
                        
                    cursor.execute("""
                        UPDATE trabajadores 
                        SET mes=?, fecha=?, trabajador=?, producto_vendido=?, cantidad=?, valor_pago=?, total_pago=? 
                        WHERE id=?
                    """, (nuevo_mes, str(fila['fecha']), fila['trabajador'], fila['producto_vendido'], int(fila['command'] if 'command' in fila else fila['cantidad']), float(fila['valor_pago']), nuevo_total_pago, int(fila['id'])))
                conn.commit()
                conn.close()
                st.success("🎉 Pagos y fechas actualizados de inmediato!")
                st.rerun()
        else:
            st.info("No hay pagos registrados.")

    # --- TAB FACTURAS ---
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
                if enviar_factura and fac_concepto:
                    conn = obtener_conexion()
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO facturas (concepto, monto, fecha_vencimiento) VALUES (?, ?, ?)", 
                                   (fac_concepto, fac_monto, str(fac_vencimiento)))
                    conn.commit()
                    conn.close()
                    st.success("✅ Factura guardada!")
                    st.rerun()

        st.subheader("📝 Lista Editable de Facturas")
        if not df_facturas_base.empty:
            facturas_editadas = st.data_editor(
                df_facturas_base,
                column_config={
                    "id": st.column_config.NumberColumn("ID", disabled=True),
                    "concepto": st.column_config.TextColumn("Concepto de la Factura"),
                    "monto": st.column_config.NumberColumn("Monto (R$)", format="R$ %.2f"),
                    "fecha_vencimiento": st.column_config.TextColumn("Vencimiento (AAAA-MM-DD)")
                },
                num_rows="dynamic",
                hide_index=True,
                key="editor_facturas"
            )
            
            if st.button("💾 Guardar Cambios en Facturas"):
                conn = obtener_conexion()
                cursor = conn.cursor()
                for _, fila in facturas_editadas.iterrows():
                    cursor.execute("""
                        UPDATE facturas 
                        SET concepto=?, monto=?, fecha_vencimiento=? 
                        WHERE id=?
                    """, (fila['concepto'], float(fila['monto']), str(fila['fecha_vencimiento']), int(fila['id'])))
                conn.commit()
                conn.close()
                st.success("🎉 Lista de facturas corregida!")
                st.rerun()
        else:
            st.info("No hay facturas registradas.")
