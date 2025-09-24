# tests/helpers.py

def run_and_check_result(client, route, headers, expected_code, expected_result, id):
    resp = client.get(route, headers=headers) if headers else client.get(route)
    assert resp.status_code == expected_code, f'test {id}'
    if resp.status_code < 400:
        data = resp.get_json()
        assert data == expected_result, f'test {id}'

def run_and_check_post_result(client, route, headers, body, expected_code, expected_result, id):
    if headers and body:
        resp = client.post(route, headers=headers, json=body)
    elif headers:
        resp = client.post(route, headers=headers)
    elif body:
        resp = client.post(route, json=body)
    else:
        resp = client.post(route)
    assert resp.status_code == expected_code, f'test {id}'
    if resp.status_code < 400:
        data = resp.get_json()
        assert data == expected_result, f'test {id}'
