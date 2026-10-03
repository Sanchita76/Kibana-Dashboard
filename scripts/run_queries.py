"""Runs a selection of Elasticsearch queries from Python and prints the results.
Usage: python scripts/run_queries.py
The same queries (plus more) are in queries/dev_tools.txt for Kibana Dev Tools.
"""
import json, os
from elasticsearch import Elasticsearch

es = Elasticsearch(os.getenv("ES_URL", "http://localhost:9200"))
IDX = "shop-sales"


def show(title, resp, keys=None):
    print("\n=== " + title + " ===")
    print(json.dumps(keys(resp) if keys else resp, indent=2, default=str)[:1500])


show("1. Full-text search: 'wireless' products", es.search(index=IDX, size=3, query={"match": {"product": "wireless"}}),
     lambda r: {"hits": r["hits"]["total"]["value"], "sample": [h["_source"]["product"] for h in r["hits"]["hits"]]})

show("2. Filter: delivered orders over $500 in Germany",
     es.search(index=IDX, size=0, track_total_hits=True, query={"bool": {"filter": [
         {"term": {"status": "delivered"}}, {"term": {"country": "Germany"}},
         {"range": {"total_amount": {"gt": 500}}}]}}),
     lambda r: {"matching_orders": r["hits"]["total"]["value"]})

show("3. Revenue by category (terms + sum + avg)",
     es.search(index=IDX, size=0, aggs={"by_cat": {"terms": {"field": "category", "size": 10,
               "order": {"rev": "desc"}}, "aggs": {"rev": {"sum": {"field": "total_amount"}},
                                                   "avg_order": {"avg": {"field": "total_amount"}}}}}),
     lambda r: [{"category": b["key"], "revenue": round(b["rev"]["value"], 2),
                 "avg_order": round(b["avg_order"]["value"], 2)} for b in r["aggregations"]["by_cat"]["buckets"]])

show("4. Monthly revenue + cumulative revenue (pipeline agg)",
     es.search(index=IDX, size=0, aggs={"m": {"date_histogram": {"field": "order_date", "calendar_interval": "month"},
               "aggs": {"rev": {"sum": {"field": "total_amount"}},
                        "cum": {"cumulative_sum": {"buckets_path": "rev"}}}}}),
     lambda r: [{"month": b["key_as_string"][:7], "rev": round(b["rev"]["value"]), "cum": round(b["cum"]["value"])}
                for b in r["aggregations"]["m"]["buckets"]])

show("5. Order value percentiles", es.search(index=IDX, size=0,
     aggs={"p": {"percentiles": {"field": "total_amount", "percents": [50, 90, 99]}}}),
     lambda r: r["aggregations"]["p"]["values"])

show("6. Top product per country (top_hits)",
     es.search(index=IDX, size=0, aggs={"c": {"terms": {"field": "country", "size": 3}, "aggs": {
         "top": {"top_hits": {"size": 1, "sort": [{"total_amount": "desc"}],
                              "_source": ["product", "total_amount"]}}}}}),
     lambda r: [{"country": b["key"], "top": b["top"]["hits"]["hits"][0]["_source"]} for b in r["aggregations"]["c"]["buckets"]])

show("7. Unique customers (cardinality)", es.search(index=IDX, size=0,
     aggs={"u": {"cardinality": {"field": "customer_id"}}}), lambda r: r["aggregations"]["u"])
