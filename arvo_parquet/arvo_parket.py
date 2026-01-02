import os
import shutil
import pandas as pd
import fastavro

ORIGEN = "registros_pacientes"
PROCESADOS = "registros_procesados"
DESTINO_PARQUET = "datalake_maestro.parquet"

if not os.path.exists(PROCESADOS):
    os.makedirs(PROCESADOS)

def procesar_solo_nuevos():
    archivos_nuevos = [f for f in os.listdir(ORIGEN) if f.endswith('.avro')]
    
    if not archivos_nuevos:
        print("No hay registros nuevos para procesar.")
        return

    # Leer los nuevos
    registros_nuevos = []
    for f in archivos_nuevos:
        ruta = os.path.join(ORIGEN, f)
        with open(ruta, 'rb') as fo:
            for registro in fastavro.reader(fo):
                registros_nuevos.append(registro)
        
        # MOVER a procesados para no leerlo la próxima vez
        shutil.move(ruta, os.path.join(PROCESADOS, f))

    df_nuevo = pd.DataFrame(registros_nuevos)

    # Si ya existe el parquet, combinamos; si no, lo creamos
    if os.path.exists(DESTINO_PARQUET):
        df_antiguo = pd.read_parquet(DESTINO_PARQUET)
        df_final = pd.concat([df_antiguo, df_nuevo], ignore_index=True)
    else:
        df_final = df_nuevo

    df_final.to_parquet(DESTINO_PARQUET, engine='pyarrow')
    print(f"✅ Se agregaron {len(archivos_nuevos)} registros nuevos al Data Lake.")
    
procesar_solo_nuevos()

# Leer el archivo completo
df = pd.read_parquet('datalake_maestro.parquet')

# Mostrar los primeros registros
print(df.head())

