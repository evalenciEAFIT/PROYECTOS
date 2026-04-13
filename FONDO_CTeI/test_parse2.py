import pandas as pd
import json

df = pd.read_excel('datos-FONDOSCTeI.xlsx', sheet_name='VISTAS_APLICATIVO', header=None)
data = df.values.tolist()

header1 = data[1]
header2 = data[2]

email_to_name = {str(r[0]).strip().lower(): str(r[1]).strip() for r in data[3:] if pd.notnull(r[0])}
name_to_email = {v.lower(): k for k, v in email_to_name.items()}

adj = {}

for col_idx in range(2, len(header1)):
    h1 = str(header1[col_idx]).strip() if pd.notnull(header1[col_idx]) else ""
    h2 = str(header2[col_idx]).strip() if pd.notnull(header2[col_idx]) else ""

    # h2 should have the exact account name (e.g. Adm)
    cabecera_name = h2 if h2 else h1
    cabecera_name = cabecera_name.strip()
    match_email = name_to_email.get(cabecera_name.lower())
    
    if not match_email:
        print(f"col: {col_idx} | h1: '{h1}' | h2: '{h2}' | cabecera_name: '{cabecera_name}' -> MISSING")
        continue

    deps = set()
    for row_idx in range(3, len(data)):
        val = data[row_idx][col_idx]
        email = str(data[row_idx][0]).strip().lower()
        if pd.notnull(val) and str(val).strip().upper() == 'X' and pd.notnull(data[row_idx][0]):
            deps.add(email)

    if match_email not in adj:
        adj[match_email] = set()
    adj[match_email].update(deps)

summary = {k: len(v) for k, v in adj.items()}
print("--- SUMMARY ---")
print(json.dumps(summary, indent=2))
