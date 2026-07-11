import os
import re
import pandas as pd
import numpy as np

def parse_time(time_str):
    try:
        match = re.match(r'(\d+):(\d+)\s*-\s*(\d+):(\d+)', str(time_str))
        if match:
            h1, m1, h2, m2 = map(int, match.groups())
            return h1 + m1 / 60.0
    except Exception:
        pass
    return None

def clean_and_process_dataset(excel_path):
    if not os.path.exists(excel_path):
        print(f"Error: Dataset no encontrado en {excel_path}")
        return None

    xl = pd.ExcelFile(excel_path)
    processed_records = []
    
    day_map = {
        'Lunes': 0,
        'Miercoles': 2,
        'Mier': 2,
        'Sabado': 5,
        'Sábado': 5,
        'Sbado': 5
    }

    vehicle_cols = {
        'AUTOS': [1, 2, 3],
        'PICK UP': [4, 5, 6],
        'BUS': [7, 8, 9],
        'SERVICIO DE TRANSP URBANO': [10, 11, 12],
        'CAMION LIGERO': [13, 14, 15],
        'CAMION MEDIANO': [16, 17, 18],
        'CAMION PESADO': [19, 20, 21],
        'ARTICULADOS': [22, 23, 24]
    }

    for sheet in xl.sheet_names:
        if 'FLUJOGRAMA' in sheet.upper():
            continue
            
        day_val = 1
        for key, val in day_map.items():
            if key.upper() in sheet.upper():
                day_val = val
                break
                
        print(f"Procesando hoja: {sheet} (Día de la semana: {day_val})")
        df = pd.read_excel(excel_path, sheet_name=sheet)
        
        header_idx = None
        for idx, row in df.iterrows():
            row_str = [str(x).strip().upper() for x in row.tolist()]
            if 'HORAS DE CONTROL' in row_str:
                header_idx = idx
                break
                
        if header_idx is None:
            print(f"No se encontró fila de cabecera 'HORAS DE CONTROL' en hoja {sheet}")
            continue
            
        for idx in range(header_idx + 5, len(df)):
            row = df.iloc[idx].tolist()
            time_val = str(row[0]).strip()
            if not time_val or time_val == 'nan' or '-' not in time_val:
                continue
                
            hour_float = parse_time(time_val)
            if hour_float is None:
                continue
                
            counts = {}
            for veh_name, indices in vehicle_cols.items():
                total_veh_count = 0
                for col_idx in indices:
                    if col_idx < len(row):
                        val = row[col_idx]
                        if not pd.isna(val) and isinstance(val, (int, float)):
                            total_veh_count += float(val)
                counts[veh_name] = total_veh_count
                
            total_flow = sum(counts.values())
            
            record = {
                'hour': hour_float,
                'day_of_week': day_val,
                'total_flow': total_flow,
                **counts
            }
            processed_records.append(record)
            
    df_clean = pd.DataFrame(processed_records)
    print(f"Dataset procesado correctamente: {len(df_clean)} registros.")
    return df_clean

if __name__ == '__main__':
    path = r'c:\Users\Jordan\Desktop\simulador\Simulador_trafico\dataset\conteo vehicuar (carros de salida) (1).xlsx'
    df = clean_and_process_dataset(path)
    if df is not None:
        print(df.describe())
        output_dir = r'c:\Users\Jordan\Desktop\simulador\Simulador_trafico\data'
        os.makedirs(output_dir, exist_ok=True)
        df.to_csv(os.path.join(output_dir, 'aforo_vehicular.csv'), index=False)
        print("Dataset limpio guardado en data/aforo_vehicular.csv")
