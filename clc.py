import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- CONFIGURACIÓN APP ---
st.set_page_config(page_title="Flor de Sauco App", layout="wide", initial_sidebar_state="collapsed")

# Estilo visual para botones grandes (ideal para celular)
st.markdown("""
    <style>
    .stButton>button { width: 100%; height: 3.5em; border-radius: 12px; font-weight: bold; background-color: #f0f2f6; }
    [data-testid="stHeader"] { visibility: hidden; }
    .block-container { padding-top: 1rem; }
    </style>
    """, unsafe_allow_html=True)

DB_FILE = "inventario_flor_de_sauco.xlsx"
DEPOSITOS = ["Molino", "Despacho", "Fábrica"]

def cargar_datos():
    if os.path.exists(DB_FILE):
        try:
            # Forzamos la lectura de las dos pestañas necesarias
            df_cat = pd.read_excel(DB_FILE, sheet_name="Catalogo").copy()
            df_movs = pd.read_excel(DB_FILE, sheet_name="Movimientos").copy()
            return df_cat, df_movs
        except Exception as e:
            st.error(f"Error al leer el Excel: {e}")
            return pd.DataFrame(), pd.DataFrame()
    return pd.DataFrame(), pd.DataFrame()

def guardar_datos(df_c, df_m):
    try:
        with pd.ExcelWriter(DB_FILE, engine="openpyxl") as writer:
            df_c.to_excel(writer, sheet_name="Catalogo", index=False)
            df_m.to_excel(writer, sheet_name="Movimientos", index=False)
        return True
    except:
        st.error("❌ El archivo está bloqueado. Cerralo en la PC para poder guardar.")
        return False

# Carga de datos inicial
df_cat, df_movs = cargar_datos()

# Menú superior por pestañas
menu = st.tabs(["📊 Stock", "🔄 Transferir", "📥 Carga", "⚙️ Ajustes"])

# --- PESTAÑA CARGA (Aquí está el arreglo de fardos) ---
with menu[2]:
    st.subheader("📥 Cargar Mercadería")
    if not df_cat.empty:
        # Selector de producto
        prod_lista = sorted(df_cat["Producto"].astype(str).unique().tolist())
        p_c = st.selectbox("Seleccionar Producto:", prod_lista, key="p_carga_manual")
        
        # Lógica de fardos
        info_p = df_cat[df_cat["Producto"] == p_c]
        # Si no existe la columna 'Unidades_Fardo', usamos 1 por defecto
        u_por_fardo = float(info_p["Unidades_Fardo"].values[0]) if "Unidades_Fardo" in info_p.columns else 1.0
        
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            modo = st.radio("Cargar por:", ["Unidades / Kg", "Fardos"], horizontal=True)
        with col_m2:
            cant_in = st.number_input(f"Cantidad:", min_value=0.0, step=1.0)
        
        # Cálculo de la cantidad final
        cantidad_final = cant_in * u_por_fardo if modo == "Fardos" else cant_in
        
        if modo == "Fardos":
            st.write(f"💡 Esto cargará **{cantidad_final}** unidades al sistema.")

        tipo_c = st.radio("Operación:", ["Ingreso", "Egreso"], horizontal=True)
        dep_c = st.selectbox("Sector:", DEPOSITOS, key="dep_carga_manual")
        
        if st.button("💾 REGISTRAR CARGA"):
            if cantidad_final > 0:
                f_now = datetime.now().strftime("%Y-%m-%d %H:%M")
                nuevo = pd.DataFrame([[f_now, p_c, tipo_c, cantidad_final, dep_c]], columns=df_movs.columns)
                if guardar_datos(df_cat, pd.concat([df_movs, nuevo], ignore_index=True)):
                    st.success(f"✅ Se registraron {cantidad_final} unidades correctamente.")
                    st.rerun()
            else:
                st.warning("La cantidad debe ser mayor a 0.")
    else:
        st.warning("Primero debés subir el catálogo en la pestaña de Ajustes.")

# --- PESTAÑA AJUSTES (Aquí está el arreglo para cargar el Excel) ---
with menu[3]:
    st.subheader("⚙️ Configuración del Sistema")
    st.write("Subí tu archivo de catálogo para actualizar la lista de productos.")
    
    archivo_subido = st.file_uploader("Elegir archivo Excel (.xlsx)", type=["xlsx"])
    
    if archivo_subido is not None:
        # Botón para confirmar la carga
        if st.button("🚀 SUBIR Y ACTUALIZAR STOCK"):
            try:
                # Leemos el nuevo catálogo
                nuevo_df_cat = pd.read_excel(archivo_subido)
                
                # Verificamos que tenga las columnas mínimas
                if "Producto" in nuevo_df_cat.columns:
                    # Guardamos el nuevo catálogo manteniendo los movimientos que ya tenías
                    if guardar_datos(nuevo_df_cat, df_movs):
                        st.success("✅ ¡Catálogo actualizado con éxito!")
                        st.balloons()
                        st.rerun()
                else:
                    st.error("El Excel debe tener al menos una columna llamada 'Producto'.")
            except Exception as e:
                st.error(f"Ocurrió un error al procesar el archivo: {e}")
