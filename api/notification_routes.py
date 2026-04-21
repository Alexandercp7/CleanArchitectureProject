from __future__ import annotations

from collections import deque
from datetime import datetime, timezone

from fastapi import APIRouter, Query, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

router = APIRouter(tags=["notifications"])

_MAX_STORED_NOTIFICATIONS = 100
_notifications: deque[dict[str, object]] = deque(maxlen=_MAX_STORED_NOTIFICATIONS)


class MatchingProduct(BaseModel):
    title: str
    cash_price: float
    in_stock: bool
    url: str


class NotifyPayload(BaseModel):
    recipient: str
    subject: str
    body: str
    alert_id: str | None = None
    query: str | None = None
    condition: str | None = None
    threshold: float | None = None
    matching_products: list[MatchingProduct] = []


@router.post("/notify", status_code=status.HTTP_202_ACCEPTED)
async def receive_notification(payload: NotifyPayload) -> dict[str, str]:
    _notifications.appendleft(
        {
            "received_at": datetime.now(tz=timezone.utc).isoformat(),
            "recipient": payload.recipient,
            "subject": payload.subject,
            "body": payload.body,
                        "alert_id": payload.alert_id,
                        "query": payload.query,
                        "condition": payload.condition,
                        "threshold": payload.threshold,
                        "matching_products": [product.model_dump() for product in payload.matching_products],
        }
    )
    return {"status": "received"}


@router.get("/notifications")
async def notifications_page() -> HTMLResponse:
        html = """
<!doctype html>
<html lang="es">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Notifications</title>
    <style>
        :root {
            --bg: #f7f2ea;
            --bg-accent: #e4ecf7;
            --panel: #fffdf8;
            --ink: #1f1e1a;
            --muted: #6b655a;
            --line: #d7d0c4;
            --brand: #1f6d5a;
            --brand-2: #2f4d82;
            --chip: #ecf3ff;
            --shadow: 0 18px 38px rgba(31, 30, 26, 0.08);
        }

        * { box-sizing: border-box; }

        body {
            margin: 0;
            min-height: 100vh;
            color: var(--ink);
            font-family: "Trebuchet MS", "Gill Sans", "Segoe UI", sans-serif;
            background:
                radial-gradient(1200px 500px at 8% -10%, #f7d9b0 0%, transparent 55%),
                radial-gradient(900px 500px at 100% 0%, #cfe1ff 0%, transparent 60%),
                linear-gradient(180deg, var(--bg-accent), var(--bg));
        }

        .wrap {
            max-width: 1100px;
            margin: 0 auto;
            padding: 28px 18px 32px;
        }

        .hero {
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 20px;
            box-shadow: var(--shadow);
            padding: 22px 20px;
            margin-bottom: 16px;
            position: relative;
            overflow: hidden;
        }

        .hero::after {
            content: "";
            position: absolute;
            right: -60px;
            top: -70px;
            width: 240px;
            height: 240px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(47, 77, 130, 0.23), rgba(47, 77, 130, 0));
            pointer-events: none;
        }

        h1 {
            margin: 0 0 6px;
            font-size: clamp(1.65rem, 3.8vw, 2.35rem);
            letter-spacing: 0.4px;
        }

        .sub {
            margin: 0;
            color: var(--muted);
            font-size: 0.95rem;
        }

        .toolbar {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            align-items: center;
            margin-top: 16px;
        }

        button {
            border: 0;
            border-radius: 999px;
            padding: 9px 16px;
            font-weight: 700;
            cursor: pointer;
            color: white;
            background: linear-gradient(92deg, var(--brand), var(--brand-2));
            box-shadow: 0 8px 20px rgba(47, 77, 130, 0.22);
            transition: transform 130ms ease, filter 130ms ease;
        }

        button:hover {
            transform: translateY(-1px);
            filter: saturate(1.08);
        }

        input[type="number"] {
            width: 84px;
            border: 1px solid var(--line);
            border-radius: 999px;
            padding: 8px 12px;
            background: #ffffff;
            color: var(--ink);
        }

        .meta {
            margin-left: auto;
            color: var(--muted);
            font-size: 0.88rem;
        }

        .cards {
            display: grid;
            gap: 12px;
            margin-top: 14px;
        }

        .card {
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 14px;
            box-shadow: var(--shadow);
            padding: 14px;
            animation: enter 340ms ease both;
        }

        @keyframes enter {
            from { opacity: 0; transform: translateY(8px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .card-head {
            display: flex;
            justify-content: space-between;
            gap: 12px;
            flex-wrap: wrap;
            margin-bottom: 8px;
        }

        .subject {
            font-size: 1.02rem;
            margin: 0;
        }

        .row {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            margin-top: 8px;
        }

        .chip {
            background: var(--chip);
            border: 1px solid #d8e5ff;
            border-radius: 999px;
            padding: 4px 10px;
            font-size: 0.77rem;
            color: #20406d;
        }

        details {
            margin-top: 12px;
            border-top: 1px dashed var(--line);
            padding-top: 8px;
        }

        summary {
            cursor: pointer;
            font-weight: 700;
            color: var(--brand-2);
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
            font-size: 0.92rem;
            overflow: hidden;
            border-radius: 10px;
        }

        th, td {
            text-align: left;
            padding: 8px 9px;
            border-bottom: 1px solid var(--line);
        }

        th {
            background: #f2f6ff;
            color: #223150;
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.45px;
        }

        .empty {
            text-align: center;
            padding: 22px;
            color: var(--muted);
            border: 1px dashed var(--line);
            border-radius: 14px;
            background: rgba(255, 255, 255, 0.65);
        }

        a { color: var(--brand-2); }

        @media (max-width: 650px) {
            .meta { margin-left: 0; width: 100%; }
            th:nth-child(3), td:nth-child(3) { display: none; }
        }
    </style>
</head>
<body>
    <div class="wrap">
        <section class="hero">
            <h1>Notificaciones de Alertas</h1>
            <p class="sub">Visualiza productos que realmente cumplen el umbral o la condicion IN_STOCK.</p>
            <div class="toolbar">
                <button id="refreshBtn">Actualizar</button>
                <label for="limitInput">Limite</label>
                <input id="limitInput" type="number" min="1" max="100" value="20" />
                <span id="meta" class="meta">Cargando...</span>
            </div>
        </section>
        <section id="cards" class="cards"></section>
    </div>

    <script>
        const cardsEl = document.getElementById('cards');
        const metaEl = document.getElementById('meta');
        const refreshBtn = document.getElementById('refreshBtn');
        const limitInput = document.getElementById('limitInput');

        function escapeHtml(value) {
            return String(value)
                .replaceAll('&', '&amp;')
                .replaceAll('<', '&lt;')
                .replaceAll('>', '&gt;')
                .replaceAll('"', '&quot;')
                .replaceAll("'", '&#39;');
        }

        function formatMoney(value) {
            const amount = Number(value || 0);
            return new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN' }).format(amount);
        }

        function renderProducts(products) {
            if (!products || products.length === 0) {
                return '<div class="empty">No hay productos guardados en esta notificacion.</div>';
            }

            const rows = products.map((item) => {
                const url = escapeHtml(item.url || '');
                const title = escapeHtml(item.title || 'Sin titulo');
                const stock = item.in_stock ? 'Si' : 'No';
                return `<tr>
                    <td>${title}</td>
                    <td>${formatMoney(item.cash_price)}</td>
                    <td>${stock}</td>
                    <td><a href="${url}" target="_blank" rel="noreferrer">Abrir</a></td>
                </tr>`;
            }).join('');

            return `<table>
                <thead>
                    <tr>
                        <th>Producto</th>
                        <th>Precio</th>
                        <th>Stock</th>
                        <th>Link</th>
                    </tr>
                </thead>
                <tbody>${rows}</tbody>
            </table>`;
        }

        function renderNotifications(data) {
            if (!data || data.length === 0) {
                cardsEl.innerHTML = '<div class="empty">Aun no hay notificaciones. Crea o dispara una alerta para ver resultados aqui.</div>';
                return;
            }

            cardsEl.innerHTML = data.map((item, index) => {
                const received = new Date(item.received_at).toLocaleString('es-MX');
                const condition = escapeHtml(item.condition || 'N/A');
                const query = escapeHtml(item.query || 'N/A');
                const recipient = escapeHtml(item.recipient || 'N/A');
                const threshold = item.threshold === null || item.threshold === undefined ? 'N/A' : formatMoney(item.threshold);
                const productCount = Array.isArray(item.matching_products) ? item.matching_products.length : 0;
                const body = escapeHtml(item.body || '');

                return `<article class="card" style="animation-delay:${Math.min(index * 45, 240)}ms">
                    <div class="card-head">
                        <h2 class="subject">${escapeHtml(item.subject || 'Notificacion')}</h2>
                        <div>${received}</div>
                    </div>
                    <div>${body}</div>
                    <div class="row">
                        <span class="chip">Query: ${query}</span>
                        <span class="chip">Condicion: ${condition}</span>
                        <span class="chip">Umbral: ${threshold}</span>
                        <span class="chip">Productos que cumplen: ${productCount}</span>
                        <span class="chip">Destinatario: ${recipient}</span>
                    </div>
                    <details>
                        <summary>Ver productos que cumplen</summary>
                        ${renderProducts(item.matching_products)}
                    </details>
                </article>`;
            }).join('');
        }

        async function loadNotifications() {
            const limit = Math.max(1, Math.min(100, Number(limitInput.value || 20)));
            metaEl.textContent = 'Actualizando...';
            try {
                const response = await fetch(`/notifications/data?limit=${limit}`);
                const data = await response.json();
                renderNotifications(data);
                metaEl.textContent = `Mostrando ${data.length} notificaciones`;
            } catch (_error) {
                cardsEl.innerHTML = '<div class="empty">No se pudieron cargar las notificaciones.</div>';
                metaEl.textContent = 'Error al cargar';
            }
        }

        refreshBtn.addEventListener('click', loadNotifications);
        limitInput.addEventListener('change', loadNotifications);
        loadNotifications();
    </script>
</body>
</html>
"""
        return HTMLResponse(content=html)


@router.get("/notifications/data")
async def list_notifications(limit: int = Query(default=20, ge=1, le=100)) -> list[dict[str, object]]:
        return list(_notifications)[:limit]
