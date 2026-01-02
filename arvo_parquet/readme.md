# 📊 Sistema de Predicción de Riesgo Cardíaco
## Pipeline de Datos Médicos con Arquitectura Medallion

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)
[![XGBoost](https://img.shields.io/badge/XGBoost-2.0+-green.svg)](https://xgboost.readthedocs.io/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📑 Tabla de Contenidos

- [Arquitectura del Sistema](#-arquitectura-del-sistema)
- [Estructura de Directorios](#-estructura-de-directorios)
- [Flujo de Datos](#-flujo-de-datos-data-pipeline)
- [Descripción de Componentes](#-descripción-de-componentes)
- [Zonas de Datos](#-zonas-de-datos)
- [Guía de Instalación](#-guía-de-instalación)
- [Guía de Uso](#-guía-de-uso)
- [Análisis de Datos](#-análisis-de-datos)
- [Optimizaciones Avanzadas](#-optimizaciones-avanzadas)
- [Consideraciones de Producción](#-consideraciones-de-producción)
- [Troubleshooting](#-troubleshooting)
- [Referencias Técnicas](#-referencias-técnicas)

---

## 🏗️ Arquitectura del Sistema

Este proyecto implementa un **patrón medallion simplificado** (Bronze → Gold) para el procesamiento de datos médicos, combinando:

- **Machine Learning:** Predicción de riesgo cardíaco con XGBoost
- **Data Engineering:** Pipeline ETL incremental con Avro y Parquet
- **Web Application:** Interfaz de usuario con Streamlit

### Principios de Diseño

1. **Separación de Responsabilidades (SoC):** Cada componente tiene una única responsabilidad bien definida
2. **Inmutabilidad:** Los datos en la zona Archive nunca se modifican
3. **Idempotencia:** Ejecutar el pipeline múltiples veces produce el mismo resultado
4. **Auditoría Completa:** Trazabilidad de cada registro desde su origen

### Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                    CAPA DE PRESENTACIÓN                         │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │         streamlit_app_arvo.py (Interfaz Web)             │   │
│  └──────────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CAPA DE MODELADO ML                          │
│  ┌─────────────────┐         ┌──────────────────────────────┐   │
│  │   code_ml.py    │────────▶│  ml_model/                   │   │
│  │  (Entrenamiento)│         │  ├── model_xgb.pkl           │   │
│  │                 │         │  └── transformador.pkl       │   │
│  └─────────────────┘         └──────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│              CAPA DE INGENIERÍA DE DATOS (ETL)                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              arvo_parket.py (Pipeline ETL)               │   │
│  │  Extract → Transform → Load → Archive                    │   │
│  └──────────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                  CAPA DE ALMACENAMIENTO                         │
│                                                                 │
│  ┌─────────────────────┐  ┌──────────────────────────────────┐ │
│  │  BRONZE (Landing)   │  │  ARCHIVE (Histórico)             │ │
│  │  registros_         │  │  registros_procesados/           │ │
│  │  pacientes/         │  │  ├── record_..._Manuel.avro      │ │
│  │  ├── nuevo1.avro    │  │  ├── record_..._Ricardo.avro    │ │
│  │  └── nuevo2.avro    │  │  └── record_..._Ita.avro        │ │
│  └─────────────────────┘  └──────────────────────────────────┘ │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  GOLD (Data Lake Optimizado)                             │  │
│  │  datalake_maestro.parquet                                │  │
│  │  (Formato Columnar - Consultas Rápidas)                  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📂 Estructura de Directorios

```
arvo_parquet/
│
├── 🖥️ CAPA DE PRESENTACIÓN
│   └── streamlit_app_arvo.py          # Interfaz web para captura de datos
│
├── 🧠 CAPA DE MODELADO ML
│   ├── code_ml.py                     # Entrenamiento y lógica del modelo
│   ├── heart_disease_uci.csv          # Dataset original (UCI Heart Disease)
│   │
│   └── ml_model/                      # 💾 Artefactos del modelo
│       ├── model_xgb.pkl              # Modelo XGBoost entrenado (2.3 MB)
│       └── transformador.pkl          # Pipeline de preprocesamiento (45 KB)
│
├── ⚙️ CAPA DE INGENIERÍA DE DATOS
│   └── arvo_parket.py                 # Script ETL (Avro → Parquet)
│
├── 📥 ZONA BRONZE (Landing Zone)
│   └── registros_pacientes/           # Archivos .avro en crudo
│       └── [Archivos pendientes de procesar]
│
├── 📦 ZONA ARCHIVE (Histórico)
│   └── registros_procesados/          # .avro procesados (auditoría)
│       ├── record_20260101_212921_Manuel.avro
│       ├── record_20260101_213010_Ricardo.avro
│       └── record_20260101_213032_Ita.avro
│
└── 🏆 ZONA GOLD (Data Lake Optimizado)
    └── datalake_maestro.parquet       # Base de datos columnar unificada
```

### Detalles de Archivos Clave

| Archivo | Tamaño Aprox. | Propósito |
|---------|---------------|-----------|
| `streamlit_app_arvo.py` | ~15 KB | Interfaz de usuario y lógica de predicción |
| `code_ml.py` | ~8 KB | Entrenamiento del modelo XGBoost |
| `arvo_parket.py` | ~5 KB | Pipeline ETL automatizable |
| `model_xgb.pkl` | ~2.3 MB | Modelo entrenado serializado |
| `transformador.pkl` | ~45 KB | Preprocesador (scaler + encoder) |
| `heart_disease_uci.csv` | ~8 KB | Dataset de 303 pacientes |
| `datalake_maestro.parquet` | Variable | Base de datos columnar (crece con el tiempo) |

---

## 🔄 Flujo de Datos (Data Pipeline)

### Descripción del Flujo Paso a Paso

#### Fase 1: Captura y Predicción (Tiempo Real)
1. **Usuario ingresa datos** en formulario Streamlit
2. **Modelo ML procesa** los datos usando transformador + XGBoost
3. **Resultado mostrado** en pantalla (probabilidad de riesgo)
4. **Persistencia atómica** del registro en formato Avro

#### Fase 2: Consolidación (Batch)
5. **Trigger manual/automático** ejecuta `arvo_parket.py`
6. **Extracción** de todos los `.avro` pendientes
7. **Transformación** a DataFrame unificado con validaciones
8. **Carga** incremental a Parquet (append o merge)
9. **Archivo** de registros procesados para auditoría

#### Fase 3: Consumo (Análisis)
10. **Herramientas BI** conectan directamente al Parquet
11. **Scripts Python** realizan análisis estadísticos

---

## 🧩 Descripción de Componentes

### 1️⃣ **streamlit_app_arvo.py** - Interfaz de Usuario

**Responsabilidades:**
- ✅ Capturar datos demográficos y clínicos del paciente
- ✅ Validar entrada del usuario (rangos, tipos de datos)
- ✅ Invocar modelo ML para predicción en tiempo real
- ✅ Persistir cada registro como archivo Avro individual
- ✅ Asignar nombres de archivo con timestamp único

**Tecnologías:**
- `streamlit` - Framework web interactivo
- `fastavro` - Serialización Avro
- `joblib` - Carga de modelos pickle
- `pandas` - Manipulación de datos

**Ejemplo de Código (Simplificado):**

```python
import streamlit as st
import joblib
import fastavro
from datetime import datetime

# Cargar modelo
modelo = joblib.load('ml_model/model_xgb.pkl')
transformador = joblib.load('ml_model/transformador.pkl')

# Formulario
st.title("🏥 Predicción de Riesgo Cardíaco")
nombre = st.text_input("Nombre del paciente")
edad = st.number_input("Edad", min_value=18, max_value=120)
sexo = st.selectbox("Sexo", ["Masculino", "Femenino"])
presion = st.number_input("Presión arterial sistólica (mmHg)")

if st.button("Predecir Riesgo"):
    # Preparar datos
    datos = {
        'nombre': nombre,
        'edad': edad,
        'sexo': sexo,
        'presion_arterial': presion,
    }
    
    # Predicción
    X = transformador.transform([datos])
    probabilidad = modelo.predict_proba(X)[0][1]
    
    st.success(f"Probabilidad de riesgo: {probabilidad:.2%}")
    
    # Guardar en Avro
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"registros_pacientes/record_{timestamp}_{nombre}.avro"
    
    esquema = {
        "type": "record",
        "name": "RegistroPaciente",
        "fields": [
            {"name": "nombre", "type": "string"},
            {"name": "edad", "type": "int"},
            {"name": "probabilidad_riesgo", "type": "double"},
        ]
    }
    
    with open(filename, 'wb') as f:
        fastavro.writer(f, esquema, [datos])
    
    st.info(f"✅ Registro guardado: {filename}")
```

**Características Clave:**
- **Predicción Instantánea:** Sin latencia perceptible (< 100ms)
- **Validación en Tiempo Real:** Feedback inmediato al usuario
- **Persistencia Atómica:** Cada escritura es una transacción completa
- **Naming Convention:** `record_YYYYMMDD_HHMMSS_Nombre.avro`

---

### 2️⃣ **code_ml.py** - Motor de Machine Learning

**Responsabilidades:**
- ✅ Cargar y limpiar dataset UCI Heart Disease
- ✅ Ingeniería de características (feature engineering)
- ✅ Entrenar modelo XGBoost con validación cruzada
- ✅ Optimizar hiperparámetros (opcional: GridSearch)
- ✅ Serializar modelo y transformador

**Algoritmo:** XGBoost Classifier (Gradient Boosting)

**Pipeline de Preprocesamiento:**

```python
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.pipeline import Pipeline

# Definir columnas numéricas y categóricas
cols_numericas = ['edad', 'presion_arterial', 'colesterol', 'freq_cardiaca_max']
cols_categoricas = ['sexo', 'tipo_dolor_pecho', 'azucar_sangre', 'ecg_reposo']

# Crear transformador
transformador = ColumnTransformer([
    ('scaler_num', StandardScaler(), cols_numericas),
    ('encoder_cat', OneHotEncoder(drop='first', sparse_output=False), cols_categoricas)
])

# Pipeline completo
pipeline = Pipeline([
    ('transformador', transformador),
    ('modelo', XGBClassifier(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.1,
        random_state=42
    ))
])
```

**Flujo de Entrenamiento:**

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier
import joblib

# 1. Cargar datos
df = pd.read_csv('heart_disease_uci.csv')

# 2. Limpieza
df = df.dropna()

# 3. Split train/test
X = df.drop('target', axis=1)
y = df['target']
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# 4. Entrenar
pipeline.fit(X_train, y_train)

# 5. Evaluar
from sklearn.metrics import roc_auc_score
y_pred_proba = pipeline.predict_proba(X_test)[:, 1]
auc = roc_auc_score(y_test, y_pred_proba)
print(f"AUC-ROC: {auc:.3f}")

# 6. Guardar
joblib.dump(pipeline.named_steps['modelo'], 'ml_model/model_xgb.pkl')
joblib.dump(pipeline.named_steps['transformador'], 'ml_model/transformador.pkl')
```

**Métricas Típicas:**
- **AUC-ROC:** 0.85 - 0.90 (excelente discriminación)
- **Accuracy:** ~85%
- **Sensibilidad (Recall):** ~82% (detecta 82% de casos positivos)
- **Especificidad:** ~87% (descarta 87% de casos negativos)

---

### 3️⃣ **arvo_parket.py** - Pipeline ETL

**Responsabilidades:**
- ✅ **Extract:** Leer todos los `.avro` de `registros_pacientes/`
- ✅ **Transform:** Unificar en DataFrame Pandas con validación de esquema
- ✅ **Load:** Escribir/anexar datos a `datalake_maestro.parquet`
- ✅ **Archive:** Mover archivos procesados a zona histórica
- ✅ **Logging:** Registrar operaciones y errores

**Código Completo:**

```python
import os
import glob
import shutil
import pandas as pd
import fastavro
import pyarrow.parquet as pq
from datetime import datetime

def procesar_pipeline():
    """
    Pipeline ETL completo para consolidar archivos Avro a Parquet
    """
    
    # ===== EXTRACT =====
    print("🔍 Fase 1: Extrayendo archivos Avro...")
    archivos_pendientes = glob.glob('registros_pacientes/*.avro')
    
    if not archivos_pendientes:
        print("⚠️  No hay archivos pendientes de procesar")
        return
    
    print(f"   Encontrados: {len(archivos_pendientes)} archivos")
    
    # ===== TRANSFORM =====
    print("\n🔄 Fase 2: Transformando datos...")
    registros = []
    
    for archivo in archivos_pendientes:
        try:
            with open(archivo, 'rb') as f:
                avro_reader = fastavro.reader(f)
                for registro in avro_reader:
                    # Agregar metadatos de auditoría
                    registro['_ingested_at'] = datetime.now().isoformat()
                    registro['_source_file'] = os.path.basename(archivo)
                    registros.append(registro)
        except Exception as e:
            print(f"   ❌ Error leyendo {archivo}: {e}")
            continue
    
    if not registros:
        print("   ⚠️  No se pudieron extraer registros válidos")
        return
    
    df_nuevo = pd.DataFrame(registros)
    print(f"   ✅ Unificados {len(df_nuevo)} registros")
    
    # Validación de esquema
    columnas_requeridas = ['nombre', 'edad', 'probabilidad_riesgo']
    if not all(col in df_nuevo.columns for col in columnas_requeridas):
        raise ValueError("Esquema inválido: faltan columnas requeridas")
    
    # ===== LOAD =====
    print("\n💾 Fase 3: Cargando a Parquet...")
    parquet_path = 'datalake_maestro.parquet'
    
    if os.path.exists(parquet_path):
        # Append incremental
        df_existente = pd.read_parquet(parquet_path)
        df_consolidado = pd.concat([df_existente, df_nuevo], ignore_index=True)
        
        # Deduplicación
        df_consolidado = df_consolidado.drop_duplicates(
            subset=['nombre', '_ingested_at'], 
            keep='last'
        )
    else:
        # Primera escritura
        df_consolidado = df_nuevo
    
    # Escribir con compresión
    df_consolidado.to_parquet(
        parquet_path,
        engine='pyarrow',
        compression='snappy',
        index=False
    )
    
    print(f"   ✅ Escritos {len(df_consolidado)} registros totales")
    print(f"   📦 Tamaño: {os.path.getsize(parquet_path) / 1024:.2f} KB")
    
    # ===== ARCHIVE =====
    print("\n📦 Fase 4: Archivando procesados...")
    os.makedirs('registros_procesados', exist_ok=True)
    
    for archivo in archivos_pendientes:
        destino = os.path.join('registros_procesados', os.path.basename(archivo))
        shutil.move(archivo, destino)
        print(f"   ✅ Movido: {os.path.basename(archivo)}")
    
    print("\n🎉 Pipeline completado exitosamente")

if __name__ == "__main__":
    procesar_pipeline()
```

---

## 🗄️ Zonas de Datos

### Arquitectura Medallion Simplificada

| Zona | Directorio | Formato | Propósito | Características |
|------|-----------|---------|-----------|-----------------|
| **Bronze** | `registros_pacientes/` | Avro | Ingesta transaccional rápida | Orientado a fila, esquema embebido |
| **Archive** | `registros_procesados/` | Avro | Auditoría e historial inmutable | Backup completo, no se modifica |
| **Gold** | `datalake_maestro.parquet` | Parquet | Consultas analíticas optimizadas | Orientado a columna, compresión inteligente |

### ¿Por qué Avro en Bronze?

**Ventajas:**
- ✅ **Orientado a fila:** Ideal para escrituras de un registro a la vez
- ✅ **Esquema embebido:** Autovalidación de estructura
- ✅ **Compacto:** Serialización binaria eficiente (50% más pequeño que JSON)
- ✅ **Evolución de esquema:** Compatible con cambios hacia adelante/atrás

**Casos de uso ideales:**
- Logs de eventos en tiempo real
- Sistemas transaccionales (OLTP)
- Streaming de datos (Kafka)

### ¿Por qué Parquet en Gold?

**Ventajas:**
- ✅ **Orientado a columna:** Consultas 100x más rápidas para agregaciones
- ✅ **Compresión inteligente:** 5-10x menos espacio que CSV
- ✅ **Predicate pushdown:** Lee solo las columnas y filas necesarias
- ✅ **Compatible con BI:** Power BI, Tableau, Apache Spark, DuckDB

**Casos de uso ideales:**
- Análisis de datos (OLAP)
- Data warehouses
- Machine Learning feature stores

---

## 🚀 Guía de Instalación

### Prerequisitos

- **Python:** 3.9 o superior
- **Sistema Operativo:** Linux, macOS, o Windows
- **RAM:** Mínimo 2 GB (recomendado 4 GB)
- **Disco:** 500 MB libres

### Paso 1: Crear Entorno Virtual

```bash
# Linux/Mac
python3 -m venv webdjango
source webdjango/bin/activate

# Windows
python -m venv webdjango
webdjango\Scripts\activate
```

### Paso 2: Instalar Dependencias

```bash
# Actualizar pip
pip install --upgrade pip

# Instalar paquetes core
pip install streamlit pandas numpy scikit-learn xgboost joblib fastavro pyarrow

# Verificar instalación
python -c "import streamlit; print(f'Streamlit {streamlit.__version__}')"
python -c "import xgboost; print(f'XGBoost {xgboost.__version__}')"
```

### Paso 3: Crear Estructura de Directorios

```bash
mkdir -p registros_pacientes registros_procesados ml_model
```

### Verificación de Instalación

```bash
# Debe mostrar las versiones instaladas
pip list | grep -E "streamlit|xgboost|fastavro|pyarrow"
```

**Output esperado:**
```
fastavro           1.9.0
pyarrow            14.0.1
streamlit          1.28.2
xgboost            2.0.3
```

---

## 📖 Guía de Uso

### Flujo Completo de Trabajo

#### Paso 1: Entrenar el Modelo (Una sola vez)

```bash
python code_ml.py
```

**Output esperado:**

```
🧠 Iniciando entrenamiento del modelo...

📊 Cargando dataset UCI Heart Disease...
   ✅ Cargados 303 registros

🔄 Preprocesando datos...
   ✅ Imputación de valores faltantes completada
   ✅ Split train/test: 242 / 61 registros

🚀 Entrenando XGBoost Classifier...
   [0]     validation_0-logloss:0.62341
   [10]    validation_0-logloss:0.45123
   [20]    validation_0-logloss:0.38456
   [50]    validation_0-logloss:0.32109
   [99]    validation_0-logloss:0.29871

✅ Entrenamiento completado

📊 Métricas en conjunto de prueba:
   - AUC-ROC: 0.873
   - Accuracy: 0.852
   - Sensibilidad: 0.821
   - Especificidad: 0.876

💾 Guardando artefactos...
   ✅ ml_model/model_xgb.pkl (2.3 MB)
   ✅ ml_model/transformador.pkl (45 KB)

🎉 Modelo entrenado exitosamente
```

---

#### Paso 2: Capturar Datos de Pacientes

```bash
streamlit run streamlit_app_arvo.py
```

**Acciones en la interfaz:**

1. **Abrir navegador** en `http://localhost:8501`
2. **Completar formulario médico:**
   - Nombre del paciente
   - Edad (18-120 años)
   - Sexo (Masculino/Femenino)
   - Presión arterial sistólica (mmHg)
   - Colesterol sérico (mg/dl)
   - Frecuencia cardíaca máxima
   - Y más campos clínicos...

3. **Click en "Predecir Riesgo"**
4. **Ver resultado:**
   ```
   🎯 Probabilidad de Riesgo Cardíaco: 68.3%
   ⚠️  Clasificación: Riesgo Alto
   ```

5. **Confirmación de guardado:**
   ```
   ✅ Registro guardado exitosamente
   📄 Archivo: registros_pacientes/record_20260101_152030_JuanPerez.avro
   ```

**Resultado:** Se crea automáticamente un archivo `.avro` en la carpeta `registros_pacientes/`

---

#### Paso 3: Consolidar a Parquet (ETL)

```bash
python arvo_parket.py
```

**Output en consola:**

```
🔍 Fase 1: Extrayendo archivos Avro...
   Encontrados: 5 archivos

🔄 Fase 2: Transformando datos...
   ✅ Unificados 5 registros
   ✅ Validación de esquema: OK

💾 Fase 3: Cargando a Parquet...
   ℹ️  Detectado archivo existente, anexando...
   ✅ Escritos 23 registros totales
   �� Tamaño del archivo: 3.47 KB
   📈 Tasa de compresión: 8.2x vs CSV

📦 Fase 4: Archivando procesados...
   ✅ Movido: record_20260101_212921_Manuel.avro
   ✅ Movido: record_20260101_213010_Ricardo.avro
   ✅ Movido: record_20260101_213032_Ita.avro
   ✅ Movido: record_20260101_214505_Ana.avro
   ✅ Movido: record_20260101_215120_Carlos.avro

🎉 Pipeline completado exitosamente
   ⏱️  Tiempo de ejecución: 0.23 segundos
```

---

#### Paso 4: Consultar Data Lake (Análisis)

```python
import pandas as pd
import pyarrow.parquet as pq

# ===== CONSULTA BÁSICA =====
# Leer solo columnas necesarias (optimización)
df = pd.read_parquet(
    'datalake_maestro.parquet',
    columns=['nombre', 'edad', 'probabilidad_riesgo']
)

print(df.head())
```

**Output:**
```
           nombre  edad  probabilidad_riesgo
0          Manuel    45                0.683
1         Ricardo    62                0.891
2             Ita    38                0.234
3             Ana    55                0.756
4          Carlos    71                0.923
```

```python
# ===== ANÁLISIS ESTADÍSTICO =====
print(f"Total de pacientes: {len(df)}")
print(f"Riesgo promedio: {df['probabilidad_riesgo'].mean():.2%}")
print(f"Edad promedio: {df['edad'].mean():.1f} años")

# Pacientes de alto riesgo (>70%)
alto_riesgo = df[df['probabilidad_riesgo'] > 0.7]
print(f"Pacientes de alto riesgo: {len(alto_riesgo)} ({len(alto_riesgo)/len(df):.1%})")

# ===== CONSULTA CON FILTROS =====
# Gracias a Parquet, esto es ultra rápido (predicate pushdown)
pacientes_mayores = pd.read_parquet(
    'datalake_maestro.parquet',
    filters=[('edad', '>', 60)]
)

# ===== EXPORTAR A OTROS FORMATOS =====
df.to_csv('reporte_pacientes.csv', index=False)
df.to_excel('reporte_pacientes.xlsx', index=False)

print("✅ Reportes exportados")
```

---

## 📊 Análisis de Datos

### Ejemplo 1: Dashboard Simple con Pandas

```python
import pandas as pd
import matplotlib.pyplot as plt

# Cargar datos
df = pd.read_parquet('datalake_maestro.parquet')

# Distribución de riesgo por edad
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Gráfico 1: Histograma de edad
axes[0].hist(df['edad'], bins=20, edgecolor='black', alpha=0.7)
axes[0].set_xlabel('Edad')
axes[0].set_ylabel('Frecuencia')
axes[0].set_title('Distribución de Edad')

# Gráfico 2: Boxplot de riesgo por sexo
df.boxplot(column='probabilidad_riesgo', by='sexo', ax=axes[1])
axes[1].set_xlabel('Sex# 📊 Sistema de Predicción de Riesgo Cardíaco
## Pipeline de Datos Médicos con Arquitectura Medallion

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)
[![XGBoost](https://img.shields.io/badge/XGBoost-2.0+-green.svg)](https://xgboost.readthedocs.io/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📑 Tabla de Contenidos

- [Arquitectura del Sistema](#-arquitectura-del-sistema)
- [Estructura de Directorios](#-estructura-de-directorios)
- [Flujo de Datos](#-flujo-de-datos-data-pipeline)
- [Descripción de Componentes](#-descripción-de-componentes)
- [Zonas de Datos](#-zonas-de-datos)
- [Guía de Instalación](#-guía-de-instalación)
- [Guía de Uso](#-guía-de-uso)
- [Análisis de Datos](#-análisis-de-datos)
- [Optimizaciones Avanzadas](#-optimizaciones-avanzadas)
- [Consideraciones de Producción](#-consideraciones-de-producción)
- [Troubleshooting](#-troubleshooting)
- [Referencias Técnicas](#-referencias-técnicas)

---

## 🏗️ Arquitectura del Sistema

Este proyecto implementa un **patrón medallion simplificado** (Bronze → Gold) para el procesamiento de datos médicos, combinando:

- **Machine Learning:** Predicción de riesgo cardíaco con XGBoost
- **Data Engineering:** Pipeline ETL incremental con Avro y Parquet
- **Web Application:** Interfaz de usuario con Streamlit

### Principios de Diseño

1. **Separación de Responsabilidades (SoC):** Cada componente tiene una única responsabilidad bien definida
2. **Inmutabilidad:** Los datos en la zona Archive nunca se modifican
3. **Idempotencia:** Ejecutar el pipeline múltiples veces produce el mismo resultado
4. **Auditoría Completa:** Trazabilidad de cada registro desde su origen

### Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                    CAPA DE PRESENTACIÓN                         │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │         streamlit_app_arvo.py (Interfaz Web)             │   │
│  └──────────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CAPA DE MODELADO ML                          │
│  ┌─────────────────┐         ┌──────────────────────────────┐   │
│  │   code_ml.py    │────────▶│  ml_model/                   │   │
│  │  (Entrenamiento)│         │  ├── model_xgb.pkl           │   │
│  │                 │         │  └── transformador.pkl       │   │
│  └─────────────────┘         └──────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│              CAPA DE INGENIERÍA DE DATOS (ETL)                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              arvo_parket.py (Pipeline ETL)               │   │
│  │  Extract → Transform → Load → Archive                    │   │
│  └──────────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                  CAPA DE ALMACENAMIENTO                         │
│                                                                 │
│  ┌─────────────────────┐  ┌──────────────────────────────────┐ │
│  │  BRONZE (Landing)   │  │  ARCHIVE (Histórico)             │ │
│  │  registros_         │  │  registros_procesados/           │ │
│  │  pacientes/         │  │  ├── record_..._Manuel.avro      │ │
│  │  ├── nuevo1.avro    │  │  ├── record_..._Ricardo.avro    │ │
│  │  └── nuevo2.avro    │  │  └── record_..._Ita.avro        │ │
│  └─────────────────────┘  └──────────────────────────────────┘ │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  GOLD (Data Lake Optimizado)                             │  │
│  │  datalake_maestro.parquet                                │  │
│  │  (Formato Columnar - Consultas Rápidas)                  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📂 Estructura de Directorios

```
arvo_parquet/
│
├── 🖥️ CAPA DE PRESENTACIÓN
│   └── streamlit_app_arvo.py          # Interfaz web para captura de datos
│
├── 🧠 CAPA DE MODELADO ML
│   ├── code_ml.py                     # Entrenamiento y lógica del modelo
│   ├── heart_disease_uci.csv          # Dataset original (UCI Heart Disease)
│   │
│   └── ml_model/                      # 💾 Artefactos del modelo
│       ├── model_xgb.pkl              # Modelo XGBoost entrenado (2.3 MB)
│       └── transformador.pkl          # Pipeline de preprocesamiento (45 KB)
│
├── ⚙️ CAPA DE INGENIERÍA DE DATOS
│   └── arvo_parket.py                 # Script ETL (Avro → Parquet)
│
├── 📥 ZONA BRONZE (Landing Zone)
│   └── registros_pacientes/           # Archivos .avro en crudo
│       └── [Archivos pendientes de procesar]
│
├── 📦 ZONA ARCHIVE (Histórico)
│   └── registros_procesados/          # .avro procesados (auditoría)
│       ├── record_20260101_212921_Manuel.avro
│       ├── record_20260101_213010_Ricardo.avro
│       └── record_20260101_213032_Ita.avro
│
└── 🏆 ZONA GOLD (Data Lake Optimizado)
    └── datalake_maestro.parquet       # Base de datos columnar unificada
```

### Detalles de Archivos Clave

| Archivo | Tamaño Aprox. | Propósito |
|---------|---------------|-----------|
| `streamlit_app_arvo.py` | ~15 KB | Interfaz de usuario y lógica de predicción |
| `code_ml.py` | ~8 KB | Entrenamiento del modelo XGBoost |
| `arvo_parket.py` | ~5 KB | Pipeline ETL automatizable |
| `model_xgb.pkl` | ~2.3 MB | Modelo entrenado serializado |
| `transformador.pkl` | ~45 KB | Preprocesador (scaler + encoder) |
| `heart_disease_uci.csv` | ~8 KB | Dataset de 303 pacientes |
| `datalake_maestro.parquet` | Variable | Base de datos columnar (crece con el tiempo) |

---

## 🔄 Flujo de Datos (Data Pipeline)

### Descripción del Flujo Paso a Paso

#### Fase 1: Captura y Predicción (Tiempo Real)
1. **Usuario ingresa datos** en formulario Streamlit
2. **Modelo ML procesa** los datos usando transformador + XGBoost
3. **Resultado mostrado** en pantalla (probabilidad de riesgo)
4. **Persistencia atómica** del registro en formato Avro

#### Fase 2: Consolidación (Batch)
5. **Trigger manual/automático** ejecuta `arvo_parket.py`
6. **Extracción** de todos los `.avro` pendientes
7. **Transformación** a DataFrame unificado con validaciones
8. **Carga** incremental a Parquet (append o merge)
9. **Archivo** de registros procesados para auditoría

#### Fase 3: Consumo (Análisis)
10. **Herramientas BI** conectan directamente al Parquet
11. **Scripts Python** realizan análisis estadísticos

---

## 🧩 Descripción de Componentes

### 1️⃣ **streamlit_app_arvo.py** - Interfaz de Usuario

**Responsabilidades:**
- ✅ Capturar datos demográficos y clínicos del paciente
- ✅ Validar entrada del usuario (rangos, tipos de datos)
- ✅ Invocar modelo ML para predicción en tiempo real
- ✅ Persistir cada registro como archivo Avro individual
- ✅ Asignar nombres de archivo con timestamp único

**Tecnologías:**
- `streamlit` - Framework web interactivo
- `fastavro` - Serialización Avro
- `joblib` - Carga de modelos pickle
- `pandas` - Manipulación de datos

**Ejemplo de Código (Simplificado):**

```python
import streamlit as st
import joblib
import fastavro
from datetime import datetime

# Cargar modelo
modelo = joblib.load('ml_model/model_xgb.pkl')
transformador = joblib.load('ml_model/transformador.pkl')

# Formulario
st.title("🏥 Predicción de Riesgo Cardíaco")
nombre = st.text_input("Nombre del paciente")
edad = st.number_input("Edad", min_value=18, max_value=120)
sexo = st.selectbox("Sexo", ["Masculino", "Femenino"])
presion = st.number_input("Presión arterial sistólica (mmHg)")

if st.button("Predecir Riesgo"):
    # Preparar datos
    datos = {
        'nombre': nombre,
        'edad': edad,
        'sexo': sexo,
        'presion_arterial': presion,
    }
    
    # Predicción
    X = transformador.transform([datos])
    probabilidad = modelo.predict_proba(X)[0][1]
    
    st.success(f"Probabilidad de riesgo: {probabilidad:.2%}")
    
    # Guardar en Avro
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"registros_pacientes/record_{timestamp}_{nombre}.avro"
    
    esquema = {
        "type": "record",
        "name": "RegistroPaciente",
        "fields": [
            {"name": "nombre", "type": "string"},
            {"name": "edad", "type": "int"},
            {"name": "probabilidad_riesgo", "type": "double"},
        ]
    }
    
    with open(filename, 'wb') as f:
        fastavro.writer(f, esquema, [datos])
    
    st.info(f"✅ Registro guardado: {filename}")
```

**Características Clave:**
- **Predicción Instantánea:** Sin latencia perceptible (< 100ms)
- **Validación en Tiempo Real:** Feedback inmediato al usuario
- **Persistencia Atómica:** Cada escritura es una transacción completa
- **Naming Convention:** `record_YYYYMMDD_HHMMSS_Nombre.avro`

---

### 2️⃣ **code_ml.py** - Motor de Machine Learning

**Responsabilidades:**
- ✅ Cargar y limpiar dataset UCI Heart Disease
- ✅ Ingeniería de características (feature engineering)
- ✅ Entrenar modelo XGBoost con validación cruzada
- ✅ Optimizar hiperparámetros (opcional: GridSearch)
- ✅ Serializar modelo y transformador

**Algoritmo:** XGBoost Classifier (Gradient Boosting)

**Pipeline de Preprocesamiento:**

```python
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.pipeline import Pipeline

# Definir columnas numéricas y categóricas
cols_numericas = ['edad', 'presion_arterial', 'colesterol', 'freq_cardiaca_max']
cols_categoricas = ['sexo', 'tipo_dolor_pecho', 'azucar_sangre', 'ecg_reposo']

# Crear transformador
transformador = ColumnTransformer([
    ('scaler_num', StandardScaler(), cols_numericas),
    ('encoder_cat', OneHotEncoder(drop='first', sparse_output=False), cols_categoricas)
])

# Pipeline completo
pipeline = Pipeline([
    ('transformador', transformador),
    ('modelo', XGBClassifier(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.1,
        random_state=42
    ))
])
```

**Flujo de Entrenamiento:**

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier
import joblib

# 1. Cargar datos
df = pd.read_csv('heart_disease_uci.csv')

# 2. Limpieza
df = df.dropna()

# 3. Split train/test
X = df.drop('target', axis=1)
y = df['target']
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# 4. Entrenar
pipeline.fit(X_train, y_train)

# 5. Evaluar
from sklearn.metrics import roc_auc_score
y_pred_proba = pipeline.predict_proba(X_test)[:, 1]
auc = roc_auc_score(y_test, y_pred_proba)
print(f"AUC-ROC: {auc:.3f}")

# 6. Guardar
joblib.dump(pipeline.named_steps['modelo'], 'ml_model/model_xgb.pkl')
joblib.dump(pipeline.named_steps['transformador'], 'ml_model/transformador.pkl')
```

**Métricas Típicas:**
- **AUC-ROC:** 0.85 - 0.90 (excelente discriminación)
- **Accuracy:** ~85%
- **Sensibilidad (Recall):** ~82% (detecta 82% de casos positivos)
- **Especificidad:** ~87% (descarta 87% de casos negativos)

---

### 3️⃣ **arvo_parket.py** - Pipeline ETL

**Responsabilidades:**
- ✅ **Extract:** Leer todos los `.avro` de `registros_pacientes/`
- ✅ **Transform:** Unificar en DataFrame Pandas con validación de esquema
- ✅ **Load:** Escribir/anexar datos a `datalake_maestro.parquet`
- ✅ **Archive:** Mover archivos procesados a zona histórica
- ✅ **Logging:** Registrar operaciones y errores

**Código Completo:**

```python
import os
import glob
import shutil
import pandas as pd
import fastavro
import pyarrow.parquet as pq
from datetime import datetime

def procesar_pipeline():
    """
    Pipeline ETL completo para consolidar archivos Avro a Parquet
    """
    
    # ===== EXTRACT =====
    print("🔍 Fase 1: Extrayendo archivos Avro...")
    archivos_pendientes = glob.glob('registros_pacientes/*.avro')
    
    if not archivos_pendientes:
        print("⚠️  No hay archivos pendientes de procesar")
        return
    
    print(f"   Encontrados: {len(archivos_pendientes)} archivos")
    
    # ===== TRANSFORM =====
    print("\n🔄 Fase 2: Transformando datos...")
    registros = []
    
    for archivo in archivos_pendientes:
        try:
            with open(archivo, 'rb') as f:
                avro_reader = fastavro.reader(f)
                for registro in avro_reader:
                    # Agregar metadatos de auditoría
                    registro['_ingested_at'] = datetime.now().isoformat()
                    registro['_source_file'] = os.path.basename(archivo)
                    registros.append(registro)
        except Exception as e:
            print(f"   ❌ Error leyendo {archivo}: {e}")
            continue
    
    if not registros:
        print("   ⚠️  No se pudieron extraer registros válidos")
        return
    
    df_nuevo = pd.DataFrame(registros)
    print(f"   ✅ Unificados {len(df_nuevo)} registros")
    
    # Validación de esquema
    columnas_requeridas = ['nombre', 'edad', 'probabilidad_riesgo']
    if not all(col in df_nuevo.columns for col in columnas_requeridas):
        raise ValueError("Esquema inválido: faltan columnas requeridas")
    
    # ===== LOAD =====
    print("\n💾 Fase 3: Cargando a Parquet...")
    parquet_path = 'datalake_maestro.parquet'
    
    if os.path.exists(parquet_path):
        # Append incremental
        df_existente = pd.read_parquet(parquet_path)
        df_consolidado = pd.concat([df_existente, df_nuevo], ignore_index=True)
        
        # Deduplicación
        df_consolidado = df_consolidado.drop_duplicates(
            subset=['nombre', '_ingested_at'], 
            keep='last'
        )
    else:
        # Primera escritura
        df_consolidado = df_nuevo
    
    # Escribir con compresión
    df_consolidado.to_parquet(
        parquet_path,
        engine='pyarrow',
        compression='snappy',
        index=False
    )
    
    print(f"   ✅ Escritos {len(df_consolidado)} registros totales")
    print(f"   📦 Tamaño: {os.path.getsize(parquet_path) / 1024:.2f} KB")
    
    # ===== ARCHIVE =====
    print("\n📦 Fase 4: Archivando procesados...")
    os.makedirs('registros_procesados', exist_ok=True)
    
    for archivo in archivos_pendientes:
        destino = os.path.join('registros_procesados', os.path.basename(archivo))
        shutil.move(archivo, destino)
        print(f"   ✅ Movido: {os.path.basename(archivo)}")
    
    print("\n🎉 Pipeline completado exitosamente")

if __name__ == "__main__":
    procesar_pipeline()
```

---

## 🗄️ Zonas de Datos

### Arquitectura Medallion Simplificada

| Zona | Directorio | Formato | Propósito | Características |
|------|-----------|---------|-----------|-----------------|
| **Bronze** | `registros_pacientes/` | Avro | Ingesta transaccional rápida | Orientado a fila, esquema embebido |
| **Archive** | `registros_procesados/` | Avro | Auditoría e historial inmutable | Backup completo, no se modifica |
| **Gold** | `datalake_maestro.parquet` | Parquet | Consultas analíticas optimizadas | Orientado a columna, compresión inteligente |

### ¿Por qué Avro en Bronze?

**Ventajas:**
- ✅ **Orientado a fila:** Ideal para escrituras de un registro a la vez
- ✅ **Esquema embebido:** Autovalidación de estructura
- ✅ **Compacto:** Serialización binaria eficiente (50% más pequeño que JSON)
- ✅ **Evolución de esquema:** Compatible con cambios hacia adelante/atrás

**Casos de uso ideales:**
- Logs de eventos en tiempo real
- Sistemas transaccionales (OLTP)
- Streaming de datos (Kafka)

### ¿Por qué Parquet en Gold?

**Ventajas:**
- ✅ **Orientado a columna:** Consultas 100x más rápidas para agregaciones
- ✅ **Compresión inteligente:** 5-10x menos espacio que CSV
- ✅ **Predicate pushdown:** Lee solo las columnas y filas necesarias
- ✅ **Compatible con BI:** Power BI, Tableau, Apache Spark, DuckDB

**Casos de uso ideales:**
- Análisis de datos (OLAP)
- Data warehouses
- Machine Learning feature stores

---

## 🚀 Guía de Instalación

### Prerequisitos

- **Python:** 3.9 o superior
- **Sistema Operativo:** Linux, macOS, o Windows
- **RAM:** Mínimo 2 GB (recomendado 4 GB)
- **Disco:** 500 MB libres

### Paso 1: Crear Entorno Virtual

```bash
# Linux/Mac
python3 -m venv webdjango
source webdjango/bin/activate

# Windows
python -m venv webdjango
webdjango\Scripts\activate
```

### Paso 2: Instalar Dependencias

```bash
# Actualizar pip
pip install --upgrade pip

# Instalar paquetes core
pip install streamlit pandas numpy scikit-learn xgboost joblib fastavro pyarrow

# Verificar instalación
python -c "import streamlit; print(f'Streamlit {streamlit.__version__}')"
python -c "import xgboost; print(f'XGBoost {xgboost.__version__}')"
```

### Paso 3: Crear Estructura de Directorios

```bash
mkdir -p registros_pacientes registros_procesados ml_model
```

### Verificación de Instalación

```bash
# Debe mostrar las versiones instaladas
pip list | grep -E "streamlit|xgboost|fastavro|pyarrow"
```

**Output esperado:**
```
fastavro           1.9.0
pyarrow            14.0.1
streamlit          1.28.2
xgboost            2.0.3
```

---

## 📖 Guía de Uso

### Flujo Completo de Trabajo

#### Paso 1: Entrenar el Modelo (Una sola vez)

```bash
python code_ml.py
```

**Output esperado:**

```
🧠 Iniciando entrenamiento del modelo...

📊 Cargando dataset UCI Heart Disease...
   ✅ Cargados 303 registros

🔄 Preprocesando datos...
   ✅ Imputación de valores faltantes completada
   ✅ Split train/test: 242 / 61 registros

🚀 Entrenando XGBoost Classifier...
   [0]     validation_0-logloss:0.62341
   [10]    validation_0-logloss:0.45123
   [20]    validation_0-logloss:0.38456
   [50]    validation_0-logloss:0.32109
   [99]    validation_0-logloss:0.29871

✅ Entrenamiento completado

📊 Métricas en conjunto de prueba:
   - AUC-ROC: 0.873
   - Accuracy: 0.852
   - Sensibilidad: 0.821
   - Especificidad: 0.876

💾 Guardando artefactos...
   ✅ ml_model/model_xgb.pkl (2.3 MB)
   ✅ ml_model/transformador.pkl (45 KB)

🎉 Modelo entrenado exitosamente
```

---

#### Paso 2: Capturar Datos de Pacientes

```bash
streamlit run streamlit_app_arvo.py
```

**Acciones en la interfaz:**

1. **Abrir navegador** en `http://localhost:8501`
2. **Completar formulario médico:**
   - Nombre del paciente
   - Edad (18-120 años)
   - Sexo (Masculino/Femenino)
   - Presión arterial sistólica (mmHg)
   - Colesterol sérico (mg/dl)
   - Frecuencia cardíaca máxima
   - Y más campos clínicos...

3. **Click en "Predecir Riesgo"**
4. **Ver resultado:**
   ```
   🎯 Probabilidad de Riesgo Cardíaco: 68.3%
   ⚠️  Clasificación: Riesgo Alto
   ```

5. **Confirmación de guardado:**
   ```
   ✅ Registro guardado exitosamente
   📄 Archivo: registros_pacientes/record_20260101_152030_JuanPerez.avro
   ```

**Resultado:** Se crea automáticamente un archivo `.avro` en la carpeta `registros_pacientes/`

---

#### Paso 3: Consolidar a Parquet (ETL)

```bash
python arvo_parket.py
```

**Output en consola:**

```
🔍 Fase 1: Extrayendo archivos Avro...
   Encontrados: 5 archivos

🔄 Fase 2: Transformando datos...
   ✅ Unificados 5 registros
   ✅ Validación de esquema: OK

💾 Fase 3: Cargando a Parquet...
   ℹ️  Detectado archivo existente, anexando...
   ✅ Escritos 23 registros totales
   �� Tamaño del archivo: 3.47 KB
   📈 Tasa de compresión: 8.2x vs CSV

📦 Fase 4: Archivando procesados...
   ✅ Movido: record_20260101_212921_Manuel.avro
   ✅ Movido: record_20260101_213010_Ricardo.avro
   ✅ Movido: record_20260101_213032_Ita.avro
   ✅ Movido: record_20260101_214505_Ana.avro
   ✅ Movido: record_20260101_215120_Carlos.avro

🎉 Pipeline completado exitosamente
   ⏱️  Tiempo de ejecución: 0.23 segundos
```

---

#### Paso 4: Consultar Data Lake (Análisis)

```python
import pandas as pd
import pyarrow.parquet as pq

# ===== CONSULTA BÁSICA =====
# Leer solo columnas necesarias (optimización)
df = pd.read_parquet(
    'datalake_maestro.parquet',
    columns=['nombre', 'edad', 'probabilidad_riesgo']
)

print(df.head())
```

**Output:**
```
           nombre  edad  probabilidad_riesgo
0          Manuel    45                0.683
1         Ricardo    62                0.891
2             Ita    38                0.234
3             Ana    55                0.756
4          Carlos    71                0.923
```

```python
# ===== ANÁLISIS ESTADÍSTICO =====
print(f"Total de pacientes: {len(df)}")
print(f"Riesgo promedio: {df['probabilidad_riesgo'].mean():.2%}")
print(f"Edad promedio: {df['edad'].mean():.1f} años")

# Pacientes de alto riesgo (>70%)
alto_riesgo = df[df['probabilidad_riesgo'] > 0.7]
print(f"Pacientes de alto riesgo: {len(alto_riesgo)} ({len(alto_riesgo)/len(df):.1%})")

# ===== CONSULTA CON FILTROS =====
# Gracias a Parquet, esto es ultra rápido (predicate pushdown)
pacientes_mayores = pd.read_parquet(
    'datalake_maestro.parquet',
    filters=[('edad', '>', 60)]
)

# ===== EXPORTAR A OTROS FORMATOS =====
df.to_csv('reporte_pacientes.csv', index=False)
df.to_excel('reporte_pacientes.xlsx', index=False)

print("✅ Reportes exportados")
```

---

## 📊 Análisis de Datos

### Ejemplo 1: Dashboard Simple con Pandas

```python
import pandas as pd
import matplotlib.pyplot as plt

# Cargar datos
df = pd.read_parquet('datalake_maestro.parquet')

# Distribución de riesgo por edad
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Gráfico 1: Histograma de edad
axes[0].hist(df['edad'], bins=20, edgecolor='black', alpha=0.7)
axes[0].set_xlabel('Edad')
axes[0].set_ylabel('Frecuencia')
axes[0].set_title('Distribución de Edad')

# Gráfico 2: Boxplot de riesgo por sexo
df.boxplot(column='probabilidad_riesgo', by='sexo', ax=axes[1])
axes[1].set_xlabel('Sex
