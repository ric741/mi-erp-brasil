import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
import os

# Configuración de la página
st.set_page_config(page_title="ERP Brasil Final", layout="wide")

# --- CONEXIÓN Y CREACIÓN DE LA BASE DE DATOS (SQLite) ---
DB_NAME = "erp_brasil.db"

def inicializar_bd():
    """Crea el archivo de base de datos y las tablas si no existen."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Tabla de Ventas
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
    
    # Tabla de Trabajadores
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
    
    # Tabla de Facturas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS facturas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        concepto TEXT,
        monto REAL,
        fecha_vencimiento TEXT
    )
    """)
    
    # Insertar datos de ejemplo solo si las tablas están completamente vacías
    cursor.execute("SELECT COUNT(*) FROM ventas")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO ventas (mes, fecha, producto_servicio, cantidad, precio, total, trabajador) VALUES ('2026-07', '2026-07-01', 'Web Design', 2, 50.0, 100.0, 'Joao Silva')")
        cursor.execute("INSERT INTO trabajadores (mes, trabajador, producto_vendido, cantidad, valor_pago, total_pago) VALUES ('2026-07', 'Joao Silva', 'Web Design', 2, 15.0, 30.0)")
        cursor.execute("INSERT INTO facturas (concepto, monto, fecha_vencimiento) VALUES ('Conta de Luz', 40.0, '2026-07-15')")
    
    conn.commit()
    conn.close()

# Ejecutamos la creación de la base de datos al arrancar
inicializar_bd()

# --- FUNCIONES PARA LEER Y GUARDAR EN LA BASE DE DATOS ---
def obtener_conexion():
    return sqlite3.connect(DB_NAME)

def cargar_datos(tabla_name):
    conn = obtener_conexion()
    df = pd.read_sql_query(f"SELECT * FROM {tabla_name}", conn)
    conn.close()
    return df

# --- 2. MENU LATERAL Y FILTROS GENERALES ---
st.sidebar.title("🎯 Controle Geral")
lista_meses = ["Todos", "2026-06", "2026-07", "2026-08"]
mes_seleccionado = st.sidebar.selectbox("📅 Selecione o Mês de Trabalho", lista_meses, index=2)

opcion_pantalla = st.sidebar.radio("🖥️ Ir para a Tela:", [
    "🏠 Início (Balanço Geral e Alertas)",
    "🛒 Vendas Mensales (Registrar y Editar)",
    "👥 Gestión de Trabajadores",
    "🔔 Alertas de Facturas (Registrar y Control)"
])

# Cargamos los DataFrames desde la base de datos real en cada recarga
ventas_df = cargar_datos("ventas")
trabajadores_df = cargar_datos("trabajadores")
facturas_df = cargar_datos("facturas")

# ====================================================================
# PANTALLA 1: INICIO
# ====================================================================
if opcion_pantalla == "🏠 Início (Balanço Geral e Alertas)":
    st.title("🏠 Balanço Geral da Empresa")
    meses_ordenados = ["2026-06", "2026-07", "2026-08"]
    saldo_anterior = 0.0
    resumen_meses = {}
    
    for m in meses_ordenados:
        v_mes = ventas_df[ventas_df["mes"] == m]
        t_mes = trabajadores_df[trabajadores_df["mes"] == m]
        
        ingresos_ventas = v_mes["total"].sum()
        pagos_trabajadores = t_mes["total_pago"].sum()
        
        f_mes = facturas_df[facturas_df["fecha_vencimiento"].str.contains(m, na=False)]
        costo_facturas = f_mes["monto"].sum()
        
        gastos_totales = pagos_trabajadores + costo_facturas
        balance_mes = ingresos_ventas - gastos_totales
        saldo_final_acumulado = saldo_anterior + balance_mes
        
        resumen_meses[m] = {
            "Saldo Anterior": saldo_anterior,
            "Vendas": ingresos_ventas,
            "Gastos": gastos_totales,
            "Líquido": balance_mes,
            "Caixa Acumulado": saldo_final_acumulado
        }
        saldo_anterior = saldo_final_acumulado

    if mes_seleccionado == "Todos":
        st.subheader("📊 Histórico Consolidado")
        st.dataframe(pd.DataFrame(resumen_meses).T, use_container_width=True)
    else:
        st.subheader(f"📈 Mês: {mes_seleccionado}")
        res = resumen_meses.get(mes_seleccionado, {"Saldo Anterior": 0.0, "Vendas": 0.0, "Gastos": 0.0, "Líquido": 0.0, "Caixa Acumulado": 0.0})
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("💰 Saldo Anterior", f"R$ {res['Saldo Anterior']:.2f}")
        c2.metric("🛒 Vendas (+)", f"R$ {res['Vendas']:.2f}")
        c3.metric("💸 Gastos (-)", f"R$ {res['Gastos']:.2f}")
        c4.metric("🏦 Caixa Total Acumulado", f"R$ {res['Caixa Acumulado']:.2f}")

    st.divider()
    st.subheader("⏰ Alertas de Faturas (7 dias ou menos)")
    hoy = date.today()
    alerta_disparada = False
    
    if not facturas_df.empty:
        for idx, row in facturas_df.iterrows():
            try:
                f_venc = datetime.strptime(str(row["fecha_vencimiento"]), "%Y-%m-%d").date()
                dias_restantes = (f_venc - hoy).days
                if 0 < dias_restantes <= 7:
                    st.warning(f"⚠️ A fatura '{row['concepto']}' de R$ {row['monto']} vence em {dias_restantes} dias ({row['fecha_vencimiento']}).")
                    alerta_disparada = True
                elif dias_restantes == 0:
                    st.error(f"🚨 A fatura '{row['concepto']}' vence HOJE!")
                    alerta_disparada = True
                elif dias_restantes < 0:
                    st.error(f"💀 VENCIDA: '{row['concepto']}' expirou há {abs(dias_restantes)} dias.")
                    alerta_disparada = True
            except:
                pass
    if not alerta_disparada:
        st.info("✅ Tudo em dia para esta semana.")

# ====================================================================
# PANTALLA 2: VENTAS
# ====================================================================
elif opcion_pantalla == "🛒 Vendas Mensales (Registrar y Editar)":
    st.title("🛒 Registro de Vendas")
    st.subheader("➕ Adicionar Nova Venda")
    col1, col2 = st.columns(2)
    with col1:
        v_fecha_input = st.text_input("Data (AAAA-MM-DD)", value=str(date.today()))
        v_prod = st.text_input("Nome do Produto / Servicio", "Produto A")
        v_cant = st.number_input("Quantidade", min_value=1, value=1)
    with col2:
        v_prec = st.number_input("Preço Unitário (R$)", min_value=0.0, value=10.0)
        v_trab = st.text_input("Nome del Trabajador", "Joao Silva")
        
    if st.button("💾 Salvar Venda"):
        try:
            v_mes = datetime.strptime(v_fecha_input, "%Y-%m-%d").strftime("%Y-%m")
        except:
            v_mes = "2026-07"
        v_total = v_cant * v_prec
        
        # Guardar directamente en SQLite
        conn = obtener_conexion()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO ventas (mes, fecha, producto_servicio, cantidad, precio, total, trabajador)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (v_mes, v_fecha_input, v_prod, int(v_cant), float(v_prec), float(v_total), v_trab))
        conn.commit()
        conn.close()
        
        st.success("¡Venta guardada permanentemente en la base de datos!")
        st.rerun()

    st.divider()
    st.subheader("📋 Lista de Vendas (Filtrável e Editável)")
    
    buscar_producto = st.text_input("🔍 Buscar por Producto o Servicio (Escribe aquí):", "")
    
    if buscar_producto:
        df_mostrar_v = ventas_df[ventas_df["producto_servicio"].str.contains(buscar_producto, case=False, na=False)]
    else:
        df_mostrar_v = ventas_df

    # Ocultamos la columna 'id' para que se vea más limpio
    df_v_editada = st.data_editor(df_mostrar_v, num_rows="dynamic", use_container_width=True, key="edit_v", disabled=["id"])
    
    if st.button("💾 Guardar Cambios en Ventas"):
        conn = obtener_conexion()
        # Volvemos a calcular los totales antes de guardar por si editaron precio o cantidad
        df_v_editada["total"] = df_v_editada["cantidad"].astype(float) * df_v_editada["precio"].astype(float)
        
        # Sobrescribimos la tabla con los cambios del editor
        df_v_editada.to_sql("ventas", conn, if_exists="replace", index=False)
        conn.close()
        st.success("¡Base de datos de ventas actualizada!")
        st.rerun()

# ====================================================================
# PANTALLA 3: TRABAJADORES
# ====================================================================
elif opcion_pantalla == "👥 Gestión de Trabajadores":
    st.title("👥 Controle de Funcionários")
    st.subheader("➕ Registrar Trabalho")
    c1, c2 = st.columns(2)
    with c1:
        t_trab = st.text_input("Nome do Trabalhador", "Joao Silva")
        t_fecha_input = st.text_input("Data (AAAA-MM-DD)", value=str(date.today()))
        t_prod = st.text_input("Produto que ele Vendeu", "Produto A")
    with c2:
        t_cant = st.number_input("Quantidade de Vendas dele", min_value=1, value=1)
        t_pago = st.number_input("Valor pago para ele por unidade (R$)", min_value=0.0, value=5.0)
        
    if st.button("💾 Salvar Registro do Trabalhador"):
        try:
            t_mes = datetime.strptime(t_fecha_input, "%Y-%m-%d").strftime("%Y-%m")
        except:
            t_mes = "2026-07"
        t_total = t_cant * t_pago
        
        # Guardar en SQLite
        conn = obtener_conexion()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO trabajadores (mes, trabajador, producto_vendido, cantidad, valor_pago, total_pago)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (t_mes, t_trab, t_prod, int(t_cant), float(t_pago), float(t_total)))
        conn.commit()
        conn.close()
        
        st.success("¡Trabajador registrado de forma permanente!")
        st.rerun()

    st.divider()
    st.subheader("📋 Lista de Pagamentos (Filtrável e Editável)")
    df_t_editada = st.data_editor(trabajadores_df, num_rows="dynamic", use_container_width=True, key="edit_t", disabled=["id"])
    
    if st.button("💾 Guardar Cambios en Trabajadores"):
        conn = obtener_conexion()
        df_t_editada["total_pago"] = df_t_editada["cantidad"].astype(float) * df_t_editada["valor_pago"].astype(float)
        df_t_editada.to_sql("trabajadores", conn, if_exists="replace", index=False)
        conn.close()
        st.success("¡Base de datos de trabajadores actualizada!")
        st.rerun()

# ====================================================================
# PANTALLA 4: FACTURAS
# ====================================================================
elif opcion_pantalla == "🔔 Alertas de Facturas (Registrar y Control)":
    st.title("🔔 Controle de Faturas")
    st.subheader("➕ Registrar Nova Fatura")
    f_col1, f_col2 = st.columns(2)
    with f_col1:
        f_con = st.text_input("Nome da Fatura / Despesa", "Internet")
        f_mon = st.number_input("Valor da Fatura (R$)", min_value=0.0, value=50.0)
    with f_col2:
        f_fecha_venc_input = st.text_input("Data de Vencimento (AAAA-MM-DD)", value=str(date.today()))
        
    if st.button("💾 Salvar Fatura"):
        # Guardar en SQLite
        conn = obtener_conexion()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO facturas (concepto, monto, fecha_vencimiento)
            VALUES (?, ?, ?)
        """, (f_con, float(f_mon), f_fecha_venc_input))
        conn.commit()
        conn.close()
        
        st.success("Fatura salva com sucesso no banco de dados!")
        st.rerun()

    st.divider()
    st.subheader("📋 Lista de Faturas Registradas")
    df_f_editada = st.data_editor(facturas_df, num_rows="dynamic", use_container_width=True, key="edit_f", disabled=["id"])
    
    if st.button("💾 Guardar Cambios en Faturas"):
        conn = obtener_conexion()
        df_f_editada.to_sql("facturas", conn, if_exists="replace", index=False)
        conn.close()
        st.success("¡Base de datos de facturas actualizada!")
        st.rerun()
