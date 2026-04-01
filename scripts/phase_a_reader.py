import pandas as pd
import json
import logging
import sys
from config import (
    EXCEL_FILE_PATH, SHEET_MASTER, SHEET_ANALYSIS, SHEET_DATAFORSEO,
    REQUIRED_MASTER_COLUMNS, OUTPUTS_DIR, LOGS_DIR
)

# Set up logging
LOG_FILE = LOGS_DIR / "phase_a_reader.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

def main():
    logging.info("Iniciando Fase A: Lectura de contenido existente")
    
    # Validate Excel existence
    if not EXCEL_FILE_PATH.exists():
        logging.error(f"El archivo Excel no existe en: {EXCEL_FILE_PATH}")
        print("\nRESULTADO DE VALIDACIÓN: ERROR")
        sys.exit(1)
        
    try:
        # Open Excel File
        excel_file = pd.ExcelFile(EXCEL_FILE_PATH)
        sheets = excel_file.sheet_names
        logging.info(f"Hojas detectadas: {sheets}")
        
        # Validate required sheets
        required_sheets = [SHEET_MASTER, SHEET_ANALYSIS, SHEET_DATAFORSEO]
        missing_sheets = [s for s in required_sheets if s not in sheets]
        
        if missing_sheets:
            logging.error(f"Faltan hojas requeridas: {missing_sheets}")
            print("\nRESULTADO DE VALIDACIÓN: ERROR")
            sys.exit(1)
            
        logging.info("Validación de hojas OK.")
        
        # Read 03_MASTER
        logging.info(f"Leyendo la hoja {SHEET_MASTER} con pandas...")
        df_master = excel_file.parse(SHEET_MASTER)
        
        # Confirm row count
        num_rows = len(df_master)
        logging.info(f"Filas leídas en {SHEET_MASTER}: {num_rows}")
        
        # Detect columns
        columns_detected = list(df_master.columns)
        logging.info(f"Columnas detectadas en {SHEET_MASTER}: {columns_detected}")
        
        # Confirm required minimum columns
        missing_columns = [col for col in REQUIRED_MASTER_COLUMNS if col not in columns_detected]
        
        if missing_columns:
            logging.error(f"Columnas faltantes en {SHEET_MASTER}: {missing_columns}")
            print("\nRESULTADO DE VALIDACIÓN: ERROR")
            sys.exit(1)
            
        logging.info("Validación de columnas OK. No faltan columnas necesarias.")
        
        # Generate Outputs
        master_schema = {
            "sheet_name": SHEET_MASTER,
            "row_count": num_rows,
            "columns": columns_detected,
            "missing_required_columns": missing_columns
        }
        
        schema_path = OUTPUTS_DIR / "master_schema.json"
        with open(schema_path, "w", encoding="utf-8") as f:
            json.dump(master_schema, f, indent=4, ensure_ascii=False)
        logging.info(f"Schema (JSON) generado en {schema_path}")
            
        preview_path = OUTPUTS_DIR / "master_preview.csv"
        df_master.head(5).to_csv(preview_path, index=False, encoding="utf-8")
        logging.info(f"Preview (5 filas CSV) generado en {preview_path}")
        
        print("\nRESULTADO DE VALIDACIÓN: OK")
        
    except Exception as e:
        logging.error(f"Error inesperado procesando el Excel: {str(e)}")
        print("\nRESULTADO DE VALIDACIÓN: ERROR")
        sys.exit(1)

if __name__ == "__main__":
    main()
