import os

import pandas as pd


def eliminar_duplicados_archivo(filename):
    if not os.path.exists(filename):
        print(f"El archivo {filename} no existe.")
        return

    print(f"\nProcesando {filename}...")
    try:
        # Leer el archivo CSV con el encoding y delimiter correctos
        df = pd.read_csv(filename, encoding="utf-8", sep=";")

        # Guardar el número original de registros
        registros_originales = len(df)
        print(f"Registros originales: {registros_originales}")

        # Eliminar duplicados
        df_sin_duplicados = df.drop_duplicates()

        # Calcular estadísticas
        registros_finales = len(df_sin_duplicados)
        duplicados_eliminados = registros_originales - registros_finales

        print(f"Duplicados encontrados y eliminados: {duplicados_eliminados}")
        print(f"Registros finales: {registros_finales}")

        # Sobreescribir el archivo original
        df_sin_duplicados.to_csv(filename, index=False, encoding="utf-8", sep=";")
        print(f"Archivo {filename} actualizado exitosamente.")

    except Exception as e:
        print(f"Error al procesar el archivo {filename}: {e}")


def main():
    # Lista de archivos a procesar
    archivos = [
        "csv/medicamentos.csv",
        "csv/drogas_no_encontradas.csv",
        "csv/drogas_encontradas.csv",
        "csv/drogas_procesadas.csv",
    ]

    for archivo in archivos:
        eliminar_duplicados_archivo(archivo)


if __name__ == "__main__":
    main()
