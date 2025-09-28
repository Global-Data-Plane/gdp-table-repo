# tests/test_repo_routes.py

from helpers import run_and_check_result, run_and_check_post_result
from flask import current_app



def test_upload(client, tables_setup):
  table = {
     "type": "RowTable",
     "schema": [{"name": "test", "type": "number"}],
     "rows": [[1]]
  }

  resp = client.post("/services/gdp/upload/foo.sdml", json=table)
  assert resp.status_code == 400
  resp = client.post("/services/gdp/upload/foo.sdml", headers = {"Authorization": "userB"}, json=table)
  assert resp.status_code == 400 # needs to be json={"table": table}
  resp = client.post("/services/gdp/upload/foo.sdml", headers = {"Authorization": "userB"}, json={"table": table})
  assert resp.status_code == 200
  resp = client.get('/services/gdp/tables', headers = {"Authorization": "userB"})
  table_keys = resp.get_json()
  assert 'rick@ai/foo.sdml'  in table_keys
  resp = client.post("/services/gdp/upload/foo", headers = {"Authorization": "userC"}, json={"table": table})
  assert resp.status_code == 200
  resp = client.get('/services/gdp/tables', headers = {"Authorization": "userC"})
  table_keys = resp.get_json()
  assert 'matt@ai/foo.sdml' in table_keys

def test_download(client, tables_setup):
  table_1 = {
    "type": "RowTable",
    "schema": [{"name": "id", "type": "number"}, {"name": "name", "type": "string"}],
    "rows": [[1, "Alice"], [2, "Bob"]]
  }
  table_2 =  {
     "type": "RowTable",
     "schema": [{"name": "score", "type": "number"}, {"name": "passed", "type": "boolean"}],
     "rows":
       [[95, True], [70, False]]
  }
  table_3 = {
    "type": "RowTable",
    "schema": [{"name": "id1", "type": "number"}, {"name": "name", "type": "string"}],
    "rows": [[1, "Mary"], [2, "Bill"]]
  }

 
  route = "/services/gdp/table"
  run_and_check_result(client, route, {"Authorization": "userC"}, 400, '', 0)
  run_and_check_result(client, f"{route}?table=nope", {"Authorization": "userC"}, 404, '', 1)
  run_and_check_result(client, f"{route}?table=aiko@ai/table_2.sdml", {"Authorization": "userC"}, 403, '', 2)
  run_and_check_result(client, f"{route}?table=aiko@ai/table_2.sdml", {"Authorization": "userA"}, 200, table_2, 3)
  run_and_check_result(client, f"{route}?table=aiko@ai/table_2.sdml", {"Authorization": "userB"}, 200,table_2, 4)
  run_and_check_result(client, f"{route}?table=rick@ai/table_3.sdml", {"Authorization": "userC"}, 200,table_3, 5)
  run_and_check_result(client, f"{route}?table=aiko@ai/table_1.sdml", None, 200, table_1, 6)

def test_delete_table_success(client, tables_setup):
  response = client.delete('/services/gdp/delete/table_2.sdml', headers={'Authorization': 'userA'})
  assert response.status_code == 200
  assert response.json['deleted'] == 'aiko@ai/table_2.sdml'
  manager = current_app.table_manager # type: ignore[attr-defined]
  assert 'aiko@ai/table_2.sdml' not in manager.list_tables() 



def test_delete_table_user_none(client, tables_setup):
  response = client.delete('/services/gdp/delete/table_2.sdml')
  assert response.status_code == 400  # Adjust if your app uses a different code


def test_delete_table_not_found(client):
  response = client.delete('/services/gdp/delete/missing_table', headers={'Authorization': 'userA'})
  assert response.status_code == 404

def test_delete_table_user_bad(client, tables_setup):
  response = client.delete('/services/gdp/delete/table_2.sdml', headers={'Authorization': 'userC'})
  assert response.status_code == 404  # Adjust if your app uses a different code


def test_share(client, tables_setup):
    # Owner can share with another user
    pass

def test_list_tables(client, tables_setup):
  # User gets list of their own + shared + public
  route = "/services/gdp/tables"
  returned_tables = {
    'userA': ["aiko@ai/table_1.sdml", "aiko@ai/table_2.sdml", "rick@ai/table_3.sdml"],
    'userB': ["aiko@ai/table_1.sdml", "aiko@ai/table_2.sdml", "rick@ai/table_3.sdml", "rick@ai/table_4.sdml"],
    'userC': ["aiko@ai/table_1.sdml", "rick@ai/table_3.sdml", "rick@ai/table_4.sdml"]
  }
 
  i = 0
  for (user_token, result) in returned_tables.items():
    run_and_check_result(client, route, {"Authorization": user_token}, 200,result, i)
    i += 1
  run_and_check_result(client, route, None, 200, ["aiko@ai/table_1.sdml"], i)

def test_share_success(client, tables_setup):
  # Owner (rick@ai, userB) shares table_4 with aiko@ai
  resp = client.post(
    '/services/gdp/share/table_4.sdml',
    headers={'Authorization': 'userB'},
    json={'share': ['aiko@ai']}
  )
  assert resp.status_code == 200
    # Optionally: check that aiko@ai can now access table_4

def test_share_forbidden(client, tables_setup):
  # Non-owner (matt@ai, userC) tries to share rick@ai/table_4
  resp = client.post(
    '/services/gdp/share/table_4.sdml',
    headers={'Authorization': 'userC'},
    json={'share': ['aiko@ai']}
  )
  assert resp.status_code == 404

def test_share_unauth(client, tables_setup):
    # Unauthenticated (no header)
  resp = client.post(
    '/services/gdp/share/table_4.sdml',
    json={'share': ['aiko@ai']}
  )
  assert resp.status_code == 400

def test_share_missing_list(client, tables_setup):
    # Unauthenticated (no header)
  resp = client.post(
    '/services/gdp/share/table_4.sdml',
    headers={'Authorization': 'userB'}
  )
  assert resp.status_code == 400 

def test_share_bad_list(client, tables_setup):
    # Unauthenticated (no header)
  resp = client.post(
    '/services/gdp/share/table_4.sdml',
    headers={'Authorization': 'userB'},
    json={'share': 'aiko@ai'}
  )
  assert resp.status_code == 400 

  

# ...and any other core endpoints (update, unshare, etc.)
