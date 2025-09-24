from flask import Blueprint, current_app, redirect
from src.auth_helpers import authenticated

debug_bp = Blueprint('debug', __name__)

@debug_bp.route('/init')
@authenticated
def init(user):
  tables = {
    "aiko@galyleo.ai/table_1.sdml": {
      "owner": "aiko@galyleo.ai",
      "shares": ['PUBLIC'],
      "table": {
        "type": "RowTable",
        "schema": [{"name": "id", "type": "number"}, {"name": "name", "type": "string"}],
        "rows": [[1, "Alice"], [2, "Bob"]]
      }
    },
    "aiko@galyleo.ai/table_2.sdml":{
      "owner": "aiko@galyleo.ai",
      "shares": ['rick@galyleo.ai'],
      "table": {
        "type": "RowTable",
        "schema": [{"name": "score", "type": "number"}, {"name": "passed", "type": "boolean"}],
        "rows": [[95, True], [70, False]]
      }
    },
    "rick@galyleo.ai/table_3.sdml": {
      "owner": "rick@galyleo.ai",
      "shares": ["matt@galyleo.ai"],
      "table": {
        "type": "RowTable",
        "schema": [{"name": "id1", "type": "number"}, {"name": "name", "type": "string"}],
        "rows": [[1, "Mary"], [2, "Bill"]]
      }
    },
    "rick@galyleo.ai/table_4.sdml": {
      "owner": "rick@galyleo.ai",
      "shares": ["HUB"],
      "table": {
        "type": "RowTable",
        "schema": [{"name": "id2", "type": "number"}, {"name": "name", "type": "string"}],
        "rows": [[1, "Jack"], [2, "Jill"]]
      }
    }
  }
  manager = current_app.table_manager # type: ignore[attr-defined]
  for (key, desc) in tables.items():
    manager.publish_table(key, desc["owner"], desc["table"])
    manager.update_access(key, desc["owner"], desc["shares"])
  return redirect('/services/gdp/ui/view_tables')
