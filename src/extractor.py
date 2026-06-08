import yfinance as yf
import pandas as pd
import os
from loguru import logger

BRONZE_PATH = "data/bronze"

def descargar_ticker(ticker):
    """Descarga datos de un ticker — incremental si ya existe"""
    try:
        ruta = f"{BRONZE_PATH}/{ticker}.parquet"

        # ¿Ya existe data histórica?
        if os.path.exists(ruta):
            df_existente = pd.read_parquet(ruta)

            # Aplanar MultiIndex si existe
            if isinstance(df_existente.columns, pd.MultiIndex):
                df_existente.columns = df_existente.columns.get_level_values(0)

            # Solo descargar los últimos 5 días
            df_nuevo = yf.download(ticker, period="5d", auto_adjust=True, progress=False)

            if df_nuevo.empty:
                logger.warning(f"{ticker}: sin datos nuevos")
                return df_existente

            # Aplanar MultiIndex si existe
            if isinstance(df_nuevo.columns, pd.MultiIndex):
                df_nuevo.columns = df_nuevo.columns.get_level_values(0)

            # Combinar existente + nuevo, eliminar duplicados
            df_combinado = pd.concat([df_existente, df_nuevo])
            df_combinado = df_combinado[~df_combinado.index.duplicated(keep="last")]
            df_combinado = df_combinado.sort_index(ascending=True)

            logger.info(f"{ticker}: actualizado incrementalmente ✅")
            return df_combinado

        else:
            # Primera vez — descarga todo el historial
            df = yf.download(ticker, period="max", auto_adjust=True, progress=False)

            if df.empty:
                logger.warning(f"{ticker}: sin datos")
                return None

            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            logger.info(f"{ticker}: descarga completa ✅")
            return df

    except Exception as e:
        logger.error(f"{ticker}: falló — {e}")
        return None


def guardar_bronze(ticker, df):
    """Guarda el ticker en Bronze"""
    ruta = f"{BRONZE_PATH}/{ticker}.parquet"
    df.to_parquet(ruta)


def extraer_tickers(lista_tickers):
    """Extrae todos los tickers"""
    logger.info(f"Iniciando extracción de {len(lista_tickers)} tickers")

    exitosos = 0
    fallidos = 0

    for i, ticker in enumerate(lista_tickers):
        df = descargar_ticker(ticker)

        if df is not None:
            guardar_bronze(ticker, df)
            exitosos += 1
        else:
            fallidos += 1

        if (i + 1) % 100 == 0:
            logger.info(f"Progreso: {i + 1}/{len(lista_tickers)}")

    logger.info(f"Extracción completa — ✅ {exitosos} exitosos | ❌ {fallidos} fallidos")
    return {"exitosos": exitosos, "fallidos": fallidos}


if __name__ == "__main__":
    tickers_prueba = ["AAPL", "MSFT", "TSLA"]
    extraer_tickers(tickers_prueba)
    
