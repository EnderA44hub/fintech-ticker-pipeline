import pandas as pd
import yfinance as yf
import os
from loguru import logger

# Rutas
BRONZE_PATH = "data/bronze"
SILVER_PATH = "data/silver"
GOLD_PATH = "data/gold"

# Filtros Gold
AÑOS_MINIMOS = 10

def aplicar_filtros_gold(ticker, df):
    motivos_rechazo = []

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # Filtro 1 — Sin dividendos (con caché)
    try:
        from src.cache_dividendos import obtener_dividendo
        info = yf.Ticker(ticker).info
        dividendo = obtener_dividendo(ticker, info)
        if dividendo > 0:
            motivos_rechazo.append(f"paga dividendos ({dividendo:.2%})")
    except Exception as e:
        motivos_rechazo.append(f"no se pudo verificar dividendos: {e}")

    # Filtro 2 — Mínimo 10 años de historia
    años_historia = (df.index[-1] - df.index[0]).days / 365
    if años_historia < AÑOS_MINIMOS:
        motivos_rechazo.append(f"solo {años_historia:.1f} años de historia")

    return motivos_rechazo


def preparar_para_gold(ticker, df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df_gold = df[["Open", "High", "Low", "Close"]].copy()
    df_gold.index.name = "Date"
    df_gold = df_gold.round(4)
    df_gold = df_gold.sort_index(ascending=True)
    return df_gold


def guardar_gold(ticker, df):
    ruta = f"{GOLD_PATH}/{ticker}.parquet"
    df.to_parquet(ruta)


def transformar_todos():
    # Limpiar Gold anterior
    archivos_gold = os.listdir(GOLD_PATH)
    for archivo in archivos_gold:
        os.remove(f"{GOLD_PATH}/{archivo}")
    logger.info(f"Gold limpiado — {len(archivos_gold)} archivos eliminados")

    # Leer tickers válidos desde Silver (JSONs)
    archivos = os.listdir(SILVER_PATH)

    if not archivos:
        logger.warning("No hay archivos en Silver para transformar")
        return

    logger.info(f"Aplicando filtros Gold a {len(archivos)} tickers")

    aprobados = []
    rechazados = []

    for archivo in archivos:
        ticker = archivo.replace(".json", "")

        # Leer historial desde Bronze
        ruta_bronze = f"{BRONZE_PATH}/{ticker}.parquet"
        if not os.path.exists(ruta_bronze):
            logger.warning(f"{ticker}: no encontrado en Bronze")
            continue

        df = pd.read_parquet(ruta_bronze)
        motivos = aplicar_filtros_gold(ticker, df)

        if not motivos:
            df_gold = preparar_para_gold(ticker, df)
            guardar_gold(ticker, df_gold)
            aprobados.append(ticker)
            logger.info(f"{ticker}: ✅ Gold")
        else:
            rechazados.append((ticker, motivos))
            logger.warning(f"{ticker}: ❌ No pasó Gold — {motivos}")

    logger.info("=" * 40)
    logger.info(f"✅ Gold:      {len(aprobados)} tickers")
    logger.info(f"❌ Rechazados: {len(rechazados)} tickers")
    logger.info("=" * 40)
    return {"aprobados": len(aprobados), "rechazados": len(rechazados)}


if __name__ == "__main__":
    transformar_todos()