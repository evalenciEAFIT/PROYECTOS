import pandas as pd
import json

try:
    df = pd.read_excel('datos-FONDOSCTeI.xlsx', sheet_name='VISTAS_APLICATIVO', header=1)
    
    result = {
        'columns': df.columns.tolist(),
        'first_rows': df.head(5).to_dict('records')
    }
    
    with open('vistas_output.json', 'w') as f:
        json.dump(result, f, indent=2, default=str)
        
    print("Success")
except Exception as e:
    print("Error:", e)
