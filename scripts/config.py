import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.parent
EXCEL_FILE_PATH = BASE_DIR / "templates" / "SEO_Master_Strategy.xlsx"
COMMERCE_CATALOG_PATH = BASE_DIR / "templates" / "Commerce_Catalog.xlsx"

OUTPUTS_DIR = BASE_DIR / "outputs"
LOGS_DIR = BASE_DIR / "logs"
BRIEFS_DIR = BASE_DIR / "examples" / "briefs"
DRAFTS_DIR = BASE_DIR / "examples" / "drafts"
HTML_DIR = BASE_DIR / "examples" / "html"

# Ensure directories exist
OUTPUTS_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
BRIEFS_DIR.mkdir(parents=True, exist_ok=True)
DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
HTML_DIR.mkdir(parents=True, exist_ok=True)

# Sheet names
SHEET_MASTER = "03_MASTER"
SHEET_ANALYSIS = "04_ANALIZAR"
SHEET_DATAFORSEO = "05_DATAFORSEO_RAW"

# Required columns in MASTER
REQUIRED_MASTER_COLUMNS = [
    "URL",
    "Title 1",
    "H1-1",
    "Keyword principal estimada",
    "Intención de búsqueda",
    "Cluster",
    "Subcluster",
    "Potencial comercial",
    "Marca/Categoría objetivo",
    "Riesgo de canibalización",
    "Acción recomendada",
    "Prioridad"
]

# Required columns in 05_DATAFORSEO_RAW
REQUIRED_DATAFORSEO_COLUMNS = [
    "seed_keyword",
    "cluster",
    "prioridad_cliente",
    "tipo_busqueda",
    "notas"
]

# Phase B output files
DATAFORSEO_RESULTS_CSV = OUTPUTS_DIR / "dataforseo_results.csv"
DATAFORSEO_RESULTS_JSON = OUTPUTS_DIR / "dataforseo_results.json"
