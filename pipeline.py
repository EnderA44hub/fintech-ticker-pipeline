import os
import schedule
import time
from datetime import datetime
from loguru import logger
import sys
from src.reporte_email import enviar_reporte

# ---- CONFIGURACIÓN DE LOGS ----
logger.remove()

logger.add(sys.stdout, format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")

logger.add(
    "logs/pipeline_{time:YYYY-MM-DD}.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    rotation="1 day",
    retention="30 days",
    level="DEBUG"
)

from src.extractor import extraer_tickers
from src.validador import validar_todos
from src.transformador import transformar_todos
from src.selector import seleccionar
from src.tickers_lista import obtener_todos_los_tickers

TICKERS = obtener_todos_los_tickers()
HORA_EJECUCION = "18:00"

# ---- PIPELINE ----
def limpiar_carpetas():
    carpetas = [
        "data/silver",
        "data/gold",
        "data/listos_para_hoy"
    ]
    for carpeta in carpetas:
        archivos = os.listdir(carpeta)
        for archivo in archivos:
            os.remove(f"{carpeta}/{archivo}")
        logger.info(f"{carpeta} limpiada — {len(archivos)} archivos eliminados")

def reintentar_dead_letter():
    import json
    from datetime import datetime, timedelta

    archivos = os.listdir("data/silver_dead_letter")

    if not archivos:
        logger.info("Dead Letter vacío — nada que reintentar")
        return

    logger.info(f"Revisando {len(archivos)} tickers en Dead Letter")
    saltados = 0
    reingresados = 0

    for archivo in archivos:
        ruta = f"data/silver_dead_letter/{archivo}"

        try:
            with open(ruta, "r") as f:
                metadata = json.load(f)
        except Exception:
            continue

        ticker = metadata.get("ticker", archivo.replace(".json", ""))
        motivos = metadata.get("motivos", [])
        ultimo_intento = metadata.get("ultimo_intento")
        motivo_str = " ".join(motivos).lower()

        if "sin datos" in motivo_str or "delisted" in motivo_str:
            saltados += 1
            continue

        if "historia" in motivo_str:
            if ultimo_intento:
                fecha = datetime.fromisoformat(ultimo_intento)
                if datetime.now() - fecha < timedelta(days=180):
                    saltados += 1
                    continue
            else:
                metadata["ultimo_intento"] = datetime.now().isoformat()
                with open(ruta, "w") as f:
                    json.dump(metadata, f)
                saltados += 1
                continue

        if ultimo_intento:
            fecha = datetime.fromisoformat(ultimo_intento)
            if datetime.now() - fecha < timedelta(days=7):
                saltados += 1
                continue

        ruta_bronze = f"data/bronze/{ticker}.parquet"
        if os.path.exists(ruta_bronze):
            import pandas as pd
            df = pd.read_parquet(ruta_bronze)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            años = (df.index[-1] - df.index[0]).days / 365
            if años >= 10:
                os.remove(ruta)
                logger.info(f"{ticker}: ahora cumple historia ✅ reingresado")
                reingresados += 1
                continue

        metadata["ultimo_intento"] = datetime.now().isoformat()
        with open(ruta, "w") as f:
            json.dump(metadata, f)
        saltados += 1

    logger.info(f"Dead Letter — saltados: {saltados} | reingresados: {reingresados}")

def correr_pipeline():
    inicio = datetime.now()
    logger.info("=" * 50)
    logger.info(f"🚀 PIPELINE INICIADO — {inicio.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 50)

    # Variables para el reporte
    stats = {
        "bronze_ok": 0,
        "bronze_fallidos": 0,
        "silver_ok": 0,
        "dead_letter": 0,
        "gold": 0,
        "gold_rechazados": 0,
        "seleccionados": [],
        "duracion": 0,
        "errores": "Ninguno"
    }

    try:
        # LIMPIEZA
        logger.info("LIMPIEZA: Preparando carpetas")
        limpiar_carpetas()

        # PASO 0 — Dead Letter
        logger.info("PASO 0: Reintentando Dead Letter")
        reintentar_dead_letter()

        # PASO 1 — Bronze
        logger.info("PASO 1: Extrayendo datos crudos → Bronze")
        resultado_bronze = extraer_tickers(TICKERS)
        if resultado_bronze:
            stats["bronze_ok"] = resultado_bronze.get("exitosos", 0)
            stats["bronze_fallidos"] = resultado_bronze.get("fallidos", 0)

        # PASO 2 — Silver
        logger.info("PASO 2: Validando datos → Silver")
        resultado_silver = validar_todos()
        if resultado_silver:
            stats["silver_ok"] = resultado_silver.get("ok", 0)
            stats["dead_letter"] = resultado_silver.get("dead_letter", 0)

        # PASO 3 — Gold
        logger.info("PASO 3: Aplicando filtros Gold")
        resultado_gold = transformar_todos()
        if resultado_gold:
            stats["gold"] = resultado_gold.get("aprobados", 0)
            stats["gold_rechazados"] = resultado_gold.get("rechazados", 0)

        # PASO 4 — Selector
        logger.info("PASO 4: Seleccionando tickers aleatorios")
        seleccionar()

        # Leer tickers seleccionados hoy
        stats["seleccionados"] = [
            f.replace(".csv", "")
            for f in os.listdir("data/listos_para_hoy")
            if f.endswith(".csv")
        ]

        # Reporte final
        fin = datetime.now()
        stats["duracion"] = (fin - inicio).seconds
        logger.info("=" * 50)
        logger.info(f"✅ PIPELINE COMPLETO en {stats['duracion']} segundos")
        logger.info(f"📁 CSVs listos en data/listos_para_hoy")
        logger.info("=" * 50)

    except Exception as e:
        stats["errores"] = str(e)
        stats["duracion"] = (datetime.now() - inicio).seconds
        logger.error(f"❌ PIPELINE FALLÓ — {e}")

    finally:
        # Siempre envía el reporte — aunque el pipeline falle
        enviar_reporte(stats)


def correr_ahora():
    logger.info("Corriendo pipeline manualmente...")
    correr_pipeline()

def correr_diario():
    logger.info(f"Pipeline programado para correr todos los días a las {HORA_EJECUCION}")
    logger.info("Presiona Ctrl+C para detener")
    schedule.every().day.at(HORA_EJECUCION).do(correr_pipeline)
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "auto":
        correr_diario()
    else:
        correr_ahora()