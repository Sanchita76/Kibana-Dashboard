# Project 1 - Kibana Dashboard + Elasticsearch Queries (ELK Stack)

**What you get:** a complete local ELK stack (Elasticsearch + Kibana + Logstash), 50,000 sample e-commerce orders,
16 ready-to-run Elasticsearch queries (full-text, bool filters, aggregations, pipeline aggs, ES|QL, SQL) and an
auto-built 8-panel Kibana dashboard ("Shop Sales Overview").

```
01-elk-kibana-dashboard/
├── docker-compose.yml          # Elasticsearch + Kibana (+ optional Logstash)
├── requirements.txt            # Python libs
├── scripts/
│   ├── datagen.py              # synthetic sales data generator
│   ├── load_data.py            # creates index mapping + loads data (+ writes data/sales.csv)
│   ├── setup_kibana.py         # auto-creates Data View, 8 visualizations, dashboard
│   └── run_queries.py          # runs sample queries from Python
├── queries/dev_tools.txt       # 16 queries to paste into Kibana Dev Tools
├── logstash/pipeline/sales.conf# optional Logstash ingestion of data/sales.csv
└── data/                       # sales.csv is written here
```

## 1. Install (one time)
| Tool | Why | Get it |
|---|---|---|
| Docker Desktop | runs Elasticsearch/Kibana | https://www.docker.com/products/docker-desktop (Windows: enable WSL2 when asked) |
| Python 3.9+ | runs the scripts | https://www.python.org/downloads (tick **"Add Python to PATH"** on Windows) |

Give Docker at least **4 GB RAM** (Docker Desktop -> Settings -> Resources).
Linux only: run `sudo sysctl -w vm.max_map_count=262144` once.

## 2. Run it (copy/paste in a terminal inside this folder)
```bash
# a) start Elasticsearch + Kibana (first time downloads ~2 GB; wait 1-2 min after it says "Started")
docker compose up -d elasticsearch kibana

# b) install python libs (optionally in a virtual env)
python -m venv venv
#   Windows: venv\Scripts\activate        Mac/Linux: source venv/bin/activate
pip install -r requirements.txt

# c) create index + load 50,000 orders
python scripts/load_data.py

# d) build the Kibana dashboard automatically
python scripts/setup_kibana.py
```
Open **http://localhost:5601/app/dashboards#/view/shop-sales-dashboard**.
If the dashboard looks empty, set the time picker (top right) to **Last 1 year**.

## 3. Run the queries
* In Kibana open **Dev Tools** (menu -> Management -> Dev Tools), paste the content of `queries/dev_tools.txt`,
  put the cursor inside a request and press **Ctrl+Enter**.
* Or from Python: `python scripts/run_queries.py`

## 4. Optional: use Logstash (the "L" in ELK)
`load_data.py` already wrote `data/sales.csv` and created the index mapping. Re-ingest it through Logstash:
```bash
docker compose --profile ingest up logstash      # Ctrl+C when dots stop appearing
```
(Documents use `order_id` as `_id`, so re-ingesting overwrites instead of duplicating.)

## 5. Build the dashboard manually (fallback if step 2d fails)
1. Kibana -> menu -> **Stack Management -> Data Views -> Create**: name `shop-sales`, timestamp field `order_date`.
2. Menu -> **Dashboard -> Create dashboard -> Create visualization**; pick the `shop-sales` data view and drag fields:
   * Line: `order_date` on X, **Sum of total_amount** on Y
   * Donut: slice by `category`, size = Sum of `total_amount`
   * Bar: `country` on X, Sum of `total_amount` on Y
   * Table: rows `customer_id` (top 10), metrics Sum of `total_amount` + Count
3. **Save** the dashboard.

## 6. Use the real Kaggle data instead (optional)
Any CSV can go in: put it in `data/`, edit the `columns` list in `logstash/pipeline/sales.conf` and the mapping in
`scripts/load_data.py`. Good Kaggle datasets for ELK: "Online Retail" (`carrie1/ecommerce-data`) or "Web server access logs".

## 7. Stop / clean up
```bash
docker compose down        # stop (keeps data)
docker compose down -v     # stop and DELETE all data
```

## Troubleshooting
| Problem | Fix |
|---|---|
| `Cannot reach Elasticsearch` | wait 1-2 min, check `docker compose ps`, open http://localhost:9200 |
| Elasticsearch exits immediately | not enough Docker RAM (need 4 GB) / Linux `vm.max_map_count` |
| `setup_kibana.py` says Kibana not ready | open http://localhost:5601 until it loads, re-run the script |
| Dashboard panels say "No results" | time picker -> Last 1 year (data spans the last 365 days) |
| Port 9200/5601 already in use | stop the other program or change the left-hand port in docker-compose.yml |

> Security is intentionally disabled for local learning. Never expose these ports to the internet.
> Note: `setup_kibana.py` was written against Kibana 8.14 saved-object formats; if a future version rejects it, use section 5.
