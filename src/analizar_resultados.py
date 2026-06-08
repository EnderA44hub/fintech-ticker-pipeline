import os
import json
import pandas as pd
from loguru import logger

RESULTADOS_PATH = "resultados"

def cargar_historial():
    """Lee todos los JSONs de resultados y los combina en un DataFrame"""
    archivos = os.listdir(RESULTADOS_PATH)
    
    if not archivos:
        logger.warning("No hay resultados todavía")
        return None

    todos = []
    for archivo in archivos:
        ruta = f"{RESULTADOS_PATH}/{archivo}"
        with open(ruta, "r") as f:
            data = json.load(f)
        
        fecha = data["fecha"]
        for ticker in data["tickers"]:
            ticker["fecha"] = fecha
            todos.append(ticker)

    df = pd.DataFrame(todos)
    logger.info(f"Historial cargado: {len(df)} registros de {df['fecha'].nunique()} sesiones")
    return df

def top_tickers(df, min_sesiones=1):
    """Tickers con mejor P&L promedio"""
    resumen = df.groupby("ticker").agg(
        sesiones=("fecha", "count"),
        pnl_total=("pnl_total", "sum"),
        pnl_promedio=("pnl_total", "mean"),
        win_rate_promedio=("win_rate", "mean"),
        trades_promedio=("trades_tomados", "mean")
    ).reset_index()

    resumen = resumen[resumen["sesiones"] >= min_sesiones]
    resumen = resumen.sort_values("pnl_total", ascending=False)
    return resumen

if __name__ == "__main__":
    df = cargar_historial()
    if df is not None:
        print("\n📊 TOP TICKERS por P&L total:")
        print(top_tickers(df).to_string(index=False))