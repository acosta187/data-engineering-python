import streamlit as st
import pandas as pd
import numpy as np
import joblib
import fastavro
import os
from datetime import datetime
from sklearn.base import BaseEstimator, TransformerMixin

# =============================================================================
# TRANSFORMADOR PERSONALIZADO (Tu lógica original)
# =============================================================================

def softM(num1, LAMBDA=2):
    PI = np.pi
    AVG = np.mean(num1)
    SD = np.std(num1)
    if SD == 0 or np.isnan(SD):
        return np.full_like(num1, 0.5, dtype=float)
    vt = (num1 - AVG) / (LAMBDA * (SD / (2 * PI)))
    return 1 / (1 + np.exp(-np.clip(vt, -500, 500)))

class softMax(BaseEstimator, TransformerMixin):
    def __init__(self, LAMBDA=2): self.LAMBDA = LAMBDA
    def fit(self, X, y=None): return self
    def transform(self, X):
        return X.apply(lambda col: softM(col, LAMBDA=self.LAMBDA))

# =============================================================================
# CONFIGURACIÓN DEL "DATA LAKE" (GUARDADO AUTOMÁTICO)
# =============================================================================

FOLDER_NAME = "registros_pacientes"
if not os.path.exists(FOLDER_NAME):
    os.makedirs(FOLDER_NAME)

# Definimos el esquema Avro incluyendo TODO: Datos personales + Datos del Modelo + Resultado
AVRO_SCHEMA = {
    "doc": "Registro completo de paciente y prediccion cardiaca",
    "name": "ExpedienteCardiaco",
    "type": "record",
    "fields": [
        # Datos personales (Ventana 1)
        {"name": "nombre", "type": "string"},
        {"name": "estado_civil", "type": "string"},
        {"name": "hijos", "type": "int"},
        {"name": "fuma", "type": "string"},
        {"name": "bebe", "type": "string"},
        {"name": "ejercicio", "type": "string"},
        # Datos del modelo (Ventana 2)
        {"name": "age", "type": "int"},
        {"name": "trestbps", "type": "int"},
        {"name": "chol", "type": "int"},
        {"name": "oldpeak", "type": "float"},
        {"name": "ca", "type": "int"},
        {"name": "sex", "type": "string"},
        {"name": "cp", "type": "string"},
        {"name": "fbs", "type": "boolean"},
        {"name": "restecg", "type": "string"},
        {"name": "exang", "type": "boolean"},
        {"name": "slope", "type": "string"},
        {"name": "thal", "type": "string"},
        # Resultado final
        {"name": "probabilidad", "type": "float"},
        {"name": "fecha_registro", "type": "string"}
    ]
}

def guardar_avro_automatico(datos):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_seguro = datos['nombre'].replace(" ", "_")[:20]
    filename = f"{FOLDER_NAME}/record_{timestamp}_{nombre_seguro}.avro"
    with open(filename, "wb") as out:
        fastavro.writer(out, AVRO_SCHEMA, [datos])
    return filename

# =============================================================================
# CARGA DE MODELOS
# =============================================================================

@st.cache_resource
def load_models():
    try:
        transformer = joblib.load("ml_model/transformador.pkl")
        model = joblib.load("ml_model/model_xgb.pkl")
        return transformer, model
    except:
        st.error("Error cargando archivos pkl.")
        st.stop()

transformer, model = load_models()

# =============================================================================
# INTERFAZ DE USUARIO (SISTEMA DE VENTANAS)
# =============================================================================

if 'paso' not in st.session_state:
    st.session_state.paso = 1
    st.session_state.datos_personales = {}

# --- VENTANA 1: INFORMACIÓN EXTRA ---
if st.session_state.paso == 1:
    st.title("📋 Paso 1: Perfil del Paciente")
    with st.form("ventana1"):
        nombre = st.text_input("Nombre Completo")
        est_civil = st.selectbox("Estado Civil", ["Soltero/a", "Casado/a", "Divorciado/a", "Viudo/a"])
        hijos = st.number_input("Número de hijos", 0, 15, 0)
        fuma = st.radio("¿Fuma?", ["Sí", "No"], horizontal=True)
        bebe = st.radio("¿Bebe alcohol?", ["Sí", "No"], horizontal=True)
        ejercicio = st.radio("¿Hace ejercicio?", ["Sí", "No"], horizontal=True)
        
        if st.form_submit_button("Siguiente ➡️"):
            if nombre:
                st.session_state.datos_personales = {
                    "nombre": nombre, "estado_civil": est_civil, "hijos": hijos,
                    "fuma": fuma, "bebe": bebe, "ejercicio": ejercicio
                }
                st.session_state.paso = 2
                st.rerun()
            else:
                st.error("Debe ingresar el nombre del paciente.")

# --- VENTANA 2: VARIABLES DEL MODELO Y CÁLCULO ---
elif st.session_state.paso == 2:
    st.title("🫀 Paso 2: Datos Médicos")
    st.write(f"Paciente: **{st.session_state.datos_personales['nombre']}**")

    with st.form("ventana2"):
        col1, col2 = st.columns(2)
        inputs = {}

        with col1:
            st.subheader("📊 Métricas")
            inputs["age"] = st.number_input("Edad", 1, 120, 50)
            inputs["trestbps"] = st.number_input("Presión arterial (mmHg)", 80, 250, 120)
            inputs["chol"] = st.number_input("Colesterol (mg/dl)", 100, 600, 200)
            inputs["oldpeak"] = st.number_input("Depresión ST", 0.0, 10.0, 1.0, 0.1)
            inputs["ca"] = st.number_input("Vasos principales", 0, 4, 0)
            inputs["sex"] = st.selectbox("Sexo", ["Male", "Female"])

        with col2:
            st.subheader("🩺 Diagnóstico")
            inputs["cp"] = st.selectbox("Dolor torácico", ["asymptomatic", "non-anginal", "atypical angina", "typical angina"])
            inputs["fbs"] = st.selectbox("Glucosa > 120 mg/dl", [False, True])
            inputs["restecg"] = st.selectbox("ECG en reposo", ["normal", "lv hypertrophy", "st-t abnormality"])
            inputs["exang"] = st.selectbox("Angina por ejercicio", [False, True])
            inputs["slope"] = st.selectbox("Pendiente ST", ["upsloping", "flat", "downsloping"])
            inputs["thal"] = st.selectbox("Talasemia", ["normal", "reversable defect", "fixed defect"])

        btn_col1, btn_col2 = st.columns(2)
        if btn_col1.form_submit_button("⬅️ Atrás"):
            st.session_state.paso = 1
            st.rerun()

        calcular = btn_col2.form_submit_button("🔍 Calcular y Guardar", type="primary")

    if calcular:
        with st.spinner("Procesando..."):
            # 1. Predicción
            df_input = pd.DataFrame([inputs])
            df_trans = transformer.transform(df_input)
            prob = float(model.predict_proba(df_trans)[0][1])

            # 2. Unificar todos los datos para el Avro
            datos_finales = {
                **st.session_state.datos_personales, # Datos ventana 1
                **inputs,                            # Datos ventana 2 (Modelo)
                "probabilidad": prob,
                "fecha_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            # 3. Guardado automático en servidor
            ruta = guardar_avro_automatico(datos_finales)

            # 4. Mostrar Resultados
            st.markdown("---")
            st.subheader("Resultado del Análisis")
            st.metric("Probabilidad de Enfermedad", f"{prob*100:.1f}%")
            
            if prob >= 0.5:
                st.error("Riesgo Alto detectado.")
            else:
                st.success("Riesgo Bajo detectado.")
            
            st.info(f"💾 Información guardada automáticamente en: {ruta}")

            if st.button("🔄 Realizar nueva consulta"):
                st.session_state.paso = 1
                st.rerun()
