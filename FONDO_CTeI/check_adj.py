import pandas as pd
import numpy as np
import json

df = pd.read_excel('datos-FONDOSCTeI.xlsx', sheet_name='VISTAS_APLICATIVO')

# Let's get the first 3 rows to see the raw headers:
rows = df.head(5).replace({np.nan: None}).to_dict('records')
print(json.dumps(rows, indent=2, ensure_ascii=False))

