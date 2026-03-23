# Piano: Backend Vinted Intelligence

## Contesto
La dashboard React/TypeScript esiste con mock data in `server.ts`. Serve un backend Python reale che: scrapi Vinted per prodotti Apple, confronta prezzi con Amazon (SerpAPI), calcola margini, salva su Supabase, e aggiorna ogni ora automaticamente.

## Stack Tecnologico
- **Backend**: Python FastAPI (nella venv `.vinted/`)
- **Database**: Supabase (PostgreSQL)
- **Vinted**: API non ufficiale (`/api/v2/catalog/items`) con gestione sessione cookie
- **Amazon Prices**: SerpAPI (Google Shopping + Amazon engine)
- **Scheduler**: APScheduler (ogni 60 min)
- **HTTP Client**: httpx (async)

---

## Struttura File

```
backend/
├── __init__.py
├── main.py                    # FastAPI app, CORS, lifespan (scheduler start/stop)
├── config.py                  # Pydantic Settings (env vars)
├── models.py                  # Pydantic models (mirror TypeScript interfaces)
├── database.py                # Supabase client singleton
├── routers/
│   ├── __init__.py
│   ├── stats.py               # GET /api/stats
│   ├── opportunities.py       # GET /api/opportunities
│   ├── watchlist.py           # GET, POST, DELETE /api/watchlist
│   └── health.py              # GET /api/health
├── services/
│   ├── __init__.py
│   ├── vinted_session.py      # Cookie/session lifecycle per Vinted
│   ├── vinted_scraper.py      # Scraping catalogo Vinted
│   ├── serpapi_client.py      # Ricerca prezzi Amazon/Google Shopping
│   ├── price_analyzer.py      # Calcolo margini e scoring
│   └── product_matcher.py     # Normalizzazione titoli Vinted -> query Amazon
├── scheduler/
│   ├── __init__.py
│   ├── jobs.py                # APScheduler config
│   └── scanner.py             # Orchestratore pipeline completa
├── utils/
│   ├── __init__.py
│   ├── rate_limiter.py        # Token bucket async
│   ├── logger.py              # Logging strutturato
│   └── apple_products.py      # Catalogo prodotti Apple e search configs
└── migrations/
    └── 001_initial_schema.sql # Schema SQL per Supabase
```

File da modificare nell'esistente:
- `vite.config.ts` - aggiungere proxy `/api` -> `localhost:8000`
- `.env.example` - aggiungere variabili Supabase, SerpAPI
- `requirements.txt` - nuovo file con dipendenze Python

---

## Schema Database Supabase

### `watchlist_items`
| Colonna | Tipo | Note |
|---------|------|------|
| id | UUID PK | gen_random_uuid() |
| type | TEXT | 'category' / 'product' |
| query | TEXT | es. "iPhone 15 Pro" |
| max_price | NUMERIC | prezzo massimo |
| min_margin | NUMERIC | margine minimo % |
| conditions | TEXT[] | filtri condizione |
| size | TEXT | opzionale |
| active | BOOLEAN | default true |
| created_at | TIMESTAMPTZ | |

### `listings`
| Colonna | Tipo | Note |
|---------|------|------|
| id | TEXT PK | ID Vinted |
| title | TEXT | titolo annuncio |
| description | TEXT | descrizione completa |
| price | NUMERIC | prezzo Vinted |
| currency | TEXT | default 'EUR' |
| condition | TEXT | stato prodotto |
| image_url | TEXT | foto principale |
| url | TEXT | link annuncio Vinted |
| published_at | TIMESTAMPTZ | data pubblicazione |
| brand | TEXT | marca |
| model | TEXT | modello |
| size | TEXT | dimensione/storage |
| seller_id | TEXT | ID venditore |
| seller_username | TEXT | nome venditore |
| seller_rating | NUMERIC | valutazione |
| category_id | INTEGER | categoria Vinted |
| watchlist_item_id | UUID FK | riferimento watchlist |
| raw_json | JSONB | risposta API completa |
| first_seen_at | TIMESTAMPTZ | prima volta visto |
| last_seen_at | TIMESTAMPTZ | ultima volta visto |
| is_sold | BOOLEAN | se venduto |

### `price_comparisons`
| Colonna | Tipo | Note |
|---------|------|------|
| id | UUID PK | |
| listing_id | TEXT FK | -> listings |
| amazon_price | NUMERIC | prezzo Amazon |
| market_price | NUMERIC | valore commerciale medio |
| asin | TEXT | ASIN Amazon |
| source | TEXT | 'serpapi' |
| search_query | TEXT | query usata |
| confidence | NUMERIC | 0.0 - 1.0 |
| raw_response | JSONB | risposta SerpAPI |
| fetched_at | TIMESTAMPTZ | |

### `opportunities`
| Colonna | Tipo | Note |
|---------|------|------|
| id | UUID PK | |
| listing_id | TEXT FK | -> listings |
| price_comparison_id | UUID FK | -> price_comparisons |
| vinted_price | NUMERIC | |
| amazon_price | NUMERIC | |
| market_price | NUMERIC | prezzo medio Vinted |
| margin_absolute | NUMERIC | amazon - vinted |
| margin_percent | NUMERIC | margine % |
| discount_vs_amazon | NUMERIC | sconto vs Amazon % |
| score | TEXT | 'high'/'medium'/'low' |
| is_active | BOOLEAN | |
| created_at | TIMESTAMPTZ | |

### `price_history` + `scan_logs`
Per storico prezzi e log delle scansioni.

---

## Approccio Scraping Vinted

1. **Sessione**: GET `https://www.vinted.it` per ottenere cookie `_vinted_fr_session`
2. **API Catalogo**: `GET /api/v2/catalog/items?search_text=iPhone&brand_ids[]=319&per_page=96&order=newest_first`
3. **Headers necessari**: User-Agent realistico, Accept JSON, Cookie sessione
4. **Refresh sessione**: ogni 25 min (scade a ~30 min)
5. **Rate limit**: max 20 req/min con delay random 2-5s tra richieste
6. **Categorie Apple**: iPhone, MacBook, iPad, Apple Watch (brand_id=319)

## Approccio SerpAPI

1. **Primario**: engine `google_shopping` con `gl=it`, `hl=it`
2. **Fallback**: engine `amazon` con `amazon_domain=amazon.it`
3. **Cache**: non ri-cercare lo stesso prodotto entro 24h
4. **Confidence scoring**: match titolo (0.4) + brand (0.2) + storage (0.2) + range prezzo (0.2)

## Logica Scoring Opportunita

- **HIGH**: margine >= 40%, confidence >= 0.7, sconto vs Amazon >= 50%
- **MEDIUM**: margine >= 20%, confidence >= 0.5, sconto vs Amazon >= 30%
- **LOW**: margine positivo ma sotto le soglie

## Connessione Frontend-Backend

- Aggiungere proxy in `vite.config.ts`: `/api` -> `http://localhost:8000`
- Rimuovere mock routes da `server.ts`
- Il frontend non cambia (continua a fare fetch su `/api/...`)

---

## Ordine Implementazione

### Fase 1: Fondamenta
1. Creare struttura `backend/`, `requirements.txt`, installare dipendenze
2. `config.py` + `models.py` + `database.py`
3. Schema SQL su Supabase (`migrations/001_initial_schema.sql`)
4. FastAPI skeleton con routers che ritornano mock data
5. Proxy in `vite.config.ts`

### Fase 2: Scraping Vinted
6. `vinted_session.py` - gestione sessione/cookie
7. `vinted_scraper.py` - scraping catalogo con `apple_products.py`
8. Salvataggio listings su Supabase

### Fase 3: Intelligence Prezzi
9. `product_matcher.py` - normalizzazione titoli
10. `serpapi_client.py` - ricerca prezzi Amazon
11. `price_analyzer.py` - calcolo margini e scoring

### Fase 4: Pipeline e Scheduler
12. `scanner.py` - orchestratore pipeline completa
13. `jobs.py` - APScheduler ogni ora
14. Collegare routers a dati reali Supabase

### Fase 5: Hardening
15. Rate limiting, retry logic, error handling
16. Logging strutturato
17. Health endpoint

---

## Variabili Ambiente (.env)
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
SERPAPI_KEY=your-serpapi-key
VINTED_BASE_URL=https://www.vinted.it
SCAN_INTERVAL_MINUTES=60
BACKEND_PORT=8000
```

## Dipendenze Python (requirements.txt)
```
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
pydantic>=2.9.0
pydantic-settings>=2.6.0
httpx>=0.28.0
supabase>=2.10.0
apscheduler>=3.10.0
python-dotenv>=1.0.0
```

## Verifica
1. `uvicorn backend.main:app --port 8000` - il server parte
2. Frontend su `localhost:5173` mostra dati reali da Supabase
3. Dopo 1 ora, nuovi listing appaiono automaticamente
4. `GET /api/health` mostra stato sessione Vinted e prossimo scan
5. Le opportunita mostrano prezzo Vinted, prezzo Amazon, margine, score
