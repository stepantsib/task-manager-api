from uuid import uuid4


def _extract_token(resp_json: dict) -> str:
    # поддержим частые форматы:
    # {"access_token": "...", "token_type":"bearer"}
    # {"token": "..."}
    # {"accessToken": "..."}
    for key in ("access_token", "token", "accessToken"):
        if key in resp_json and resp_json[key]:
            return resp_json[key]
    raise AssertionError(f"Token not found in response: {resp_json}")


from uuid import uuid4

REGISTER_ENDPOINTS = [
    "/auth/register",
    "/auth/signup",
    "/auth/registration",
    "/register",
]

LOGIN_ENDPOINTS = [
    "/auth/login",
    "/auth/token",
    "/login",
]


def _extract_token(resp_json: dict) -> str:
    for key in ("access_token", "token", "accessToken"):
        if key in resp_json and resp_json[key]:
            return resp_json[key]
    raise AssertionError(f"Token not found in response: {resp_json}")


def _post_first_ok(client, endpoints: list[str], *, json=None, data=None):
    last = None
    for ep in endpoints:
        r = client.post(ep, json=json, data=data)
        last = (ep, r)
        if r.status_code < 400:
            return ep, r
    ep, r = last
    raise AssertionError(f"All endpoints failed. Last tried: {ep} -> {r.status_code} {r.text}")


def register_and_login(client, email: str, password: str) -> dict:
    # register (json)
    _, r = _post_first_ok(client, REGISTER_ENDPOINTS, json={"email": email, "password": password})
    assert r.status_code in (200, 201), r.text

    # login: сначала form (OAuth2PasswordRequestForm), потом json
    try:
        _, r = _post_first_ok(client, LOGIN_ENDPOINTS, data={"username": email, "password": password})
    except AssertionError:
        _, r = _post_first_ok(client, LOGIN_ENDPOINTS, json={"email": email, "password": password})

    assert r.status_code == 200, r.text
    token = _extract_token(r.json())
    return {"Authorization": f"Bearer {token}"}


def create_task(client, headers: dict, payload: dict) -> dict:
    r = client.post("/tasks", json=payload, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


def test_tasks_requires_auth(client):
    r = client.get("/tasks")
    assert r.status_code == 401, r.text


def test_user_cannot_access_foreign_task(client):
    email_a = f"a_{uuid4().hex}@test.local"
    email_b = f"b_{uuid4().hex}@test.local"
    password = "Password123!"

    headers_a = register_and_login(client, email_a, password)
    headers_b = register_and_login(client, email_b, password)

    task = create_task(client, headers_a, {"title": "A task", "status": "todo", "priority": 2})
    task_id = task["id"]

    # user B should not see A's task
    r = client.get(f"/tasks/{task_id}", headers=headers_b)
    assert r.status_code in (404, 403), r.text  # 404 предпочтительнее


def test_list_tasks_filter_sort_paginate(client):
    email = f"user_{uuid4().hex}@test.local"
    password = "Password123!"
    headers = register_and_login(client, email, password)

    # создадим набор задач
    create_task(client, headers, {"title": "t1", "status": "todo", "priority": 3})
    create_task(client, headers, {"title": "t2", "status": "done", "priority": 1})
    create_task(client, headers, {"title": "t3", "status": "todo", "priority": 2})

    # фильтр по статусу
    r = client.get("/tasks?status=todo", headers=headers)
    assert r.status_code == 200, r.text
    items = r.json()
    assert all(x["status"] == "todo" for x in items), items

    # сортировка по приоритету (по возрастанию)
    r = client.get("/tasks?sort=priority", headers=headers)
    assert r.status_code == 200, r.text
    items = r.json()
    pr = [x["priority"] for x in items]
    assert pr == sorted(pr), pr

    # пагинация
    r1 = client.get("/tasks?limit=2&offset=0", headers=headers)
    r2 = client.get("/tasks?limit=2&offset=2", headers=headers)
    assert r1.status_code == 200 and r2.status_code == 200
    assert len(r1.json()) == 2
    # во втором ответе может быть 1 элемент (если всего 3)
    assert len(r2.json()) in (0, 1, 2)
