import pandas as pd
import json

try:
    # Try different headers if needed, lets try header=0
    df = pd.read_excel('datos-FONDOSCTeI.xlsx', sheet_name='Hoja1')
    
    # Just grab the columns and first 5 rows
    result = {
        'columns': df.columns.tolist(),
        'first_rows': df.head(5).to_dict('records')
    }
    
    with open('hoja1_output.json', 'w') as f:
        json.dump(result, f, indent=2, default=str)
        
    print("Success")
except Exception as e:
    with open('hoja1_output.json', 'w') as f:
        json.dump({"error": str(e)}, f)
    print("Error")
