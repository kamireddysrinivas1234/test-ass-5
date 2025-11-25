from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database import SessionLocal
from app import crud_users, schemas, security, dependencies, calculation_factory, crud_calculations, models

client = TestClient(app)


def get_db() -> Session:
    return SessionLocal()


def get_token_for(username: str, password: str) -> str:
    # OAuth2PasswordRequestForm is urlencoded body
    resp = client.post(
        "/users/login",
        data={
            "username": username,
            "password": password,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "access_token" in data
    return data["access_token"]


def test_root_page_and_demo_login_and_addition():
    # Root HTML
    resp = client.get("/")
    assert resp.status_code == 200
    assert "FastAPI Calculator" in resp.text

    # Login with seeded demo user
    token = get_token_for("demo", "Test123!")

    # Simple add calculation via API
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"type": "add", "a": 2, "b": 3}
    resp = client.post("/calculations/", json=payload, headers=headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["result"] == 5
    assert body["type"] == "add"


def test_register_duplicate_user_and_login_error_paths():
    db = get_db()
    # Register a new user via CRUD so we can trigger duplicate path via API
    user_in = schemas.UserCreate(username="user1", email="user1@example.com", password="Pass123!")
    user = crud_users.create_user(db, user_in)
    assert user.username == "user1"

    # Calling API register again with same username should result in HTTP 400
    resp = client.post("/users/register", json=user_in.model_dump())
    assert resp.status_code == 400
    assert "Username already registered" in resp.text

    # Wrong username path in authenticate_user / login
    resp = client.post(
        "/users/login",
        data={"username": "nosuch", "password": "whatever"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 400

    # Wrong password path
    resp = client.post(
        "/users/login",
        data={"username": "user1", "password": "wrong"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 400


def test_security_helpers_and_dependencies_paths():
    # Hash & verify
    password = "Secret123!"
    hashed = security.hash_password(password)
    assert security.verify_password(password, hashed)

    # Token encode/decode happy path
    token = security.create_access_token({"sub": "demo"})
    payload = security.decode_access_token(token)
    assert payload and payload["sub"] == "demo"

    # decode_access_token invalid token path
    assert security.decode_access_token("invalid-token") is None

    db = get_db()

    # get_current_user happy path with real user
    good_token = security.create_access_token({"sub": "demo"})
    user = dependencies.get_current_user(token=good_token, db=db)
    assert user.username == "demo"

    # get_current_user invalid token path
    try:
        dependencies.get_current_user(token="bad-token", db=db)
    except Exception as exc:
        from fastapi import HTTPException
        assert isinstance(exc, HTTPException)
        assert exc.status_code == 401

    # get_current_user user-not-found path
    ghost_token = security.create_access_token({"sub": "ghost"})
    try:
        dependencies.get_current_user(token=ghost_token, db=db)
    except Exception as exc:
        from fastapi import HTTPException
        assert isinstance(exc, HTTPException)
        assert exc.status_code == 401


def test_calculation_factory_and_crud_calculations():
    # Direct factory usage for all operations
    add = calculation_factory.get_operation(schemas.CalculationType.add, 1, 2)
    sub = calculation_factory.get_operation(schemas.CalculationType.sub, 5, 3)
    mul = calculation_factory.get_operation(schemas.CalculationType.mul, 2, 4)
    div = calculation_factory.get_operation(schemas.CalculationType.div, 8, 2)
    assert add.compute() == 3
    assert sub.compute() == 2
    assert mul.compute() == 8
    assert div.compute() == 4

    # Invalid type branch in factory
    try:
        calculation_factory.get_operation("weird", 1, 1)  # type: ignore[arg-type]
    except ValueError as exc:
        assert "Unsupported type" in str(exc)

    db = get_db()

    # CRUD browse with and without user_id
    all_for_none = crud_calculations.browse_calculations(db, user_id=None)
    assert isinstance(all_for_none, list)

    # Create a user and a calculation linked to that user
    user_in = schemas.UserCreate(username="calcuser", email="calcuser@example.com", password="Calc123!")
    user = crud_users.create_user(db, user_in)

    calc_in = schemas.CalculationCreate(type=schemas.CalculationType.mul, a=3, b=4)
    created = crud_calculations.create_calculation(db, calc_in, user_id=user.id)
    assert created.result == 12

    # Browse with user_id (filtered)
    by_user = crud_calculations.browse_calculations(db, user_id=user.id)
    assert any(c.id == created.id for c in by_user)

    # Get calculation
    fetched = crud_calculations.get_calculation(db, created.id)
    assert fetched is not None and fetched.id == created.id

    # Update calculation (a, b, type all set)
    update = schemas.CalculationUpdate(type=schemas.CalculationType.add, a=10, b=5)
    updated = crud_calculations.update_calculation(db, fetched, update)
    assert updated.result == 15

    # Delete calculation
    crud_calculations.delete_calculation(db, updated)
    assert crud_calculations.get_calculation(db, updated.id) is None


def test_calculation_routes_full_flow_and_error_paths():
    # Use API-level endpoints; need a fresh user for ownership checks
    username = "apiuser"
    password = "Api123!"
    email = "apiuser@example.com"
    user_in = {"username": username, "email": email, "password": password}
    resp = client.post("/users/register", json=user_in)
    assert resp.status_code == 201

    token = get_token_for(username, password)
    headers = {"Authorization": f"Bearer {token}"}

    # Create four calculations to hit all operation types through the router
    payloads = [
        {"type": "add", "a": 1, "b": 2},
        {"type": "sub", "a": 5, "b": 3},
        {"type": "mul", "a": 2, "b": 4},
        {"type": "div", "a": 8, "b": 2},
    ]
    created_ids = []
    for p in payloads:
        resp = client.post("/calculations/", json=p, headers=headers)
        assert resp.status_code == 201
        created_ids.append(resp.json()["id"])

    # Browse
    resp = client.get("/calculations/", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 4

    # Read first calculation
    calc_id = created_ids[0]
    resp = client.get(f"/calculations/{calc_id}", headers=headers)
    assert resp.status_code == 200

    # Update using PUT
    resp = client.put(
        f"/calculations/{calc_id}",
        json={"type": "add", "a": 10, "b": 20},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["result"] == 30

    # Update using PATCH (only one field)
    resp = client.patch(
        f"/calculations/{calc_id}",
        json={"b": 5},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["result"] == 15

    # Delete
    resp = client.delete(f"/calculations/{calc_id}", headers=headers)
    assert resp.status_code == 204

    # Reading deleted calculation should raise 404
    resp = client.get(f"/calculations/{calc_id}", headers=headers)
    assert resp.status_code == 404

    # Protected route with invalid token: triggers first 401 branch
    resp = client.get("/calculations/", headers={"Authorization": "Bearer badtoken"})
    assert resp.status_code == 401

    # Ownership error path: user2 cannot access user1 calculation
    # register new user2
    resp = client.post(
        "/users/register",
        json={"username": "apiuser2", "email": "apiuser2@example.com", "password": "Api234!"},
    )
    assert resp.status_code == 201

    token2 = get_token_for("apiuser2", "Api234!")
    headers2 = {"Authorization": f"Bearer {token2}"}

    other_calc_id = created_ids[1]
    resp = client.get(f"/calculations/{other_calc_id}", headers=headers2)
    assert resp.status_code == 404

    resp = client.delete(f"/calculations/{other_calc_id}", headers=headers2)
    assert resp.status_code == 404


def test_division_by_zero_validation_error():
    # Login as demo and attempt invalid division to cover validator raise
    token = get_token_for("demo", "Test123!")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"type": "div", "a": 10, "b": 0}
    resp = client.post("/calculations/", json=payload, headers=headers)
    assert resp.status_code == 422
