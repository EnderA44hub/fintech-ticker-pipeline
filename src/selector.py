import pandas as pd
import os
import random
from datetime import datetime
from loguru import logger

# Rutas
GOLD_PATH = "data/gold"
OUTPUT_PATH = "data/listos_para_hoy"

# Cuántos tickers seleccionar por día
CANTIDAD_DIARIA = 40

def limpiar_output():
    """Limpia la carpeta listos_para_hoy para no mezclar con el día anterior"""
    archivos = os.listdir(OUTPUT_PATH)
    for archivo in archivos:
        os.remove(f"{OUTPUT_PATH}/{archivo}")
    logger.info(f"Carpeta listos_para_hoy limpiada")

def seleccionar_tickers_aleatorios():
    """Selecciona tickers aleatorios del Gold"""
    archivos = os.listdir(GOLD_PATH)

    if not archivos:
        logger.warning("No hay tickers en Gold para seleccionar")
        return []

    # Si hay menos tickers que la cantidad diaria, toma todos
    cantidad = min(CANTIDAD_DIARIA, len(archivos))

    seleccionados = random.sample(archivos, cantidad)
    logger.info(f"Seleccionados {cantidad} tickers aleatorios del universo Gold ({len(archivos)} disponibles)")

    return seleccionados

def exportar_csv(ticker, df):
    """Exporta el ticker como CSV listo para arrastrar al motor"""
    # Aplanar MultiIndex si existe
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # Formato exacto que necesita tu motor
    df_export = df[["Open", "High", "Low", "Close"]].copy()
    df_export.index.name = "Date"

    # Guardar como CSV
    ruta = f"{OUTPUT_PATH}/{ticker}.csv"
    df_export.to_csv(ruta)
    logger.info(f"{ticker}: ✅ CSV listo en listos_para_hoy")

def seleccionar():
    """Proceso completo de selección diaria"""
    fecha_hoy = datetime.today().strftime("%Y-%m-%d")
    logger.info(f"Selección diaria — {fecha_hoy}")

    # Limpiar output del día anterior
    limpiar_output()

    # Seleccionar tickers aleatorios
    seleccionados = seleccionar_tickers_aleatorios()

    if not seleccionados:
        return

    # Exportar cada uno como CSV
    for archivo in seleccionados:
        ticker = archivo.replace(".parquet", "")
        ruta = f"{GOLD_PATH}/{archivo}"

        df = pd.read_parquet(ruta)
        exportar_csv(ticker, df)

    logger.info("=" * 40)
    logger.info(f"✅ {len(seleccionados)} CSVs listos en data/listos_para_hoy")
    logger.info("Arrastra los CSVs a tu motor de backtest")
    logger.info("=" * 40)

if __name__ == "__main__":
    seleccionar()