# Vinted Intelligence

Tool per monitorare Vinted e identificare opportunità di acquisto/rivendita. Scansiona automaticamente i listing in base a criteri configurabili e li presenta ordinati per margine di profitto stimato.

## Stack

| Layer | Tecnologia |
|---|---|
| Frontend | React 19 + TypeScript + Tailwind CSS + Recharts |
| Backend | FastAPI + Python |
| Database | Supabase (PostgreSQL) |
| Dev server | Express + Vite (con mock data) |

## Struttura

```
├── backend/
│   ├── main.py                  # FastAPI app + scheduler lifecycle
│   ├── config.py                # Settings da .env
│   ├── database.py              # Client Supabase
│   ├── models.py                # Pydantic models
│   ├── migrations/              # SQL migrations da eseguire in Supabase
│   ├── routers/                 # Endpoint API (watchlist, opportunities, purchases, scan, stats)
│   ├── scheduler/               # Scanner periodico (APScheduler)
│   ├── services/                # Vinted scraper, session, price analyzer
│   └── utils/                  # Rate limiter, logger
├── src/
│   ├── components/              # Dashboard, Watchlist, Purchases, Layout
│   ├── types.ts                 # Interfacce TypeScript
│   └── App.tsx                  # Routing
└── server.ts                    # Mock server per sviluppo locale
```

## Setup

### Prerequisiti

- Node.js 18+
- Python 3.11+
- Account Supabase

### 1. Variabili d'ambiente

Crea un file `.env` nella root del progetto:

```env
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=your_supabase_anon_key
VINTED_BASE_URL=https://www.vinted.it
SCAN_INTERVAL_MINUTES=60
BACKEND_PORT=8000

# Opzionali
SERPAPI_KEY=your_serpapi_key
GEMINI_API_KEY=your_gemini_key
```

### 2. Database

Esegui le migration in ordine nel SQL Editor di Supabase:

```
backend/migrations/001_initial_schema.sql
backend/migrations/002_add_market_margins.sql
backend/migrations/003_watchlist_filters.sql
backend/migrations/004_purchases.sql
backend/migrations/005_opportunities_unique_listing.sql
```

### 3. Frontend

```bash
npm install
```

### 4. Backend

```bash
python -m venv .vinted
source .vinted/bin/activate      # macOS/Linux
# oppure: .vinted\Scripts\activate  # Windows

pip install -r requirements.txt
```

## Avvio

### Sviluppo con mock data (solo frontend)

```bash
npm run dev:mock
```

Avvia un server Express con dati mock su `http://localhost:5173`.

### Produzione (frontend + backend reale)

Terminale 1 — Backend:
```bash
source .vinted/bin/activate
uvicorn backend.main:app --reload --port 8000
```

Terminale 2 — Frontend:
```bash
npm run dev
```

## Funzionalità

- **Watchlist**: crea monitor con query, fascia di prezzo, condizione, brand, colori e altri filtri Vinted
- **Scansione automatica**: il backend scannerizza Vinted ogni `SCAN_INTERVAL_MINUTES` minuti
- **Opportunità**: listing ordinati per margine di profitto stimato
- **Acquisti**: traccia gli acquisti effettuati con prezzo di compra e rivendita
- **Dashboard**: statistiche aggregate e grafici

## API

Il backend espone queste route:

| Metodo | Path | Descrizione |
|--------|------|-------------|
| GET | `/api/watchlist` | Lista monitor attivi |
| POST | `/api/watchlist` | Crea nuovo monitor |
| DELETE | `/api/watchlist/{id}` | Elimina monitor e relativi listing |
| GET | `/api/opportunities` | Listing trovati ordinati per margine |
| GET | `/api/purchases` | Lista acquisti |
| POST | `/api/purchases` | Registra acquisto |
| POST | `/api/scan` | Avvia scansione manuale completa |
| POST | `/api/scan/{id}` | Scansione per singolo monitor |
| GET | `/api/stats` | Statistiche dashboard |
| GET | `/api/health` | Stato del sistema |
