import os
import sys
import json
import logging
import time
import requests
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

# Load .env before importing config (dotenv must populate env vars first)
_BASE_DIR = Path(__file__).parent.parent
load_dotenv(dotenv_path=_BASE_DIR / ".env")

from config import (
    EXCEL_FILE_PATH,
    SHEET_DATAFORSEO,
    REQUIRED_DATAFORSEO_COLUMNS,
    DATAFORSEO_RESULTS_CSV,
    DATAFORSEO_RESULTS_JSON,
    LOGS_DIR,
)

# ──────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────
LOG_FILE = LOGS_DIR / "phase_b_dataforseo.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)

# ──────────────────────────────────────────────
# DataForSEO endpoint decision:
# We use the "Keywords for Keywords" endpoint from the DataForSEO
# Keywords Data → Bing/Google Search Volume & Related Keywords API.
#
# Chosen endpoint: POST /v3/keywords_data/google/search_volume/live
#   - Input: list of keywords (seeds)
#   - Returns: search_volume, competition, cpc per keyword
#
# For keyword ideas we use: POST /v3/keywords_data/google/keywords_for_keywords/live
#   - Input: seed keyword
#   - Returns: semantically related keyword suggestions with volume/cpc
#
# Both endpoints use HTTP Basic Auth with your DataForSEO login/password.
# See: https://docs.dataforseo.com/v3/keywords_data/google/
# ──────────────────────────────────────────────

DATAFORSEO_BASE_URL = "https://api.dataforseo.com"
ENDPOINT_SEARCH_VOLUME = f"{DATAFORSEO_BASE_URL}/v3/keywords_data/google/search_volume/live"
ENDPOINT_KEYWORD_IDEAS = f"{DATAFORSEO_BASE_URL}/v3/keywords_data/google/keywords_for_keywords/live"

# Max keywords per search_volume request (API limit)
BATCH_SIZE = 100


def get_credentials():
    """Load and validate DataForSEO credentials from environment variables."""
    login = os.getenv("DATAFORSEO_LOGIN", "").strip()
    password = os.getenv("DATAFORSEO_PASSWORD", "").strip()
    location_name = os.getenv("DATAFORSEO_LOCATION_NAME", "Spain").strip()
    language_name = os.getenv("DATAFORSEO_LANGUAGE_NAME", "Spanish").strip()

    if not login or not password:
        logging.error(
            "Faltan credenciales de DataForSEO. "
            "Rellena DATAFORSEO_LOGIN y DATAFORSEO_PASSWORD en el archivo .env"
        )
        return None

    return {
        "login": login,
        "password": password,
        "location_name": location_name,
        "language_name": language_name,
    }


def read_seeds(excel_path: Path, sheet_name: str, required_cols: list) -> pd.DataFrame | None:
    """Read and validate the DataForSEO seed sheet."""
    try:
        df = pd.read_excel(excel_path, sheet_name=sheet_name, engine="openpyxl")
        logging.info(f"Hoja '{sheet_name}' leída: {len(df)} filas.")
    except Exception as e:
        logging.error(f"No se pudo leer la hoja '{sheet_name}': {e}")
        return None

    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        logging.error(f"Columnas faltantes en '{sheet_name}': {missing}")
        return None

    # Drop rows with empty seed_keyword
    df = df[df["seed_keyword"].notna() & (df["seed_keyword"].astype(str).str.strip() != "")]
    logging.info(f"Seeds válidas (no vacías): {len(df)}")
    return df


def request_search_volume(seeds: list[str], creds: dict) -> dict:
    """
    Batch-query DataForSEO for search volume, competition and CPC.

    Returns a dict: {keyword_lower: {"search_volume": int, "competition": float, "cpc": float}}
    """
    results = {}
    auth = (creds["login"], creds["password"])
    headers = {"Content-Type": "application/json"}

    for i in range(0, len(seeds), BATCH_SIZE):
        batch = seeds[i: i + BATCH_SIZE]
        payload = [
            {
                "keywords": batch,
                "location_name": creds["location_name"],
                "language_name": creds["language_name"],
            }
        ]

        try:
            resp = requests.post(
                ENDPOINT_SEARCH_VOLUME,
                auth=auth,
                headers=headers,
                json=payload,
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()

            if data.get("status_code") != 20000:
                logging.error(
                    f"Error DataForSEO en search_volume (batch {i // BATCH_SIZE + 1}): "
                    f"status_code={data.get('status_code')}, "
                    f"status_message={data.get('status_message')}"
                )
                continue

            tasks = data.get("tasks", [])
            for task in tasks:
                task_result = task.get("result", []) or []
                for item in task_result:
                    kw = (item.get("keyword") or "").lower()
                    results[kw] = {
                        "search_volume": item.get("search_volume"),
                        "competition": item.get("competition"),
                        "cpc": item.get("cpc"),
                    }

        except requests.exceptions.RequestException as e:
            logging.error(f"Error HTTP en search_volume (batch {i // BATCH_SIZE + 1}): {e}")

        # Respectful delay between batches
        if i + BATCH_SIZE < len(seeds):
            time.sleep(1)

    return results


def request_keyword_ideas(seed: str, creds: dict) -> list[dict]:
    """
    Query DataForSEO for keyword ideas related to a single seed.

    Returns a list of dicts: [{keyword, search_volume, competition, cpc}]
    """
    auth = (creds["login"], creds["password"])
    headers = {"Content-Type": "application/json"}
    payload = [
        {
            "keywords": [seed],
            "location_name": creds["location_name"],
            "language_name": creds["language_name"],
        }
    ]

    try:
        resp = requests.post(
            ENDPOINT_KEYWORD_IDEAS,
            auth=auth,
            headers=headers,
            json=payload,
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()

        if data.get("status_code") != 20000:
            logging.error(
                f"Error DataForSEO en keyword_ideas para '{seed}': "
                f"status_code={data.get('status_code')}, "
                f"status_message={data.get('status_message')}"
            )
            return []

        ideas = []
        for task in data.get("tasks", []):
            for item in (task.get("result") or []):
                kw = item.get("keyword", "")
                if kw:
                    ideas.append(
                        {
                            "keyword": kw,
                            "search_volume": item.get("search_volume"),
                            "competition": item.get("competition"),
                            "cpc": item.get("cpc"),
                        }
                    )
        return ideas

    except requests.exceptions.RequestException as e:
        logging.error(f"Error HTTP en keyword_ideas para '{seed}': {e}")
        return []


def build_results(df_seeds: pd.DataFrame, volume_map: dict, ideas_map: dict) -> list[dict]:
    """Normalise all data into the canonical output row format."""
    rows = []

    for _, seed_row in df_seeds.iterrows():
        seed_kw = str(seed_row["seed_keyword"]).strip()
        cluster = seed_row.get("cluster", "")
        prioridad = seed_row.get("prioridad_cliente", "")

        # Row for the seed keyword itself (from search_volume endpoint)
        seed_data = volume_map.get(seed_kw.lower(), {})
        rows.append(
            {
                "seed_keyword": seed_kw,
                "cluster": cluster,
                "prioridad_cliente": prioridad,
                "keyword": seed_kw,
                "search_volume": seed_data.get("search_volume"),
                "competition": seed_data.get("competition"),
                "cpc": seed_data.get("cpc"),
                "location_name": os.getenv("DATAFORSEO_LOCATION_NAME", "Spain"),
                "language_name": os.getenv("DATAFORSEO_LANGUAGE_NAME", "Spanish"),
                "source": "search_volume",
            }
        )

        # Rows for related keyword ideas
        for idea in ideas_map.get(seed_kw, []):
            rows.append(
                {
                    "seed_keyword": seed_kw,
                    "cluster": cluster,
                    "prioridad_cliente": prioridad,
                    "keyword": idea.get("keyword"),
                    "search_volume": idea.get("search_volume"),
                    "competition": idea.get("competition"),
                    "cpc": idea.get("cpc"),
                    "location_name": os.getenv("DATAFORSEO_LOCATION_NAME", "Spain"),
                    "language_name": os.getenv("DATAFORSEO_LANGUAGE_NAME", "Spanish"),
                    "source": "keyword_ideas",
                }
            )

    return rows


def save_results(rows: list[dict]):
    """Persist results to CSV and JSON."""
    df_out = pd.DataFrame(rows)
    df_out.to_csv(DATAFORSEO_RESULTS_CSV, index=False, encoding="utf-8")
    logging.info(f"CSV guardado en: {DATAFORSEO_RESULTS_CSV}")

    with open(DATAFORSEO_RESULTS_JSON, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=4, ensure_ascii=False)
    logging.info(f"JSON guardado en: {DATAFORSEO_RESULTS_JSON}")


def main():
    logging.info("Iniciando Fase B: Conexión con DataForSEO")
    total_requests = 0

    # 1. Credentials
    creds = get_credentials()
    if creds is None:
        print("\nRESULTADO DE VALIDACIÓN: ERROR — credenciales no configuradas.")
        sys.exit(1)

    # 2. Read seeds
    df_seeds = read_seeds(EXCEL_FILE_PATH, SHEET_DATAFORSEO, REQUIRED_DATAFORSEO_COLUMNS)
    if df_seeds is None:
        print("\nRESULTADO DE VALIDACIÓN: ERROR — no se pudo leer el archivo de seeds.")
        sys.exit(1)

    seed_list = df_seeds["seed_keyword"].astype(str).str.strip().tolist()
    logging.info(f"Seeds a procesar: {len(seed_list)}")
    print(f"\nSeeds leídas: {len(seed_list)}")

    # 3. Batch search_volume
    logging.info("Consultando volúmenes de búsqueda (search_volume/live)...")
    volume_map = request_search_volume(seed_list, creds)
    total_requests += (len(seed_list) // BATCH_SIZE) + (1 if len(seed_list) % BATCH_SIZE else 0)
    logging.info(f"Volúmenes obtenidos: {len(volume_map)} keywords")

    # 4. Per-seed keyword ideas
    logging.info("Consultando keyword ideas (keywords_for_keywords/live) por seed...")
    ideas_map = {}
    for seed in seed_list:
        ideas = request_keyword_ideas(seed, creds)
        ideas_map[seed] = ideas
        total_requests += 1
        logging.info(f"  '{seed}': {len(ideas)} ideas recibidas")
        time.sleep(0.5)  # Respectful rate limit

    # 5. Build normalised rows
    rows = build_results(df_seeds, volume_map, ideas_map)
    total_keywords = len(rows)
    print(f"Keywords obtenidas (seed + ideas): {total_keywords}")
    print(f"Peticiones realizadas: {total_requests}")

    if not rows:
        logging.warning("No se obtuvieron resultados. Verifica credenciales y seeds.")
        print("\nRESULTADO DE VALIDACIÓN: ERROR — sin resultados.")
        sys.exit(1)

    # 6. Save
    save_results(rows)

    logging.info("Fase B completada correctamente.")
    print("\nRESULTADO DE VALIDACIÓN: OK")


if __name__ == "__main__":
    main()
