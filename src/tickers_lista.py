import pandas as pd
from loguru import logger

LISTA_NEGRA = [
    "PXD",
    "PARA",
]

def obtener_sp500():
    try:
        df = pd.read_csv("tickers_sp500.csv")
        tickers = df["Symbol"].dropna().tolist()
        tickers = [t.replace(".", "-") for t in tickers]
        logger.info(f"S&P 500: {len(tickers)} tickers")
        return tickers
    except Exception as e:
        logger.warning(f"S&P 500 falló: {e}")
        return []

def obtener_nasdaq():
    try:
        df = pd.read_csv("tickers_nasdaq.csv")
        # Detectar columna correcta
        for col in df.columns:
            if "symbol" in col.lower() or "ticker" in col.lower():
                tickers = df[col].dropna().tolist()
                logger.info(f"Nasdaq: {len(tickers)} tickers")
                return tickers
        logger.warning("Nasdaq CSV: no se encontró columna de tickers")
        return []
    except Exception as e:
        logger.warning(f"Nasdaq falló: {e}")
        return []

def obtener_todos_los_tickers():
    todos = []

    todos += obtener_sp500()
    todos += obtener_nasdaq()

    # Limpiar
    todos = [t for t in todos if isinstance(t, str)]
    todos = [t.strip() for t in todos]
    todos = [t for t in todos if str(t).replace("-","").isalpha() and len(t) <= 5]
    todos = [t for t in todos if t not in LISTA_NEGRA]
    todos = list(set(todos))

    logger.info(f"Total universo: {len(todos)} tickers únicos")
    return todos

if __name__ == "__main__":
    tickers = obtener_todos_los_tickers()
    print(f"Total: {len(tickers)}")
    print(f"Primeros 10: {tickers[:10]}")