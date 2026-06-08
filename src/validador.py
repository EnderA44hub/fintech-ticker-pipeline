import pandas as pd
import os
import json
from loguru import logger

BRONZE_PATH = "data/bronze"
SILVER_PATH = "data/silver"
DEAD_LETTER_PATH = "data/silver_dead_letter"

AÑOS_MINIMOS = 10

def validar_ticker(ticker, df):
    errores = []
    advertencias = []

    if df.empty:
        return "descartado", ["sin datos"]

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    columnas_necesarias = ["Open", "High", "Low", "Close", "Volume"]
    for col in columnas_necesarias:
        if col not in df.columns:
            return "descartado", [f"falta columna {col}"]

    if (df["High"] < df["Low"]).any():
        errores.append("High < Low detectado")

    if (df["Close"] <= 0).any():
        errores.append("precio negativo o cero")

    if errores:
        return "descartado", errores

    años_de_historia = (df.index[-1] - df.index[0]).days / 365
    if años_de_historia < AÑOS_MINIMOS:
        advertencias.append(f"solo {años_de_historia:.1f} años de historia")

    if advertencias:
        return "dead_letter", advertencias

    return "ok", []


def guardar_silver(ticker, estado, motivos):
    """
    Silver solo guarda metadata — no el dataframe completo
    El historial completo vive en Bronze
    """
    metadata = {
        "ticker": ticker,
        "estado": estado,
        "motivos": motivos
    }

    if estado == "ok":
        ruta = f"{SILVER_PATH}/{ticker}.json"
    else:
        ruta = f"{DEAD_LETTER_PATH}/{ticker}.json"

    with open(ruta, "w") as f:
        json.dump(metadata, f)


def validar_todos():
    archivos = os.listdir(BRONZE_PATH)

    if not archivos:
        logger.warning("No hay archivos en Bronze para validar")
        return

    logger.info(f"Validando {len(archivos)} tickers desde Bronze")

    resultados = {"ok": [], "dead_letter": [], "descartado": []}

    for archivo in archivos:
        ticker = archivo.replace(".parquet", "")
        ruta = f"{BRONZE_PATH}/{archivo}"

        df = pd.read_parquet(ruta)
        estado, motivos = validar_ticker(ticker, df)

        guardar_silver(ticker, estado, motivos)

        if estado == "ok":
            logger.info(f"{ticker}: ✅ Silver")
        elif estado == "dead_letter":
            logger.warning(f"{ticker}: ⚠️  Dead Letter — {motivos}")
        else:
            logger.error(f"{ticker}: ❌ Descartado — {motivos}")

        resultados[estado].append(ticker)

    logger.info("=" * 40)
    logger.info(f"✅ Silver:       {len(resultados['ok'])}")
    logger.info(f"⚠️  Dead Letter: {len(resultados['dead_letter'])}")
    logger.info(f"❌ Descartados: {len(resultados['descartado'])}")
    logger.info("=" * 40)
    return {"ok": len(resultados["ok"]), "dead_letter": len(resultados["dead_letter"])}


if __name__ == "__main__":
    validar_todos()