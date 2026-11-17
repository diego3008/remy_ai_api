import uuid

API = "/api/v1"


async def _business(client, **overrides):
    body = {"name": "Tacos Don Pepe", "phone": "+528110000000", **overrides}
    r = await client.post(f"{API}/businesses", json=body)
    assert r.status_code == 201, r.text
    return r.json()


async def _menu(client, business_id):
    r = await client.post(f"{API}/menus", json={"business_id": business_id})
    assert r.status_code == 201, r.text
    return r.json()


async def _dish(client, menu_id, price="50.00", **overrides):
    body = {"menu_id": menu_id, "name": "Taco al pastor", "price": price, **overrides}
    r = await client.post(f"{API}/dishes", json=body)
    assert r.status_code == 201, r.text
    return r.json()


async def _customer(client, business_id, phone="+528112345678", **overrides):
    body = {"business_id": business_id, "phone": phone, **overrides}
    r = await client.post(f"{API}/customers", json=body)
    assert r.status_code == 201, r.text
    return r.json()


async def test_business_crud(client):
    b = await _business(client)
    assert b["b_active"] is True
    assert b["timezone"] == "America/Monterrey"
    assert b["created_at"] and b["updated_at"]

    r = await client.get(f"{API}/businesses/{b['id']}")
    assert r.status_code == 200 and r.json()["name"] == "Tacos Don Pepe"

    r = await client.patch(f"{API}/businesses/{b['id']}", json={"name": "Renamed"})
    assert r.status_code == 200 and r.json()["name"] == "Renamed"

    r = await client.patch(f"{API}/businesses/{b['id']}", json={"name": None})
    assert r.status_code == 422

    r = await client.get(f"{API}/businesses", params={"b_active": True})
    assert [x["id"] for x in r.json()] == [b["id"]]

    assert (await client.delete(f"{API}/businesses/{b['id']}")).status_code == 204
    assert (await client.get(f"{API}/businesses/{b['id']}")).status_code == 404
    assert (await client.delete(f"{API}/businesses/{b['id']}")).status_code == 404


async def test_menu_and_dish_crud(client):
    b = await _business(client)
    assert (await client.post(f"{API}/menus", json={"business_id": 999})).status_code == 404

    m = await _menu(client, b["id"])
    assert m["name"] == "Main"
    r = await client.patch(f"{API}/menus/{m['id']}", json={"is_active": False})
    assert r.json()["is_active"] is False

    d = await _dish(client, m["id"], description="con piña")
    assert d["price"] == "50.00"
    assert (await _dish_bad_price(client, m["id"])) == 422

    r = await client.patch(f"{API}/dishes/{d['id']}", json={"price": "55.50"})
    assert r.json()["price"] == "55.50"

    r = await client.get(f"{API}/dishes", params={"business_id": b["id"]})
    assert [x["id"] for x in r.json()] == [d["id"]]

    # Deleting the menu cascades to its dishes.
    assert (await client.delete(f"{API}/menus/{m['id']}")).status_code == 204
    assert (await client.get(f"{API}/dishes/{d['id']}")).status_code == 404


async def _dish_bad_price(client, menu_id):
    r = await client.post(
        f"{API}/dishes", json={"menu_id": menu_id, "name": "x", "price": "-1"}
    )
    return r.status_code


async def test_customer_unique_phone_per_business(client):
    b = await _business(client)
    c = await _customer(client, b["id"], name="Ana")
    r = await client.post(
        f"{API}/customers", json={"business_id": b["id"], "phone": c["phone"]}
    )
    assert r.status_code == 409

    r = await client.get(f"{API}/customers", params={"phone": c["phone"]})
    assert [x["id"] for x in r.json()] == [c["id"]]

    r = await client.patch(f"{API}/customers/{c['id']}", json={"default_address": "Calle 1"})
    assert r.json()["default_address"] == "Calle 1"


async def test_order_lifecycle(client):
    b = await _business(client)
    m = await _menu(client, b["id"])
    taco = await _dish(client, m["id"], price="25.00")
    soda = await _dish(client, m["id"], price="20.00", name="Coca")
    cust = await _customer(client, b["id"], default_address="Av. Siempre Viva 742")

    r = await client.post(
        f"{API}/orders",
        json={
            "business_id": b["id"],
            "customer_id": cust["id"],
            "channel": "telegram",
            "fulfillment": "delivery",
            "items": [{"dish_id": taco["id"], "quantity": 3, "notes": "sin cebolla"}],
        },
    )
    assert r.status_code == 201, r.text
    order = r.json()
    assert order["status"] == "pending"
    assert order["total"] == "75.00"
    assert order["delivery_address"] == "Av. Siempre Viva 742"  # from customer default
    assert order["items"][0]["unit_price"] == "25.00"

    # Price changes don't affect existing order items (snapshot).
    await client.patch(f"{API}/dishes/{taco['id']}", json={"price": "99.00"})

    r = await client.post(
        f"{API}/orders/{order['id']}/items", json={"dish_id": soda["id"], "quantity": 2}
    )
    assert r.status_code == 201
    assert r.json()["total"] == "115.00"
    soda_item = next(i for i in r.json()["items"] if i["dish_id"] == soda["id"])

    r = await client.patch(
        f"{API}/orders/{order['id']}/items/{soda_item['id']}", json={"quantity": 1}
    )
    assert r.json()["total"] == "95.00"

    r = await client.delete(f"{API}/orders/{order['id']}/items/{soda_item['id']}")
    assert r.status_code == 200
    assert r.json()["total"] == "75.00" and len(r.json()["items"]) == 1

    r = await client.patch(f"{API}/orders/{order['id']}", json={"status": "confirmed"})
    assert r.json()["status"] == "confirmed"

    r = await client.patch(f"{API}/orders/{order['id']}", json={"delivery_address": None})
    assert r.status_code == 422

    r = await client.get(f"{API}/orders", params={"status": "confirmed"})
    assert [o["id"] for o in r.json()] == [order["id"]]
    r = await client.get(f"{API}/orders", params={"status": "pending"})
    assert r.json() == []

    # RESTRICT FKs: business, customer and dish can't be deleted while an order exists.
    assert (await client.delete(f"{API}/businesses/{b['id']}")).status_code == 409
    assert (await client.delete(f"{API}/customers/{cust['id']}")).status_code == 409
    assert (await client.delete(f"{API}/dishes/{taco['id']}")).status_code == 409

    assert (await client.delete(f"{API}/orders/{order['id']}")).status_code == 204
    assert (await client.get(f"{API}/orders/{order['id']}")).status_code == 404
    assert (await client.delete(f"{API}/customers/{cust['id']}")).status_code == 204


async def test_order_validation(client):
    b1 = await _business(client)
    b2 = await _business(client, name="Other")
    other_dish = await _dish(client, (await _menu(client, b2["id"]))["id"])
    unavailable = await _dish(
        client, (await _menu(client, b1["id"]))["id"], is_available=False
    )
    cust = await _customer(client, b1["id"])
    base = {
        "business_id": b1["id"],
        "customer_id": cust["id"],
        "channel": "whatsapp",
        "fulfillment": "pickup",
    }

    async def post(**extra):
        return (await client.post(f"{API}/orders", json={**base, **extra})).status_code

    assert await post(fulfillment="delivery") == 422  # no address anywhere
    assert await post(items=[{"dish_id": other_dish["id"]}]) == 422
    assert await post(items=[{"dish_id": unavailable["id"]}]) == 422
    assert await post(items=[{"dish_id": 12345}]) == 404
    assert await post(items=[{"dish_id": unavailable["id"], "quantity": 0}]) == 422
    assert await post(business_id=b2["id"]) == 422  # customer belongs to b1
    assert await post(channel="fax") == 422
    assert await post() == 201


async def test_conversation_crud(client):
    body = {
        "chat_id": str(uuid.uuid4()),
        "thread_id": str(uuid.uuid4()),
        "parent_thread_id": str(uuid.uuid4()),
    }
    r = await client.post(f"{API}/conversations", json=body)
    assert r.status_code == 201, r.text
    conv = r.json()
    assert conv["message_count"] == 0 and conv["b_active"] is True

    r = await client.patch(f"{API}/conversations/{conv['id']}", json={"message_count": 4})
    assert r.json()["message_count"] == 4

    r = await client.get(f"{API}/conversations", params={"chat_id": body["chat_id"]})
    assert len(r.json()) == 1

    assert (await client.delete(f"{API}/conversations/{conv['id']}")).status_code == 204
    assert (await client.get(f"{API}/conversations/{conv['id']}")).status_code == 404
