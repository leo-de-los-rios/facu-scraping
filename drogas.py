import os

import pandas as pd

# Ruta del archivo CSV de entrada
input_csv_path = "csv/base_medic_limpia - copia.csv"  # Cambia esta ruta si es necesario

# Leer el archivo CSV, omitiendo las líneas con errores
data = pd.read_csv(input_csv_path, on_bad_lines="skip", encoding="utf-8", sep=";")

# Inicializar un conjunto para almacenar drogas únicas
drogas = set()

# Agregar valores únicos de las columnas droga1 y droga2, omitiendo nulos
if "droga1" in data.columns:
    drogas.update(data["droga1"].dropna().unique())
if "droga2" in data.columns:
    drogas.update(data["droga2"].dropna().unique())

# Convertir el conjunto a una lista ordenada
drogas_unicas = sorted(list(drogas))

# Crear un DataFrame con las drogas únicas
drogas_df = pd.DataFrame(drogas_unicas, columns=["droga"])

# Ruta del archivo CSV de salida
output_csv_path = "csv/drogas_a_buscar.csv"

# Guardar las drogas únicas en el archivo CSV, sobrescribiéndolo si ya existe
drogas_df.to_csv(output_csv_path, index=False, encoding="utf-8", sep=";")

print(
    f"Las drogas únicas de las columnas 'droga1' y 'droga2' han sido guardadas en '{output_csv_path}'"
)
