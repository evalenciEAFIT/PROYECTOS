import pandas as pd

try:
    df = pd.read_excel('/home/edi/PROYECTOS/FONDO_CTeI/datos-FONDOSCTeI.xlsx', sheet_name='Hoja1')
    print("Columns:", df.columns.tolist())
    print("\nHead 3:")
    print(df.head(3).to_dict('records'))
except Exception as e:
    print("Error:", e)
