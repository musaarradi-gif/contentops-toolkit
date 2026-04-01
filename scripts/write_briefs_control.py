import pandas as pd
from config import EXCEL_FILE_PATH

def main():
    """Example script to update brief control status in the master spreadsheet."""
    editorial_file = EXCEL_FILE_PATH
    output_sheet = "09_BRIEFS_CONTROL"
    
    # Mock data for demonstration
    demo_data = [
        {
            "keyword_principal": "beneficios cepillo dientes bambu",
            "titulo_sugerido": "Por qué cambiar a un cepillo de dientes de bambú este año",
            "archivo_brief": "examples/briefs/cepillos_dientes_bambu.md",
            "estado": "Generado",
            "notas": "Foco en sostenibilidad y zero waste"
        }
    ]
    
    df_out = pd.DataFrame(demo_data)
    
    try:
        with pd.ExcelWriter(editorial_file, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            df_out.to_excel(writer, sheet_name=output_sheet, index=False)
        print(f"Status updated in {output_sheet}")
    except Exception as e:
        print(f"Error updating status: {e}")

if __name__ == "__main__":
    main()
