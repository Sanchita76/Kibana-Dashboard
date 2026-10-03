"""Create the index (explicit mapping), generate sample data, bulk-load it into Elasticsearch.

Usage:  python scripts/load_data.py [--rows 50000] [--es http://localhost:9200]
Also writes data/sales.csv (used by the optional Logstash pipeline).
"""
import argparse, csv, os, sys
from elasticsearch import Elasticsearch, helpers
from datagen import generate_rows, COLUMNS

INDEX = "shop-sales"
MAPPING = {
    "settings": {"number_of_shards": 1, "number_of_replicas": 0},
    "mappings": {"properties": {
        "order_id": {"type": "keyword"},
        "order_date": {"type": "date"},
        "customer_id": {"type": "keyword"},
        "country": {"type": "keyword"},
        "city": {"type": "keyword"},
        "category": {"type": "keyword"},
        "product": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
        "quantity": {"type": "integer"},
        "unit_price": {"type": "float"},
        "discount_pct": {"type": "integer"},
        "total_amount": {"type": "float"},
        "payment_method": {"type": "keyword"},
        "status": {"type": "keyword"},
        "rating": {"type": "integer"},
    }},
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", type=int, default=50000)
    ap.add_argument("--es", default=os.getenv("ES_URL", "http://localhost:9200"))
    a = ap.parse_args()

    es = Elasticsearch(a.es)
    if not es.ping():
        sys.exit(f"Cannot reach Elasticsearch at {a.es}. Did you run 'docker compose up -d'?")
    if es.indices.exists(index=INDEX):
        es.indices.delete(index=INDEX)
    es.indices.create(index=INDEX, settings=MAPPING["settings"], mappings=MAPPING["mappings"])
    print(f"Created index '{INDEX}'")

    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
    os.makedirs(data_dir, exist_ok=True)
    csv_path = os.path.join(data_dir, "sales.csv")
    rows = list(generate_rows(a.rows))
    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {csv_path}")

    actions = ({"_index": INDEX, "_id": r["order_id"], "_source": r} for r in rows)
    ok, _ = helpers.bulk(es, actions, chunk_size=2000, request_timeout=120)
    es.indices.refresh(index=INDEX)
    print(f"Indexed {ok} documents. Total in index: {es.count(index=INDEX)['count']}")


if __name__ == "__main__":
    main()
