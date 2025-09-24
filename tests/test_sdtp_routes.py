from helpers import run_and_check_result, run_and_check_post_result



def test_users(client):
  USERS = {
    "userA": {"email": "aiko@ai"},
    "userB": {"email": "rick@ai"},
    "userC": {"email": "matt@ai"}
  }
  for (user_token, email_struct) in USERS.items():
    run_and_check_result(client, "/services/gdp/echo", {"Authorization": user_token}, 200, [email_struct, email_struct['email']], 1)
  run_and_check_result(client, "/services/gdp/echo", None, 200, [None, None], 2)

   
def test_get_table_names(client, tables_setup):
  route = "/services/gdp/get_table_names"
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
  

def test_get_tables(client, tables_setup):
  route = "/services/gdp/get_tables"
  result = {
    "aiko@ai/table_1.sdml":[{"name": "id", "type": "number"}, {"name": "name", "type": "string"}], 
    "rick@ai/table_3.sdml": [{"name": "id1", "type": "number"}, {"name": "name", "type": "string"}],
    "rick@ai/table_4.sdml":[{"name": "id2", "type": "number"}, {"name": "name", "type": "string"}]
  }
  run_and_check_result(client, route, {"Authorization": "userC"}, 200, result, 0)
  result = {
    "aiko@ai/table_1.sdml": [{"name": "id", "type": "number"}, {"name": "name", "type": "string"}]
  }
  run_and_check_result(client, route, None, 200, result, 1)


def test_get_table_schema(client, tables_setup):
  route = "/services/gdp/get_table_schema"
  run_and_check_result(client, route, {"Authorization": "userC"}, 400, '', 0)
  run_and_check_result(client, f"{route}?table=nope", {"Authorization": "userC"}, 404, '', 1)
  run_and_check_result(client, f"{route}?table=aiko@ai/table_2.sdml", {"Authorization": "userC"}, 401, '', 2)
  run_and_check_result(client, f"{route}?table=aiko@ai/table_2.sdml", {"Authorization": "userA"}, 200,[ {"name": "score", "type": "number"}, {"name": "passed", "type": "boolean"}], 3)
  run_and_check_result(client, f"{route}?table=aiko@ai/table_2.sdml", {"Authorization": "userB"}, 200,[ {"name": "score", "type": "number"}, {"name": "passed", "type": "boolean"}], 4)
  run_and_check_result(client, f"{route}?table=rick@ai/table_3.sdml", {"Authorization": "userC"}, 200,[{"name": "id1", "type": "number"}, {"name": "name", "type": "string"}], 5)
  run_and_check_result(client, f"{route}?table=aiko@ai/table_1.sdml", None, 200,[{"name": "id", "type": "number"}, {"name": "name", "type": "string"}], 6)


def test_get_range_spec(client, tables_setup):
  route = "/services/gdp/get_range_spec"
  run_and_check_result(client, route, {"Authorization": "userC"}, 400, '', 0)
  run_and_check_result(client, f"{route}?table=nope&column=id", {"Authorization": "userC"}, 404, '', 1)
  run_and_check_result(client, f"{route}?table=aiko@ai/table_2.sdml&column=score", {"Authorization": "userC"}, 401, '', 2)
  run_and_check_result(client, f"{route}?column=score", {"Authorization": "userA"}, 400, '', 3)
  run_and_check_result(client, f"{route}?table=aiko@ai/table_2.sdml", {"Authorization": "userA"}, 400, '', 4)
  run_and_check_result(client, f"{route}?table=aiko@ai/table_2.sdml&column=score", {"Authorization": "userA"}, 200, [70, 95], 5)
  run_and_check_result(client, f"{route}?table=aiko@ai/table_2.sdml&column=score", {"Authorization": "userB"}, 200, [70, 95], 8)
  run_and_check_result(client, f"{route}?table=rick@ai/table_3.sdml&column=id1", {"Authorization": "userC"}, 200, [1, 2], 7)
  run_and_check_result(client, f"{route}?table=aiko@ai/table_1.sdml&column=id", None, 200, [1, 2],8)

def test_get_all_values(client, tables_setup):
  route = "/services/gdp/get_all_values?table=aiko@ai/table_1.sdml&column=id"
  run_and_check_result(client, route, {"Authorization": "userC"}, 200, [1, 2],0)

def test_get_column(client, tables_setup):
  route = "/services/gdp/get_column?table=aiko@ai/table_1.sdml&column=id"
  run_and_check_result(client, route, None, 200, [1, 2], 0)


def test_get_filtered_rows(client, tables_setup):
  route="/services/gdp/get_filtered_rows"
  body = {"columns": ["id"]}
  run_and_check_post_result(client, route, {"Authorization": "userA"}, body, 400, '', 0 )
  body = {"columns": ["id"], "table": "aiko@ai/table_2.sdml"}
  run_and_check_post_result(client, route, {"Authorization": "userC"}, body, 401, '', 1 )
  body = {"columns": ["id"], "table": "aiko@ai/table_2.sdml", "filter_spec": "bad"}
  run_and_check_post_result(client, route, {"Authorization": "userA"}, body, 400, '', 2 )
  body = {"columns": ["id"], "table": "aiko@ai/table_2.sdml", "format": "nope"}
  run_and_check_post_result(client, route, {"Authorization": "userA"}, body, 400, '', 3 )
  body = {"columns": "nope", "table": "aiko@ai/table_2.sdml"}
  run_and_check_post_result(client, route, {"Authorization": "userA"}, body, 400, '', 4 )
  body = {"table": "aiko@ai/table_2.sdml", "format": "list"}
  run_and_check_post_result(client, route, {"Authorization": "userA"}, body, 200, [[95, True], [70, False]], 5 )
  body = {"table": "aiko@ai/table_2.sdml"}
  run_and_check_post_result(client, route, {"Authorization": "userA"}, body, 200, [[95, True], [70, False]], 6 )
  body = {"table": "aiko@ai/table_2.sdml", "format": "dict"}
  run_and_check_post_result(client, route, {"Authorization": "userA"}, body, 200, [{"score": 95, "passed": True}, {"score":70, "passed": False}], 7 )
  body = {"table": "aiko@ai/table_2.sdml", "format": "sdml"}
  run_and_check_post_result(client, route, {"Authorization": "userA"}, body, 200, {
      "type": "RowTable",
      "schema": [{"name": "score", "type": "number"}, {"name": "passed", "type": "boolean"}],
      "rows": [[95, True], [70, False]]
    }, 8 )
  body = {"table": "aiko@ai/table_2.sdml", "filter_spec": {"operator": "IN_LIST", "column": "passed", "values": [True]}}
  run_and_check_post_result(client, route, {"Authorization": "userA"}, body, 200, [[95, True]], 9 )
  body = {"table": "aiko@ai/table_2.sdml", "columns": ["score"],"filter_spec": {"operator": "IN_LIST", "column": "passed", "values": [True]}}
  run_and_check_post_result(client, route, {"Authorization": "userA"}, body, 200, [[95]], 10 )
