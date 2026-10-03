"""Automatically create the Kibana Data View, 8 visualizations and 1 dashboard.

Usage:  python scripts/setup_kibana.py [--kibana http://localhost:5601]
If anything fails, follow the manual steps in README.md (section 'Build the dashboard manually').
"""
import argparse, json, sys, time
import requests

DV_ID = "shop-sales-dv"
IDX_REF = {"name": "kibanaSavedObjectMeta.searchSourceJSON.index", "type": "index-pattern", "id": DV_ID}
SEARCH_SRC = json.dumps({"query": {"query": "", "language": "kuery"}, "filter": [],
                         "indexRefName": "kibanaSavedObjectMeta.searchSourceJSON.index"})


def metric(id_, typ, field=None, schema="metric"):
    p = {"field": field} if field else {}
    return {"id": id_, "enabled": True, "type": typ, "params": p, "schema": schema}


def terms(id_, field, size=10, schema="segment", order_by="1"):
    return {"id": id_, "enabled": True, "type": "terms", "schema": schema, "params": {
        "field": field, "orderBy": order_by, "order": "desc", "size": size,
        "otherBucket": False, "otherBucketLabel": "Other", "missingBucket": False, "missingBucketLabel": "Missing"}}


def date_hist(id_, field="order_date", interval="auto"):
    return {"id": id_, "enabled": True, "type": "date_histogram", "schema": "segment", "params": {
        "field": field, "useNormalizedEsInterval": True, "scaleMetricValues": False, "interval": interval,
        "drop_partials": False, "min_doc_count": 1, "extended_bounds": {}}}


def xy_params(kind, y_title):
    return {"type": kind, "grid": {"categoryLines": False},
            "categoryAxes": [{"id": "CategoryAxis-1", "type": "category", "position": "bottom", "show": True,
                              "style": {}, "scale": {"type": "linear"},
                              "labels": {"show": True, "filter": True, "truncate": 100}, "title": {}}],
            "valueAxes": [{"id": "ValueAxis-1", "name": "LeftAxis-1", "type": "value", "position": "left",
                           "show": True, "style": {}, "scale": {"type": "linear", "mode": "normal"},
                           "labels": {"show": True, "rotate": 0, "filter": False, "truncate": 100},
                           "title": {"text": y_title}}],
            "seriesParams": [{"show": True, "type": kind, "mode": "normal",
                              "data": {"label": y_title, "id": "1"}, "valueAxis": "ValueAxis-1",
                              "drawLinesBetweenPoints": True, "lineWidth": 2, "showCircles": True,
                              "interpolate": "linear"}],
            "addTooltip": True, "addLegend": True, "legendPosition": "right", "times": [],
            "addTimeMarker": False, "labels": {"show": False},
            "thresholdLine": {"show": False, "value": 10, "width": 1, "style": "full", "color": "#E7664C"}}


PIE = {"type": "pie", "addTooltip": True, "addLegend": True, "legendPosition": "right", "isDonut": True,
       "labels": {"show": False, "values": True, "last_level": True, "truncate": 100}}
TABLE = {"perPage": 10, "showPartialRows": False, "showMetricsAtAllLevels": False, "showTotal": False,
         "totalFunc": "sum", "percentageCol": ""}


def vis(id_, title, vtype, params, aggs):
    state = {"title": title, "type": vtype, "aggs": aggs, "params": params}
    return {"type": "visualization", "id": id_, "attributes": {
        "title": title, "description": "", "visState": json.dumps(state), "uiStateJSON": "{}", "version": 1,
        "kibanaSavedObjectMeta": {"searchSourceJSON": SEARCH_SRC}}, "references": [IDX_REF]}


def build_objects():
    V = []
    kpi_aggs = [metric("1", "sum", "total_amount"), metric("2", "count"),
                metric("3", "avg", "total_amount"), metric("4", "cardinality", "customer_id")]
    V.append(vis("v-kpis", "KPIs: Revenue | Orders | Avg Order | Customers", "table", TABLE, kpi_aggs))
    V.append(vis("v-rev-time", "Revenue over time", "line", xy_params("line", "Revenue"),
                 [metric("1", "sum", "total_amount"), date_hist("2")]))
    V.append(vis("v-cat-pie", "Revenue by category", "pie", PIE,
                 [metric("1", "sum", "total_amount"), terms("2", "category")]))
    V.append(vis("v-country-bar", "Revenue by country", "histogram", xy_params("histogram", "Revenue"),
                 [metric("1", "sum", "total_amount"), terms("2", "country")]))
    V.append(vis("v-pay-pie", "Payment methods", "pie", PIE, [metric("1", "count"), terms("2", "payment_method")]))
    V.append(vis("v-status-pie", "Order status", "pie", PIE, [metric("1", "count"), terms("2", "status")]))
    V.append(vis("v-top-customers", "Top 10 customers by spend", "table", TABLE,
                 [metric("1", "sum", "total_amount"), metric("3", "count"),
                  terms("2", "customer_id", 10, "bucket")]))
    V.append(vis("v-rating-cat", "Average rating by category", "histogram", xy_params("histogram", "Avg rating"),
                 [metric("1", "avg", "rating"), terms("2", "category")]))

    layout = [("v-kpis", 0, 0, 48, 8), ("v-rev-time", 0, 8, 32, 14), ("v-cat-pie", 32, 8, 16, 14),
              ("v-country-bar", 0, 22, 24, 14), ("v-rating-cat", 24, 22, 24, 14),
              ("v-pay-pie", 0, 36, 16, 14), ("v-status-pie", 16, 36, 16, 14), ("v-top-customers", 32, 36, 16, 14)]
    panels, refs = [], []
    for i, (vid, x, y, w, h) in enumerate(layout, 1):
        panels.append({"version": "8.14.3", "type": "visualization",
                       "gridData": {"x": x, "y": y, "w": w, "h": h, "i": str(i)},
                       "panelIndex": str(i), "embeddableConfig": {}, "panelRefName": f"panel_{i}"})
        refs.append({"name": f"panel_{i}", "type": "visualization", "id": vid})
    dash = {"type": "dashboard", "id": "shop-sales-dashboard", "attributes": {
        "title": "Shop Sales Overview", "description": "Sample e-commerce dashboard (ELK project)",
        "panelsJSON": json.dumps(panels),
        "optionsJSON": json.dumps({"useMargins": True, "syncColors": False, "syncCursor": True,
                                   "syncTooltips": False, "hidePanelTitles": False}),
        "timeRestore": True, "timeFrom": "now-1y", "timeTo": "now",
        "refreshInterval": {"pause": True, "value": 0},
        "kibanaSavedObjectMeta": {"searchSourceJSON": json.dumps(
            {"query": {"language": "kuery", "query": ""}, "filter": []})}}, "references": refs}
    dv = {"type": "index-pattern", "id": DV_ID, "attributes": {
        "title": "shop-sales", "name": "Shop Sales", "timeFieldName": "order_date"}, "references": []}
    return [dv] + V + [dash]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kibana", default="http://localhost:5601")
    a = ap.parse_args()
    for _ in range(60):
        try:
            r = requests.get(f"{a.kibana}/api/status", timeout=5)
            if r.ok and r.json().get("status", {}).get("overall", {}).get("level") == "available":
                break
        except requests.RequestException:
            pass
        print("Waiting for Kibana to become ready...")
        time.sleep(5)
    else:
        sys.exit("Kibana not ready. Open http://localhost:5601 to check it.")
    r = requests.post(f"{a.kibana}/api/saved_objects/_bulk_create?overwrite=true",
                      headers={"kbn-xsrf": "true"}, json=build_objects(), timeout=60)
    if not r.ok:
        sys.exit(f"Failed: {r.status_code} {r.text}")
    errors = [o for o in r.json().get("saved_objects", []) if "error" in o]
    if errors:
        print("Some objects failed:", json.dumps(errors, indent=2)); sys.exit(1)
    print("Done! Open: %s/app/dashboards#/view/shop-sales-dashboard" % a.kibana)


if __name__ == "__main__":
    main()
