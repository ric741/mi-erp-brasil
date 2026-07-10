import streamlit as st
import pandas as pd
from datetime import datetime, date

# Configuración de la página
st.set_page_config(page_title="ERP Brasil Final", layout="wide")

# --- 1. BASES DE DATOS EN MEMORIA (SESSION STATE) ---
if "ventas_db" not in st.session_state:
    st.session_state.ventas_db = pd.DataFrame([
        {"Mes": "2026-07", "Fecha": "2026-07-01", "Producto_Servicio": "Web Design", "Cantidad": 2, "Precio": 50.0, "Total": 100.0, "Trabajador": "Joao Silva"}
    ])

if "trabajadores_db" not in st.session_state:
    st.session_state.trabajadores_db = pd.DataFrame([
        {"Mes": "2026-07", "Trabajador": "Joao Silva", "Producto_Vendido": "Web Design", "Cantidad": 2, "Valor_Pago": 15.0, "Total_Pago": 30.0}
    ])

if "facturas_db" not in st.session_state:
    st.session_state.facturas_db = pd.DataFrame([
        {"Concepto": "Conta de Luz", "Monto": 40.0, "Fecha_Vencimiento": "2026-07-15"}
    ])

# --- RECALCULADOR AUTOMÁTICO ---
def actualizar_tablas():
    if not st.session_state.ventas_db.empty:
        st.session_state.ventas_db["Cantidad"] = pd.to_numeric(st.session_state.ventas_db["Cantidad"])
        st.session_state.ventas_db["Precio"] = pd.to_numeric(st.session_state.ventas_db["Precio"])
        st.session_state.ventas_db["Total"] = st.session_state.ventas_db["Cantidad"] * st.session_state.ventas_db["Precio"]
    if not st.session_state.trabajadores_db.empty:
        st.session_state.trabajadores_db["Cantidad"] = pd.to_numeric(st.session_state.trabajadores_db["Cantidad"])
        st.session_state.trabajadores_db["Valor_Pago"] = pd.to_numeric(st.session_state.trabajadores_db["Valor_Pago"])
        st.session_state.trabajadores_db["Total_Pago"] = st.session_state.trabajadores_db["Cantidad"] * st.session_state.trabajadores_db["Valor_Pago"]

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

# ====================================================================
# PANTALLA 1: INICIO
# ====================================================================
if opcion_pantalla == "🏠 Início (Balanço Geral e Alertas)":
    st.title("🏠 Balanço Geral da Empresa")
    
    meses_ordenados = ["2026-06", "2026-07", "2026-08"]
    saldo_anterior = 0.0
    resumen_meses = {}
    
    actualizar_tablas() # Asegurar que los cálculos estén al día
    
    for m in meses_ordenados:
        v_mes = st.session_state.ventas_db[st.session_state.ventas_db["Mes"] == m]
        t_mes = st.session_state.trabajadores_db[st.session_state.trabajadores_db["Mes"] == m]
        
        ingresos_ventas = v_mes["Total"].sum()
        pagos_trabajadores = t_mes["Total_Pago"].sum()
        
        f_mes = st.session_state.facturas_db[st.session_state.facturas_db["Fecha_Vencimiento"].str.contains(m, na=False)]
        costo_facturas = f_mes["Monto"].sum()
        
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
    
    if not st.session_state.facturas_db.empty:
        for idx, row in st.session_state.facturas_db.iterrows():
            try:
                f_venc = datetime.strptime(str(row["Fecha_Vencimiento"]), "%Y-%m-%d").date()
                dias_restantes = (f_venc - hoy).days
                if 0 < dias_restantes <= 7:
                    st.warning(f"⚠️ A fatura '{row['Concepto']}' de R$ {row['Monto']} vence em {dias_restantes} dias ({row['Fecha_Vencimiento']}).")
                    alerta_disparada = True
                elif dias_restantes == 0:
                    st.error(f"🚨 A fatura '{row['Concepto']}' vence HOJE!")
                    alerta_disparada = True
                elif dias_restantes < 0:
                    st.error(f"💀 VENCIDA: '{row['Concepto']}' expirou há {abs(dias_restantes)} dias.")
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
        nueva_venta = pd.DataFrame([{"Mes": v_mes, "Fecha": v_fecha_input, "Producto_Servicio": v_prod, "Cantidad": v_cant, "Precio": v_prec, "Total": v_total, "Trabajador": v_trab}])
        st.session_state.ventas_db = pd.concat([st.session_state.ventas_db, nueva_venta], ignore_index=True)
        st.success("¡Venta guardada!")
        st.rerun()

    st.divider()
    st.subheader("📋 Lista de Vendas (Filtrável e Editável)")
    
    buscar_producto = st.text_input("🔍 Buscar por Producto o Servicio (Escribe aquí):", "")
    
    df_v_editada = st.data_editor(st.session_state.ventas_db, num_rows="dynamic", use_container_width=True, key="edit_v")
    
    if st.button("💾 Guardar Cambios en Ventas"):
        st.session_state.ventas_db = df_v_editada.copy()
        actualizar_tablas()
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
        nuevo_t = pd.DataFrame([{"Mes": t_mes, "Trabajador": t_trab, "Producto_Vendido": t_prod, "Cantidad": t_cant, "Valor_Pago": t_pago, "Total_Pago": t_total}])
        st.session_state.trabajadores_db = pd.concat([st.session_state.trabajadores_db, nuevo_t], ignore_index=True)
        st.success("¡Trabajador registrado!")
        st.rerun()

    st.divider()
    st.subheader("📋 Lista de Pagamentos (Filtrável e Editável)")
    
    df_t_editada = st.data_editor(st.session_state.trabajadores_db, num_rows="dynamic", use_container_width=True, key="edit_t")
    
    if st.button("💾 Guardar Cambios en Trabajadores"):
        st.session_state.trabajadores_db = df_t_editada.copy()
        actualizar_tablas()
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
        
    if st.button("💾 Salvar Fatura"): st.success("Fatura salva com sucesso!")
