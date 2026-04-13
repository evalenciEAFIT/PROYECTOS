import pandas as pd
import json

df = pd.read_excel('datos-FONDOSCTeI.xlsx', sheet_name='VISTAS_APLICATIVO', header=None)
data = df.values.tolist()

print("RAW row 0 length:", len(data[0]))
print("RAW row 1 length:", len(data[1]))
print("RAW row 0 cols 2..6:", data[0][2:7])
print("RAW row 1 cols 2..6:", data[1][2:7])

header1 = data[0]
header2 = data[1]

email_to_name = {str(r[0]).strip().lower(): str(r[1]).strip() for r in data[2:] if pd.notnull(r[0])}
name_to_email = {v.lower(): k for k, v in email_to_name.items()}

adj = {}

for col_idx in range(2, len(header1)):
    h1 = str(header1[col_idx]).strip() if pd.notnull(header1[col_idx]) else ""
    h2 = str(header2[col_idx]).strip() if pd.notnull(header2[col_idx]) else ""
    
    cabecera_name = h2 if h2 and 'Unnamed' not in h2 else h1
    if 'Unnamed' in cabecera_name:
        cabecera_name = h2
        
    cabecera_name = cabecera_name.strip()
    match_email = name_to_email.get(cabecera_name.lower())
    
    if not match_email:
        print(f"col: {col_idx} | h1: '{h1}' | h2: '{h2}' | cabecera_name: '{cabecera_name}' -> MISSING")
        continue

