from prometheus_client import generate_latest

from nemwatch.observability.metrics import HTTP_REQUESTS


def test_metrics_use_bounded_route_labels() -> None:
    HTTP_REQUESTS.labels("GET", "/api/v1/alerts/{alert_id}", "2xx").inc()
    body = generate_latest().decode()
    assert "nemwatch_http_requests_total" in body
    assert 'route="/api/v1/alerts/{alert_id}"' in body
