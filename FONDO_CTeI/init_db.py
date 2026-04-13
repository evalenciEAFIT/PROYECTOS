import pandas as pd
import sqlite3
import random


def initialize_database():
    excel_file = 'datos-FONDOSCTeI.xlsx'

    # Lee la hoja sin header para tener control total de filas
    df_raw = pd.read_excel(excel_file, sheet_name='VISTAS_APLICATIVO', header=None)
    data = df_raw.values.tolist()

    # Estructura del Excel (índices de fila, base 0):
    # Fila 0: header → [Tipo, Cuentas@eafit, Nombre de la cuenta, Root, VR_CteI, Adm, AyH, ...]
    # Fila 1+: datos de cada cuenta
    #   col 0 = Tipo, col 1 = email, col 2 = nombre cuenta, col 3+ = X de jerarquía

    # Construir lista de cuentas desde fila 1+
    accounts_list = []
    for r in data[1:]:
        if pd.notnull(r[1]) and str(r[1]).strip():
            accounts_list.append({
                'Tipo': str(r[0]).strip() if pd.notnull(r[0]) else '',
                'Cuentas@eafit': str(r[1]).strip(),
                'Nombre de la cuenta': str(r[2]).strip() if pd.notnull(r[2]) else ''
            })

    accounts_df = pd.DataFrame(accounts_list)
    accounts_df['cuenta_eafit_lower'] = accounts_df['Cuentas@eafit'].str.lower().str.strip()

    # Leer Hoja1 (info descriptiva del docente/investigador)
    try:
        df_hoja1 = pd.read_excel(excel_file, sheet_name='Hoja1')
        df_hoja1 = df_hoja1[['DOCUMENTO', 'NOMBRES Y APELLIDOS', 'EMAIL', 'ÁREA', 'ESCUELA',
                               'GRUPO DE INVESTIGACIÓN AL QUE PERTENECE']]
        df_hoja1['EMAIL_lower'] = df_hoja1['EMAIL'].str.lower().str.strip()
        merged_df = pd.merge(accounts_df, df_hoja1,
                             left_on='cuenta_eafit_lower', right_on='EMAIL_lower', how='left')
    except Exception as e:
        print("Aviso: No se pudo leer Hoja1:", e)
        merged_df = accounts_df.copy()
        for col in ['DOCUMENTO', 'NOMBRES Y APELLIDOS', 'ÁREA', 'ESCUELA',
                    'GRUPO DE INVESTIGACIÓN AL QUE PERTENECE']:
            merged_df[col] = None

    conn = sqlite3.connect('banco.db')
    cursor = conn.cursor()

    # Limpiar y recrear tablas
    cursor.execute('DROP TABLE IF EXISTS transaccion')
    cursor.execute('DROP TABLE IF EXISTS jerarquia')
    cursor.execute('DROP TABLE IF EXISTS cuenta')

    cursor.execute('''
        CREATE TABLE cuenta (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cuenta_eafit TEXT NOT NULL,
            nombre_cuenta TEXT NOT NULL,
            tipo TEXT,
            saldo REAL DEFAULT 0.0,
            ingresos REAL DEFAULT 0.0,
            egresos REAL DEFAULT 0.0,
            documento TEXT,
            nombre_docente TEXT,
            area TEXT,
            escuela TEXT,
            grupo_investigacion TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE transaccion (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cuenta_id INTEGER,
            tipo TEXT NOT NULL,
            categoria TEXT NOT NULL,
            monto REAL NOT NULL,
            fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(cuenta_id) REFERENCES cuenta(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE jerarquia (
            cabecera_id INTEGER,
            dependiente_id INTEGER,
            FOREIGN KEY(cabecera_id) REFERENCES cuenta(id),
            FOREIGN KEY(dependiente_id) REFERENCES cuenta(id),
            PRIMARY KEY (cabecera_id, dependiente_id)
        )
    ''')

    categorias_ingreso = [
        "Transferencia Fondo CTeI",
        "Reconocimiento en Investigación",
        "Donación",
        "Transferencia desde la Comunidad Académica",
        "Otro"
    ]
    categorias_egreso = [
        "Insumo o Materiales",
        "Infraestructura o Equipos",
        "Eventos académicos",
        "Servicios",
        "Transferencia a la Comunidad Académica",
        "Otros"
    ]

    # Insertar cuentas y generar transacciones de prueba
    email_to_id = {}
    for _, row in merged_df.iterrows():
        cuenta_eafit  = row.get('Cuentas@eafit', '')
        nombre_cuenta = row.get('Nombre de la cuenta', '')
        tipo_cuenta   = str(row.get('Tipo', '')) if pd.notnull(row.get('Tipo')) else ''
        documento     = str(row.get('DOCUMENTO', '')) if pd.notnull(row.get('DOCUMENTO')) else ''
        nombre_doc    = str(row.get('NOMBRES Y APELLIDOS', '')) if pd.notnull(row.get('NOMBRES Y APELLIDOS')) else ''
        area          = str(row.get('ÁREA', '')) if pd.notnull(row.get('ÁREA')) else ''
        escuela       = str(row.get('ESCUELA', '')) if pd.notnull(row.get('ESCUELA')) else ''
        grupo         = str(row.get('GRUPO DE INVESTIGACIÓN AL QUE PERTENECE', '')) \
                        if pd.notnull(row.get('GRUPO DE INVESTIGACIÓN AL QUE PERTENECE')) else ''

        cursor.execute('''
            INSERT INTO cuenta (cuenta_eafit, nombre_cuenta, tipo, saldo, ingresos, egresos,
                                documento, nombre_docente, area, escuela, grupo_investigacion)
            VALUES (?, ?, ?, 0, 0, 0, ?, ?, ?, ?, ?)
        ''', (cuenta_eafit, nombre_cuenta, tipo_cuenta, documento, nombre_doc, area, escuela, grupo))

        cuenta_id = cursor.lastrowid
        email_to_id[cuenta_eafit.lower().strip()] = cuenta_id

        # Transacciones aleatorias de prueba
        num_ingresos = random.randint(1, 3)
        total_ingresos = 0
        for _ in range(num_ingresos):
            cat = random.choice(categorias_ingreso)
            monto = round(random.uniform(500, 20000), 2)
            total_ingresos += monto
            cursor.execute('INSERT INTO transaccion (cuenta_id, tipo, categoria, monto) VALUES (?, ?, ?, ?)',
                           (cuenta_id, 'ingreso', cat, monto))

        num_egresos = random.randint(0, 2)
        total_egresos = 0
        for _ in range(num_egresos):
            cat = random.choice(categorias_egreso)
            monto = round(random.uniform(100, (total_ingresos / 2) + 100), 2)
            total_egresos += monto
            cursor.execute('INSERT INTO transaccion (cuenta_id, tipo, categoria, monto) VALUES (?, ?, ?, ?)',
                           (cuenta_id, 'egreso', cat, monto))

        saldo = round(total_ingresos - total_egresos, 2)
        cursor.execute('UPDATE cuenta SET ingresos=?, egresos=?, saldo=? WHERE id=?',
                       (round(total_ingresos, 2), round(total_egresos, 2), saldo, cuenta_id))

    # ---------------------------------------------------------------
    # Parsear jerarquías
    # Fila 0 tiene los nombres de cabeceras en cols 3+
    # Ej: Root, VR_CteI, Adm, AyH, CAeI, Der, FEG, ...
    # Fila 1+ tiene las X para cada dependiente
    # ---------------------------------------------------------------

    # Mapa: nombre corto (minúsculas) → email de la cuenta
    name_to_email = {}
    for r in data[1:]:
        if pd.notnull(r[1]) and pd.notnull(r[2]):
            short_name = str(r[2]).strip().lower()
            email = str(r[1]).strip().lower()
            name_to_email[short_name] = email

    cabecera_row = data[0]  # fila 0 = header con nombres de cabeceras

    inserted = 0
    for col_idx in range(3, len(cabecera_row)):
        cell = cabecera_row[col_idx]
        if not pd.notnull(cell) or not str(cell).strip():
            continue

        cabecera_short = str(cell).strip().lower()
        match_email = name_to_email.get(cabecera_short)

        if not match_email or match_email not in email_to_id:
            continue

        cabecera_id = email_to_id[match_email]

        # Buscar dependientes: filas 1+ con X en esta columna
        for row_idx in range(1, len(data)):
            val = data[row_idx][col_idx] if col_idx < len(data[row_idx]) else None
            email_dep = str(data[row_idx][1]).strip().lower() if pd.notnull(data[row_idx][1]) else ''
            if pd.notnull(val) and str(val).strip().upper() == 'X' and email_dep in email_to_id:
                dependiente_id = email_to_id[email_dep]
                try:
                    cursor.execute(
                        'INSERT OR IGNORE INTO jerarquia (cabecera_id, dependiente_id) VALUES (?, ?)',
                        (cabecera_id, dependiente_id)
                    )
                    inserted += 1
                except sqlite3.IntegrityError:
                    pass

    conn.commit()
    conn.close()
    print(f"✓ Cuentas cargadas: {len(email_to_id)}")
    print(f"✓ Relaciones jerárquicas insertadas: {inserted}")


if __name__ == "__main__":
    initialize_database()
