import os
import json
import sys
import yfinance as yf
import pandas as pd
from datetime import datetime
from loguru import logger
from src.reporte_email import enviar_reporte
from src.selector import seleccionar

# ---- LOGS ----
logger.remove()
logger.add(sys.stdout, format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")
logger.add(
    "logs/diario_{time:YYYY-MM-DD}.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    rotation="1 day", retention="30 days", level="DEBUG"
)

BRONZE_PATH = "data/bronze"
GOLD_PATH = "data/gold"

def leer_universo_gold():
    """Lee la lista de tickers Gold del último pipeline semanal"""
    if not os.path.exists("universo_gold.json"):
        logger.error("❌ No existe universo_gold.json — corre el pipeline semanal primero")
        return []
    with open("universo_gold.json", "r") as f:
        data = json.load(f)
    logger.info(f"📂 Universo Gold: {len(data['tickers'])} tickers (generado {data['fecha_generado'][:10]})")
    return data["tickers"]

def actualizar_precios(tickers):
    """Descarga los últimos 5 días e incorpora a Bronze y Gold"""
    actualizados = 0
    fallidos = 0

    for ticker in tickers:
        try:
            nuevo = yf.download(ticker, period="5d", progress=False, auto_adjust=False)
            if nuevo.empty:
                fallidos += 1
                continue

            if isinstance(nuevo.columns, pd.MultiIndex):
                nuevo.columns = nuevo.columns.get_level_values(0)

            # Combinar con Bronze existente
            ruta_bronze = f"{BRONZE_PATH}/{ticker}.parquet"
            if os.path.exists(ruta_bronze):
                viejo = pd.read_parquet(ruta_bronze)
                if isinstance(viejo.columns, pd.MultiIndex):
                    viejo.columns = viejo.columns.get_level_values(0)
                combinado = pd.concat([viejo, nuevo])
                combinado = combinado[~combinado.index.duplicated(keep="last")]
                combinado = combinado.sort_index()
            else:
                combinado = nuevo

            combinado.to_parquet(ruta_bronze)

            # Regenerar Gold (solo OHLC)
            df_gold = combinado[["Open", "High", "Low", "Close"]].copy()
            df_gold.index.name = "Date"
            df_gold = df_gold.round(4).sort_index()
            df_gold.to_parquet(f"{GOLD_PATH}/{ticker}.parquet")

            actualizados += 1
        except Exception as e:
            logger.warning(f"{ticker}: error actualizando — {e}")
            fallidos += 1

    logger.info(f"Precios actualizados: {actualizados} | fallidos: {fallidos}")
    return actualizados, fallidos

def limpiar_listos():
    """Limpia solo la carpeta de selección diaria"""
    carpeta = "data/listos_para_hoy"
    archivos = os.listdir(carpeta)
    for a in archivos:
        os.remove(f"{carpeta}/{a}")
    logger.info(f"listos_para_hoy limpiada — {len(archivos)} archivos")

def abrir_motor():
    import webbrowser, threading, time, http.server, socketserver
    logger.info("🌐 Levantando servidor local")
    def servidor():
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        handler = http.server.SimpleHTTPRequestHandler
        handler.log_message = lambda *a: None
        with socketserver.TCPServer(("", 8080), handler) as httpd:
            httpd.serve_forever()
    threading.Thread(target=servidor, daemon=True).start()
    time.sleep(1)
    webbrowser.open("http://localhost:8080/motor/index.html")

def correr_diario():
    inicio = datetime.now()
    logger.info("=" * 50)
    logger.info(f"⚡ PIPELINE DIARIO — {inicio.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 50)

    stats = {
        "bronze_ok": 0, "bronze_fallidos": 0,
        "silver_ok": 0, "dead_letter": 0,
        "gold": 0, "gold_rechazados": 0,
        "seleccionados": [], "duracion": 0, "errores": "Ninguno"
    }

    try:
        limpiar_listos()
        tickers = leer_universo_gold()
        if not tickers:
            raise Exception("Universo Gold vacío — corre el semanal")

        logger.info(f"Actualizando precios de {len(tickers)} tickers Gold")
        ok, fall = actualizar_precios(tickers)
        stats["gold"] = ok
        stats["bronze_ok"] = ok
        stats["bronze_fallidos"] = fall

        logger.info("Seleccionando 40 aleatorios")
        seleccionar()

        stats["seleccionados"] = [
            f.replace(".csv", "")
            for f in os.listdir("data/listos_para_hoy")
            if f.endswith(".csv")
        ]

        fin = datetime.now()
        stats["duracion"] = (fin - inicio).seconds
        logger.info("=" * 50)
        logger.info(f"✅ DIARIO COMPLETO en {stats['duracion']} segundos")
        logger.info("=" * 50)

    except Exception as e:
        stats["errores"] = str(e)
        stats["duracion"] = (datetime.now() - inicio).seconds
        logger.error(f"❌ DIARIO FALLÓ — {e}")

    finally:
        enviar_reporte(stats)
        abrir_motor()

if __name__ == "__main__":
    correr_diario()