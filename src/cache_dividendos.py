import json
import os
from datetime import datetime, timedelta
from loguru import logger

CACHE_PATH = "cache_dividendos.json"
DIAS_VALIDEZ = 7  # refrescar cada 7 días

def cargar_cache():
    """Lee el caché del disco"""
    if not os.path.exists(CACHE_PATH):
        return {}
    try:
        with open(CACHE_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def guardar_cache(cache):
    """Guarda el caché en disco"""
    with open(CACHE_PATH, "w") as f:
        json.dump(cache, f, indent=2)

def cache_vigente(entrada):
    """Verifica si el dato en caché tiene menos de 7 días"""
    try:
        fecha = datetime.fromisoformat(entrada["fecha"])
        return datetime.now() - fecha < timedelta(days=DIAS_VALIDEZ)
    except Exception:
        return False

def obtener_dividendo(ticker, info_yahoo):
    """
    Retorna el dividendo de un ticker.
    Primero busca en caché, si no existe o expiró pregunta a Yahoo.
    """
    cache = cargar_cache()

    # ¿Está en caché y vigente?
    if ticker in cache and cache_vigente(cache[ticker]):
        return cache[ticker]["dividendo"]

    # Si no — leer de Yahoo y guardar en caché
    try:
        dividendo = info_yahoo.get("dividendYield", 0) or 0
        if dividendo > 1:
            dividendo = dividendo / 100

        cache[ticker] = {
            "dividendo": dividendo,
            "fecha": datetime.now().isoformat()
        }
        guardar_cache(cache)
        return dividendo

    except Exception as e:
        logger.warning(f"{ticker}: error obteniendo dividendo — {e}")
        return 0

def stats_cache():
    """Muestra estadísticas del caché"""
    cache = cargar_cache()
    vigentes = sum(1 for v in cache.values() if cache_vigente(v))
    expirados = len(cache) - vigentes
    logger.info(f"Caché dividendos: {len(cache)} tickers | {vigentes} vigentes | {expirados} expirados")

if __name__ == "__main__":
    stats_cache()