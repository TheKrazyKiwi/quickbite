def test_reports_today(client, staff_token):
    r = client.get("/api/reports/today", headers={"Authorization": f"Bearer {staff_token}"})
    assert r.status_code == 200
    data = r.json()
    assert "orders" in data
    assert "revenue" in data
    assert data["orders"] >= 1
    assert data["revenue"] > 0


def test_reports_popular_food(client, staff_token):
    r = client.get("/api/reports/popular-food", headers={"Authorization": f"Bearer {staff_token}"})
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 1
    assert "name" in data[0]
    assert "quantity" in data[0]


def test_reports_low_stock(client, staff_token):
    r = client.get("/api/reports/low-stock", headers={"Authorization": f"Bearer {staff_token}"})
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    low_names = [x["food"] for x in data]
    # Samosa has 0 stock (< 8 min stock), Pizza has 5 stock (< 6 min stock)
    assert "Samosa" in low_names or "Pizza" in low_names


def test_reports_pickup_slots(client, staff_token):
    r = client.get("/api/reports/pickup-slots", headers={"Authorization": f"Bearer {staff_token}"})
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 1
    assert "slot" in data[0]
    assert "orders" in data[0]


def test_reports_sales_view(client, staff_token):
    r = client.get("/api/reports/sales", headers={"Authorization": f"Bearer {staff_token}"})
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 1
    assert "date" in data[0]
    assert "revenue" in data[0]
