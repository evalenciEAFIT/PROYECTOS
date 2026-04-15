// ======= NAVEGACIÓN Y RED =======

// Global Fetch Interceptor to log User sessions
const originalFetch = window.fetch;
window.fetch = async function(...args) {
    if (window.currentUser && window.currentUser.cuenta_eafit) {
        let options = args[1] || {};
        options.headers = options.headers || {};
        // Add the user to track them in the Node Backend Logs
        options.headers['x-user'] = window.currentUser.cuenta_eafit;
        args[1] = options;
    }
    return originalFetch.apply(this, args);
};
const SECTIONS = ['resumen', 'movimientos', 'informe'];
const SECTION_IDS = {
    resumen: ['userInfoCard', 'summary-cards-wrap', 'chartsSection', 'evolutionChartSection', 'accounts-section-wrap'],
    movimientos: ['sectionMovimientos'],
    informe: ['sectionInforme']
};

window.showSection = function (name) {
    // --- Activate nav link ---
    document.querySelectorAll('.nav-links a').forEach(a => a.classList.remove('active'));
    const navMap = {
        resumen: 'navResumen',
        movimientos: 'navMovimientosLink',
        informe: 'navInformeLink',
        aprobaciones: 'navAprobacionesLink',
        ayuda: 'navAyudaLink'
    };
    const activeLink = document.getElementById(navMap[name]);
    if (activeLink) activeLink.classList.add('active');

    // --- Element groups ---
    const summaryCards = document.querySelector('.summary-cards');
    const globalWindow = document.getElementById('globalTimeWindowContainer');
    const chartEls = [
        document.getElementById('chartsSection'),
        document.getElementById('evolutionChartSection')
    ];
    const accountsSection = document.querySelector('.accounts-section');
    const secMov = document.getElementById('sectionMovimientos');
    const secInf = document.getElementById('sectionInforme');
    const secAprob = document.getElementById('sectionAprobaciones');
    const secAyuda = document.getElementById('sectionAyuda');

    // Helper
    const show = el => { if (el) el.style.display = ''; };
    const hide = el => { if (el) el.style.display = 'none'; };

    if (name === 'resumen') {
        show(summaryCards);
        show(globalWindow);
        chartEls.forEach(show);
        hide(accountsSection);
        hide(secMov);
        hide(secInf);
        hide(secAprob);
        hide(secAyuda);
    } else if (name === 'movimientos') {
        hide(summaryCards);
        hide(globalWindow);
        chartEls.forEach(hide);
        hide(accountsSection);
        hide(secInf);
        hide(secAprob);
        hide(secAyuda);
        if (secMov) { secMov.style.display = 'block'; loadMovimientosSection(); }
    } else if (name === 'informe') {
        hide(summaryCards);
        hide(globalWindow);
        chartEls.forEach(hide);
        hide(secMov);
        hide(secAprob);
        hide(secInf);
        hide(secAyuda);
        show(accountsSection);
    } else if (name === 'aprobaciones') {
        hide(summaryCards);
        hide(globalWindow);
        chartEls.forEach(hide);
        hide(accountsSection);
        hide(secMov);
        hide(secInf);
        hide(secAyuda);
        if (secAprob) { secAprob.style.display = 'block'; window.loadAprobacionesSection(); }
    } else if (name === 'ayuda') {
        hide(summaryCards);
        hide(globalWindow);
        chartEls.forEach(hide);
        hide(accountsSection);
        hide(secMov);
        hide(secAprob);
        hide(secInf);
        show(secAyuda);
    }
};

window._aproData = [];
window._aproSort = { col: 'fecha', dir: 'desc' };

window.sortAprob = function (col) {
    if (window._aproSort.col === col) {
        window._aproSort.dir = window._aproSort.dir === 'asc' ? 'desc' : 'asc';
    } else {
        window._aproSort.col = col;
        window._aproSort.dir = 'asc';
    }
    window.renderAprobacionesTable();
};

window.renderAprobacionesTable = function () {
    const body = document.getElementById('aprobacionesTableBody');
    const empty = document.getElementById('aprobacionesEmpty');
    const fechaDesde = document.getElementById('aprobFechaDesde')?.value;
    const fechaHasta = document.getElementById('aprobFechaHasta')?.value;
    const searchVal = (document.getElementById('aprobSearchInput')?.value || '').toLowerCase().trim();

    let dFrom = fechaDesde ? new Date(fechaDesde + 'T00:00:00') : null;
    let dTo = fechaHasta ? new Date(fechaHasta + 'T23:59:59') : null;
    const filterEstado = document.getElementById('filterAprobEstado')?.value || '';
    const filterCC = (document.getElementById('aprobFilterCC')?.value || '').toLowerCase().trim();

    let filtered = window._aproData.filter(tx => {
        if (filterEstado) {
            let txEstado = (tx.estado || '').toLowerCase();
            if (txEstado === 'generado') txEstado = 'solicitada';
            if (txEstado === 'aceptado') txEstado = 'aprobada';
            if (txEstado === 'rechazado') txEstado = 'rechazada';
            if (txEstado !== filterEstado) return false;
        }

        if (searchVal) {
            const matchesNombre = (tx.nombre_cuenta || '').toLowerCase().includes(searchVal);
            const matchesCat = (tx.categoria || '').toLowerCase().includes(searchVal);
            if (!matchesNombre && !matchesCat) return false;
        }

        if (filterCC) {
            const matchesCC = (tx.centro_costo || '').toLowerCase().includes(filterCC);
            if (!matchesCC) return false;
        }

        let fStr = tx.fecha || '';
        if (fStr.includes('T')) fStr = fStr.split('T')[0];
        else fStr = fStr.split(' ')[0];

        // Evitar error en parseo
        let f = new Date(fStr + 'T12:00:00');
        if (dFrom && f < dFrom) return false;
        if (dTo && f > dTo) return false;
        return true;
    });

    filtered.sort((a, b) => {
        let va = a[window._aproSort.col] || '';
        let vb = b[window._aproSort.col] || '';
        if (window._aproSort.col === 'monto') { va = Number(va); vb = Number(vb); }
        if (window._aproSort.col === 'fecha') { va = new Date(va).getTime(); vb = new Date(vb).getTime(); }

        if (va < vb) return window._aproSort.dir === 'asc' ? -1 : 1;
        if (va > vb) return window._aproSort.dir === 'asc' ? 1 : -1;
        return 0;
    });

    // Update header classes
    document.querySelectorAll('#sectionAprobaciones th.sortable').forEach(th => {
        th.classList.remove('sort-asc', 'sort-desc');
        if (th.dataset.col === window._aproSort.col) th.classList.add(window._aproSort.dir === 'asc' ? 'sort-asc' : 'sort-desc');
    });

    const isRoot = window.currentUser && window.currentUser.cuenta_eafit === 'root_ctei@eafit.edu.co';
    const thAprobAdmin = document.getElementById('thAprobAdmin');
    if (thAprobAdmin) thAprobAdmin.style.display = isRoot ? 'table-cell' : 'none';

    if (filtered.length === 0) {
        body.innerHTML = '';
        if (empty) empty.style.display = 'block';
    } else {
        body.innerHTML = filtered.map(tx => {
            const monto = '$' + Number(tx.monto).toLocaleString('en-US');

            let estadoHtml = '—';
            if (tx.estado) {
                let color = '#f59e0b'; // pending/generado/solicitada
                let normState = tx.estado;
                if (normState === 'generado') normState = 'solicitada';
                if (normState === 'aceptado') normState = 'aprobada';
                if (normState === 'rechazado') normState = 'rechazada';

                if (normState === 'aprobada') color = '#10b981';
                if (normState === 'rechazada') color = '#ef4444';
                if (normState === 'en estudio') color = '#3b82f6';
                if (normState === 'en ejecución') color = '#8b5cf6';
                if (normState === 'terminada') color = '#14b8a6';

                estadoHtml = `<div style="text-align:center;"><span style="color:${color};font-size:11px;font-weight:700;text-transform:uppercase;border:1px solid ${color};padding:2px 6px;border-radius:10px;display:inline-block;margin-bottom:4px;">${normState}</span>`;

                let current_date = tx.fecha;
                try {
                    if (tx.historial_estados) {
                        const h = JSON.parse(tx.historial_estados);
                        const k = tx.estado;
                        if (h[k] && h[k].fecha) current_date = h[k].fecha;
                        else if (h[normState] && h[normState].fecha) current_date = h[normState].fecha;
                        else {
                            const dates = Object.values(h).map(x => x.fecha).sort();
                            if (dates.length) current_date = dates[dates.length - 1];
                        }
                    }
                } catch(e) {}
                if (current_date) {
                    let dAcc = current_date.replace('T', ' ');
                    if (dAcc.indexOf('.') > -1) dAcc = dAcc.split('.')[0];
                    estadoHtml += `<div style="font-size:10px;color:var(--text-muted);margin-bottom:4px;white-space:nowrap;">Date: ${dAcc.split(' ')[0]}</div>`;
                }

                // Acciones - Flow Buttons Card & Timeline
                estadoHtml += getFlowButtonsHtml(tx.id, tx.estado, tx.historial_estados, isRoot);

                estadoHtml += `</div>`;
            }

            let adminTd = '';
            if (isRoot) {
                adminTd = `<td style="text-align:center; vertical-align:middle;">
                    <div style="display:flex; flex-direction:column; gap:4px; align-items:center;">
                        <button onclick="window.editTransactionAmount(${tx.id}, ${tx.monto})" style="background:var(--accent-light);color:var(--accent-color);border:1px solid rgba(26,58,143,0.2);padding:4px 10px;border-radius:6px;font-size:10px;font-weight:700;cursor:pointer;transition:background 0.2s;width:100%;max-width:80px;">EDITAR</button>
                        <button onclick="window.deleteTransactionData(${tx.id})" style="background:var(--expense-bg);color:var(--expense-color);border:1px solid rgba(192,57,43,0.2);padding:4px 10px;border-radius:6px;font-size:10px;font-weight:700;cursor:pointer;transition:background 0.2s;width:100%;max-width:80px;">ELIMINAR</button>
                    </div>
                </td>`;
            }

            return `
                <tr>
                    <td><div class="account-name">${tx.nombre_cuenta || '-'}</div></td>
                    <td><div style="font-size:13px; font-weight:600; color:var(--text-secondary);">${tx.centro_costo || '-'}</div></td>
                    <td>
                        <div style="font-weight:500;color:var(--text-primary);">${tx.categoria || '-'}</div>
                        ${tx.cuenta_vinculada ? `<div style="font-size:11px;color:var(--accent-color);font-weight:600;margin-top:4px;display:inline-flex;align-items:center;gap:4px;background:var(--accent-light);padding:2px 6px;border-radius:4px;"><svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg> Destino: ${tx.cuenta_vinculada}</div><br>` : ''}
                        ${tx.justificacion ? `<div style="font-size:11px;color:var(--text-muted);margin-top:3px;display:inline-block;">Ref: ${tx.justificacion}</div>` : ''}
                    </td>
                    <td class="amount-col val-expense">-${monto}</td>
                    <td><div style="font-size:13px;">${tx.fecha || '-'}</div></td>
                    <td style="text-align:center; vertical-align:middle;">
                        ${estadoHtml}
                    </td>
                    ${adminTd}
                </tr>
            `;
        }).join('');
        if (empty) empty.style.display = 'none';
    }
};

window.exportarAprobExcel = function () {
    let csvContent = "data:text/csv;charset=utf-8,";
    csvContent += "Cuenta Origen,Centro Costo,Categoría,Justificación,Monto,Fecha Generación,Estado\n";

    const fechaDesde = document.getElementById('aprobFechaDesde')?.value;
    const fechaHasta = document.getElementById('aprobFechaHasta')?.value;
    let dFrom = fechaDesde ? new Date(fechaDesde + 'T00:00:00') : null;
    let dTo = fechaHasta ? new Date(fechaHasta + 'T23:59:59') : null;

    const searchVal = (document.getElementById('aprobSearchInput')?.value || '').toLowerCase().trim();
    const filterEstado = document.getElementById('filterAprobEstado')?.value || '';
    const filterCC = (document.getElementById('aprobFilterCC')?.value || '').toLowerCase().trim();

    let filtered = window._aproData.filter(tx => {
        // Filter Estado
        if (filterEstado) {
            let txEstado = (tx.estado || '').toLowerCase();
            if (txEstado === 'generado') txEstado = 'solicitada';
            if (txEstado === 'aceptado') txEstado = 'aprobada';
            if (txEstado === 'rechazado') txEstado = 'rechazada';
            if (txEstado !== filterEstado) return false;
        }
        // Filter Search
        if (searchVal) {
            const matchesNombre = (tx.nombre_cuenta || '').toLowerCase().includes(searchVal);
            const matchesCat = (tx.categoria || '').toLowerCase().includes(searchVal);
            if (!matchesNombre && !matchesCat) return false;
        }
        // Filter CC
        if (filterCC) {
            const matchesCC = (tx.centro_costo || '').toLowerCase().includes(filterCC);
            if (!matchesCC) return false;
        }

        let fStr = tx.fecha || '';
        if (fStr.includes('T')) fStr = fStr.split('T')[0];
        else fStr = fStr.split(' ')[0];
        let f = new Date(fStr + 'T12:00:00');
        if (dFrom && f < dFrom) return false;
        if (dTo && f > dTo) return false;
        return true;
    });

    // Ordenar con el mismo criterio actual
    filtered.sort((a, b) => {
        let va = a[window._aproSort.col] || '';
        let vb = b[window._aproSort.col] || '';
        if (window._aproSort.col === 'monto') { va = Number(va); vb = Number(vb); }
        if (window._aproSort.col === 'fecha') { va = new Date(va).getTime(); vb = new Date(vb).getTime(); }

        if (va < vb) return window._aproSort.dir === 'asc' ? -1 : 1;
        if (va > vb) return window._aproSort.dir === 'asc' ? 1 : -1;
        return 0;
    });

    filtered.forEach(function (rowArray) {
        let row = [
            `"${(rowArray.nombre_cuenta || '').replace(/"/g, '""')}"`,
            `"${(rowArray.centro_costo || '').replace(/"/g, '""')}"`,
            `"${(rowArray.categoria || '').replace(/"/g, '""')}"`,
            `"${(rowArray.justificacion || '').replace(/"/g, '""')}"`,
            rowArray.monto,
            `"${(rowArray.fecha || '').replace(/"/g, '""')}"`,
            `"${(rowArray.estado || '').replace(/"/g, '""')}"`
        ];
        csvContent += row.join(",") + "\n";
    });

    var encodedUri = encodeURI(csvContent);
    var link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "gestion_egresos.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
};

window.loadAprobacionesSection = async function () {
    const body = document.getElementById('aprobacionesTableBody');
    const empty = document.getElementById('aprobacionesEmpty');
    if (!body || !empty) return;

    body.innerHTML = '<tr><td colspan="5" style="text-align:center;padding:48px;color:var(--text-muted);">Cargando pendientes...</td></tr>';
    empty.style.display = 'none';

    try {
        const res = await fetch('/api/movimientos?cuenta_id=null');
        const data = await res.json();
        if (data.message === 'success' && data.data) {
            // Filtrar todos los egresos que NO sean transferencias y ordenar los más recientes primero
            const pendientes = data.data.filter(t => t.tipo === 'egreso' && t.categoria !== 'Transferencia a la Comunidad Académica');

            window._aproData = pendientes;
            window.renderAprobacionesTable();
        }
    } catch (e) {
        body.innerHTML = '<tr><td colspan="5" style="text-align:center;padding:48px;color:var(--text-muted);">Error al cargar.</td></tr>';
    }
};

let _movData = [];

// ---- Estado de filtros/ordenamiento de movimientos ----
let _movSort = { col: 'fecha', dir: 'desc' };
let _movPreset = 'all';

async function loadMovimientosSection() {
    window.loadMovimientosSection = loadMovimientosSection;
    if (!window.currentUser || !window.currentUser.id) return;
    const body = document.getElementById('movTableBody');
    const empty = document.getElementById('movEmpty');
    body.innerHTML = '<tr><td colspan="4" style="text-align:center;padding:48px;color:var(--text-muted);">Cargando transacciones...</td></tr>';
    if (empty) empty.style.display = 'none';

    try {
        const id = window.currentUser.id;
        const res = await fetch(`/api/cuentas/${id}/transacciones`);
        const data = await res.json();
        const nombre = window.currentUser.nombre_cuenta || '';
        _movData = (data.message === 'success' && data.data)
            ? data.data.map(t => ({ ...t, nombre_cuenta: nombre }))
            : [];
        renderMovTable(_movData);
    } catch (e) {
        body.innerHTML = '<tr><td colspan="5" style="text-align:center;padding:48px;color:var(--text-muted);">Error al cargar.</td></tr>';
    }
}

function getPresetDates(preset) {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    switch (preset) {
        case 'today': return [today, now];
        case 'week': return [new Date(today.getTime() - 6 * 86400000), now];
        case 'fortnight': return [new Date(today.getTime() - 14 * 86400000), now];
        case 'month': return [new Date(today.getTime() - 30 * 86400000), now];
        case 'quarter': return [new Date(today.getTime() - 90 * 86400000), now];
        case 'year': return [new Date(now.getFullYear(), 0, 1), now];
        default: return [null, null];
    }
}

function renderMovTable(txs) {
    const body = document.getElementById('movTableBody');
    const empty = document.getElementById('movEmpty');
    const countEl = document.getElementById('movCount');
    const filterVal = document.getElementById('filterMovTipo')?.value || '';
    const searchVal = (document.getElementById('movSearchInput')?.value || '').toLowerCase().trim();
    const desdeEl = document.getElementById('movFechaDesde');
    const hastaEl = document.getElementById('movFechaHasta');
    const clearBtn = document.getElementById('movClearFechas');

    // --- Resolver rango de fechas ---
    let desde = null, hasta = null;
    if (_movPreset !== 'all') {
        [desde, hasta] = getPresetDates(_movPreset);
    } else if (desdeEl?.value || hastaEl?.value) {
        if (desdeEl?.value) desde = new Date(desdeEl.value + 'T00:00:00');
        if (hastaEl?.value) hasta = new Date(hastaEl.value + 'T23:59:59');
    }
    if (clearBtn) clearBtn.style.display = (desde || hasta) ? 'inline-flex' : 'none';

    // --- Aplicar filtros ---
    let filtered = txs;
    if (filterVal) filtered = filtered.filter(t => t.tipo === filterVal);
    if (searchVal) filtered = filtered.filter(t =>
        (t.nombre_cuenta || '').toLowerCase().includes(searchVal) ||
        (t.categoria || '').toLowerCase().includes(searchVal)
    );
    if (desde || hasta) {
        filtered = filtered.filter(t => {
            if (!t.fecha) return false;
            const d = new Date(t.fecha.replace(' ', 'T'));
            if (desde && d < desde) return false;
            if (hasta && d > hasta) return false;
            return true;
        });
    }

    // --- Ordenar ---
    const { col, dir } = _movSort;
    filtered = [...filtered].sort((a, b) => {
        let va = a[col] ?? '';
        let vb = b[col] ?? '';
        if (col === 'fecha') { va = new Date(String(va).replace(' ', 'T')); vb = new Date(String(vb).replace(' ', 'T')); }
        else if (col === 'monto') { va = parseFloat(va); vb = parseFloat(vb); }
        else { va = String(va).toLowerCase(); vb = String(vb).toLowerCase(); }
        if (va < vb) return dir === 'asc' ? -1 : 1;
        if (va > vb) return dir === 'asc' ? 1 : -1;
        return 0;
    });

    // Actualizar iconos de sort
    document.querySelectorAll('.mov-th-sort').forEach(th => {
        th.classList.remove('sort-asc', 'sort-desc');
        if (th.dataset.col === col) th.classList.add(dir === 'asc' ? 'sort-asc' : 'sort-desc');
    });

    if (countEl) countEl.textContent = `${filtered.length} registro${filtered.length !== 1 ? 's' : ''}`;

    if (filtered.length === 0) {
        body.innerHTML = '';
        if (empty) empty.style.display = 'block';
        return;
    }
    if (empty) empty.style.display = 'none';

    const isRoot = window.currentUser && window.currentUser.cuenta_eafit === 'root_ctei@eafit.edu.co';
    const thMovAdmin = document.getElementById('thMovAdmin');
    if (thMovAdmin) thMovAdmin.style.display = isRoot ? 'table-cell' : 'none';

    body.innerHTML = '';

    filtered.forEach((tx) => {
        const row = document.createElement('tr');
        let dateStr = tx.fecha || '';
        if (dateStr.includes('T')) dateStr = dateStr.replace('T', ' ');
        if (dateStr.indexOf('.') > -1) dateStr = dateStr.split('.')[0];
        const dateParts = dateStr.split(' ');
        const dp = dateParts[0] || '—';
        const tp = dateParts[1] || '';
        const isIng = tx.tipo === 'ingreso';
        const aC = isIng ? 'val-income' : 'val-expense';
        const sign = isIng ? '+' : '−';
        const cuentaNombre = tx.nombre_cuenta || `Cta. #${tx.cuenta_id}`;

        let estadoHtml = '—';
        if (tx.tipo === 'egreso' && tx.estado) {
            let color = '#f59e0b';
            let normState = tx.estado;
            if (normState === 'generado') normState = 'solicitada';
            if (normState === 'aceptado') normState = 'aprobada';
            if (normState === 'rechazado') normState = 'rechazada';

            if (normState === 'aprobada') color = '#10b981';
            if (normState === 'rechazada') color = '#ef4444';
            if (normState === 'en estudio') color = '#3b82f6';
            if (normState === 'en ejecución') color = '#8b5cf6';
            if (normState === 'terminada') color = '#14b8a6';

            estadoHtml = `<div style="text-align:center;"><span style="color:${color};font-size:11px;font-weight:700;text-transform:uppercase;border:1px solid ${color};padding:2px 6px;border-radius:10px;display:inline-block;margin-bottom:4px;">${normState}</span>`;

            let current_date = tx.fecha;
            try {
                if (tx.historial_estados) {
                    const h = JSON.parse(tx.historial_estados);
                    const k = tx.estado;
                    if (h[k] && h[k].fecha) current_date = h[k].fecha;
                    else if (h[normState] && h[normState].fecha) current_date = h[normState].fecha;
                    else {
                        const dates = Object.values(h).map(x => x.fecha).sort();
                        if (dates.length) current_date = dates[dates.length - 1];
                    }
                }
            } catch(e) {}
            if (current_date) {
                let dAcc = current_date.replace('T', ' ');
                if (dAcc.indexOf('.') > -1) dAcc = dAcc.split('.')[0];
                estadoHtml += `<div style="font-size:10px;color:var(--text-muted);margin-bottom:4px;white-space:nowrap;">Date: ${dAcc.split(' ')[0]}</div>`;
            }

            // Acciones - Flow Buttons Card & Timeline (Read-only in Movimientos view)
            estadoHtml += getFlowButtonsHtml(tx.id, tx.estado, tx.historial_estados, false);
            estadoHtml += `</div>`;
        }

        let adminTd = '';
        if (isRoot) {
            adminTd = `<td style="text-align:center; vertical-align:middle;">
                <div style="display:flex; flex-direction:column; gap:4px; align-items:center;">
                    <button onclick="window.editTransactionAmount(${tx.id}, ${tx.monto})" style="background:var(--accent-light);color:var(--accent-color);border:1px solid rgba(26,58,143,0.2);padding:4px 10px;border-radius:6px;font-size:10px;font-weight:700;cursor:pointer;transition:background 0.2s;width:100%;max-width:80px;">EDITAR</button>
                    <button onclick="window.deleteTransactionData(${tx.id})" style="background:var(--expense-bg);color:var(--expense-color);border:1px solid rgba(192,57,43,0.2);padding:4px 10px;border-radius:6px;font-size:10px;font-weight:700;cursor:pointer;transition:background 0.2s;width:100%;max-width:80px;">ELIMINAR</button>
                </div>
            </td>`;
        }

        row.innerHTML = `
            <td>
                <div style="font-size:13px;font-weight:600;color:var(--text-primary);white-space:nowrap;">${dp}</div>
                <div style="font-size:11px;color:var(--text-muted);margin-top:1px;">${tp}</div>
            </td>
            <td><span class="tx-badge ${tx.tipo}">${tx.tipo}</span></td>
            <td>
               <div style="color:var(--text-primary);font-size:13px;font-weight:500;">${tx.categoria || '—'}</div>
               ${tx.cuenta_vinculada ? `<div style="font-size:11px;color:var(--accent-color);font-weight:600;margin-top:4px;display:inline-flex;align-items:center;gap:4px;background:var(--accent-light);padding:2px 6px;border-radius:4px;"><svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">${tx.tipo === 'egreso' ? '<path d="M5 12h14M12 5l7 7-7 7"/>' : '<path d="M19 12H5M12 19l-7-7 7-7"/>'}</svg> ${tx.tipo === 'egreso' ? 'Destino' : 'Origen'}: ${tx.cuenta_vinculada}</div><br>` : ''}
               ${tx.justificacion ? `<div style="font-size:11px;color:var(--text-muted);margin-top:3px;max-width:250px;white-space:normal;display:inline-block;">Ref: ${tx.justificacion}</div>` : ''}
            </td>
            <td style="text-align:right;font-size:14.5px;font-weight:700;font-variant-numeric:tabular-nums;white-space:nowrap;" class="${aC}">${sign} $${(tx.monto || 0).toLocaleString('es-CO', { maximumFractionDigits: 0 })}</td>
            <td style="text-align:center;vertical-align:middle;">${estadoHtml}</td>
            ${adminTd}
        `;
        body.appendChild(row);
    });
}


window.renderInformeTable = function () {
    const el = document.getElementById('informeContent');
    if (!el || !window.allAccounts || !window.allHierarchy) {
        if (el) el.innerHTML = '<div style="padding:32px;text-align:center;color:var(--text-muted);">Datos no disponibles. Regresa al Resumen primero.</div>';
        return;
    }
    const accounts = window.allAccounts;
    const hier = window.allHierarchy;

    // Build parent map
    const parentMap = {};
    Object.entries(hier).forEach(([cab, deps]) => {
        deps.forEach(d => { parentMap[d] = parseInt(cab); });
    });

    // Top-level (no parent) accounts
    const tops = accounts.filter(a => !parentMap[a.id]);

    let html = `<div style="overflow-x:auto;">
    <table class="movimientos-table" style="min-width:600px;">
        <thead><tr>
            <th>Dependencia / Cuenta</th>
            <th style="text-align:right;">Ingresos</th>
            <th style="text-align:right;">Egresos</th>
            <th style="text-align:right;">Saldo</th>
            <th>Tipo</th>
        </tr></thead>
        <tbody>`;

    function buildRows(list, depth) {
        list.forEach(a => {
            const indent = depth * 24;
            const isTop = depth === 0;
            const saldoC = a.saldo >= 0 ? 'val-income' : 'val-expense';
            const bgStyle = isTop ? 'background:rgba(79,70,229,0.04);' : '';
            const fw = isTop ? 'font-weight:700;' : 'font-weight:500;';
            html += `<tr style="${bgStyle}">
                <td style="padding-left:${16 + indent}px;${fw}color:var(--text-primary);">
                    ${depth > 0 ? '<span style="color:var(--text-muted);margin-right:6px;">↳</span>' : ''}${a.nombre_cuenta}
                    ${a.centro_costo ? `<div style="font-size:10.5px; color:var(--text-muted); font-weight:400; margin-top:2px;">Centro de Costo: ${a.centro_costo}</div>` : ''}
                </td>
                <td style="text-align:right;" class="val-income">$${(a.ingresos || 0).toLocaleString('es-CO', { maximumFractionDigits: 0 })}</td>
                <td style="text-align:right;" class="val-expense">$${(a.egresos || 0).toLocaleString('es-CO', { maximumFractionDigits: 0 })}</td>
                <td style="text-align:right;font-weight:700;" class="${saldoC}">$${(a.saldo || 0).toLocaleString('es-CO', { maximumFractionDigits: 0 })}</td>
                <td><span style="font-size:11px;background:rgba(79,70,229,0.08);color:var(--accent-color);padding:3px 8px;border-radius:10px;font-weight:600;">${a.tipo || '—'}</span></td>
            </tr>`;
            // Children
            const childIds = hier[a.id] || [];
            const children = accounts.filter(c => childIds.includes(c.id));
            if (children.length > 0) buildRows(children, depth + 1);
        });
    }

    buildRows(tops, 0);
    // Accounts not in tops but also not children (orphaned)
    html += '</tbody></table></div>';
    el.innerHTML = html;
};

let currentUser = null;
window.currentUser = null;

let categorias_ingreso = [
    "Transferencia Fondo CTeI",
    "Reconocimiento en Investigación",
    "Donación",
    "Transferencia desde la Comunidad Académica",
    "Otro"
];

let categorias_egreso = [
    "Insumo o Materiales",
    "Infraestructura o Equipos",
    "Eventos académicos",
    "Servicios",
    "Transferencia a la Comunidad Académica",
    "Otros",
    "Reactivos"
];

let categorias_transferencias = [
    "Transferencia Fondo CTeI",
    "Reconocimiento propiedad intelectual",
    "Incentivos",
    "Convenios",
    "Otro"
];

const categoryIcons = {
    "Transferencia Fondo CTeI": `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="10" width="18" height="10" rx="2" ry="2"/><line x1="12" y1="2" x2="12" y2="6"/><polyline points="8 6 12 2 16 6"/></svg>`,
    "Reconocimiento en Investigación": `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>`,
    "Donación": `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>`,
    "Transferencia desde la Comunidad Académica": `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>`,
    "Otro": `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="9" y1="3" x2="9" y2="21"/></svg>`,
    "Insumo o Materiales": `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 16.2A2 2 0 0 0 21 15V9a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 9v6a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4Z"/><line x1="3.27" x2="12" y1="6.96" y2="12"/><line x1="12" x2="12" y1="22.08" y2="12"/><line x1="20.73" x2="12" y1="6.96" y2="12"/></svg>`,
    "Infraestructura o Equipos": `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="4" y="4" width="16" height="16" rx="2" ry="2"/><rect x="9" y="9" width="6" height="6"/></svg>`,
    "Eventos académicos": `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>`,
    "Servicios": `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/><line x1="16" x2="8" y1="13" y2="13"/><line x1="16" x2="8" y1="17" y2="17"/><line x1="10" x2="8" y1="9" y2="9"/></svg>`,
    "Transferencia a la Comunidad Académica": `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/></svg>`,
    "Otros": `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/><circle cx="5" cy="12" r="1"/></svg>`,
    "Reactivos": `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10 2v7.31M14 2v7.31M8.5 2h7M14 9.3V19a2 2 0 0 1-2 2h-4a2 2 0 0 1-2-2V9.3L4.5 5A2 2 0 0 1 6 2h12a2 2 0 0 1 1.5 3l-1.5 4.3z"/></svg>`,
    "default": `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>`
};

document.addEventListener('DOMContentLoaded', () => {

    // ===== REACTIVIDAD EN TIEMPO REAL (SSE) =====
    const sse = new EventSource('/api/stream');
    sse.onmessage = async (event) => {
        if (event.data === 'update') {
            // Refresca la vista principal
            if (typeof window.fetchData === 'function') {
                window.fetchData();
            }
            // Refresca tablas activas si están visibles
            try {
                if (window.showSection && document.getElementById('sectionMovimientos').style.display !== 'none' && typeof loadMovimientosSection === 'function') {
                    await loadMovimientosSection();
                } else if (document.getElementById('modalMovimientos')?.classList.contains('active') && window.currentUser) {
                    await openMovimientosModal(new Event('click'), window.currentUser.id);
                } else if (window.showSection && document.getElementById('sectionAprobaciones').style.display !== 'none' && typeof loadAprobacionesSection === 'function') {
                    await window.loadAprobacionesSection();
                }
            } catch (e) {
                console.warn("Retrying SSE refresh for active section:", e);
            }
        }
    };

    // ===== FILTROS Y ORDENAMIENTO DE MOVIMIENTOS =====

    // Búsqueda y tipo
    const filterMovTipoEl = document.getElementById('filterMovTipo');
    if (filterMovTipoEl) filterMovTipoEl.addEventListener('change', () => renderMovTable(_movData));
    const movSearchInputEl = document.getElementById('movSearchInput');
    if (movSearchInputEl) movSearchInputEl.addEventListener('input', () => renderMovTable(_movData));

    // Rango personalizado
    const movFechaDesdeEl = document.getElementById('movFechaDesde');
    const movFechaHastaEl = document.getElementById('movFechaHasta');
    const movClearFechasEl = document.getElementById('movClearFechas');

    if (movFechaDesdeEl) movFechaDesdeEl.addEventListener('change', () => {
        _movPreset = 'all';
        document.querySelectorAll('.mov-preset-btn').forEach(b => b.classList.toggle('active', b.dataset.preset === 'all'));
        renderMovTable(_movData);
    });
    if (movFechaHastaEl) movFechaHastaEl.addEventListener('change', () => {
        _movPreset = 'all';
        document.querySelectorAll('.mov-preset-btn').forEach(b => b.classList.toggle('active', b.dataset.preset === 'all'));
        renderMovTable(_movData);
    });
    if (movClearFechasEl) movClearFechasEl.addEventListener('click', () => {
        if (movFechaDesdeEl) movFechaDesdeEl.value = '';
        if (movFechaHastaEl) movFechaHastaEl.value = '';
        _movPreset = 'all';
        document.querySelectorAll('.mov-preset-btn').forEach(b => b.classList.toggle('active', b.dataset.preset === 'all'));
        renderMovTable(_movData);
    });

    // Botones preset de fecha (event delegation)
    const presetsContainer = document.getElementById('movDatePresets');
    if (presetsContainer) {
        presetsContainer.addEventListener('click', (e) => {
            const btn = e.target.closest('.mov-preset-btn');
            if (!btn) return;
            _movPreset = btn.dataset.preset;
            // Limpiar rango personalizado al usar preset
            if (_movPreset !== 'all') {
                if (movFechaDesdeEl) movFechaDesdeEl.value = '';
                if (movFechaHastaEl) movFechaHastaEl.value = '';
            }
            document.querySelectorAll('.mov-preset-btn').forEach(b => b.classList.toggle('active', b === btn));
            renderMovTable(_movData);
        });
    }

    // Ordenamiento por columnas (click en <th>)
    document.addEventListener('click', (e) => {
        const th = e.target.closest('.mov-th-sort');
        if (!th) return;
        const col = th.dataset.col;
        if (_movSort.col === col) {
            _movSort.dir = _movSort.dir === 'asc' ? 'desc' : 'asc';
        } else {
            _movSort.col = col;
            _movSort.dir = col === 'fecha' ? 'desc' : 'asc';
        }
        renderMovTable(_movData);
    });

    let chartIngresos = null;
    let chartEgresos = null;
    let chartEvolucion = null;
    let allTransacciones = [];    // cache de transacciones para el gráfico de evolución
    let globalWindow = 'all'; // ventana activa global: 7d | 1m | 3m | 6m | ytd | all
    const winLabels = {
        '7d': 'Últimos 7 días', '1m': 'Últimos 30 días', '3m': 'Últimos 90 días',
        '6m': 'Últimos 6 meses', 'ytd': 'Año en curso', 'all': 'Todo el historial'
    };

    // UI Elements
    const loginOverlay = document.getElementById('loginOverlay');
    const loginBtn = document.getElementById('loginBtn');
    const loginEmail = document.getElementById('loginEmail');
    const loginPassword = document.getElementById('loginPassword');
    const loginError = document.getElementById('loginError');
    const navLogout = document.getElementById('navLogout');

    // Inicialización MSAL (La configuración maestra fue extraída a /js/azure-config.js)
    const msalConfig = {
        auth: window.AZURE_CONFIG || {
            clientId: "TU_AZURE_CLIENT_ID",
            authority: "https://login.microsoftonline.com/common",
            redirectUri: window.location.origin
        }
    };
    let msalInstance;
    try {
        if (window.msal) {
            msalInstance = new msal.PublicClientApplication(msalConfig);
        }
    } catch (e) { console.error("MSAL init error", e); }

    const onLoginSuccess = async (userData) => {
        currentUser = userData;
        window.currentUser = userData;
        loginOverlay.classList.remove('active');

        try {
            const catRes = await fetch('/api/categorias');
            const catData = await catRes.json();
            if (catData.message === 'success') {
                categorias_ingreso = catData.data.ingresos || [];
                categorias_egreso = catData.data.egresos || [];
                categorias_transferencias = catData.data.transferencias || categorias_transferencias;
            }
        } catch (e) {
            console.error("Error al cargar categorías", e);
        }

        // Update header visually
        document.getElementById('userNameDisplay').textContent = currentUser.nombre_cuenta;
        document.getElementById('userAvatar').textContent = currentUser.nombre_cuenta.charAt(0).toUpperCase();

        if (currentUser.cuenta_eafit !== 'admin') {
            document.getElementById('userInfoCard').style.display = 'block';
            document.getElementById('infoDocente').textContent = currentUser.nombre_cuenta;
            document.getElementById('infoDocumento').textContent = currentUser.documento ? `Doc. ${currentUser.documento}` : '';
            document.getElementById('infoTipo').textContent = currentUser.tipo || '-';
            document.getElementById('infoEscuela').textContent = currentUser.escuela || '-';
            document.getElementById('infoArea').textContent = currentUser.area || '-';
            document.getElementById('infoGrupo').textContent = currentUser.grupo_investigacion || '-';
        } else {
            document.getElementById('userInfoCard').style.display = 'none';
        }

        // Inicializar controles de tabla y de ventana global
        initTableControls();
        initGlobalControls();
        document.getElementById('globalTimeWindowContainer').style.display = 'flex';

        // Mostrar botones de operación en el cuadro saldo (solo si tiene cuenta propia)
        if (currentUser.id) {
            const saldoActions = document.getElementById('saldoActions');
            saldoActions.style.display = 'block';

            const btnEgreso = document.getElementById('btnSaldoEgreso');
            const btnTransf = document.getElementById('btnSaldoTransferencia');
            const btnIngreso = document.getElementById('btnSaldoIngreso');

            const isRoot = currentUser.cuenta_eafit === 'root_ctei@eafit.edu.co';

            if (isRoot) {
                if (btnIngreso) {
                    btnIngreso.style.display = 'flex';
                    btnIngreso.onclick = (e) => openIngresoModal(e, currentUser.id, true);
                }
            } else {
                if (btnIngreso) btnIngreso.style.display = 'none';
            }

            if (btnEgreso) {
                btnEgreso.style.display = 'flex';
                btnEgreso.onclick = (e) => openEgresoModal(e, currentUser.id, false);
            }
            if (btnTransf) {
                btnTransf.style.display = 'flex';
                btnTransf.onclick = (e) => openEgresoModal(e, currentUser.id, true);
            }

            // Show sidebar nav items
            const navMovItem = document.getElementById('navMovimientosItem');
            const navInfItem = document.getElementById('navInformeItem');
            const navAnalLabel = document.getElementById('navAnalisisLabel');
            const navAprob = document.getElementById('navAprobacionesItem');

            if (navMovItem) navMovItem.style.display = 'block';
            if (navInfItem) navInfItem.style.display = 'block';
            if (navAnalLabel) navAnalLabel.style.display = 'block';

            // Solo mostrar botón "Añadir Cuenta" a root
            const navCrearItem = document.getElementById('navCrearCuentaItem');
            if (navCrearItem) {
                navCrearItem.style.display = isRoot ? 'block' : 'none';
            }

            if (navAprob) navAprob.style.display = isRoot ? 'block' : 'none';
            const navEditCats = document.getElementById('navEditCatsItem');
            if (navEditCats) navEditCats.style.display = isRoot ? 'block' : 'none';
            const navBackup = document.getElementById('navBackupItem');
            if (navBackup) navBackup.style.display = isRoot ? 'block' : 'none';
            const navAyuda = document.getElementById('navAyudaItem');
            if (navAyuda) navAyuda.style.display = 'block';

            // Add id to Resumen link if not present
            const resLink = document.querySelector('#navResumen') || document.querySelector('.nav-links a.active');
            if (resLink && !resLink.id) resLink.id = 'navResumen';
        }

        // Forzar el estado inicial a la pestaña de Resumen
        if (window.showSection) window.showSection('resumen');

        // Load contextual data
        fetchData();
    };

    // Login Handling
    const attemptLogin = () => {
        const email = loginEmail.value.trim();
        const password = loginPassword.value.trim();

        if (!email) {
            loginError.textContent = "Ingrese su usuario o correo.";
            loginError.style.display = "block";
            return;
        }

        fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        })
            .then(res => res.json())
            .then(async data => {
                if (data.error) {
                    loginError.textContent = data.error;
                    loginError.style.display = "block";
                } else {
                    await onLoginSuccess(data.data);
                }
            })
            .catch(err => {
                console.error(err);
                loginError.textContent = "Error al conectar con el servidor.";
                loginError.style.display = "block";
            });
    };

    loginBtn.addEventListener('click', attemptLogin);

    // Evento de Azure Login
    document.getElementById('azureLoginBtn')?.addEventListener('click', async () => {
        if (!msalInstance) {
            loginError.textContent = "Librería de MSAL (Azure) no cargó. Refresque la pestaña.";
            loginError.style.display = "block";
            return;
        }

        if (msalConfig.auth.clientId === "TU_AZURE_CLIENT_ID") {
            const testEmail = prompt("SIMULADOR AZURE (Modo de Desarrollo)\n\nLa plataforma detecta que no has configurado el Client ID del portal de Azure aún.\nPara no bloquear tu desarrollo, ingresa un correo electrónico (ej: evalenci@eafit.edu.co o root_ctei@eafit.edu.co) para simular el inicio de sesión vía directorio Microsoft:");
            if (!testEmail) return;

            try {
                loginBtn.innerHTML = '<span class="loading-spinner" style="border-color:#fff;border-top-color:transparent;width:16px;height:16px;margin:0 auto;display:block;"></span>';
                const res = await fetch('/api/azure-login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email: testEmail.toLowerCase().trim() })
                });
                
                const data = await res.json();
                if (data.error) {
                    loginBtn.innerHTML = 'Ingresar';
                    loginError.textContent = data.error;
                    loginError.style.display = "block";
                } else {
                    await onLoginSuccess(data.data);
                }
            } catch(e) {
                loginBtn.innerHTML = 'Ingresar';
                loginError.textContent = "Error conectando al backend simulado.";
                loginError.style.display = "block";
            }
            return;
        }

        try {
            const response = await msalInstance.loginPopup({ scopes: ["user.read"] });
            const account = response.account;
            
            if (account && account.username) { // username is usually the email in Azure AD
                const email = account.username.toLowerCase();
                
                // Enviar petición al backend
                const res = await fetch('/api/azure-login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email })
                });
                
                const data = await res.json();
                if (data.error) {
                    loginError.textContent = data.error;
                    loginError.style.display = "block";
                    // Forzamos desloguear del caché frontend de MSAL si falla la bd
                    msalInstance.logoutPopup(); 
                } else {
                    await onLoginSuccess(data.data);
                }
            }
        } catch (error) {
            console.error("Azure login cancelled/error:", error);
            
            if (error.errorMessage && error.errorMessage.includes('AADSTS50173')) {
                loginError.innerHTML = "<b>Sesión Caducada:</b> La sesión ligada a su cuenta de EAFIT ha expirado o cambió de contraseña recientemente.<br><br>Por favor ingrese a Office.com para reactivar su cuenta y luego intente ingresar aquí nuevamente.";
            } else if (error.errorMessage && error.errorMessage.includes('AADSTS')) {
                loginError.innerHTML = "Error de Microsoft Azure: Se encontraron restricciones de directorio o identificadores inválidos. Contacte a soporte de TI EAFIT.";
            } else {
                loginError.innerHTML = "Se canceló la autenticación con Microsoft o hubo un problema de conexión.";
            }
            loginError.style.display = "block";
        }
    });
    loginPassword.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') attemptLogin();
    });
    loginEmail.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') loginPassword.focus();
    });

    const dropdownLogout = document.getElementById('dropdownLogout');

    // --- Lógica del modal de Editar Cuenta ---
    const modalEditarCuenta = document.getElementById('modalEditarCuenta');
    const errorEditarCuenta = document.getElementById('errorEditarCuenta');

    const openEditCuentaModal = (e, forceNew = false) => {
        if (e) e.preventDefault();

        // Quitar la clase active de todos los del sidebar para comportamiento normal
        document.querySelectorAll('.nav-links a').forEach(a => a.classList.remove('active'));

        if (!currentUser || currentUser.cuenta_eafit !== 'root_ctei@eafit.edu.co') return;

        const isRoot = true;
        if (forceNew && !isRoot) return; // Sólo el root puede forzar la creación de cuentas
        const selectContainer = document.getElementById('editSelectCuenta').parentElement;
        const emailGroup = document.getElementById('editEmailGroup');
        const selectCuenta = document.getElementById('editSelectCuenta');
        const emailInput = document.getElementById('editEmail');

        if (isRoot) {
            selectContainer.style.display = 'block';
            selectCuenta.innerHTML = '<option value="new">-- NUEVA CUENTA --</option>';
            systemAccounts.forEach(acc => {
                const opt = document.createElement('option');
                opt.value = acc.id;
                opt.textContent = `${acc.nombre_cuenta} (${acc.cuenta_eafit})`;
                if (!forceNew && acc.id === currentUser.id) opt.selected = true;
                selectCuenta.appendChild(opt);
            });
            if (forceNew) {
                const optNew = selectCuenta.querySelector('option[value="new"]');
                if (optNew) optNew.selected = true;
            }
        } else {
            selectContainer.style.display = 'none';
        }

        const populateFields = (accId) => {
            let targetAcc = currentUser;
            if (isRoot && accId !== 'new') {
                targetAcc = systemAccounts.find(a => String(a.id) === String(accId)) || currentUser;
            }

            if (accId === 'new') {
                emailGroup.style.display = 'block';
                emailInput.value = '';
                document.getElementById('editNombre').value = '';
                document.getElementById('editDocumento').value = '';
                populateSelect('editTipo', 'tipo', '');
                populateSelect('editEscuela', 'escuela', '');
                populateSelect('editArea', 'area', '');
                populateSelect('editGrupo', 'grupo_investigacion', '');
                document.getElementById('editCentroCosto').value = '';
            } else {
                emailGroup.style.display = 'none';
                document.getElementById('editNombre').value = targetAcc.nombre_cuenta || '';
                document.getElementById('editDocumento').value = targetAcc.documento || '';
                populateSelect('editTipo', 'tipo', targetAcc.tipo || '');
                populateSelect('editEscuela', 'escuela', targetAcc.escuela || '');
                populateSelect('editArea', 'area', targetAcc.area || '');
                populateSelect('editGrupo', 'grupo_investigacion', targetAcc.grupo_investigacion || '');
                document.getElementById('editCentroCosto').value = targetAcc.centro_costo || '';
            }
        };

        // Helper to populate datalist and set value
        const populateSelect = (inputId, accountKey, currentVal) => {
            const inputEl = document.getElementById(inputId);
            const listId = inputId.replace('edit', 'list');
            const dataList = document.getElementById(listId);
            
            if (inputEl) inputEl.value = currentVal || '';
            
            if (dataList) {
                dataList.innerHTML = '';
                let options = new Set();
                systemAccounts.forEach(acc => {
                    if (acc[accountKey]) options.add(acc[accountKey].trim());
                });

                [...options].sort().forEach(val => {
                    if (val) {
                        const opt = document.createElement('option');
                        opt.value = val;
                        dataList.appendChild(opt);
                    }
                });
            }
        };

        populateFields(isRoot ? (forceNew ? 'new' : String(currentUser.id)) : null);

        // Bind select change
        selectCuenta.onchange = (ev) => populateFields(ev.target.value);

        errorEditarCuenta.style.display = 'none';

        modalEditarCuenta.classList.add('active');
    };

    const closeEditCuentaModal = () => {
        modalEditarCuenta.classList.remove('active');
    };

    const saveEditCuenta = async () => {
        const isRoot = currentUser.cuenta_eafit === 'root_ctei@eafit.edu.co';
        const selectVal = isRoot ? document.getElementById('editSelectCuenta').value : currentUser.id;
        const isNew = isRoot && selectVal === 'new';

        const dataToSave = {
            nombre_cuenta: document.getElementById('editNombre').value.trim(),
            documento: document.getElementById('editDocumento').value.trim(),
            tipo: document.getElementById('editTipo').value.trim(),
            escuela: document.getElementById('editEscuela').value.trim(),
            area: document.getElementById('editArea').value.trim(),
            grupo_investigacion: document.getElementById('editGrupo').value.trim(),
            centro_costo: document.getElementById('editCentroCosto').value.trim()
        };

        if (isNew) {
            dataToSave.cuenta_eafit = document.getElementById('editEmail').value.trim();
            if (!dataToSave.cuenta_eafit) {
                errorEditarCuenta.textContent = 'El correo es obligatorio para una cuenta nueva';
                errorEditarCuenta.style.display = 'block';
                return;
            }
        }

        if (!dataToSave.nombre_cuenta) {
            errorEditarCuenta.textContent = 'El nombre de la cuenta es obligatorio';
            errorEditarCuenta.style.display = 'block';
            return;
        }

        try {
            const btnGuardar = document.getElementById('btnGuardarCuenta');
            btnGuardar.disabled = true;
            btnGuardar.textContent = 'Guardando...';

            const method = isNew ? 'POST' : 'PUT';
            const endpoint = isNew ? '/api/cuentas' : `/api/cuentas/${selectVal}`;

            const res = await fetch(endpoint, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(dataToSave)
            });
            const result = await res.json();

            if (result.error) throw new Error(result.error);

            if (isNew) {
                // Agregar al systemAccounts
                systemAccounts.push(result.data);
                alert("Cuenta creada con éxito.");
            } else {
                // Update in systemAccounts
                const idx = systemAccounts.findIndex(a => String(a.id) === String(selectVal));
                if (idx > -1) systemAccounts[idx] = { ...systemAccounts[idx], ...result.data };
                
                if (String(selectVal) === String(currentUser.id)) {
                    currentUser = { ...currentUser, ...result.data };
                    window.currentUser = currentUser;

                    document.getElementById('userNameDisplay').textContent = currentUser.nombre_cuenta;
                    document.getElementById('userAvatar').textContent = currentUser.nombre_cuenta.charAt(0).toUpperCase();

                    document.getElementById('infoDocente').textContent = currentUser.nombre_cuenta;
                    document.getElementById('infoDocumento').textContent = currentUser.documento ? `Doc. ${currentUser.documento}` : '';
                    document.getElementById('infoTipo').textContent = currentUser.tipo || '-';
                    document.getElementById('infoEscuela').textContent = currentUser.escuela || '-';
                    document.getElementById('infoArea').textContent = currentUser.area || '-';
                    document.getElementById('infoGrupo').textContent = currentUser.grupo_investigacion || '-';
                }
            }

            closeEditCuentaModal();
        } catch (e) {
            errorEditarCuenta.textContent = e.message;
            errorEditarCuenta.style.display = 'block';
        } finally {
            const btnGuardar = document.getElementById('btnGuardarCuenta');
            btnGuardar.disabled = false;
            btnGuardar.textContent = 'Guardar Cambios';
        }
    };

    // if (dropdownConfig) dropdownConfig.addEventListener('click', (e) => openEditCuentaModal(e, false));
    const btnCrearCuenta = document.getElementById('menuCrearCuenta');
    if (btnCrearCuenta) btnCrearCuenta.addEventListener('click', (e) => openEditCuentaModal(e, true));
    document.getElementById('closeEditarCuenta')?.addEventListener('click', closeEditCuentaModal);
    document.getElementById('btnCancelEditarCuenta')?.addEventListener('click', closeEditCuentaModal);
    document.getElementById('btnGuardarCuenta')?.addEventListener('click', saveEditCuenta);

    // --- Lógica del modal de Editar Categorias (Admin) ---
    const modalEditCats = document.getElementById('modalEditCats');
    
    let tempIngresos = [];
    let tempEgresos = [];
    let tempTransferencias = [];

    const renderTags = (listId, dataArray, arrayName) => {
        const list = document.getElementById(listId);
        if (!list) return;
        list.innerHTML = '';
        dataArray.forEach((tag, idx) => {
            const chip = document.createElement('div');
            chip.className = `tag-chip chip-${arrayName}`;
            chip.innerHTML = `
                ${tag} 
                <span class="tag-remove" onclick="window.removeCatTag(${idx}, '${arrayName}')">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </span>
            `;
            list.appendChild(chip);
        });
    };

    window.removeCatTag = (idx, arrayName) => {
        if (arrayName === 'ingresos') { tempIngresos.splice(idx, 1); renderTags('listIngresos', tempIngresos, 'ingresos'); }
        if (arrayName === 'egresos') { tempEgresos.splice(idx, 1); renderTags('listEgresos', tempEgresos, 'egresos'); }
        if (arrayName === 'transferencias') { tempTransferencias.splice(idx, 1); renderTags('listTransferencias', tempTransferencias, 'transferencias'); }
    };

    const setupTagInput = (inputId, arrayName) => {
        const input = document.getElementById(inputId);
        if (!input) return;
        
        const addValues = (valStr) => {
            const vals = valStr.split(',').map(s => s.trim()).filter(Boolean);
            if (vals.length > 0) {
                if (arrayName === 'ingresos') { vals.forEach(v => { if(!tempIngresos.includes(v)) tempIngresos.push(v); }); renderTags('listIngresos', tempIngresos, 'ingresos'); }
                if (arrayName === 'egresos') { vals.forEach(v => { if(!tempEgresos.includes(v)) tempEgresos.push(v); }); renderTags('listEgresos', tempEgresos, 'egresos'); }
                if (arrayName === 'transferencias') { vals.forEach(v => { if(!tempTransferencias.includes(v)) tempTransferencias.push(v); }); renderTags('listTransferencias', tempTransferencias, 'transferencias'); }
            }
        };

        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ',') {
                e.preventDefault();
                addValues(input.value);
                input.value = '';
            }
        });
        
        input.addEventListener('blur', (e) => {
            addValues(input.value);
            input.value = '';
        });
    };

    setupTagInput('inputIngresos', 'ingresos');
    setupTagInput('inputEgresos', 'egresos');
    setupTagInput('inputTransferencias', 'transferencias');

    const openEditCatsModal = (e) => {
        if (e) e.preventDefault();
        const success = document.getElementById('successEditCats');
        const err = document.getElementById('errorEditCats');
        if (success) success.style.display = 'none';
        if (err) err.style.display = 'none';

        tempIngresos = [...categorias_ingreso];
        tempEgresos = [...categorias_egreso];
        tempTransferencias = [...categorias_transferencias];

        renderTags('listIngresos', tempIngresos, 'ingresos');
        renderTags('listEgresos', tempEgresos, 'egresos');
        renderTags('listTransferencias', tempTransferencias, 'transferencias');

        modalEditCats.style.display = 'flex';
        setTimeout(() => modalEditCats.classList.add('active'), 10);
    };

    const closeEditCatsModal = () => {
        modalEditCats.classList.remove('active');
        setTimeout(() => modalEditCats.style.display = 'none', 300);
    };

    const saveEditCats = async () => {
        const newIngresos = [...tempIngresos];
        const newEgresos = [...tempEgresos];
        const newTransferencias = [...tempTransferencias];

        const btnGuardar = document.getElementById('btnGuardarCats');
        const success = document.getElementById('successEditCats');
        const err = document.getElementById('errorEditCats');
        success.style.display = 'none';
        err.style.display = 'none';

        btnGuardar.disabled = true;
        btnGuardar.textContent = 'Guardando...';

        try {
            const res = await fetch('/api/categorias', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ingresos: newIngresos, egresos: newEgresos, transferencias: newTransferencias })
            });
            const result = await res.json();

            if (result.error) throw new Error(result.error);

            categorias_ingreso = newIngresos;
            categorias_egreso = newEgresos;
            categorias_transferencias = newTransferencias;

            if (typeof fetchData === 'function') fetchData();

            success.textContent = "Categorías guardadas correctamente.";
            success.style.display = 'block';
            setTimeout(() => {
                closeEditCatsModal();
            }, 1000);
        } catch (e) {
            err.textContent = e.message || 'Error al guardar';
            err.style.display = 'block';
        } finally {
            btnGuardar.disabled = false;
            btnGuardar.textContent = 'Guardar Categorías';
        }
    };

    document.getElementById('menuEditCats')?.addEventListener('click', openEditCatsModal);
    document.getElementById('closeEditCats')?.addEventListener('click', closeEditCatsModal);
    document.getElementById('btnCancelEditCats')?.addEventListener('click', closeEditCatsModal);
    document.getElementById('btnGuardarCats')?.addEventListener('click', saveEditCats);

    // Acción de logout desde el dropdown
    const doLogout = async (e) => {
        if (e) e.preventDefault();
        
        // Registrar silenciosamente abandono de sesión en Auditoría antes de limpiar currentUser
        if (window.currentUser) {
            try {
                await fetch('/api/logout', { 
                    method: 'POST', 
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ event: 'logout_manual' })
                });
            } catch(error) {}
        }

        currentUser = null;
        window.currentUser = null;
        loginEmail.value = '';
        loginPassword.value = '123';
        loginError.style.display = 'none';
        document.getElementById('accountsList').innerHTML = '';
        document.getElementById('ingresosBreakdown').innerHTML = '';
        document.getElementById('egresosBreakdown').innerHTML = '';
        document.getElementById('totalIngresos').innerText = '$0';
        document.getElementById('totalEgresos').innerText = '$0';
        document.getElementById('balanceActual').innerText = '$0';
        document.getElementById('userInfoCard').style.display = 'none';
        document.getElementById('saldoActions').style.display = 'none';
        document.getElementById('chartsSection').style.display = 'none';
        document.getElementById('evolutionChartSection').style.display = 'none';
        document.getElementById('globalTimeWindowContainer').style.display = 'none';
        if (chartIngresos) chartIngresos.destroy();
        if (chartEgresos) chartEgresos.destroy();
        if (chartEvolucion) chartEvolucion.destroy();
        loginOverlay.classList.add('active');
        loginEmail.focus();
    };

    dropdownLogout.addEventListener('click', doLogout);
    // También mantener compatibilidad con el navLogout (oculto en sidebar)
    navLogout.addEventListener('click', doLogout);

    // Fecha en el header
    const today = new Date();
    const dateStr = today.toLocaleDateString('es-ES', { day: 'numeric', month: 'short', year: 'numeric' }).toUpperCase();
    document.getElementById('dateLabel').textContent = `SALDO DISPONIBLE (${dateStr})`;

    // Inicializar categorías en los selectores de los modales
    function fillSelect(selectId, items) {
        const sel = document.getElementById(selectId);
        sel.innerHTML = '';
        items.forEach(cat => {
            const opt = document.createElement('option');
            opt.value = cat;
            opt.textContent = cat;
            sel.appendChild(opt);
        });
    }
    fillSelect('ingresoCategory', categorias_ingreso);

    // fillSelect('egresoCategory', categorias_egreso); // Se hará dinámicamente al abrir modal

    const CAT_TRANSFERENCIA = 'Transferencia a la Comunidad Académica';

    // Reaccionar al cambio de categoría en el egreso
    document.getElementById('egresoCategory').addEventListener('change', function () {
        const esTransferenciaModal = document.getElementById('modalEgreso').dataset.isTransfer === 'true';
        const esTransferCat = this.value === CAT_TRANSFERENCIA;
        const isTransferMode = esTransferenciaModal || esTransferCat;
        document.getElementById('cuentaDestinoWrapper').style.display = isTransferMode ? 'block' : 'none';
        document.getElementById('egresoAmountLabel').textContent = isTransferMode ? 'Monto a Transferir' : 'Monto Ejecutado';
        document.getElementById('saveEgresoLabel').textContent = isTransferMode ? 'Ejecutar Transferencia' : 'Registrar Gasto';
    });

    // ---- Modal Ingreso ----
    const modalIngreso = document.getElementById('modalIngreso');
    document.getElementById('closeIngreso').addEventListener('click', () => closeModalIngreso());
    document.getElementById('cancelIngreso').addEventListener('click', () => closeModalIngreso());
    modalIngreso.addEventListener('click', e => { if (e.target === modalIngreso) closeModalIngreso(); });

    // Filter Logic for Ingreso Destino
    const searchIngreso = document.getElementById('cuentaDestinoIngresoSearch');
    if (searchIngreso) {
        searchIngreso.addEventListener('input', function (e) {
            const term = e.target.value.toLowerCase();
            const select = document.getElementById('cuentaDestinoIngreso');
            if (!select) return;

            Array.from(select.options).forEach(opt => {
                if (opt.value === "") return;
                const match = opt.textContent.toLowerCase().includes(term);
                opt.style.display = match ? '' : 'none';
            });

            Array.from(select.querySelectorAll('optgroup')).forEach(grp => {
                const visibleOpts = Array.from(grp.querySelectorAll('option')).filter(o => o.style.display !== 'none');
                grp.style.display = visibleOpts.length > 0 ? '' : 'none';
            });
        });
    }

    document.getElementById('saveIngreso').addEventListener('click', () => {
        let id = document.getElementById('ingresoAccountId').value;
        const msgEl = document.getElementById('ingresoMsg');

        const category = document.getElementById('ingresoCategory').value;
        const amount = parseAmountInput(document.getElementById('ingresoAmount').value);

        const rawFecha = document.getElementById('ingresoFecha').value;
        let fechaDb = null;
        if (rawFecha) {
            fechaDb = rawFecha.replace('T', ' ') + ':00';
        }

        const desc = document.getElementById('ingresoReferencia').value || '';
        if (isNaN(amount) || amount <= 0) {
            showModalMsg(msgEl, 'Monto inválido. Ingrese un valor mayor a 0.', 'error');
            return;
        }

        fetch(`/api/cuentas/${id}/transaccion`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tipo: 'ingreso', categoria: category, monto: amount, fecha: fechaDb, justificacion: desc })
        })
            .then(res => res.json())
            .then(data => {
                if (data.error) { showModalMsg(msgEl, 'Error: ' + data.error, 'error'); return; }
                showModalMsg(msgEl, '✓ Traslado registrado correctamente.', 'success');
                fetchData();
                setTimeout(() => closeModalIngreso(), 1200);
            })
            .catch(() => showModalMsg(msgEl, 'Error al conectar con el servidor.', 'error'));
    });

    // ---- Modal Egreso ----
    const modalEgreso = document.getElementById('modalEgreso');
    document.getElementById('closeEgreso').addEventListener('click', () => closeModalEgreso());
    document.getElementById('cancelEgreso').addEventListener('click', () => closeModalEgreso());
    modalEgreso.addEventListener('click', e => { if (e.target === modalEgreso) closeModalEgreso(); });

    // Filter Logic for Egreso Destino
    const searchEgreso = document.getElementById('cuentaDestinoSearch');
    if (searchEgreso) {
        searchEgreso.addEventListener('input', function (e) {
            const term = e.target.value.toLowerCase();
            const select = document.getElementById('cuentaDestino');
            if (!select) return;

            Array.from(select.options).forEach(opt => {
                if (opt.value === "") return;
                const match = opt.textContent.toLowerCase().includes(term);
                opt.style.display = match ? '' : 'none';
            });

            Array.from(select.querySelectorAll('optgroup')).forEach(grp => {
                const visibleOpts = Array.from(grp.querySelectorAll('option')).filter(o => o.style.display !== 'none');
                grp.style.display = visibleOpts.length > 0 ? '' : 'none';
            });
        });
    }

    // ---- Modal Movimientos ----
    const modalMovimientos = document.getElementById('modalMovimientos');
    if (document.getElementById('closeMovimientos')) {
        document.getElementById('closeMovimientos').addEventListener('click', () => closeModalMovimientos());
    }
    if (document.getElementById('cancelMovimientos')) {
        document.getElementById('cancelMovimientos').addEventListener('click', () => closeModalMovimientos());
    }
    if (modalMovimientos) {
        modalMovimientos.addEventListener('click', e => { if (e.target === modalMovimientos) closeModalMovimientos(); });
    }

    document.getElementById('saveEgreso').addEventListener('click', () => {
        const id = document.getElementById('egresoAccountId').value;
        const category = document.getElementById('egresoCategory').value;
        const amount = parseAmountInput(document.getElementById('egresoAmount').value);
        const msgEl = document.getElementById('egresoMsg');
        const esTransferencia = document.getElementById('modalEgreso').dataset.isTransfer === 'true';

        const rawFecha = document.getElementById('egresoFecha').value;
        let fechaDb = null;
        if (rawFecha) {
            fechaDb = rawFecha.replace('T', ' ') + ':00';
        }

        if (isNaN(amount) || amount <= 0) {
            showModalMsg(msgEl, 'Monto inválido. Ingrese un valor mayor a 0.', 'error');
            return;
        }

        const justificacion = document.getElementById('egresoJustificacion').value || '';

        // Validar que el monto no supere el saldo disponible
        const saldoActual = currentUser ? (currentUser.saldo || 0) : 0;
        if (amount > saldoActual) {
            showModalMsg(msgEl, `Saldo insuficiente. Disponible: $${formatNumber(saldoActual)}`, 'error');
            return;
        }

        // Para transferencias: validar que se seleccionó cuenta destino
        const destId = document.getElementById('cuentaDestino')?.value;
        if (esTransferencia && !destId) {
            showModalMsg(msgEl, 'Seleccione una cuenta destino para la transferencia.', 'error');
            return;
        }

        // 1. Registrar el EGRESO en la cuenta origen
        fetch(`/api/cuentas/${id}/transaccion`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tipo: 'egreso', categoria: category, monto: amount, fecha: fechaDb, justificacion: justificacion })
        })
            .then(res => res.json())
            .then(data => {
                if (data.error) { showModalMsg(msgEl, 'Error al debitar: ' + data.error, 'error'); return; }

                if (esTransferencia && destId) {
                    // 2. Registrar el INGRESO en la cuenta destino
                    fetch(`/api/cuentas/${destId}/transaccion`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            tipo: 'ingreso',
                            categoria: category,
                            monto: amount,
                            fecha: fechaDb,
                            justificacion: justificacion
                        })
                    })
                        .then(r => r.json())
                        .then(d2 => {
                            if (d2.error) {
                                showModalMsg(msgEl, '⚠ Débito OK, error al acreditar: ' + d2.error, 'error');
                            } else {
                                showModalMsg(msgEl, '✓ Transferencia realizada correctamente.', 'success');
                                fetchData();
                                setTimeout(() => closeModalEgreso(), 1200);
                            }
                        })
                        .catch(() => showModalMsg(msgEl, 'Error al acreditar en cuenta destino.', 'error'));
                } else {
                    showModalMsg(msgEl, '✓ Gasto registrado correctamente.', 'success');
                    fetchData();
                    setTimeout(() => closeModalEgreso(), 1200);
                }
            })
            .catch(() => showModalMsg(msgEl, 'Error al conectar con el servidor.', 'error'));
    });


    // Helpers para los modales
    function showModalMsg(el, msg, type) {
        el.textContent = msg;
        el.className = 'modal-msg ' + type;
        el.style.display = 'block';
    }

    function closeModalIngreso() {
        const m = document.getElementById('modalIngreso');
        m.classList.remove('active');
        document.getElementById('ingresoAmount').value = '';
        document.getElementById('ingresoReferencia').value = '';
        const destInput = document.getElementById('cuentaDestinoIngreso');
        if (destInput) destInput.value = '';
        const searchInput = document.getElementById('cuentaDestinoIngresoSearch');
        if (searchInput) searchInput.value = '';
        const msgEl = document.getElementById('ingresoMsg');
        msgEl.style.display = 'none';
    }

    function closeModalEgreso() {
        const m = document.getElementById('modalEgreso');
        m.classList.remove('active');
        document.getElementById('egresoAmount').value = '';
        document.getElementById('egresoJustificacion').value = '';
        const searchInput = document.getElementById('cuentaDestinoSearch');
        if (searchInput) searchInput.value = '';
        const destInput = document.getElementById('cuentaDestino');
        if (destInput) destInput.value = '';
        const msgEl = document.getElementById('egresoMsg');
        msgEl.style.display = 'none';
    }

    window.openIngresoModal = async function (event, accountId, isRootGlobal = false) {
        event.stopPropagation();
        document.getElementById('ingresoAccountId').value = accountId;
        document.getElementById('ingresoAmount').value = '';
        document.getElementById('ingresoReferencia').value = '';
        document.getElementById('ingresoMsg').style.display = 'none';

        // Poblado de categorías dinámico
        const catSelect = document.getElementById('ingresoCategory');
        if (catSelect) {
            catSelect.innerHTML = '';
            categorias_ingreso.forEach(cat => {
                const opt = document.createElement('option');
                opt.value = cat;
                opt.textContent = cat;
                catSelect.appendChild(opt);
            });
        }

        const now = new Date();
        const tzOffset = now.getTimezoneOffset() * 60000;
        document.getElementById('ingresoFecha').value = new Date(now - tzOffset).toISOString().slice(0, 16);

        const wrapper = document.getElementById('cuentaDestinoIngresoWrapper');
        wrapper.style.display = 'none';

        document.getElementById('modalIngreso').classList.add('active');
    };

    window.openEgresoModal = async function (event, accountId, isTransfer = false) {
        event.stopPropagation();
        document.getElementById('egresoAccountId').value = accountId;
        document.getElementById('egresoAmount').value = '';
        document.getElementById('egresoJustificacion').value = '';
        document.getElementById('egresoMsg').style.display = 'none';

        const now = new Date();
        const tzOffset = now.getTimezoneOffset() * 60000;
        document.getElementById('egresoFecha').value = new Date(now - tzOffset).toISOString().slice(0, 16);

        const dynHeader = document.getElementById('dynamicEgresoHeader');
        const btnSave = document.getElementById('saveEgreso');
        const dynTitle = document.getElementById('dynamicEgresoTitle');
        const dynIcon = document.getElementById('dynamicEgresoIcon');

        // Actualizar diseño del modal: azul para transferencias, rojo para egresos
        if (isTransfer) {
            dynHeader.className = 'modal-type-header transferencia-header';
            btnSave.className = 'btn-modal-transferencia';
            if (dynTitle) dynTitle.textContent = 'TRANSFERENCIA DE SALDO';
            if (dynIcon) dynIcon.innerHTML = '<polyline points="17 1 21 5 17 9"></polyline><path d="M3 11V9a4 4 0 0 1 4-4h14"></path><polyline points="7 23 3 19 7 15"></polyline><path d="M21 13v2a4 4 0 0 1-4 4H3"></path>';
        } else {
            dynHeader.className = 'modal-type-header egreso-header';
            btnSave.className = 'btn-modal-egreso';
            if (dynTitle) dynTitle.textContent = 'REGISTRO DE GASTOS / EJECUCIÓN';
            if (dynIcon) dynIcon.innerHTML = '<path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" /><polyline points="14 2 14 8 20 8" /><line x1="12" x2="12" y1="18" y2="12" /><polyline points="9 15 12 18 15 15" />';
        }

        document.getElementById('modalEgreso').dataset.isTransfer = isTransfer;

        // Configurar opciones de categoría según si es transferencia o no
        const categorySelect = document.getElementById('egresoCategory');
        categorySelect.innerHTML = '';

        if (isTransfer) {
            categorias_transferencias.forEach(cat => {
                const opt = document.createElement('option');
                opt.value = cat;
                opt.textContent = cat;
                categorySelect.appendChild(opt);
            });
            if (categorySelect.options.length > 0) categorySelect.value = categorySelect.options[0].value;
        } else {
            categorias_egreso.forEach(cat => {
                if (cat !== CAT_TRANSFERENCIA) {
                    const opt = document.createElement('option');
                    opt.value = cat;
                    opt.textContent = cat;
                    categorySelect.appendChild(opt);
                }
            });
            categorySelect.value = categorySelect.options[0].value;
        }

        // Despachar evento para que la UI (etiquetas y campos) se actualice (mostrar/ocultar destino)
        categorySelect.dispatchEvent(new Event('change'));

        // Poblar selector de cuentas destino incorporando a TODOS
        const destSelect = document.getElementById('cuentaDestino');
        destSelect.innerHTML = '<option value="">Cargando cuentas...</option>';

        // Asegurar que las cuentas del sistema estén cargadas
        if (systemAccounts.length === 0) {
            try {
                const res = await fetch('/api/cuentas');
                const data = await res.json();
                if (data.message === 'success') {
                    systemAccounts = (data.data || []);
                }
            } catch (err) {
                console.error('Error fetching system accounts:', err);
            }
        }

        destSelect.innerHTML = '<option value="">— Seleccione una cuenta —</option>';

        // Usar systemAccounts para disponer de todas las cuentas, con fallback a allAccounts
        const sourceAccounts = systemAccounts.length > 0 ? systemAccounts : allAccounts;

        const validAccounts = sourceAccounts
            .filter(a => a.id !== parseInt(accountId))
            .sort((a, b) => (a.nombre_cuenta || '').localeCompare(b.nombre_cuenta || '', 'es'));

        const grouped = validAccounts.reduce((accMap, acc) => {
            const t = (acc.tipo || 'Sin Tipo').toUpperCase();
            if (!accMap[t]) accMap[t] = [];
            accMap[t].push(acc);
            return accMap;
        }, {});

        // Ordenar alfabéticamente los nombres de los grupos
        const keys = Object.keys(grouped).sort((a, b) => a.localeCompare(b, 'es'));

        keys.forEach(tipo => {
            const optgroup = document.createElement('optgroup');
            optgroup.label = tipo;
            grouped[tipo].forEach(a => {
                const opt = document.createElement('option');
                opt.value = a.id;
                opt.textContent = `${a.nombre_cuenta}  (${a.cuenta_eafit})`;
                optgroup.appendChild(opt);
            });
            destSelect.appendChild(optgroup);
        });

        const searchInput = document.getElementById('cuentaDestinoSearch');
        if (searchInput) {
            searchInput.value = '';
            // Trigger filter in case there are changes from before
            searchInput.dispatchEvent(new Event('input'));
        }

        document.getElementById('modalEgreso').classList.add('active');
    };

    function closeModalMovimientos() {
        if (document.getElementById('modalMovimientos')) {
            document.getElementById('modalMovimientos').classList.remove('active');
        }
    }

    window.openMovimientosModal = async function (event, accountId) {
        event.stopPropagation();

        const tableBody = document.getElementById('movimientosTableBody');
        const emptyMsg = document.getElementById('movimientosEmpty');
        const txCountEl = document.getElementById('movimientosCount');
        tableBody.innerHTML = '<tr><td colspan="4" style="text-align:center; padding: 20px;">Cargando movimientos...</td></tr>';
        emptyMsg.style.display = 'none';
        txCountEl.textContent = '0 movimientos';

        document.getElementById('modalMovimientos').classList.add('active');

        try {
            const res = await fetch(`/api/cuentas/${accountId}/transacciones`);
            const data = await res.json();

            if (data.message === 'success' && data.data && data.data.length > 0) {
                window._modalMovData = data.data; // Store for ticket printing
                tableBody.innerHTML = '';
                txCountEl.textContent = `${data.data.length} movimiento${data.data.length !== 1 ? 's' : ''}`;
                data.data.forEach((tx, idx) => {
                    const row = document.createElement('tr');
                    if (idx % 2 === 0) row.style.background = 'rgba(248, 250, 252, 0.5)';

                    // Format date
                    let dateStr = tx.fecha || '';
                    if (dateStr.includes('T')) dateStr = dateStr.replace('T', ' ');
                    if (dateStr.indexOf('.') > -1) dateStr = dateStr.split('.')[0];
                    const dateParts = dateStr.split(' ');
                    const datePart = dateParts[0] || '—';
                    const timePart = dateParts[1] || '';

                    const isIngreso = tx.tipo === 'ingreso';
                    const amountClass = isIngreso ? 'val-income' : 'val-expense';
                    const sign = isIngreso ? '+ ' : '− ';

                    const isRoot = window.currentUser && window.currentUser.cuenta_eafit === 'root_ctei@eafit.edu.co';
                    let estadoHtml = '—';
                    if (tx.tipo === 'egreso' && tx.estado) {
                        let color = '#f59e0b'; // pending/generado
                        let normState = tx.estado;
                        if (normState === 'generado') normState = 'solicitada';
                        if (normState === 'aceptado') normState = 'aprobada';
                        if (normState === 'rechazado') normState = 'rechazada';

                        if (normState === 'aprobada') color = '#10b981';
                        if (normState === 'rechazada') color = '#ef4444';
                        if (normState === 'en estudio') color = '#3b82f6';
                        if (normState === 'en ejecución') color = '#8b5cf6';
                        if (normState === 'terminada') color = '#14b8a6';

                        estadoHtml = `<div style="text-align:center;"><span style="color:${color};font-size:11px;font-weight:700;text-transform:uppercase;border:1px solid ${color};padding:2px 6px;border-radius:10px;display:inline-block;margin-bottom:4px;">${normState}</span>`;

                        let current_date = tx.fecha;
                        try {
                            if (tx.historial_estados) {
                                const h = JSON.parse(tx.historial_estados);
                                const k = tx.estado;
                                if (h[k] && h[k].fecha) current_date = h[k].fecha;
                                else if (h[normState] && h[normState].fecha) current_date = h[normState].fecha;
                                else {
                                    const dates = Object.values(h).map(x => x.fecha).sort();
                                    if (dates.length) current_date = dates[dates.length - 1];
                                }
                            }
                        } catch(e) {}
                        if (current_date) {
                            let dAcc = current_date.replace('T', ' ');
                            if (dAcc.indexOf('.') > -1) dAcc = dAcc.split('.')[0];
                            estadoHtml += `<div style="font-size:10px;color:var(--text-muted);margin-bottom:4px;white-space:nowrap;">Date: ${dAcc.split(' ')[0]}</div>`;
                        }

                        // Acciones - Flow Buttons Card & Timeline (Read-only in Movimientos Modal)
                        estadoHtml += getFlowButtonsHtml(tx.id, tx.estado, tx.historial_estados, false);
                        estadoHtml += `</div>`;
                    }

                    row.innerHTML = `
                        <td>
                            <div style="font-size:13px;font-weight:600;color:var(--text-primary);">${datePart}</div>
                            <div style="font-size:11px;color:var(--text-muted);margin-top:2px;">${timePart}</div>
                        </td>
                        <td><span class="tx-badge ${tx.tipo}">${tx.tipo}</span></td>
                        <td>
                            <div style="color:var(--text-secondary);font-size:13.5px;">${tx.categoria || '—'}</div>
                            ${tx.justificacion ? `<div style="font-size:11px;color:var(--text-muted);margin-top:2px;max-width:250px;white-space:normal;">Ref: ${tx.justificacion}</div>` : ''}
                        </td>
                        <td style="text-align:right;font-size:15px;font-variant-numeric:tabular-nums;" class="${amountClass}">
                            ${sign}$${formatNumber(tx.monto)}
                        </td>
                        <td style="text-align:center; vertical-align:middle;">${estadoHtml}</td>
                    `;
                    tableBody.appendChild(row);
                });
            } else {
                tableBody.innerHTML = '';
                emptyMsg.style.display = 'block';
                txCountEl.textContent = '0 movimientos';
            }
        } catch (err) {
            console.error('Error fetching transactions', err);
            tableBody.innerHTML = '';
            emptyMsg.style.display = 'block';
            emptyMsg.textContent = 'Error al cargar los movimientos.';
        }
    };

    // --- Estado de la tabla ---
    let allAccounts = [];       // todas las cuentas del usuario (jerarquía dependiente)
    let systemAccounts = [];    // todas las cuentas en BD (transferibles al 100%)
    let allHierarchy = {};      // jerarquía completa
    // Expose globally for Informe section
    window.allAccounts = allAccounts;
    window.allHierarchy = allHierarchy;
    let currentSort = { col: '', dir: 1 };  // columna activa y dirección

    function fetchData(targetCuentaId = null) {
        window.fetchData = fetchData; // Make it globally accessible
        if (!currentUser) return;

        const fetchId = targetCuentaId || currentUser.id;
        const userQueryParam = fetchId ? `?cuenta_id=${fetchId}` : '';

        // 1. Cuentas
        fetch(`/api/cuentas${userQueryParam}`)
            .then(res => res.json())
            .then(data => {
                if (data.message === 'success') {
                    allAccounts = (data.data || []);
                    allHierarchy = data.hierarchy || {};
                    // Expose globally for section views
                    window.allAccounts = allAccounts;
                    window.allHierarchy = allHierarchy;
                    populateFilterTipo(allAccounts);
                    applyTableFilters();
                }
            })
            .catch(err => console.error('Error fetching data:', err));

        // 2. Resumen
        fetch(`/api/resumen${userQueryParam}`)
            .then(res => res.json())
            .then(data => {
                if (data.message === 'success') renderSummary(data.data);
            });

        // 3. Transacciones Históricas (Evolución)
        fetch(`/api/transacciones${userQueryParam}`)
            .then(res => res.json())
            .then(data => {
                if (data.message === 'success') {
                    allTransacciones = data.data;
                    renderEvolutionChart(allTransacciones, globalWindow);
                }
            });

        // 3. Sistema general de cuentas (Para el modal de transferencias)
        if (systemAccounts.length === 0) {
            fetch('/api/cuentas')
                .then(res => res.json())
                .then(data => {
                    if (data.message === 'success') {
                        systemAccounts = (data.data || []);
                    }
                })
                .catch(err => console.error('Error fetching system accounts:', err));
        }
    }

    // Rellena el selector de tipo con los valores únicos del conjunto actual
    function populateFilterTipo(accounts) {
        const sel = document.getElementById('filterTipo');
        const prev = sel.value;
        const tipos = [...new Set(accounts.map(a => a.tipo || 'Sin tipo').filter(Boolean))].sort();
        sel.innerHTML = '<option value="">Todos los tipos</option>';
        tipos.forEach(t => {
            const opt = document.createElement('option');
            opt.value = t;
            opt.textContent = t;
            sel.appendChild(opt);
        });
        if (tipos.includes(prev)) sel.value = prev;
    }

    // Aplica búsqueda + filtro de tipo + ordenamiento y re-renderiza
    function applyTableFilters() {
        const search = (document.getElementById('searchInput')?.value || '').toLowerCase();
        const tipo = document.getElementById('filterTipo')?.value || '';

        let filtered = allAccounts.filter(a => {
            const matchSearch = !search ||
                (a.cuenta_eafit || '').toLowerCase().includes(search) ||
                (a.nombre_cuenta || '').toLowerCase().includes(search);
            const matchTipo = !tipo || (a.tipo || 'Sin tipo') === tipo;
            return matchSearch && matchTipo;
        });

        // Ordenamiento
        if (currentSort.col) {
            filtered.sort((a, b) => {
                let va = a[currentSort.col] ?? '';
                let vb = b[currentSort.col] ?? '';
                if (typeof va === 'number') return (va - vb) * currentSort.dir;
                return String(va).localeCompare(String(vb), 'es') * currentSort.dir;
            });
        }

        renderAccountsList(filtered);

        // Contador
        const countEl = document.getElementById('rowCount');
        if (countEl) countEl.textContent = `${filtered.length} registro${filtered.length !== 1 ? 's' : ''}`;
    }

    // Inicializa eventos de búsqueda, filtro y sort (se llama 1 vez al login)
    function initTableControls() {
        document.getElementById('searchInput')?.addEventListener('input', applyTableFilters);
        document.getElementById('filterTipo')?.addEventListener('change', applyTableFilters);

        document.querySelectorAll('.th-sortable').forEach(th => {
            th.addEventListener('click', () => {
                const col = th.dataset.col;
                if (currentSort.col === col) {
                    currentSort.dir *= -1;
                } else {
                    currentSort.col = col;
                    currentSort.dir = 1;
                }
                // Actualizar clases visuales
                document.querySelectorAll('.th-sortable').forEach(h => {
                    h.classList.remove('sort-asc', 'sort-desc');
                    h.querySelector('.sort-icon').textContent = '⇅';
                });
                th.classList.add(currentSort.dir === 1 ? 'sort-asc' : 'sort-desc');
                th.querySelector('.sort-icon').textContent = currentSort.dir === 1 ? '↑' : '↓';
                applyTableFilters();
            });
        });
    }

    function renderBreadcrumb() {
        // Ya no se usa la navegación drillDown, se mantiene por compatibilidad
    }

    function renderAccountsList(accounts) {
        const listContainer = document.getElementById('accountsList');
        listContainer.innerHTML = '';

        if (!accounts || accounts.length === 0) {
            listContainer.innerHTML = `
            <div style="padding: 48px 32px; text-align: center; color: var(--text-muted);">
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                    stroke-width="1.5" style="margin-bottom:12px; opacity:0.4;">
                    <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
                </svg>
                <div style="font-size:15px; font-weight:500;">Sin resultados</div>
                <div style="font-size:13px; margin-top:4px;">Intenta con otro término de búsqueda</div>
            </div>`;
            return;
        }

        // Agrupar por tipo para separadores visuales
        const groupedAccounts = accounts.reduce((map, acc) => {
            const t = acc.tipo || 'Sin tipo';
            if (!map[t]) map[t] = [];
            map[t].push(acc);
            return map;
        }, {});

        // Solo mostrar grupos si NO hay búsqueda/filtro activo para no fragmentar
        const search = (document.getElementById('searchInput')?.value || '').toLowerCase();
        const tipo = document.getElementById('filterTipo')?.value || '';
        const showGroups = !search && !tipo;

        if (showGroups) {
            const orderMap = {
                'escuela': 1,
                'área': 2,
                'grupo de investigación': 3,
                'investigador': 4
            };

            Object.keys(groupedAccounts).sort((a, b) => {
                const keyA = (a || '').trim().toLowerCase();
                const keyB = (b || '').trim().toLowerCase();
                const orderA = orderMap[keyA] || 99;
                const orderB = orderMap[keyB] || 99;
                if (orderA !== orderB) return orderA - orderB;
                return a.localeCompare(b, 'es'); // fallback a alfabético para los no mapeados
            }).forEach(tipoKey => {
                const groupHeader = document.createElement('div');
                groupHeader.className = 'group-header group-header-interactive';
                groupHeader.innerHTML = `
                    <div style="display:flex; align-items:center; gap:8px;">
                        <svg class="group-chevron" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="6 9 12 15 18 9"/>
                        </svg>
                        <h4 style="color: var(--accent-color); margin: 0; font-size: 13px; text-transform: uppercase; letter-spacing: 1px; font-weight: 700;">${tipoKey}</h4>
                    </div>
                    <span style="font-size: 12px; color: var(--text-muted); background: rgba(79,70,229,0.08); padding: 3px 10px; border-radius: 12px; font-weight: 600;">${groupedAccounts[tipoKey].length}</span>
                `;

                const rowsContainer = document.createElement('div');
                rowsContainer.className = 'group-rows-container';
                rowsContainer.style.display = 'none'; // oculto por defecto
                groupedAccounts[tipoKey].forEach(acc => rowsContainer.appendChild(buildRow(acc)));

                groupHeader.addEventListener('click', () => {
                    groupHeader.classList.toggle('expanded');
                    if (groupHeader.classList.contains('expanded')) {
                        rowsContainer.style.display = 'block';
                    } else {
                        rowsContainer.style.display = 'none';
                    }
                });

                listContainer.appendChild(groupHeader);
                listContainer.appendChild(rowsContainer);
            });
        } else {
            accounts.forEach(acc => listContainer.appendChild(buildRow(acc)));
        }
    }

    function getParentName(childId) {
        let parentId = null;
        for (const [cabecera, deps] of Object.entries(allHierarchy)) {
            if (deps.includes(childId)) {
                parentId = cabecera;
                break;
            }
        }
        if (parentId) {
            const p = allAccounts.find(a => a.id == parentId);
            return p ? p.nombre_cuenta : 'Dependencia Principal';
        }
        return '';
    }

    function buildRow(acc) {
        const row = document.createElement('div');
        const isOwn = currentUser && acc.id === currentUser.id;
        row.className = 'account-row' + (isOwn ? ' own-row' : '');

        const saldoClass = acc.saldo >= 0 ? 'val-saldo' : 'val-expense';
        row.innerHTML = `
        <div class="account-name" title="${acc.nombre_cuenta}">
            <div>${acc.nombre_cuenta}</div>
        </div>
        <div class="amount-col val-income">$${formatNumber(acc.ingresos)}</div>
        <div class="amount-col val-expense">$${formatNumber(acc.egresos)}</div>
        <div class="amount-col ${saldoClass}">$${formatNumber(acc.saldo)}</div>
    `;
        return row;
    }

    function renderSummary(summaryData) {
        animateValue('totalIngresos', summaryData.ingresos || 0);
        animateValue('totalEgresos', summaryData.egresos || 0);
        animateValue('balanceActual', summaryData.saldo || 0);

        // Sincronizar saldo actual en currentUser para validaciones (egreso)
        if (currentUser) {
            currentUser.saldo = summaryData.saldo || 0;
            currentUser.ingresos = summaryData.ingresos || 0;
            currentUser.egresos = summaryData.egresos || 0;
        }

        const breakdown = summaryData.breakdown || [];

        const ingresadosMap = {};
        const egresadosMap = {};

        breakdown.forEach(item => {
            if (item.tipo === 'ingreso') ingresadosMap[item.categoria] = item.total;
            else if (item.tipo === 'egreso') egresadosMap[item.categoria] = item.total;
        });

        document.getElementById('ingresosBreakdown').innerHTML = buildBreakdownHTML(categorias_ingreso, ingresadosMap);
        document.getElementById('egresosBreakdown').innerHTML = buildBreakdownHTML(categorias_egreso, egresadosMap);

        // Usar transacciones si ya están cargadas (para respetar ventana global)
        const mapsToUse = allTransacciones.length > 0
            ? computeDistributionMaps(allTransacciones, globalWindow)
            : { ingMap: ingresadosMap, egrMap: egresadosMap };
        renderCharts(mapsToUse.ingMap, mapsToUse.egrMap, globalWindow);

        // Actualizar títulos de las tarjetas de resumen
        const titleSuffix = winLabels[globalWindow] ? ` (${winLabels[globalWindow].toUpperCase()})` : '';
        const ingTitle = document.getElementById('ingresosTitle');
        const egrTitle = document.getElementById('egresosTitle');
        if (ingTitle) ingTitle.textContent = 'INGRESOS TOTALES' + titleSuffix;
        if (egrTitle) egrTitle.textContent = 'SALIDAS TOTALES' + titleSuffix;
    }

    // Genera el HTML de las filas de desglose por categoría (reutilizable)
    function buildBreakdownHTML(categories, dataMap) {
        let html = '';
        categories.forEach(cat => {
            const amount = dataMap[cat] || 0;
            const icon = categoryIcons[cat] || categoryIcons["default"];
            html += `
            <div class="breakdown-row">
                ${icon}
                <span class="breakdown-cat-name">${cat}:</span>
                <span class="breakdown-value">$${formatNumber(amount)}</span>
            </div>
        `;
        });
        return html;
    }

    // ── Calcula ingresadosMap y egresadosMap filtrados por ventana de tiempo ──
    function computeDistributionMaps(transacciones, win) {
        const now = new Date();
        const pad = n => String(n).padStart(2, '0');
        const toDateStr = dt => `${dt.getFullYear()}-${pad(dt.getMonth() + 1)}-${pad(dt.getDate())}`;
        const todayStr = toDateStr(now);

        let windowStartStr;
        if (win === 'all') {
            windowStartStr = '0000-00-00';
        } else if (win === 'ytd') {
            windowStartStr = `${now.getFullYear()}-01-01`;
        } else {
            const daysMap = { '7d': 7, '1m': 30, '3m': 90, '6m': 180 };
            const days = daysMap[win] || 36500;
            const start = new Date(now);
            start.setDate(start.getDate() - (days - 1));
            windowStartStr = toDateStr(start);
        }

        const ingMap = {};
        const egrMap = {};
        transacciones.forEach(tx => {
            const dateStr = (tx.fecha || '').split(' ')[0];
            if (dateStr >= windowStartStr && dateStr <= todayStr) {
                if (tx.tipo === 'ingreso') ingMap[tx.categoria] = (ingMap[tx.categoria] || 0) + Math.abs(tx.monto);
                if (tx.tipo === 'egreso') egrMap[tx.categoria] = (egrMap[tx.categoria] || 0) + Math.abs(tx.monto);
            }
        });
        return { ingMap, egrMap };
    }

    // Inicializa los botones de ventana global
    function initGlobalControls() {
        const container = document.getElementById('globalWindowBtns');
        if (!container) return;
        container.querySelectorAll('[data-window]').forEach(btn => {
            btn.addEventListener('click', () => {
                container.querySelectorAll('[data-window]').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                globalWindow = btn.dataset.window;
                if (allTransacciones.length > 0) {
                    const { ingMap, egrMap } = computeDistributionMaps(allTransacciones, globalWindow);

                    // Calcular totales de la ventana y actualizar tarjetas
                    const totalIng = Object.values(ingMap).reduce((s, v) => s + v, 0);
                    const totalEgr = Object.values(egrMap).reduce((s, v) => s + v, 0);
                    animateValue('totalIngresos', totalIng);
                    animateValue('totalEgresos', totalEgr);

                    // Actualizar títulos de las tarjetas con la fecha
                    const titleSuffix = winLabels[globalWindow] ? ` (${winLabels[globalWindow].toUpperCase()})` : '';
                    const ingTitle = document.getElementById('ingresosTitle');
                    const egrTitle = document.getElementById('egresosTitle');
                    if (ingTitle) ingTitle.textContent = 'INGRESOS TOTALES' + titleSuffix;
                    if (egrTitle) egrTitle.textContent = 'SALIDAS TOTALES' + titleSuffix;

                    // Actualizar desglose por categoría en las tarjetas
                    document.getElementById('ingresosBreakdown').innerHTML = buildBreakdownHTML(categorias_ingreso, ingMap);
                    document.getElementById('egresosBreakdown').innerHTML = buildBreakdownHTML(categorias_egreso, egrMap);

                    // Re-renderizar las gráficas de distribución y evolución
                    renderCharts(ingMap, egrMap, globalWindow);
                    renderEvolutionChart(allTransacciones, globalWindow);
                }
            });
        });
    }

    function renderCharts(ingresadosMap, egresadosMap, win = 'all') {
        // La visibilidad se controla desde showSection ('resumen')
        // document.getElementById('chartsSection').style.display = 'block';

        // Actualizar subtítulo con el período seleccionado
        const subtitle = winLabels[win] || 'Por categoría · acumulado';
        const subIng = document.getElementById('distIngSubtitle');
        const subEgr = document.getElementById('distEgrSubtitle');
        if (subIng) subIng.textContent = subtitle;
        if (subEgr) subEgr.textContent = subtitle;

        // Colores predefinidos para ambas gráficas
        const ingColors = [
            '#4f46e5',  // Indigo
            '#10b981',  // Emerald
            '#f59e0b',  // Amber
            '#06b6d4',  // Cyan
            '#8b5cf6'   // Violet
        ];
        const egColors = [
            '#ef4444',  // Red
            '#f97316',  // Orange
            '#eab308',  // Yellow
            '#ec4899',  // Pink
            '#14b8a6',  // Teal
            '#8b5cf6'   // Violet
        ];

        const doughnutOptions = (total, colors) => ({
            responsive: true,
            maintainAspectRatio: false,
            cutout: '68%',
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        boxWidth: 10,
                        usePointStyle: true,
                        pointStyle: 'circle',
                        padding: 14,
                        font: { size: 11, family: "'Inter', sans-serif" },
                        color: '#4a5568',
                        generateLabels: function (chart) {
                            const data = chart.data;
                            return data.labels.map((label, i) => {
                                const value = data.datasets[0].data[i];
                                const pct = total > 0 ? Math.round(value / total * 100) : 0;
                                const shortLabel = label.length > 22 ? label.substring(0, 20) + '…' : label;
                                return {
                                    text: `${shortLabel}  (${pct}%)`,
                                    fillStyle: data.datasets[0].backgroundColor[i],
                                    strokeStyle: 'transparent',
                                    index: i
                                };
                            });
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            const val = Number(context.raw);
                            const displayVal = total > 0 ? val : 0;
                            const pct = total > 0 ? (val / total * 100).toFixed(1) : 0;
                            return ` $${displayVal.toLocaleString('es-CO', { maximumFractionDigits: 0 })}  (${pct}%)`;
                        }
                    }
                }
            },
            animation: { animateRotate: true, animateScale: true, duration: 600 }
        });

        // Plugin para texto central en doughnut
        const centerTextPlugin = {
            id: 'centerText',
            afterDraw(chart) {
                if (chart.config.type !== 'doughnut') return;
                const { ctx, chartArea: { top, bottom, left, right } } = chart;
                const cx = (left + right) / 2;
                const cy = (top + bottom) / 2;
                
                const isPlaceholder = chart.config.data.labels[0] === 'Sin Ingresos' || chart.config.data.labels[0] === 'Sin Egresos';
                const total = isPlaceholder ? 0 : chart.config.data.datasets[0].data.reduce((s, v) => s + v, 0);
                
                ctx.save();
                if (total > 0) {
                    ctx.font = "700 13px 'Inter', sans-serif";
                    ctx.fillStyle = '#8a94a6';
                    ctx.textAlign = 'center';
                    ctx.fillText('TOTAL', cx, cy - 10);
                    const label = total >= 1000000
                        ? '$' + (total / 1000000).toFixed(1) + 'M'
                        : total >= 1000
                            ? '$' + (total / 1000).toFixed(0) + 'k'
                            : '$' + total;
                    ctx.font = "800 17px 'Inter', sans-serif";
                    ctx.fillStyle = '#0d1b3e';
                    ctx.fillText(label, cx, cy + 12);
                } else {
                    ctx.font = "600 12px 'Inter', sans-serif";
                    ctx.fillStyle = '#8a94a6';
                    ctx.textAlign = 'center';
                    ctx.fillText('Sin datos', cx, cy + 4);
                }
                ctx.restore();
            }
        };

        // ---- Gráfica de INGRESOS ----
        let ingDataPairs = categorias_ingreso.map(cat => ({
            label: cat,
            value: ingresadosMap[cat] || 0
        })).filter(item => item.value > 0).sort((a, b) => b.value - a.value);

        const ingTotal = ingDataPairs.reduce((s, x) => s + x.value, 0);

        if (chartIngresos) chartIngresos.destroy();
        const ctxIng = document.getElementById('ingresosChart').getContext('2d');
        chartIngresos = new Chart(ctxIng, {
            type: 'doughnut',
            data: {
                labels: ingDataPairs.length ? ingDataPairs.map(x => x.label) : ['Sin Ingresos'],
                datasets: [{
                    data: ingDataPairs.length ? ingDataPairs.map(x => x.value) : [1],
                    backgroundColor: ingDataPairs.length ? ingColors.slice(0, ingDataPairs.length) : ['#e4e8f0'],
                    borderWidth: 3,
                    borderColor: '#ffffff',
                    hoverBorderWidth: 2,
                    hoverOffset: 8
                }]
            },
            options: doughnutOptions(ingTotal, ingColors),
            plugins: [centerTextPlugin]
        });

        // ---- Gráfica de EGRESOS ----
        let egDataPairs = categorias_egreso.map(cat => ({
            label: cat,
            value: egresadosMap[cat] || 0
        })).filter(item => item.value > 0).sort((a, b) => b.value - a.value);

        const egTotal = egDataPairs.reduce((s, x) => s + x.value, 0);

        if (chartEgresos) chartEgresos.destroy();
        const ctxEg = document.getElementById('egresosChart').getContext('2d');
        chartEgresos = new Chart(ctxEg, {
            type: 'doughnut',
            data: {
                labels: egDataPairs.length ? egDataPairs.map(x => x.label) : ['Sin Egresos'],
                datasets: [{
                    data: egDataPairs.length ? egDataPairs.map(x => x.value) : [1],
                    backgroundColor: egDataPairs.length ? egColors.slice(0, egDataPairs.length) : ['#e4e8f0'],
                    borderWidth: 3,
                    borderColor: '#ffffff',
                    hoverBorderWidth: 2,
                    hoverOffset: 8
                }]
            },
            options: doughnutOptions(egTotal, egColors),
            plugins: [centerTextPlugin]
        });
    }

    // Funciones Gráfica de Evolución
    // window: '7d' | '1m' | '3m' | '6m' | 'ytd' | 'all'
    function renderEvolutionChart(transacciones, window = 'ytd') {
        const ctx = document.getElementById('evolucionSaldoChart');
        if (!ctx) return;
        // La visibilidad se controla desde showSection ('resumen')
        // document.getElementById('evolutionChartSection').style.display = 'block';

        if (chartEvolucion) {
            chartEvolucion.destroy();
        }

        let runningBalance = 0;
        const now = new Date();

        // ── Helpers ───────────────────────────────────────────────────────────
        const pad = n => String(n).padStart(2, '0');
        const toDateStr = dt => `${dt.getFullYear()}-${pad(dt.getMonth() + 1)}-${pad(dt.getDate())}`;
        const todayStr = toDateStr(now);

        // ── Rango de visualización según ventana ─────────────────────────────
        let windowStartStr;
        if (window === 'all') {
            // Primera fecha registrada (transacciones ya llegan ordenadas ASC)
            const dates = transacciones.map(t => (t.fecha || '').split(' ')[0]).filter(Boolean).sort();
            windowStartStr = dates.length ? dates[0] : `${now.getFullYear()}-01-01`;
        } else if (window === 'ytd') {
            windowStartStr = `${now.getFullYear()}-01-01`;
        } else {
            const daysMap = { '7d': 7, '1m': 30, '3m': 90, '6m': 180 };
            const days = daysMap[window] || 365;
            const start = new Date(now);
            start.setDate(start.getDate() - (days - 1));
            windowStartStr = toDateStr(start);
        }

        // ── Saldo acumulado ANTES del inicio de la ventana ───────────────────
        transacciones.forEach(tx => {
            const dateStr = (tx.fecha || '').split(' ')[0];
            if (dateStr < windowStartStr) {
                if (tx.tipo === 'ingreso') runningBalance += Math.abs(tx.monto);
                if (tx.tipo === 'egreso') runningBalance -= Math.abs(tx.monto);
            }
        });

        const labels = [];
        const balances = [];
        const ingresosArr = [];
        const egresosArr = [];

        // ── Buckets diarios dentro de la ventana visible ─────────────────────
        let groupedByDate = {};
        let d = new Date(windowStartStr + 'T00:00:00');
        const endDate = new Date(todayStr + 'T00:00:00');
        while (d <= endDate) {
            const dStr = toDateStr(d);
            groupedByDate[dStr] = { ingreso: 0, egreso: 0 };
            d.setDate(d.getDate() + 1);
        }

        transacciones.forEach(tx => {
            const dateStr = (tx.fecha || '').split(' ')[0];
            if (dateStr >= windowStartStr && dateStr <= todayStr) {
                if (groupedByDate[dateStr]) {
                    if (tx.tipo === 'ingreso') groupedByDate[dateStr].ingreso += Math.abs(tx.monto);
                    if (tx.tipo === 'egreso') groupedByDate[dateStr].egreso += Math.abs(tx.monto);
                }
            }
        });

        const sortedDates = Object.keys(groupedByDate).sort();

        sortedDates.forEach(date => {
            const rec = groupedByDate[date];
            runningBalance += (rec.ingreso - rec.egreso);
            labels.push(date);
            balances.push(runningBalance);
            ingresosArr.push(rec.ingreso);
            egresosArr.push(rec.egreso);
        });

        // Color adaptativo: verde si saldo positivo, rojo si negativo
        const lastBalance = balances.length ? balances[balances.length - 1] : 0;
        const lineColor = lastBalance >= 0 ? '#10b981' : '#ef4444';
        const fillColorTop = lastBalance >= 0 ? 'rgba(16, 185, 129, 0.20)' : 'rgba(239, 68, 68, 0.20)';
        const fillColorBot = lastBalance >= 0 ? 'rgba(16, 185, 129, 0.00)' : 'rgba(239, 68, 68, 0.00)';

        // Plugin: degradado bajo la curva
        const gradientFillPlugin = {
            id: 'gradientFill',
            beforeDatasetDraw(chart) {
                const { ctx: c, chartArea } = chart;
                if (!chartArea) return;
                const gradient = c.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
                gradient.addColorStop(0, fillColorTop);
                gradient.addColorStop(1, fillColorBot);
                if (chart.data.datasets[0]) chart.data.datasets[0].backgroundColor = gradient;
            }
        };

        // Plugin: línea vertical (crosshair) al hacer hover
        const crosshairPlugin = {
            id: 'crosshair',
            afterDatasetsDraw(chart) {
                const { ctx: c, tooltip, chartArea } = chart;
                if (!tooltip || !tooltip._active || !tooltip._active.length) return;
                const x = tooltip._active[0].element.x;
                c.save();
                c.beginPath();
                c.moveTo(x, chartArea.top);
                c.lineTo(x, chartArea.bottom);
                c.lineWidth = 1.5;
                c.strokeStyle = 'rgba(100, 100, 130, 0.35)';
                c.setLineDash([4, 4]);
                c.stroke();
                c.restore();
            }
        };

        const fmtMoney = v => {
            const abs = Math.abs(v);
            if (abs >= 1000000) return (v < 0 ? '-' : '') + '$' + (abs / 1000000).toFixed(2) + 'M';
            if (abs >= 1000) return (v < 0 ? '-' : '') + '$' + (abs / 1000).toFixed(1) + 'k';
            return '$' + v.toLocaleString('es-CO', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
        };

        chartEvolucion = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels.length ? labels : ['Aún no hay transacciones'],
                datasets: [
                    {
                        label: 'Saldo Neto Acumulado',
                        data: balances.length ? balances : [0],
                        borderColor: lineColor,
                        backgroundColor: fillColorTop,
                        borderWidth: 2.5,
                        fill: true,
                        tension: 0.4,
                        pointRadius: balances.map((v, i) =>
                            (ingresosArr[i] > 0 || egresosArr[i] > 0) ? 4 : 0
                        ),
                        pointHoverRadius: 7,
                        pointBackgroundColor: '#ffffff',
                        pointBorderColor: lineColor,
                        pointBorderWidth: 2.5,
                        yAxisID: 'y'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        align: 'start',
                        labels: {
                            usePointStyle: true,
                            pointStyle: 'circle',
                            boxWidth: 8,
                            font: { size: 12, family: "'Inter', sans-serif", weight: '600' },
                            color: '#374151'
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(15, 23, 42, 0.92)',
                        titleColor: '#e2e8f0',
                        bodyColor: '#cbd5e1',
                        padding: 12,
                        cornerRadius: 10,
                        titleFont: { size: 12, weight: '700' },
                        bodyFont: { size: 12 },
                        callbacks: {
                            title: items => items[0]?.label || '',
                            label: function (context) {
                                const i = context.dataIndex;
                                const bal = balances[i] ?? 0;
                                const ing = ingresosArr[i] ?? 0;
                                const egr = egresosArr[i] ?? 0;
                                const lines = [`  Saldo acumulado : ${fmtMoney(bal)}`];
                                if (ing > 0) lines.push(`  ▲ Ingresos hoy  : +${fmtMoney(ing)}`);
                                if (egr > 0) lines.push(`  ▼ Egresos hoy   : -${fmtMoney(egr)}`);
                                return lines;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        type: 'linear',
                        position: 'left',
                        title: { display: true, text: 'Saldo Neto Acumulado ($)', color: '#6b7280', font: { size: 11 } },
                        grid: { color: 'rgba(243, 244, 246, 0.8)' },
                        ticks: { color: '#6b7280', callback: v => fmtMoney(v) }
                    },
                    x: {
                        grid: { display: false },
                        title: { display: true, text: 'Fecha', color: '#6b7280', font: { size: 11 } },
                        ticks: { color: '#9ca3af', maxTicksLimit: 12, font: { size: 11 } }
                    }
                }
            },
            plugins: [gradientFillPlugin, crosshairPlugin]
        });
    }

    function formatNumber(num) {
        if (num === null || num === undefined || isNaN(num)) return '0';
        return Number(num).toLocaleString('es-CO', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
    }

    // Parse input con k y m
    function parseAmountInput(val) {
        if (!val) return 0;
        let str = String(val).trim().replace(/,/g, ''); // Quitar comas si las hay
        let multiplier = 1;
        if (str.toLowerCase().endsWith('k')) {
            multiplier = 1000;
            str = str.slice(0, -1);
        } else if (str.toLowerCase().endsWith('m')) {
            multiplier = 1000000;
            str = str.slice(0, -1);
        }
        const parsed = parseFloat(str);
        if (isNaN(parsed)) return 0;
        return Math.floor(parsed * multiplier);
    }

    function openModal(account) {
        const overlay = document.getElementById('modalOverlay');
        const accountNameEl = document.getElementById('modalAccountName');
        const accountEmailEl = document.getElementById('modalAccountEmail');
        const accountIdEl = document.getElementById('accountId');
        const amountEl = document.getElementById('transAmount');
        const typeEl = document.getElementById('transType');

        accountNameEl.textContent = account.nombre_cuenta;
        accountEmailEl.textContent = account.cuenta_eafit;
        accountIdEl.value = account.id;
        amountEl.value = '';

        // Reset defaults
        typeEl.value = 'ingreso';
        typeEl.dispatchEvent(new Event('change'));

        overlay.style.display = 'flex';
        setTimeout(() => {
            overlay.classList.add('active');
            amountEl.focus();
        }, 10);
    }

    function closeModal() {
        const overlay = document.getElementById('modalOverlay');
        overlay.classList.remove('active');
        setTimeout(() => {
            overlay.style.display = 'none';
        }, 300);
    }

    // Micro-animation for values updating
    function animateValue(id, end, duration = 500) {
        const obj = document.getElementById(id);
        let startTimestamp = null;

        let currentText = obj.innerText.replace(/[^0-9.-]+/g, "");
        let start = parseFloat(currentText);
        if (isNaN(start)) start = 0;

        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            const currentVal = start + progress * (end - start);
            obj.innerText = '$' + formatNumber(currentVal);

            if (progress < 1) {
                window.requestAnimationFrame(step);
            } else {
                // End exactly
                obj.innerText = '$' + formatNumber(end);
            }
        };
        window.requestAnimationFrame(step);
    }
}); // cierre DOMContentLoaded

window.getFlowButtonsHtml = function(txId, currentState, historialStr, isRoot = true) {
    const linearFlow = ['solicitada', 'en estudio', 'aprobada', 'en ejecución', 'terminada'];
    const icons = {
        'solicitada': '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>',
        'en estudio': '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>',
        'aprobada': '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg>',
        'rechazada': '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>',
        'en ejecución': '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
        'terminada': '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>'
    };
    const labels = {
        'solicitada': 'Solicitud',
        'en estudio': 'Estudio',
        'aprobada': 'Aprobación',
        'rechazada': 'Rechazado',
        'en ejecución': 'Ejecución',
        'terminada': 'Terminada'
    };
    const stateColors = {
        'solicitada': '#f59e0b',
        'en estudio': '#3b82f6',
        'aprobada': '#10b981',
        'rechazada': '#ef4444',
        'en ejecución': '#8b5cf6',
        'terminada': '#14b8a6'
    };
    
    let normState = currentState;
    if (currentState === 'generado') normState = 'solicitada';
    if (currentState === 'aceptado') normState = 'aprobada';
    if (currentState === 'rechazado') normState = 'rechazada';

    // Parse History
    let histCount = 0;
    let entries = [];
    try {
        if (historialStr) {
            const h = JSON.parse(historialStr);
            entries = Object.keys(h).map(state => ({
                state,
                fecha: h[state].fecha, // Keep standard format mm/dd/yyyy if possible
                comentario: h[state].comentario
            })).sort((a,b) => a.fecha.localeCompare(b.fecha));
        }
    } catch(e) {}
    histCount = entries.length;

    // Stepper UI
    let stepperHtml = `<div style="display:flex; justify-content:space-between; align-items:flex-start; position:relative; margin: 6px 15px 20px 15px;">`;
    stepperHtml += `<div style="position:absolute; top:12px; left:0; right:0; height:2px; background:#e2e8f0; z-index:0;"></div>`;
    
    const currentIndex = linearFlow.indexOf(normState === 'rechazada' ? 'aprobada' : normState);

    linearFlow.forEach((stepState, i) => {
        const isCurrent = (normState === stepState) || (normState === 'rechazada' && stepState === 'aprobada');
        const isPast = currentIndex > i || isCurrent;
        const isRechazadoNode = isCurrent && normState === 'rechazada';
        
        const actualStateOfNode = (stepState === 'aprobada' && isRechazadoNode) ? 'rechazada' : stepState;
        
        const baseColor = stateColors[actualStateOfNode];
        
        // Colors mapping logic:
        // Future steps: gray outline, white bg, gray icon
        // Past steps: solid color outline, white bg, solid color icon
        // Current step: solid color outline, solid color bg, white icon
        let bgColor = '#fff';
        let borderColor = '#cbd5e1';
        let iconColor = '#94a3b8';
        let bWidth = '2px';
        let scaleStyle = 'scale(1)';
        
        if (isPast) {
            borderColor = baseColor;
            iconColor = baseColor;
        }
        if (isCurrent) {
            bgColor = baseColor + '1A'; // Fondo difuminado tenue (10% opacidad)
            iconColor = baseColor;
            borderColor = baseColor;
            bWidth = '2.5px'; // Borde un poco más grueso para destacarlo
            scaleStyle = 'scale(1.35)'; // Marcador agrandado
        }

        const onClickAttr = (isRoot && !(stepState === 'aprobada' && normState === 'en estudio')) ? `onclick="cambiarEstado(${txId}, '${actualStateOfNode}')"` : '';
        const cursorStyle = (isRoot && !(stepState === 'aprobada' && normState === 'en estudio')) ? 'pointer' : 'default';

        stepperHtml += `<div style="display:flex; flex-direction:column; align-items:center; z-index:1; position:relative;" title="${labels[actualStateOfNode]}">`;
        stepperHtml += `<button ${onClickAttr} style="width:26px; height:26px; border-radius:50%; border:${bWidth} solid ${borderColor}; background:${bgColor}; color:${iconColor}; display:flex; align-items:center; justify-content:center; padding:0; cursor:${cursorStyle}; transform:${scaleStyle}; transition:all 0.25s cubic-bezier(0.4, 0, 0.2, 1);">
            ${icons[actualStateOfNode]}
        </button>`;
        stepperHtml += `</div>`;
    });
    stepperHtml += `</div>`;

    // Branching and progression explicit action buttons for root user
    let branchHtml = '';
    if (isRoot) {
        if (normState === 'solicitada') {
            const btnColor = stateColors['en estudio'];
            branchHtml = `<div style="display:flex; justify-content:center; align-items:center; gap:12px; margin-bottom:12px; margin-top:12px;">
               <span style="font-size:11.5px; font-weight:700; color:#64748b;">Próximo evento:</span>
               <button onclick="cambiarEstado(${txId}, 'en estudio')" style="font-size:12.5px; padding:8px 24px; border-radius:24px; background:${btnColor}; color:white; border:none; cursor:pointer; font-weight:700; box-shadow:0 6px 16px ${btnColor}80; display:flex; align-items:center; gap:8px; transition:all 0.2s cubic-bezier(0.4, 0, 0.2, 1); will-change:transform,box-shadow;" onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 8px 20px ${btnColor}99';" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 6px 16px ${btnColor}80';"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg> En Estudio</button>
            </div>`;
        } else if (normState === 'en estudio') {
            const btnOk = stateColors['aprobada'];
            const btnNo = stateColors['rechazada'];
            branchHtml = `<div style="display:flex; justify-content:center; align-items:center; gap:12px; margin-bottom:12px; margin-top:12px;">
               <span style="font-size:11.5px; font-weight:700; color:#64748b;">Próximo evento:</span>
               <button onclick="cambiarEstado(${txId}, 'aprobada')" style="font-size:12.5px; padding:8px 24px; border-radius:24px; background:${btnOk}; color:white; border:none; cursor:pointer; font-weight:700; box-shadow:0 6px 16px ${btnOk}80; display:flex; align-items:center; gap:8px; transition:all 0.2s cubic-bezier(0.4, 0, 0.2, 1); will-change:transform,box-shadow;" onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 8px 20px ${btnOk}99';" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 6px 16px ${btnOk}80';"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg> Aprobada</button>
               <button onclick="cambiarEstado(${txId}, 'rechazada')" style="font-size:12.5px; padding:8px 24px; border-radius:24px; background:${btnNo}; color:white; border:none; cursor:pointer; font-weight:700; box-shadow:0 6px 16px ${btnNo}80; display:flex; align-items:center; gap:8px; transition:all 0.2s cubic-bezier(0.4, 0, 0.2, 1); will-change:transform,box-shadow;" onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 8px 20px ${btnNo}99';" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 6px 16px ${btnNo}80';"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg> Rechazada</button>
            </div>`;
        } else if (normState === 'aprobada' || normState === 'aceptado') {
            const btnColor = stateColors['en ejecución'];
            branchHtml = `<div style="display:flex; justify-content:center; align-items:center; gap:12px; margin-bottom:12px; margin-top:12px;">
               <span style="font-size:11.5px; font-weight:700; color:#64748b;">Próximo evento:</span>
               <button onclick="cambiarEstado(${txId}, 'en ejecución')" style="font-size:12.5px; padding:8px 24px; border-radius:24px; background:${btnColor}; color:white; border:none; cursor:pointer; font-weight:700; box-shadow:0 6px 16px ${btnColor}80; display:flex; align-items:center; gap:8px; transition:all 0.2s cubic-bezier(0.4, 0, 0.2, 1); will-change:transform,box-shadow;" onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 8px 20px ${btnColor}99';" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 6px 16px ${btnColor}80';"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg> En Ejecución</button>
            </div>`;
        } else if (normState === 'en ejecución') {
            const btnColor = stateColors['terminada'];
            branchHtml = `<div style="display:flex; justify-content:center; align-items:center; gap:12px; margin-bottom:12px; margin-top:12px;">
               <span style="font-size:11.5px; font-weight:700; color:#64748b;">Próximo evento:</span>
               <button onclick="cambiarEstado(${txId}, 'terminada')" style="font-size:12.5px; padding:8px 24px; border-radius:24px; background:${btnColor}; color:white; border:none; cursor:pointer; font-weight:700; box-shadow:0 6px 16px ${btnColor}80; display:flex; align-items:center; gap:8px; transition:all 0.2s cubic-bezier(0.4, 0, 0.2, 1); will-change:transform,box-shadow;" onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 8px 20px ${btnColor}99';" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 6px 16px ${btnColor}80';"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg> Terminada</button>
            </div>`;
        }
    }

    // History Log (Accordion/Details visible for every user)
    let histHtml = '';
    if (histCount > 0) {
        histHtml = `<details style="text-align: left; font-size: 10.5px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; overflow: hidden; margin-top: 8px;">`;
        histHtml += `<summary style="padding: 6px 10px; cursor: pointer; color: #475569; font-weight: 600; outline: none; user-select: none;">Ver Historial (${histCount})</summary>`;
        histHtml += `<div style="padding: 0 10px 8px 10px; border-top: 1px solid #e2e8f0;">`;
        entries.forEach((e) => {
            const dateStr = e.fecha.replace('T', ' '); // Format string
            histHtml += `<div style="margin-top:6px;">`;
            histHtml += `<div style="display:flex; justify-content:space-between; margin-bottom: 2px;">
                <strong style="text-transform:capitalize; color: ${stateColors[e.state] || '#334155'};">${e.state}</strong>
                <span style="color:#94a3b8; font-size:9px;">${dateStr}</span>
            </div>`;
            if (e.comentario) {
                histHtml += `<div style="color:#475569; background:#fff; border-left:2px solid ${stateColors[e.state] || '#cbd5e1'}; padding:4px 6px; font-style:italic; border-radius: 0 4px 4px 0;">"${e.comentario}"</div>`;
            }
            histHtml += `</div>`;
        });
        histHtml += `</div></details>`;
    }

    // Theme color based on normalized state for the outer container highlight
    const themeColor = stateColors[normState] || '#e2e8f0';

    // Wrap everything
    let html = `<div style="position: relative; width: fit-content; min-width: 320px; max-width: 100%; margin: 6px auto; background: white; padding: 12px 20px; border-radius: 12px; border: 1.5px solid ${themeColor}50; box-shadow: 0 8px 20px ${themeColor}20; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); border-top: 3px solid ${themeColor};">`;
    html += stepperHtml;
    html += branchHtml;
    
    // Bottom Section for History and PDF
    html += `<div style="display:flex; justify-content:space-between; align-items:flex-end; gap:8px;">`;
    html += `<div style="flex:1;">${histHtml}</div>`;
    html += `<button onclick="imprimirTicket(${txId})" style="flex-shrink:0; align-self:${histCount > 0 ? 'flex-end' : 'center'}; font-size:9px; padding:5px 8px; cursor:pointer; background:#f8fafc; color:#475569; border:1px solid #cbd5e1; border-radius:6px; font-weight:600; box-shadow:0 1px 2px rgba(0,0,0,0.02); display:flex; align-items:center; gap:4px; transition:all 0.2s; margin-top:8px; line-height:1;" title="Generar Ticket PDF">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg> PDF
    </button>`;
    html += `</div>`;
    
    html += `</div>`;

    return html;
};

// -- Tickets global functions --
window.cambiarEstado = async function (txId, nuevoEstado) {
    // Helper to request comment via Custom Modal instead of native prompt
    const obtenerComentario = () => {
        return new Promise((resolve) => {
            let modal = document.getElementById('customEstadoModal');
            if (!modal) {
                modal = document.createElement('div');
                modal.id = 'customEstadoModal';
                modal.style.position = 'fixed';
                modal.style.top = '0';
                modal.style.left = '0';
                modal.style.width = '100%';
                modal.style.height = '100%';
                modal.style.backgroundColor = 'rgba(15, 23, 42, 0.6)';
                modal.style.backdropFilter = 'blur(2px)';
                modal.style.zIndex = '9999';
                modal.style.display = 'none';
                modal.style.justifyContent = 'center';
                modal.style.alignItems = 'center';
                modal.style.opacity = '0';
                modal.style.transition = 'opacity 0.2s ease';
                
                modal.innerHTML = `
                    <div style="background:white; border-radius:12px; padding:24px; width:400px; max-width:90%; box-shadow:0 10px 25px rgba(0,0,0,0.1); transform: scale(0.95); transition: transform 0.2s ease;">
                        <h2 style="margin-top:0; font-size:18px; color:#1e293b; margin-bottom: 6px;">Actualizar Trámite</h2>
                        <p style="font-size:14px; color:#64748b; margin-bottom: 20px; line-height:1.4;">Vas a registrar esta etapa en el flujo como <strong id="modalEstadoText" style="text-transform:uppercase; color:#3b82f6;"></strong>.</p>
                        
                        <label style="display:block; font-size:13px; font-weight:600; color:#475569; margin-bottom:8px;">Observaciones o Justificación (Opcional)</label>
                        <textarea id="modalEstadoComentario" rows="3" style="width:100%; padding:10px; border:1px solid #cbd5e1; border-radius:8px; font-family:inherit; font-size:13px; resize:vertical; box-sizing: border-box; outline:none;" placeholder="Escribe aquí los motivos o detalles de la confirmación..."></textarea>
                        
                        <div style="display:flex; justify-content:flex-end; gap:10px; margin-top:24px;">
                            <button id="modalEstadoCancel" style="padding:8px 16px; border:none; background:#f1f5f9; color:#475569; border-radius:6px; cursor:pointer; font-weight:600; font-size:13px; transition: background 0.2s;">Cancelar</button>
                            <button id="modalEstadoConfirm" style="padding:8px 16px; border:none; background:#3b82f6; color:white; border-radius:6px; cursor:pointer; font-weight:600; font-size:13px; transition: background 0.2s; box-shadow:0 1px 2px rgba(59,130,246,0.3);">Confirmar Cambio</button>
                        </div>
                    </div>
                `;
                document.body.appendChild(modal);

                // Add hover effects manually
                const cancelBtn = modal.querySelector('#modalEstadoCancel');
                cancelBtn.onmouseenter = () => cancelBtn.style.background = '#e2e8f0';
                cancelBtn.onmouseleave = () => cancelBtn.style.background = '#f1f5f9';

                const confirmBtn = modal.querySelector('#modalEstadoConfirm');
                confirmBtn.onmouseenter = () => confirmBtn.style.background = '#2563eb';
                confirmBtn.onmouseleave = () => confirmBtn.style.background = '#3b82f6';
            }

            // Define state colors to colorize the keyword
            const stateColors = {
                'solicitada': '#f59e0b',
                'en estudio': '#3b82f6',
                'aprobada': '#10b981',
                'rechazada': '#ef4444',
                'en ejecución': '#8b5cf6',
                'terminada': '#14b8a6'
            };

            const textEl = document.getElementById('modalEstadoText');
            textEl.innerText = nuevoEstado;
            textEl.style.color = stateColors[nuevoEstado] || '#3b82f6';
            
            const textArea = document.getElementById('modalEstadoComentario');
            textArea.value = '';

            // Show animation
            modal.style.display = 'flex';
            setTimeout(() => {
                modal.style.opacity = '1';
                modal.firstElementChild.style.transform = 'scale(1)';
            }, 10);
            textArea.focus();

            const close = (val) => {
                modal.style.opacity = '0';
                modal.firstElementChild.style.transform = 'scale(0.95)';
                setTimeout(() => modal.style.display = 'none', 200);
                resolve(val);
            };

            document.getElementById('modalEstadoCancel').onclick = () => close(null);
            document.getElementById('modalEstadoConfirm').onclick = () => close(textArea.value);
        });
    };

    const comentario = await obtenerComentario();
    if (comentario === null) return; // User clicked Cancel

    try {
        const res = await fetch(`/api/transacciones/${txId}/estado`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ estado: nuevoEstado, comentario: comentario })
        });
        const data = await res.json();

        if (data.error) {
            // Replace generic alert too for consistency
            alert('Error: ' + data.error);
        } else {
            // Toast notification instead of alert (Optional but better UX)
            const toast = document.createElement('div');
            toast.innerText = 'Trámite actualizado correctamente';
            toast.style.cssText = 'position:fixed; bottom:20px; right:20px; background:#10b981; color:white; padding:12px 20px; border-radius:8px; font-weight:600; font-size:14px; box-shadow:0 4px 12px rgba(16,185,129,0.3); z-index:9999; animation: slideIn 0.3s ease-out;';
            document.body.appendChild(toast);
            setTimeout(() => {
                toast.style.opacity = '0';
                toast.style.transition = 'opacity 0.3s';
                setTimeout(() => toast.remove(), 300);
            }, 2500);

            if (!document.getElementById('toastKeyframes')) {
                const style = document.createElement('style');
                style.id = 'toastKeyframes';
                style.innerHTML = `@keyframes slideIn { from { transform: translateY(20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }`;
                document.head.appendChild(style);
            }

            if (window.currentUser) {
                try {
                    if (window.showSection && document.getElementById('sectionMovimientos').style.display !== 'none') {
                        await loadMovimientosSection();
                    } else if (document.getElementById('modalMovimientos')?.classList.contains('active')) {
                        await openMovimientosModal(new Event('click'), window.currentUser.id);
                    } else if (window.showSection && document.getElementById('sectionAprobaciones').style.display !== 'none') {
                        await window.loadAprobacionesSection();
                    }
                } catch (e) {
                    console.error("Error refreshing section:", e);
                }
                const fetchId = window.currentUser.id;
                fetch(`/api/resumen?cuenta_id=${fetchId}`)
                    .then(r => r.json())
                    .then(d => {
                        if (d.message === 'success') {
                            if (typeof window.fetchData === 'function') {
                                window.fetchData();
                            } else {
                                console.warn("fetchData is not globally accessible, cannot refresh summary in background.");
                            }
                        }
                    });
            }
        }
    } catch (err) {
        alert('Error conectando al servidor: ' + err.message);
    }
};

window.imprimirTicket = async function (txId) {
    // Find transaction from _movData or _modalMovData
    let tx = null;
    if (typeof _movData !== 'undefined' && _movData.length > 0) {
        tx = _movData.find(t => t.id === txId);
    }
    if (!tx && window._modalMovData) {
        tx = window._modalMovData.find(t => t.id === txId);
    }
    if (!tx && window._aproData) {
        tx = window._aproData.find(t => t.id === txId);
    }

    if (!tx) {
        alert('Por favor recargue los datos para generar el PDF (tx.id=' + txId + ')');
        return;
    }

    const formatNumberLocal = (num) => {
        if (num === null || num === undefined) return '0';
        return Number(num).toLocaleString('es-CO', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
    };

    let historyHtml = '';
    if (tx.historial_estados) {
        try {
            const h = JSON.parse(tx.historial_estados);
            const entries = Object.keys(h).map(state => ({
                state,
                fecha: h[state].fecha,
                comentario: h[state].comentario
            })).sort((a,b) => a.fecha.localeCompare(b.fecha));
            
            if (entries.length > 0) {
                historyHtml = `<div style="margin-top: 30px; border-top: 1px solid #e2e8f0; padding-top: 20px;">
                    <h3 style="color: #334155; font-size: 14px; margin-bottom: 15px;">Trazabilidad del Trámite</h3>
                    <div style="padding-left: 10px; border-left: 2px solid #cbd5e1; margin-left: 5px;">`;
                
                entries.forEach(e => {
                    historyHtml += `<div style="margin-bottom: 12px; position:relative;">
                        <div style="position:absolute; left:-15px; top:4px; width:8px; height:8px; border-radius:50%; background:#1a3a8f;"></div>
                        <div style="display: flex; justify-content: space-between;">
                            <span style="font-weight: bold; text-transform: capitalize; color: #1e293b; font-size: 13px;">${e.state}</span>
                            <span style="color: #64748b; font-size: 11px;">${e.fecha.replace('T', ' ')}</span>
                        </div>`;
                    if (e.comentario) {
                        historyHtml += `<div style="margin-top: 4px; font-style: italic; color: #475569; font-size: 12px; background: #f8fafc; padding: 6px; border-radius: 4px; border-left: 2px solid #cbd5e1;">"${e.comentario}"</div>`;
                    }
                    historyHtml += `</div>`;
                });
                historyHtml += `</div></div>`;
            }
        } catch(e) {}
    }

    const htmlContent = `
        <html>
        <head>
            <title>Ticket Operación #${txId}</title>
            <style>
                body { font-family: 'Inter', sans-serif; padding: 20px; color: #1e293b; max-width: 600px; margin: 0 auto; border: 1px solid #e2e8f0; border-radius: 8px; margin-top: 40px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
                h1 { color: #1a3a8f; text-align: center; border-bottom: 2px solid #e2e8f0; padding-bottom: 15px; margin-bottom: 20px; font-size: 20px; }
                .row { display: flex; justify-content: space-between; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid #f1f5f9; font-size: 14px; }
                .label { font-weight: bold; color: #64748b; }
                .val { font-weight: 600; text-align: right; }
                .monto { font-size: 24px; color: #ef4444; font-weight: bold; text-align: center; margin: 20px 0; }
                .estado { text-align: center; margin-top: 15px; font-weight: bold; padding: 10px; border-radius: 6px; font-size: 14px; color: white; }
                .footer {text-align: center; font-size: 11px; margin-top: 50px; color: gray; border-top: 1px solid #e2e8f0; padding-top: 20px;}
                @media print {
                    body { border: none; margin-top: 0; box-shadow: none; }
                }
            </style>
        </head>
        <body onload="window.print(); window.setTimeout(() => window.close(), 500);">
            <div style="text-align: center; margin-bottom: 20px;">
                <img src="/Monoliticos-Vicerrectoria_Azul.png" alt="Vicerrectoría CTeI" style="max-height: 50px; object-fit: contain;" onerror="this.style.display='none'" />
            </div>
            
            <h1>Ticket de Egreso #${tx.id}</h1>
            <div class="monto">$ ${formatNumberLocal(tx.monto)}</div>
            
            <div class="row">
                <span class="label">Cuenta:</span>
                <span class="val">${tx.nombre_cuenta || window.currentUser?.nombre_cuenta || 'Desconocida'}</span>
            </div>
            <div class="row">
                <span class="label">Categoría:</span>
                <span class="val">${tx.categoria || '-'}</span>
            </div>
            <div class="row">
                <span class="label">Fecha Generación:</span>
                <span class="val">${tx.fecha || '-'}</span>
            </div>
            
            <div class="estado" style="background: ${tx.estado === 'rechazada' || tx.estado === 'rechazado' ? '#ef4444' : (tx.estado === 'terminada' ? '#14b8a6' : (tx.estado === 'aprobada' || tx.estado === 'aceptado' ? '#10b981' : '#3b82f6'))}">
                ESTADO ACTUAL: ${String(tx.estado || 'DESCONOCIDO').toUpperCase()}
            </div>
            
            ${historyHtml}
            
            <div class="footer">
                Fondo CTeI - Sistema de Gestión<br/>
                Generado el ${new Date().toLocaleString()}
            </div>
        </body>
        </html>
    `;

    const printWindow = window.open('', '_blank');
    if (printWindow) {
        printWindow.document.write(htmlContent);
        printWindow.document.close();
    } else {
        alert("Por favor permita las ventanas emergentes (pop-ups) para generar el PDF.");
    }
};

window.editTransactionAmount = async function(id, currentAmount) {
    if (!window.currentUser || window.currentUser.cuenta_eafit !== 'root_ctei@eafit.edu.co') return;

    const val = await window.asyncPrompt('Editar Monto', 'Modifica el monto de este movimiento. Si corresponde a una transferencia, el sistema ajustará automáticamente ambas cuentas.', `$${currentAmount.toLocaleString('es-CO')}`);
    if (val === null || val.trim() === '') return;
    
    // Parse Colombian currency formatting: dots for thousands, commas for decimals
    let cleanVal = val.replace(/\./g, '');         // Remove thousands dots
    cleanVal = cleanVal.replace(/,/g, '.');          // Convert decimal comma to dot
    const floatVal = parseFloat(cleanVal);
    
    if (isNaN(floatVal) || floatVal < 0) {
        alert('Monto inválido.');
        return;
    }

    try {
        const res = await fetch(`/api/transacciones/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ monto: floatVal })
        });
        const d = await res.json();
        if (d.error) throw new Error(d.error);
        
        // Headless refresh to maintain Root Session active
        if (window.fetchData) window.fetchData();
        if (window.loadAprobacionesSection) window.loadAprobacionesSection();
        if (window.loadMovimientosSection) window.loadMovimientosSection();
    } catch(e) {
        alert("Error editando monto: " + e.message);
    }
};

window.deleteTransactionData = async function(id) {
    if (!window.currentUser || window.currentUser.cuenta_eafit !== 'root_ctei@eafit.edu.co') return;

    const confirmed = await window.asyncConfirm('¿Eliminar transacción?', 'Se borrará físicamente el registro (y sus clones en la cuenta destino si aplica). Esta acción recalculará los totales permanentemente y no se puede deshacer.');
    if (!confirmed) return;

    try {
        const res = await fetch(`/api/transacciones/${id}`, {
            method: 'DELETE'
        });
        const d = await res.json();
        if (d.error) throw new Error(d.error);

        // Headless refresh to maintain Root Session active
        if (window.fetchData) window.fetchData();
        if (window.loadAprobacionesSection) window.loadAprobacionesSection();
        if (window.loadMovimientosSection) window.loadMovimientosSection();
    } catch(e) {
        alert("Error eliminando transacción: " + e.message);
    }
};

window.asyncPrompt = function(title, message, defaultValue) {
    return new Promise((resolve) => {
        const overlay = document.createElement('div');
        overlay.style.cssText = `
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(15,23,42,0.5); backdrop-filter: blur(4px);
            z-index: 9999; display: flex; align-items: center; justify-content: center;
            opacity: 0; transition: opacity 0.2s ease-out;
        `;
        
        const card = document.createElement('div');
        card.style.cssText = `
            background: #fff; border-radius: 16px; 
            box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1), 0 10px 10px -5px rgba(0,0,0,0.04);
            width: 400px; max-width: 90%; overflow: hidden;
            transform: translateY(15px) scale(0.95); opacity: 0;
            transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
        `;
        
        card.innerHTML = `
            <div style="padding:24px;border-bottom:1px solid #f1f5f9;">
                <h3 style="margin:0;font-size:18px;font-weight:700;color:#0f172a;display:flex;align-items:center;gap:10px;">
                    <div style="background:var(--accent-light);color:var(--accent-color);border-radius:8px;padding:6px;display:flex;align-items:center;justify-content:center;">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
                    </div>
                    ${title}
                </h3>
                <p style="margin:10px 0 0;font-size:13.5px;color:#64748b;line-height:1.5;">${message}</p>
            </div>
            <div style="padding:24px;">
                <input type="text" id="promptInputVal" value="${defaultValue}" style="width:100%;padding:12px 16px;border:1px solid #cbd5e1;border-radius:8px;font-size:16px;font-weight:500;color:#1e293b;outline:none;transition:border-color 0.2s, box-shadow 0.2s; box-sizing:border-box;" autocomplete="off" />
            </div>
            <div style="padding:16px 24px;background:#f8fafc;display:flex;justify-content:flex-end;gap:12px;border-top:1px solid #e2e8f0;">
                <button id="promptCancelBtn" style="padding:9px 18px;border-radius:8px;font-size:13.5px;font-weight:600;border:none;background:#e2e8f0;color:#475569;cursor:pointer;transition:all 0.2s;">Cancelar</button>
                <button id="promptConfirmBtn" style="padding:9px 18px;border-radius:8px;font-size:13.5px;font-weight:600;border:none;background:var(--accent-color,#3b82f6);color:#fff;cursor:pointer;transition:all 0.2s;box-shadow:0 2px 8px rgba(59,130,246,0.3);">Guardar</button>
            </div>
        `;

        overlay.appendChild(card);
        document.body.appendChild(overlay);

        requestAnimationFrame(() => {
            overlay.style.opacity = '1';
            card.style.transform = 'translateY(0) scale(1)';
            card.style.opacity = '1';
        });

        const inputEl = card.querySelector('#promptInputVal');
        const btnCancel = card.querySelector('#promptCancelBtn');
        const btnConfirm = card.querySelector('#promptConfirmBtn');

        inputEl.addEventListener('focus', () => {
            inputEl.style.borderColor = 'var(--accent-color)';
            inputEl.style.boxShadow = '0 0 0 3px rgba(59, 130, 246, 0.15)';
        });
        inputEl.addEventListener('blur', () => {
            inputEl.style.borderColor = '#cbd5e1';
            inputEl.style.boxShadow = 'none';
        });

        setTimeout(() => {
            inputEl.focus();
            inputEl.setSelectionRange(0, inputEl.value.length);
        }, 200);

        const close = (val) => {
            overlay.style.opacity = '0';
            card.style.transform = 'translateY(10px) scale(0.95)';
            card.style.opacity = '0';
            setTimeout(() => {
                if (document.body.contains(overlay)) document.body.removeChild(overlay);
                resolve(val);
            }, 200);
        };

        btnCancel.addEventListener('click', () => close(null));
        btnCancel.onmouseover = () => btnCancel.style.background = '#cbd5e1';
        btnCancel.onmouseout = () => btnCancel.style.background = '#e2e8f0';
        
        btnConfirm.addEventListener('click', () => close(inputEl.value));
        btnConfirm.onmouseover = () => btnConfirm.style.transform = 'translateY(-1px)';
        btnConfirm.onmouseout = () => btnConfirm.style.transform = 'translateY(0)';

        inputEl.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') close(inputEl.value);
            if (e.key === 'Escape') close(null);
        });
    });
};

window.asyncConfirm = function(title, message) {
    return new Promise((resolve) => {
        const overlay = document.createElement('div');
        overlay.style.cssText = `
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(15,23,42,0.5); backdrop-filter: blur(4px);
            z-index: 9999; display: flex; align-items: center; justify-content: center;
            opacity: 0; transition: opacity 0.2s ease-out;
        `;
        
        const card = document.createElement('div');
        card.style.cssText = `
            background: #fff; border-radius: 16px; 
            box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1), 0 10px 10px -5px rgba(0,0,0,0.04);
            width: 400px; max-width: 90%; overflow: hidden;
            transform: translateY(15px) scale(0.95); opacity: 0;
            transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
        `;
        
        card.innerHTML = `
            <div style="padding:32px 24px 24px;text-align:center;">
                <div style="width:56px;height:56px;background:rgba(239, 68, 68, 0.1);color:#ef4444;border-radius:50%;display:flex;align-items:center;justify-content:center;margin:0 auto 20px;">
                    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"></path><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>
                </div>
                <h3 style="margin:0;font-size:19px;font-weight:700;color:#0f172a;">
                    ${title}
                </h3>
                <p style="margin:12px 0 0;font-size:14px;color:#64748b;line-height:1.6;">${message}</p>
            </div>
            <div style="padding:16px 24px;background:#f8fafc;display:flex;justify-content:center;gap:12px;border-top:1px solid #e2e8f0;">
                <button id="confirmCancelBtn" style="padding:10px 24px;border-radius:8px;font-size:14px;font-weight:600;border:none;background:#e2e8f0;color:#475569;cursor:pointer;transition:all 0.2s;">Cancelar</button>
                <button id="confirmAcceptBtn" style="padding:10px 24px;border-radius:8px;font-size:14px;font-weight:600;border:none;background:#ef4444;color:#fff;cursor:pointer;transition:all 0.2s;box-shadow:0 4px 12px rgba(239,68,68,0.2);">Eliminar</button>
            </div>
        `;

        overlay.appendChild(card);
        document.body.appendChild(overlay);

        requestAnimationFrame(() => {
            overlay.style.opacity = '1';
            card.style.transform = 'translateY(0) scale(1)';
            card.style.opacity = '1';
        });

        const btnCancel = card.querySelector('#confirmCancelBtn');
        const btnAccept = card.querySelector('#confirmAcceptBtn');

        btnCancel.onmouseover = () => btnCancel.style.background = '#cbd5e1';
        btnCancel.onmouseout = () => btnCancel.style.background = '#e2e8f0';
        
        btnAccept.onmouseover = () => {
            btnAccept.style.background = '#dc2626';
            btnAccept.style.transform = 'translateY(-1px)';
        };
        btnAccept.onmouseout = () => {
            btnAccept.style.background = '#ef4444';
            btnAccept.style.transform = 'translateY(0)';
        };

        const close = (val) => {
            overlay.style.opacity = '0';
            card.style.transform = 'translateY(10px) scale(0.95)';
            card.style.opacity = '0';
            setTimeout(() => {
                if (document.body.contains(overlay)) document.body.removeChild(overlay);
                resolve(val);
            }, 200);
        };

        btnCancel.addEventListener('click', () => close(false));
        btnAccept.addEventListener('click', () => close(true));
        
        setTimeout(() => btnCancel.focus(), 200);

        window.addEventListener('keydown', function onKey(e) {
            if (e.key === 'Escape') {
                window.removeEventListener('keydown', onKey);
                close(false);
            }
        });
    });
};
