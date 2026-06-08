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

def obtener_info_ticker(ticker, info_yahoo):
    """
    Retorna toda la info relevante de un ticker.
    Primera vez consulta Yahoo y guarda todo en caché.
    Siguientes veces lee del caché sin llamar a Yahoo.
    """
    cache = cargar_cache()

    # ¿Está en caché y vigente?
    if ticker in cache and cache_vigente(cache[ticker]):
        entrada = cache[ticker]
        return {
            "dividendo": entrada.get("dividendo", 0),
            "sector": entrada.get("sector", ""),
            "industria": entrada.get("industria", ""),
            "precio": entrada.get("precio", 0)
        }

    # Si no — leer de Yahoo y guardar TODO en caché
    try:
        dividendo = info_yahoo.get("dividendYield", 0) or 0
        if dividendo > 1:
            dividendo = dividendo / 100

        sector = info_yahoo.get("sector", "") or ""
        industria = info_yahoo.get("industry", "") or ""
        precio = info_yahoo.get("currentPrice", 0) or \
                 info_yahoo.get("regularMarketPrice", 0) or 0

        cache[ticker] = {
            "dividendo": dividendo,
            "sector": sector,
            "industria": industria,
            "precio": precio,
            "fecha": datetime.now().isoformat()
        }
        guardar_cache(cache)

        return {
            "dividendo": dividendo,
            "sector": sector,
            "industria": industria,
            "precio": precio
        }

    except Exception as e:
        logger.warning(f"{ticker}: error obteniendo info — {e}")
        return {"dividendo": 0, "sector": "", "industria": "", "precio": 0}

def stats_cache():
    """Muestra estadísticas del caché"""
    cache = cargar_cache()
    vigentes = sum(1 for v in cache.values() if cache_vigente(v))
    expirados = len(cache) - vigentes
    logger.info(f"Caché: {len(cache)} tickers | {vigentes} vigentes | {expirados} expirados")

if __name__ == "__main__":
    stats_cache()