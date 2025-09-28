from flask import Blueprint, request, jsonify, abort, Response
from src.auth_helpers import authenticated, _get_email
from flask import current_app
from src.gdp_table_manager import GDPNotFoundException, GDPNotPermittedException, GDPNotOwnerException
from src.config import HUB_URL
from sdtp import json_serialize
from json import dumps


repo_bp = Blueprint('repo', __name__, url_prefix='/services/gdp')

def _get_email_and_abort_if_unauthenticated(user, route):
  email = _get_email(user)
  if email is None:
    abort(400, f'{route} requires login/token access')
  return email

def _make_url(key):
  return f'{HUB_URL}/table/{key}'


@repo_bp.route('/tables', methods=['GET'])
@authenticated
def list_tables(user):
  """
  List all table names the user can access. keys are returned.
  """
  manager = current_app.table_manager  # type: ignore[attr-defined]
  email = _get_email(user)
  all_tables = manager.list_tables()
  result = [key for key in all_tables if manager.table_access_permitted(key, email, email is not None)]
  return jsonify(result)


@repo_bp.route('/upload/<name>', methods=['POST'])
@authenticated
def upload_table(user, name):
  """
  Owner uploads a new table (with name). Table data is in request body or file.
  """
  owner = _get_email_and_abort_if_unauthenticated(user, '/upload')
  valid_name  =  name if name.endswith('sdml') else name + '.sdml'
  sdml = None
  content_type = request.content_type or ""
    
  if content_type.startswith('application/json'):
    # JSON body: { "table": "<SDML string>" }
    data = request.get_json()
    sdml = data.get('table')
    if not sdml:
        return jsonify({"error": "Missing table in JSON"}), 400

  elif content_type.startswith('multipart/form-data'):
    # Multipart: file field named "table"
    if 'table' not in request.files:
        return jsonify({"error": "Missing table file"}), 400
    file = request.files['table']
    sdml = file.read().decode()  # Decode bytes to string

  else:
    return jsonify({"error": "Unsupported Content-Type"}), 400
   
  manager = current_app.table_manager  # type: ignore[attr-defined]
  key = f'{owner}/{valid_name}'
  manager.publish_table(key, sdml)
  return jsonify(key)

@repo_bp.route('/table', methods=['GET'])
@authenticated
def get_table(user):
  """
  Download a table by <owner>/<name> (the key).
  """
  email = _get_email(user)
  
  manager = current_app.table_manager  # type: ignore[attr-defined]
  key = request.args['table'] if 'table' in request.args else None
  current_app.logger.debug(f'in /table, email is {email}, key is {key}')
  if key is None:
    current_app.logger.debug(f'Aborting due to missing table parameter')
    return 'parameter table is missing in /table', 400
  try:
    table = manager.get_table_if_permitted(key, email, email is not None)
    current_app.logger.debug(f'/tables fetched table at {key}: {table}')
    result = table.to_dictionary()
    response = dumps(result, default=json_serialize)
    return Response(response, mimetype = "application/json")
  except GDPNotPermittedException:
    message = f"user {email} is not permitted to access {key}"
    current_app.logger.debug(f'/tables: GDPNotPermittedException: {message}')
    return message, 403
  except GDPNotFoundException:
    message = f"Table  {key} is not found"
    current_app.logger.debug(f'/tables: GDPNotFoundException: {message}')
    return jsonify(message), 404

@repo_bp.route('/delete/<name>', methods=['DELETE'])
@authenticated
def delete_table(user, name):
  """
  Owner deletes a table by name.
  """
  current_app.logger.debug(f'/delete, user is {user}, name is {name}')
  email = _get_email_and_abort_if_unauthenticated(user, '/delete')
  key = f'{email}/{name}'
  current_app.logger.debug(f'/delete, key is {key}')

  manager = current_app.table_manager  # type: ignore[attr-defined]
  try:
    manager.delete_table(key)
    current_app.logger.debug(f'/delete, {key} successfully deleted')
    return jsonify({'deleted': key})
  except  GDPNotFoundException as e:
    current_app.logger.debug(f'/delete, {key} not found')
    return repr(e), 404
  

@repo_bp.route('/share/<name>', methods=['POST'])
@authenticated
def share_table(user, name):
  """
  Owner updates (replaces) the share list for a table.
  Expects JSON: {"share": ["user1", "user2", ...]}
  """
  email = _get_email_and_abort_if_unauthenticated(user, '/share')
  key = f'{email}/{name}'
  manager = current_app.table_manager  # type: ignore[attr-defined]
  user_list = None
  content_type = request.content_type or ""
    
  if content_type.startswith('application/json'):
    # JSON body: { "table": "<SDML string>" }
    data = request.get_json()
    user_list = data.get('share')
    if not user_list:
      return jsonify({"error": "Missing share in JSON"}), 400

  else:
    return jsonify({"error": "Unsupported Content-Type"}), 400
  
  if type(user_list) != list:
    return jsonify(f'Error: parameter share must be a list, not {type(user_list)}'), 400
  try:
    manager.update_access(key, email, user_list)
    return jsonify({'update': _make_url(key)})
  except GDPNotFoundException as e:
    return repr(e), 404
