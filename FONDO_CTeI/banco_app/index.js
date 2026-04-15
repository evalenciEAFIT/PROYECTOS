const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');
const cors = require('cors');
const fs = require('fs');
require('dotenv').config();
const ldap = require('ldapjs');

const categoriasPath = path.resolve(__dirname, 'categorias.json');
if (!fs.existsSync(categoriasPath)) {
    fs.writeFileSync(categoriasPath, JSON.stringify({
        ingresos: [
            "Transferencia Fondo CTeI",
            "Reconocimiento en Investigación",
            "Donación",
            "Transferencia desde la Comunidad Académica",
            "Otro"
        ],
        transferencias: [
            "Transferencia Fondo CTeI",
            "Reconocimiento propiedad intelectual",
            "Incentivos",
            "Convenios",
            "Otro"
        ],
        egresos: [
            "Insumo o Materiales",
            "Infraestructura o Equipos",
            "Eventos académicos",
            "Servicios",
            "Transferencia a la Comunidad Académica",
            "Otros",
            "Reactivos"
        ]
    }, null, 2));
}

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());

// Logger de Auditoría de Operaciones
app.use((req, res, next) => {
    if (['POST', 'PUT', 'DELETE'].includes(req.method)) {
        const timestamp = new Date().toLocaleString('es-CO');
        const b = { ...req.body };
        if (b.password) b.password = '********';
        if (b.token) b.token = '********';
        if (b.clave) b.clave = '********';
        const user = req.headers['x-user'] || 'Usuario Desconocido';
        const logContent = `[${timestamp}] [USER: ${user}] ${req.method} ${req.originalUrl} | DATA: ${JSON.stringify(b)}\n`;
        require('fs').appendFile(path.join(__dirname, 'operaciones.log'), logContent, (err) => {
            if (err) console.error('Error escribiendo log:', err);
        });
    }
    next();
});
app.use(express.static(path.join(__dirname, 'public')));
app.use('/views', express.static(path.join(__dirname, 'views')));

// Database connection
const dbPath = path.resolve(__dirname, 'banco.db');
const db = new sqlite3.Database(dbPath, (err) => {
    if (err) {
        console.error('Error connecting to database:', err.message);
    } else {
        console.log('Connected to the SQLite database at', dbPath);
        db.run('ALTER TABLE transaccion ADD COLUMN fecha_aceptado DATETIME', (err) => {
             // Silently ignore if column exists
        });
        db.run('ALTER TABLE transaccion ADD COLUMN justificacion TEXT', (err) => {
             // Silently ignore if column exists
        });
        db.run('ALTER TABLE transaccion ADD COLUMN historial_estados TEXT', (err) => {
             // Silently ignore if column exists
        });
        db.run('ALTER TABLE cuenta ADD COLUMN centro_costo TEXT', (err) => {
             // Silently ignore if column exists
        });
    }
});

// --- API Routes ---
app.get('/api/logs', (req, res) => {
    const logPath = path.resolve(__dirname, 'operaciones.log');
    if (!fs.existsSync(logPath)) {
        return res.status(404).send('No hay operaciones registradas en el sistema aún.');
    }
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    res.download(logPath, `Auditoria_FONDO_CTeI_${timestamp}.log`);
});

app.get('/api/backup-db', (req, res) => {
    const backupPath = path.resolve(__dirname, 'banco.db');
    if (!fs.existsSync(backupPath)) {
        return res.status(404).send('Base de datos no encontrada.');
    }
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    res.download(backupPath, `banco_backup_${timestamp}.db`);
});

// Disable caching for API routes to fix the "requires refresh" issue
app.use('/api', (req, res, next) => {
    res.set('Cache-Control', 'no-store, no-cache, must-revalidate, private');
    res.set('Pragma', 'no-cache');
    res.set('Expires', '0');
    next();
});

// --- SSE Real-time Updates ---
let sseClients = [];
app.get('/api/stream', (req, res) => {
    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');
    res.flushHeaders();
    sseClients.push(res);
    req.on('close', () => { sseClients = sseClients.filter(c => c !== res); });
});
function notifyClients() { sseClients.forEach(c => c.write(`data: update\n\n`)); }

// Categories
app.get('/api/categorias', (req, res) => {
    fs.readFile(categoriasPath, 'utf8', (err, data) => {
        if (err) return res.status(500).json({ error: 'Error reading categories' });
        res.json({ message: 'success', data: JSON.parse(data) });
    });
});

app.put('/api/categorias', (req, res) => {
    const { ingresos, egresos, transferencias } = req.body;
    const newData = { ingresos: ingresos || [], egresos: egresos || [], transferencias: transferencias || [] };
    fs.writeFile(categoriasPath, JSON.stringify(newData, null, 2), (err) => {
        if (err) return res.status(500).json({ error: 'Error saving categories' });
        notifyClients();
        res.json({ message: 'success', data: newData });
    });
});

// Login
app.post('/api/login', (req, res) => {
    const { email, password } = req.body;

    // Custom Admin login wrapper
    if (email === 'admin' && password === '123') {
        return res.json({ message: 'success', data: { id: null, nombre_cuenta: 'Administrador General', cuenta_eafit: 'admin' } });
    }

    // Si la validacion LDAP está activada vía variables de entorno
    if (process.env.USE_ACTIVE_DIRECTORY === 'true') {
        const adUrl = process.env.LDAP_URL || 'ldap://ad.eafit.edu.co:389';
        const client = ldap.createClient({ url: adUrl });

        // Intentamos autenticar con el Active Directory
        // Importante: El UPN (User Principal Name) o correo es usualmente el primer argumento
        client.bind(email, password, (err) => {
            if (err) {
                client.unbind();
                return res.status(401).json({ error: 'Contraseña incorrecta o usuario no válido (Validado con Active Directory de EAFIT).' });
            }

            client.unbind();
            
            // Si la clave en EAFIT es válida, comprobamos si tienen cuenta en nuestra DB
            db.get('SELECT * FROM cuenta WHERE cuenta_eafit = ?', [email], (dbErr, row) => {
                if (dbErr || !row) {
                    return res.status(404).json({ error: 'Tu contraseña de EAFIT es correcta, pero tu cuenta no está registrada aún en esta plataforma.' });
                }
                res.json({ message: 'success', data: row });
            });
        });
    } else {
        // Fallback local/desarrollo: valida solo con "123" (modo actual/antiguo)
        if (password !== '123') {
            return res.status(401).json({ error: 'Contraseña incorrecta. (Modo Local: Tip: es 123)' });
        }

        db.get('SELECT * FROM cuenta WHERE cuenta_eafit = ?', [email], (err, row) => {
            if (err || !row) {
                return res.status(404).json({ error: 'Cuenta no encontrada. Verifica tu correo @eafit.' });
            }
            res.json({ message: 'success', data: row });
        });
    }
});

// Endpoint silencioso para registrar formalmente el cierre de sesión en Auditoría
app.post('/api/logout', (req, res) => {
    res.json({ message: 'Sesion cerrada' });
});

// Azure SSO Login (Solo verifica existencia de cuenta ya que Azure valida identidad)
app.post('/api/azure-login', (req, res) => {
    const { email } = req.body;
    
    if (email === 'admin') {
        return res.json({ message: 'success', data: { id: null, nombre_cuenta: 'Administrador General', cuenta_eafit: 'admin' } });
    }

    db.get('SELECT * FROM cuenta WHERE cuenta_eafit = ?', [email], (err, row) => {
        if (err || !row) {
            return res.status(404).json({ error: `La cuenta de Azure verificada (${email}) no está sincronizada/registrada aún en esta plataforma CTeI.` });
        }
        res.json({ message: 'success', data: row });
    });
});

// Get all accounts (or filter by one)
app.get('/api/cuentas', (req, res) => {
    const cuentaId = req.query.cuenta_id;
    let sql = 'SELECT * FROM cuenta';
    let params = [];
    if (cuentaId && cuentaId !== 'null') {
        sql += ' WHERE id = ? OR id IN (SELECT dependiente_id FROM jerarquia WHERE cabecera_id = ?)';
        params.push(cuentaId, cuentaId);
    }
    db.all(sql, params, (err, rows) => {
        if (err) {
            return res.status(500).json({ error: err.message });
        }

        // Also fetch the hierarchy so the frontend knows the relations
        db.all('SELECT cabecera_id, dependiente_id FROM jerarquia', [], (err2, jRows) => {
            if (err2) return res.status(500).json({ error: err2.message });

            const hierarchy = {};
            jRows.forEach(j => {
                if (!hierarchy[j.cabecera_id]) hierarchy[j.cabecera_id] = [];
                hierarchy[j.cabecera_id].push(j.dependiente_id);
            });

            res.json({
                message: 'success',
                data: rows,
                hierarchy: hierarchy
            });
        });
    });
});

// Get summary for dashboard
app.get('/api/resumen', (req, res) => {
    const cuentaId = req.query.cuenta_id;
    let sumSql = 'SELECT SUM(saldo) as totalSaldo, SUM(ingresos) as allIngresos, SUM(egresos) as allEgresos FROM cuenta';
    let sumParams = [];
    if (cuentaId && cuentaId !== 'null') {
        sumSql += ' WHERE id = ?';
        sumParams.push(cuentaId);
    }

    db.get(sumSql, sumParams, (err, saldoRow) => {
        if (err) return res.status(500).json({ error: err.message });

        let txSql = 'SELECT tipo, categoria, SUM(monto) as total FROM transaccion';
        let txParams = [];
        if (cuentaId && cuentaId !== 'null') {
            txSql += ' WHERE cuenta_id = ?';
            txParams.push(cuentaId);
        }
        txSql += ' GROUP BY tipo, categoria';

        db.all(txSql, txParams, (err, rows) => {
            if (err) {
                return res.status(500).json({ error: err.message });
            }
            res.json({
                message: 'success',
                data: {
                    saldo: saldoRow.totalSaldo || 0,
                    ingresos: saldoRow.allIngresos || 0,
                    egresos: saldoRow.allEgresos || 0,
                    breakdown: rows
                }
            });
        });
    });
});

// Register a new transaction
app.post('/api/cuentas/:id/transaccion', (req, res) => {
    const cuenta_id = req.params.id;
    const { tipo, categoria, monto, fecha, justificacion } = req.body;

    if (!tipo || !categoria || !monto) {
        return res.status(400).json({ error: 'Faltan datos de la transacción' });
    }

    db.serialize(() => {
        db.run('BEGIN TRANSACTION');

        const isEgreso = tipo === 'egreso';
        const isTransfer = isEgreso && categoria === 'Transferencia a la Comunidad Académica';
        // Egresos that are NOT transfers go to 'solicitada'
        const estado = (isEgreso && !isTransfer) ? 'solicitada' : 'aprobada';

        const stmt = fecha 
            ? `INSERT INTO transaccion (cuenta_id, tipo, categoria, monto, fecha, estado, justificacion) VALUES (?, ?, ?, ?, ?, ?, ?)`
            : `INSERT INTO transaccion (cuenta_id, tipo, categoria, monto, estado, justificacion) VALUES (?, ?, ?, ?, ?, ?)`;
        const params = fecha
            ? [cuenta_id, tipo, categoria, monto, fecha, estado, justificacion || null]
            : [cuenta_id, tipo, categoria, monto, estado, justificacion || null];

        db.run(stmt, params, function (err) {
            if (err) {
                db.run('ROLLBACK');
                return res.status(500).json({ error: err.message });
            }
            const tx_id = this.lastID;

            db.get('SELECT * FROM cuenta WHERE id = ?', [cuenta_id], (err, row) => {
                if (err || !row) {
                    db.run('ROLLBACK');
                    return res.status(500).json({ error: err ? err.message : 'Cuenta no encontrada' });
                }

                let newIngresos = row.ingresos;
                let newEgresos = row.egresos;

                if (tipo === 'ingreso') {
                    newIngresos += parseFloat(monto);
                } else if (tipo === 'egreso') {
                    newEgresos += parseFloat(monto);
                }

                let newSaldo = newIngresos - newEgresos;

                const updateSql = `UPDATE cuenta SET ingresos = ?, egresos = ?, saldo = ? WHERE id = ?`;
                db.run(updateSql, [newIngresos, newEgresos, newSaldo, cuenta_id], function (err) {
                    if (err) {
                        db.run('ROLLBACK');
                        return res.status(500).json({ error: err.message });
                    }
                    db.run('COMMIT');
                    notifyClients();
                    res.json({
                        message: 'success',
                        data: { id: cuenta_id, saldo: newSaldo, ingresos: newIngresos, egresos: newEgresos },
                        transaccion_id: tx_id
                    });
                });
            });
        });
    });
});

// Get transactions for a specific account
app.get('/api/cuentas/:id/transacciones', (req, res) => {
    const cuenta_id = req.params.id;
    const sql = `
        SELECT t.*, 
        (SELECT c2.nombre_cuenta FROM transaccion t2 JOIN cuenta c2 ON c2.id = t2.cuenta_id WHERE t2.categoria = t.categoria AND t2.tipo != t.tipo AND t2.fecha = t.fecha AND t2.monto = t.monto AND t2.id != t.id LIMIT 1) as cuenta_vinculada
        FROM transaccion t WHERE t.cuenta_id = ? ORDER BY t.fecha DESC
    `;
    db.all(sql, [cuenta_id], (err, rows) => {
        if (err) {
            return res.status(500).json({ error: err.message });
        }
        res.json({
            message: 'success',
            data: rows
        });
    });
});

// Get all transactions for a specific context (for charts - ASC)
app.get('/api/transacciones', (req, res) => {
    const cuentaId = req.query.cuenta_id;
    let sql = `SELECT t.*,
               (SELECT c2.nombre_cuenta FROM transaccion t2 JOIN cuenta c2 ON c2.id = t2.cuenta_id WHERE t2.categoria = t.categoria AND t2.tipo != t.tipo AND t2.fecha = t.fecha AND t2.monto = t.monto AND t2.id != t.id LIMIT 1) as cuenta_vinculada
               FROM transaccion t`;
    let params = [];
    if (cuentaId && cuentaId !== 'null') {
        sql += ' WHERE t.cuenta_id = ?';
        params.push(cuentaId);
    }
    sql += ' ORDER BY t.fecha ASC';
    db.all(sql, params, (err, rows) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json({ message: 'success', data: rows });
    });
});

// Get all transactions with account name for the movimientos section (DESC)
app.get('/api/movimientos', (req, res) => {
    const cuentaId = req.query.cuenta_id;

    // Helper: get all sub-account IDs in the hierarchy of a given account ID
    const getAllSubIds = (rootId, jRows) => {
        const result = new Set([parseInt(rootId)]);
        const queue = [parseInt(rootId)];
        while (queue.length > 0) {
            const curr = queue.shift();
            jRows.forEach(j => {
                if (j.cabecera_id === curr && !result.has(j.dependiente_id)) {
                    result.add(j.dependiente_id);
                    queue.push(j.dependiente_id);
                }
            });
        }
        return Array.from(result);
    };

    db.all('SELECT cabecera_id, dependiente_id FROM jerarquia', [], (err, jRows) => {
        if (err) return res.status(500).json({ error: err.message });

        let sql = `SELECT t.*, c.nombre_cuenta, c.centro_costo,
                   (SELECT c2.nombre_cuenta FROM transaccion t2 JOIN cuenta c2 ON c2.id = t2.cuenta_id WHERE t2.categoria = t.categoria AND t2.tipo != t.tipo AND t2.fecha = t.fecha AND t2.monto = t.monto AND t2.id != t.id LIMIT 1) as cuenta_vinculada
                   FROM transaccion t
                   LEFT JOIN cuenta c ON c.id = t.cuenta_id`;
        let params = [];

        if (cuentaId && cuentaId !== 'null') {
            const ids = getAllSubIds(cuentaId, jRows);
            sql += ` WHERE t.cuenta_id IN (${ids.map(() => '?').join(',')})`;
            params = ids;
        }

        sql += ' ORDER BY t.fecha DESC';

        db.all(sql, params, (err, rows) => {
            if (err) return res.status(500).json({ error: err.message });
            res.json({ message: 'success', data: rows });
        });
    });
});

// Update the ticket/transaction status (for egresos)
app.put('/api/transacciones/:id/estado', (req, res) => {
    const txId = req.params.id;
    const { estado, comentario } = req.body; // 'aceptado' or 'rechazado', comentario is optional

    if (!['solicitada', 'en estudio', 'aprobada', 'rechazada', 'en ejecución', 'terminada', 'generado', 'aceptado', 'rechazado'].includes(estado)) {
        return res.status(400).json({ error: 'Estado inválido' });
    }

    db.get('SELECT * FROM transaccion WHERE id = ?', [txId], (err, tx) => {
        if (err || !tx) return res.status(404).json({ error: 'Transacción no encontrada' });

        if (tx.estado === estado) {
            return res.json({ message: 'Sin cambios', data: tx });
        }

        db.serialize(() => {
            db.run('BEGIN TRANSACTION');

            // Update historial with comments
            let historial = {};
            if (tx.historial_estados) {
                try { historial = JSON.parse(tx.historial_estados); } catch (e) {}
            }
            historial[estado] = { fecha: new Date().toISOString().replace('T', ' ').substring(0, 19), comentario: comentario || '' };
            const historialStr = JSON.stringify(historial);

            // If we are rejecting a previously 'generado' or 'aceptado' egress, we refund the money
            // If we are changing from 'rechazado' back to 'generado' or 'aceptado', we charge the money again
            // For simplicity, handle standard transitions: generado -> aceptado/rechazado
            const updateQ = (estado === 'aprobada' || estado === 'aceptado')
                ? 'UPDATE transaccion SET estado = ?, fecha_aceptado = CURRENT_TIMESTAMP, historial_estados = ? WHERE id = ?'
                : 'UPDATE transaccion SET estado = ?, historial_estados = ? WHERE id = ?';
            db.run(updateQ, [estado, historialStr, txId], function(errUpdate) {
                if (errUpdate) {
                    db.run('ROLLBACK');
                    return res.status(500).json({ error: errUpdate.message });
                }

                // Balance modifications
                let amountModifier = 0;
                if (tx.tipo === 'egreso') {
                    const wasRechazado = (tx.estado === 'rechazado' || tx.estado === 'rechazada');
                    const isRechazado = (estado === 'rechazado' || estado === 'rechazada');
                    if (!wasRechazado && isRechazado) {
                        // Refund the expense
                        amountModifier = -tx.monto;
                    } else if (wasRechazado && !isRechazado) {
                        // Charge the expense again
                        amountModifier = tx.monto;
                    }
                } else if (tx.tipo === 'ingreso') {
                    const wasRechazado = (tx.estado === 'rechazado' || tx.estado === 'rechazada');
                    const isRechazado = (estado === 'rechazado' || estado === 'rechazada');
                    if (!wasRechazado && isRechazado) {
                        // Undo the income
                        amountModifier = -tx.monto;
                    } else if (wasRechazado && !isRechazado) {
                        // Redo the income
                        amountModifier = tx.monto;
                    }
                }

                if (amountModifier !== 0) {
                    db.get('SELECT * FROM cuenta WHERE id = ?', [tx.cuenta_id], (err2, cuenta) => {
                        if (err2 || !cuenta) {
                            db.run('ROLLBACK');
                            return res.status(500).json({ error: 'Cuenta no encontrada' });
                        }

                        let newIngresos = cuenta.ingresos;
                        let newEgresos = cuenta.egresos;

                        if (tx.tipo === 'egreso') {
                            newEgresos += amountModifier;
                        } else if (tx.tipo === 'ingreso') {
                            newIngresos += amountModifier; // Actually modifying ingresos
                        }

                        let newSaldo = newIngresos - newEgresos;

                        db.run('UPDATE cuenta SET ingresos = ?, egresos = ?, saldo = ? WHERE id = ?', [newIngresos, newEgresos, newSaldo, tx.cuenta_id], function(err3) {
                            if (err3) {
                                db.run('ROLLBACK');
                                return res.status(500).json({ error: err3.message });
                            }
                            db.run('COMMIT');
                            notifyClients();
                            res.json({ message: 'success', estado });
                        });
                    });
                } else {
                    db.run('COMMIT');
                    notifyClients();
                    res.json({ message: 'success', estado });
                }
            });
        });
    });
});

// Helper for recalculating balances after an edit or delete
function recalculateBalancesForCuenta(cuenta_id, cb) {
    const sql = `
        SELECT 
            SUM(CASE WHEN tipo = 'ingreso' THEN monto ELSE 0 END) AS total_ingresos,
            SUM(CASE WHEN tipo = 'egreso' THEN monto ELSE 0 END) AS total_egresos
        FROM transaccion
        WHERE cuenta_id = ? AND (estado IS NULL OR estado NOT IN ('rechazado', 'rechazada'))
    `;
    db.get(sql, [cuenta_id], (err, res) => {
        if (err) return cb(err);
        const newIngresos = res.total_ingresos || 0;
        const newEgresos = res.total_egresos || 0;
        const newSaldo = newIngresos - newEgresos;
        db.run('UPDATE cuenta SET ingresos = ?, egresos = ?, saldo = ? WHERE id = ?', 
               [newIngresos, newEgresos, newSaldo, cuenta_id], (err2) => {
            if (err2) return cb(err2);
            notifyClients();
            cb(null, { ingresos: newIngresos, egresos: newEgresos, saldo: newSaldo });
        });
    });
}

// Edit transaction amount (Root only conceptually, validated on frontend)
app.put('/api/transacciones/:id', (req, res) => {
    const txId = req.params.id;
    const { monto } = req.body;
    
    if (monto === undefined || isNaN(monto)) {
        return res.status(400).json({ error: 'Monto inválido' });
    }

    db.get('SELECT * FROM transaccion WHERE id = ?', [txId], (err, tx) => {
        if (err || !tx) return res.status(404).json({ error: 'Transacción no encontrada' });

        // Companion finding logic: Since transfers are saved as independent rows 
        // with the exact same fecha, categoria, and monto but opposite tipo
        const companionSql = `
            SELECT id, cuenta_id FROM transaccion 
            WHERE categoria = ? AND tipo != ? AND fecha = ? AND monto = ? AND id != ?
        `;
        db.get(companionSql, [tx.categoria, tx.tipo, tx.fecha, tx.monto, tx.id], (errComp, companion) => {
            
            db.serialize(() => {
                db.run('BEGIN TRANSACTION');
                
                db.run('UPDATE transaccion SET monto = ? WHERE id = ?', [parseFloat(monto), txId]);
                if (companion) {
                    db.run('UPDATE transaccion SET monto = ? WHERE id = ?', [parseFloat(monto), companion.id]);
                }
                
                db.run('COMMIT', (errCommit) => {
                    if (errCommit) return res.status(500).json({ error: errCommit.message });
                    
                    recalculateBalancesForCuenta(tx.cuenta_id, (errRecalc) => {
                        if (companion) {
                            recalculateBalancesForCuenta(companion.cuenta_id, () => res.json({ message: 'success' }));
                        } else {
                            res.json({ message: 'success' });
                        }
                    });
                });
            });
        });
    });
});

// Delete transaction (Root only)
app.delete('/api/transacciones/:id', (req, res) => {
    const txId = req.params.id;

    db.get('SELECT * FROM transaccion WHERE id = ?', [txId], (err, tx) => {
        if (err || !tx) return res.status(404).json({ error: 'Transacción no encontrada' });

        const companionSql = `
            SELECT id, cuenta_id FROM transaccion 
            WHERE categoria = ? AND tipo != ? AND fecha = ? AND monto = ? AND id != ?
        `;
        db.get(companionSql, [tx.categoria, tx.tipo, tx.fecha, tx.monto, tx.id], (errComp, companion) => {
            
            db.serialize(() => {
                db.run('BEGIN TRANSACTION');
                
                db.run('DELETE FROM transaccion WHERE id = ?', [txId]);
                if (companion) {
                    db.run('DELETE FROM transaccion WHERE id = ?', [companion.id]);
                }
                
                db.run('COMMIT', (errCommit) => {
                    if (errCommit) return res.status(500).json({ error: errCommit.message });
                    
                    recalculateBalancesForCuenta(tx.cuenta_id, (errRecalc) => {
                        if (companion) {
                            recalculateBalancesForCuenta(companion.cuenta_id, () => res.json({ message: 'success' }));
                        } else {
                            res.json({ message: 'success' });
                        }
                    });
                });
            });
        });
    });
});

// Create new account
app.post('/api/cuentas', (req, res) => {
    const { cuenta_eafit, nombre_cuenta, documento, tipo, escuela, area, grupo_investigacion } = req.body;
    
    // Default values since it's a new account
    const saldo = 0.0;
    const ingresos = 0.0;
    const egresos = 0.0;
    
    const sql = `INSERT INTO cuenta (cuenta_eafit, nombre_cuenta, tipo, saldo, ingresos, egresos, documento, nombre_docente, area, escuela, grupo_investigacion, centro_costo) 
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`;
const { centro_costo } = req.body;
    db.run(sql, [cuenta_eafit, nombre_cuenta, tipo, saldo, ingresos, egresos, documento, nombre_cuenta, area, escuela, grupo_investigacion, centro_costo], function(err) {
        if (err) {
            return res.status(500).json({ error: err.message });
        }
        
        const newId = this.lastID;
        db.get('SELECT * FROM cuenta WHERE id = ?', [newId], (err2, row) => {
            if (err2 || !row) return res.status(500).json({ error: 'Error cargando la nueva cuenta' });
            notifyClients();
            res.json({ message: 'success', data: row });
        });
    });
});

// Update account details
app.put('/api/cuentas/:id', (req, res) => {
    const cuentaId = req.params.id;
    const { nombre_cuenta, documento, tipo, escuela, area, grupo_investigacion, centro_costo } = req.body;

    const sql = `UPDATE cuenta 
                 SET nombre_cuenta = ?, documento = ?, tipo = ?, escuela = ?, area = ?, grupo_investigacion = ?, centro_costo = ?
                 WHERE id = ?`;
    
    db.run(sql, [nombre_cuenta, documento, tipo, escuela, area, grupo_investigacion, centro_costo, cuentaId], function(err) {
        if (err) {
            return res.status(500).json({ error: err.message });
        }
        if (this.changes === 0) {
            return res.status(404).json({ error: 'Cuenta no encontrada' });
        }
        
        // Fetch the updated row to return it
        db.get('SELECT * FROM cuenta WHERE id = ?', [cuentaId], (err2, row) => {
            if (err2 || !row) return res.status(500).json({ error: 'Error recargando la cuenta' });
            notifyClients();
            res.json({ message: 'success', data: row });
        });
    });
});

// Serve the main application page
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'views', 'index.html'));
});

// Start server
app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
});
