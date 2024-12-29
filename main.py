import csv
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

TIEMPO_ESPERA = 2
URL = "https://servicios.pami.org.ar/vademecum/views/consultaPublica/listado.zul"


class DrogaScraper:
    def __init__(self):
        self.lock = threading.Lock()

    def inicializar_driver(self):
        driver = webdriver.Chrome()
        driver.get(URL)
        return driver, WebDriverWait(driver, 10)

    def guardar_en_csv(self, filename, data, headers=None):
        with self.lock:
            archivo_existe = os.path.exists(filename)
            modo = "a" if archivo_existe else "w"
            with open(filename, modo, newline="", encoding="utf-8") as f:
                writer = csv.writer(f, delimiter=";")
                if not archivo_existe and headers:
                    writer.writerow(headers)
                writer.writerow(data)

    def buscar_droga(self, driver, wait, droga):
        try:
            input_box = wait.until(
                EC.presence_of_element_located((By.ID, "zk_comp_28"))
            )
            input_box.clear()
            input_box.send_keys(droga)

            search_button = driver.find_element(By.ID, "zk_comp_80")
            search_button.click()
            time.sleep(TIEMPO_ESPERA)

            try:
                table_body = driver.find_element(By.ID, "zk_comp_109")
                rows = table_body.find_elements(By.TAG_NAME, "tr")
                return rows
            except NoSuchElementException:
                return []
        except Exception as e:
            print(f"Error buscando la droga {droga}: {e}")
            return []

    def guardar_medicamento(self, medicamento):
        with self.lock:
            archivo_existe = os.path.exists("csv/medicamentos.csv")
            modo = "a" if archivo_existe else "w"
            with open("csv/medicamentos.csv", modo, newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=medicamento.keys(), delimiter=";")
                if not archivo_existe:
                    writer.writeheader()
                writer.writerow(medicamento)

    def procesar_medicamento(self, driver, wait, row):
        try:
            tds = row.find_elements(By.TAG_NAME, "td")

            medicamento = {
                "ID": tds[6]
                .find_element(By.TAG_NAME, "span")
                .get_attribute("textContent"),
                "N° Certificado": tds[1].find_element(By.TAG_NAME, "span").text,
                "Laboratorio": tds[2].find_element(By.TAG_NAME, "span").text,
                "Nombre Comercial": tds[3].find_element(By.TAG_NAME, "span").text,
                "Forma Farmacéutica": tds[4].find_element(By.TAG_NAME, "span").text,
                "Presentación": tds[5].find_element(By.TAG_NAME, "span").text,
                "Genérico": tds[7].find_element(By.TAG_NAME, "span").text,
            }

            detail_button = tds[8].find_element(By.TAG_NAME, "a")
            detail_button.click()
            time.sleep(TIEMPO_ESPERA)

            medicamento["Drogas"] = driver.find_element(By.ID, "zk_comp_62").text
            medicamento["Condición de Expendio"] = driver.find_element(
                By.ID, "zk_comp_107"
            ).text

            back_button = wait.until(EC.element_to_be_clickable((By.ID, "zk_comp_165")))
            back_button.click()
            time.sleep(TIEMPO_ESPERA)

            return medicamento
        except Exception as e:
            print(f"Error procesando medicamento: {e}")
            return None

    def procesar_droga(self, droga):
        driver, wait = self.inicializar_driver()
        try:
            rows = self.buscar_droga(driver, wait, droga)

            if rows:
                # Agregar a drogas encontradas
                self.guardar_en_csv("csv/drogas_encontradas.csv", [droga], ["droga"])

                while True:  # Bucle para manejar la paginación
                    rows = driver.find_element(By.ID, "zk_comp_109").find_elements(
                        By.TAG_NAME, "tr"
                    )
                    for i in range(len(rows)):
                        rows = driver.find_element(By.ID, "zk_comp_109").find_elements(
                            By.TAG_NAME, "tr"
                        )
                        medicamento = self.procesar_medicamento(driver, wait, rows[i])

                        if medicamento:
                            self.guardar_medicamento(medicamento)
                            print(
                                f"Se guardó el medicamento: {medicamento['Genérico']}"
                            )

                    try:
                        boton_siguiente = driver.find_element(
                            By.NAME, "zk_comp_98-next"
                        )

                        if "disabled" in boton_siguiente.get_attribute("outerHTML"):
                            # Agregar a drogas procesadas después de procesar toda la paginación
                            self.guardar_en_csv(
                                "csv/drogas_procesadas.csv", [droga], ["droga"]
                            )
                            break
                        else:
                            boton_siguiente.click()
                            time.sleep(TIEMPO_ESPERA)
                    except NoSuchElementException:
                        print(
                            f"No se encontró el botón de siguiente página para la droga: {droga}"
                        )
                        # Agregar a drogas procesadas si no hay más páginas
                        self.guardar_en_csv(
                            "csv/drogas_procesadas.csv", [droga], ["droga"]
                        )
                        break
            else:
                # Agregar directamente a drogas no encontradas
                self.guardar_en_csv("csv/drogas_no_encontradas.csv", [droga], ["droga"])
                print(f"No se encontraron medicamentos para la droga: {droga}")

        except Exception as e:
            print(f"Error procesando la droga {droga}: {e}")
        finally:
            driver.quit()

    def cargar_drogas_desde_csv(self, filename):
        if os.path.exists(filename):
            df = pd.read_csv(filename, encoding="utf-8", sep=";")
            return df["droga"].tolist()
        return []


def eliminar_duplicados_inicial():
    if os.path.exists("csv/drogas_no_encontradas.csv"):
        df = pd.read_csv("csv/drogas_no_encontradas.csv", encoding="utf-8", sep=";")
        registros_originales = len(df)
        df = df.drop_duplicates()
        df.to_csv(
            "csv/drogas_no_encontradas.csv", index=False, encoding="utf-8", sep=";"
        )
        print(
            f"Duplicados eliminados en drogas_no_encontradas.csv: {registros_originales - len(df)}"
        )


def main():
    # Primero eliminar duplicados en csv/drogas_no_encontradas.csv
    eliminar_duplicados_inicial()

    # Leer drogas a buscar
    df_drogas = pd.read_csv("csv/drogas_a_buscar.csv", encoding="utf-8")
    drogas = df_drogas["droga"].tolist()

    # Inicializar scraper
    scraper = DrogaScraper()

    # Obtener drogas ya procesadas y no encontradas
    drogas_no_encontradas = scraper.cargar_drogas_desde_csv(
        "csv/drogas_no_encontradas.csv"
    )
    drogas_procesadas = scraper.cargar_drogas_desde_csv("csv/drogas_procesadas.csv")

    # Filtrar drogas que no han sido procesadas
    drogas_a_procesar = [
        d
        for d in drogas
        if d not in drogas_no_encontradas and d not in drogas_procesadas
    ]

    print(f"Procesando {len(drogas_a_procesar)} drogas...")

    # Procesar drogas en paralelo
    with ThreadPoolExecutor(max_workers=7) as executor:
        executor.map(scraper.procesar_droga, drogas_a_procesar)


if __name__ == "__main__":
    main()
