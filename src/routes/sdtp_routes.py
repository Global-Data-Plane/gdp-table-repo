# ------------- SDTP Endpoints (per protocol) ------------- #
from flask import Blueprint, request, jsonify, abort, Response
from src.auth_helpers import authenticated, _get_email
from flask import current_app
from src.gdp_table_manager import GDPNotFoundException, GDPNotPermittedException
from sdtp import InvalidDataException, json_serialize, RowTable
from json import dumps

sdtp_bp = Blueprint('sdtp', __name__, url_prefix='/services/gdp')

@sdtp_bp.route('/echo')
@authenticated
def echo(user):
   return jsonify([user, _get_email(user)])

@sdtp_bp.route('/get_table_names', methods=['GET'])
@authenticated
def get_table_names(user):
  print(user)
  # Return list of table names user can see
  manager = current_app.table_manager  # type: ignore[attr-defined]
  email = _get_email(user)
  all_tables = manager.all_user_tables(email, email is not None)
  return jsonify(all_tables)


@sdtp_bp.route('/get_tables', methods=['GET'])
@authenticated
def get_tables(user):
# Return table objects (dicts) with 
  manager = current_app.table_manager  # type: ignore[attr-defined]
  email = _get_email(user)
  is_hub_user = email is not None
  all_tables = manager.all_user_tables(email, is_hub_user)
  result = {}
  for key in all_tables:
    try:
      table = manager.get_table_if_permitted(key, email, is_hub_user)
      result[key] = table.schema
    except Exception: # can't happen
      pass
  return jsonify(result)

def _check_and_return_parameters(parameters, route):
  result = request.args.to_dict()
  missing = parameters - set(result.keys())
  if len(missing) > 0:
    abort(400, f'{route} requires missing parameters: {missing}')
  return result

def _get_table_for_query(parameters, user, route):
  parms = _check_and_return_parameters(parameters, route)
  manager = current_app.table_manager  # type: ignore[attr-defined]
  email = _get_email(user)
  is_hub_user = email is not None
  try:
    table = manager.get_table_if_permitted(parms["table"], email, is_hub_user)
    return (parms, table)
  except GDPNotPermittedException as e:
    abort(401, e)
  except GDPNotFoundException as e:
    abort(404, e)

  
@sdtp_bp.route('/get_table_schema', methods=['GET'])
@authenticated
def get_table_schema(user):
# Query: ?table=... or body JSON {"table": ...}
  (parms, table) = _get_table_for_query({'table'}, user, '/get_table_schema')
  return jsonify(table.schema)

def _column_query_result(result):
  return Response(
    dumps(result, default= json_serialize),
    mimetype = "application/json"
  )


@sdtp_bp.route('/get_range_spec', methods=['GET'])
@authenticated
def get_range_spec(user):
  # Query: ?table=...&column=...
  (parms, table) = _get_table_for_query({'table', 'column'}, user, '/get_range_spec')
  try:
    column = parms['column']
    result = (table.range_spec(column))
    return _column_query_result(result)
  except InvalidDataException as e:
     abort(400, f'{column} is not a valid column of table {parms["table"]}')



@sdtp_bp.route('/get_all_values', methods=['GET'])
@authenticated
def get_all_values(user):
  # Query: ?table=...&column=...
  (parms, table) = _get_table_for_query({'table', 'column'}, user, '/get_all_values')
  try:
    column = parms['column']
    return _column_query_result(table.all_values(column))
  except InvalidDataException as e:
    abort(400, f'{column} is not a valid column of table {parms["table"]}')

@sdtp_bp.route('/get_column', methods=['GET'])
@authenticated
def get_column(user):
  # Query: ?table=...&column=...
  (parms, table) = _get_table_for_query({'table', 'column'}, user, '/get_all_values')
  try:
    column = parms['column']
    return _column_query_result(table.get_column(column))
  except InvalidDataException as e:
     abort(400, f'{column} is not a valid column of table {parms["table"]}')

def _check_and_return_json_parameters(parameters, route):
    result = request.get_json(silent=True) or {}
    missing = parameters - set(result.keys())
    if missing:
        abort(400, f'{route} requires missing parameters: {missing}')
    return result

def _get_table_for_json_query(parameters, user, route):
    parms = _check_and_return_json_parameters(parameters, route)
    manager = current_app.table_manager  # type: ignore[attr-defined]
    email = _get_email(user)
    is_hub_user = email is not None
    try:
        table = manager.get_table_if_permitted(parms["table"], email, is_hub_user)
        return (parms, table)
    except GDPNotPermittedException as e:
        abort(401, e)
    except GDPNotFoundException as e:
        abort(404, e)

@sdtp_bp.route('/get_filtered_rows', methods=['POST'])
@authenticated
def get_filtered_rows(user):
# Body: {"table": ..., "filter_spec": ...}
  (parms, table) = _get_table_for_json_query({'table'}, user, '/get_filtered_rows')
  # Now parms is your JSON dict (e.g., may have filter_spec, columns, format)
  # table is the permitted table object
  # You can now pull out and validate filter_spec, columns, etc.
  # For example:
  filter_spec = parms.get('filter_spec')
  columns = parms.get('columns', [])
  fmt = parms.get('format', 'list')
  try:
    result = table.get_filtered_rows(filter_spec = filter_spec, columns = columns, format=fmt)
    if isinstance(result, RowTable):
      result = result.to_dictionary()
    return Response(
       dumps(result, default= json_serialize),
        mimetype = "application/json"
    )

  except Exception as e:
     abort(400, e)
  # Then do whatever: rows = table.filtered_rows(filter_spec, columns, fmt)
  # return jsonify(rows)
