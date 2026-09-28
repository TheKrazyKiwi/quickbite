def test_get_foods_list(client):
    r = client.get("/api/foods")
    assert r.status_code == 200
    foods = r.json()
    assert len(foods) >= 10
    names = [f["name"] for f in foods]
    assert "Veg Sandwich" in names
    assert "Cold Coffee" in names


def test_place_order_and_transaction(client, student_token, staff_token):
    # 1. Get food items
    r = client.get("/api/foods")
    foods = {f["name"]: f for f in r.json()}
    sandwich = foods["Veg Sandwich"]
    coffee = foods["Cold Coffee"]

    initial_sandwich_stock = sandwich["inventory"]["stock_quantity"]
    initial_coffee_stock = coffee["inventory"]["stock_quantity"]

    # 2. Place order: 2x Veg Sandwich, 1x Cold Coffee
    order_payload = {
        "items": [
            {"food_id": sandwich["id"], "quantity": 2},
            {"food_id": coffee["id"], "quantity": 1}
        ],
        "pickup_slot": "1:15 PM – 1:30 PM",
        "payment_mode": "MOCK_ONLINE"
    }
    r = client.post("/api/orders", json=order_payload, headers={"Authorization": f"Bearer {student_token}"})
    assert r.status_code == 201
    order = r.json()
    order_id = order["id"]
    assert order["status"] == "PLACED"
    assert order["total_amount"] == (sandwich["price"] * 2) + (coffee["price"] * 1)
    assert order["token"].startswith("QB-")
    assert order["payment"]["status"] == "SUCCESS"

    # 3. Check inventory was deducted accurately
    r = client.get("/api/foods")
    updated_foods = {f["name"]: f for f in r.json()}
    assert updated_foods["Veg Sandwich"]["inventory"]["stock_quantity"] == initial_sandwich_stock - 2
    assert updated_foods["Cold Coffee"]["inventory"]["stock_quantity"] == initial_coffee_stock - 1

    # 4. Staff advances status: PLACED -> PREPARING
    r = client.patch(
        f"/api/orders/{order_id}/status",
        json={"status": "PREPARING"},
        headers={"Authorization": f"Bearer {staff_token}"}
    )
    assert r.status_code == 200
    assert r.json()["status"] == "PREPARING"

    # 5. Staff advances status: PREPARING -> READY
    r = client.patch(
        f"/api/orders/{order_id}/status",
        json={"status": "READY"},
        headers={"Authorization": f"Bearer {staff_token}"}
    )
    assert r.status_code == 200
    assert r.json()["status"] == "READY"

    # 6. Staff advances status: READY -> COMPLETED
    r = client.patch(
        f"/api/orders/{order_id}/status",
        json={"status": "COMPLETED"},
        headers={"Authorization": f"Bearer {staff_token}"}
    )
    assert r.status_code == 200
    assert r.json()["status"] == "COMPLETED"


def test_order_out_of_stock_fails(client, student_token):
    r = client.get("/api/foods")
    foods = {f["name"]: f for f in r.json()}
    samosa = foods["Samosa"]
    assert samosa["available"] is False

    r = client.post("/api/orders", json={
        "items": [{"food_id": samosa["id"], "quantity": 1}],
        "pickup_slot": "1:15 PM – 1:30 PM",
        "payment_mode": "MOCK_ONLINE"
    }, headers={"Authorization": f"Bearer {student_token}"})
    assert r.status_code == 409


def test_cancel_order_restores_inventory(client, student_token, staff_token):
    # Get brownie initial stock
    r = client.get("/api/foods")
    foods = {f["name"]: f for f in r.json()}
    brownie = foods["Brownie"]
    initial_stock = brownie["inventory"]["stock_quantity"]

    # Place order for 2 brownies
    r = client.post("/api/orders", json={
        "items": [{"food_id": brownie["id"], "quantity": 2}],
        "pickup_slot": "1:30 PM – 1:45 PM",
        "payment_mode": "PAY_AT_PICKUP"
    }, headers={"Authorization": f"Bearer {student_token}"})
    assert r.status_code == 201
    order_id = r.json()["id"]

    # Verify stock decremented
    r = client.get("/api/foods")
    updated_brownie = {f["name"]: f for f in r.json()}["Brownie"]
    assert updated_brownie["inventory"]["stock_quantity"] == initial_stock - 2

    # Staff cancels order
    r = client.patch(
        f"/api/orders/{order_id}/status",
        json={"status": "CANCELLED"},
        headers={"Authorization": f"Bearer {staff_token}"}
    )
    assert r.status_code == 200

    # Verify inventory was restored!
    r = client.get("/api/foods")
    restored_brownie = {f["name"]: f for f in r.json()}["Brownie"]
    assert restored_brownie["inventory"]["stock_quantity"] == initial_stock
