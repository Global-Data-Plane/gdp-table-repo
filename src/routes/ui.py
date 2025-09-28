# routes/ui_bp.py
import uuid
import os
import json
from flask import Blueprint, render_template, request, redirect, flash, current_app, abort, jsonify, url_for
from src.auth_helpers import _get_email, authenticated
from src.gdp_table_manager import GDPNotFoundException, GDPNotOwnerException, GDPNotPermittedException, owner

ui_bp = Blueprint('ui', __name__, url_prefix='/services/gdp')

API_ROUTES = [
    {
        "route": "/tables",
        "methods": ["GET"],
        "parameters": [],
        "description": "List all table names the user can access. Keys are returned."
    },
    {
        "route": "/upload/<name>",
        "methods": ["POST"],
        "parameters": ["table"],
        "description": "Upload a table in the table argument to the GDP repository. Returns the key of the uploaded table."
    },
    {
        "route": "/table/<key>",
        "methods": ["GET"],
        "parameters": [],
        "description": "Returns the table with key <key>, as an SDML object."
    },
    {
        "route": "/delete/<name>",
        "methods": ["DELETE"],
        "parameters": [],
        "description": "Delete the table with name <name>. Only the owner of the table can call this."
    },
    {
        "route": "/share/<name>",
        "methods": ["POST"],
        "parameters": ["share"],
        "description": "Share the table with name <name> with users in the list share. Note the contents of this list replaces the previous share. Only the owner of the table can call this."
    },
    {
        "route": "/get_table_names",
        "methods": ["GET"],
        "parameters": [],
        "description": "List all table names the user can access. Keys are returned."
    },
    {
        "route": "/get_tables",
        "methods": ["GET"],
        "parameters": [],
        "description": "Get a dictionary <key>: <schema> of all the tables the user can access."
    },
    {
        "route": "/get_table_schema",
        "methods": ["GET"],
        "parameters": ["table"],
        "description": "Get the schema for the table with key <table>."
    },
    {
        "route": "/get_range_spec",
        "methods": ["GET"],
        "parameters": ["table", "column"],
        "description": "Return the minimum and maximum values of the column as a list."
    },
    {
        "route": "/get_all_values",
        "methods": ["GET"],
        "parameters": ["table", "column"],
        "description": "Get all the values from column."
    },
    {
        "route": "/get_column",
        "methods": ["GET"],
        "parameters": ["table", "column"],
        "description": "Get all the values from column."
    },
    {
        "route": "/get_filtered_rows",
        "methods": ["POST"],
        "parameters": ["table", "columns (optional)", "filter_spec (optional)", "format (optional)"],
        "description": "Filter the rows according to the specification given by filter_spec. Returns the rows for which the resulting filter returns True. If columns is specified, return only those columns. Return in the format specified by format. If 'dict', return a list of dictionaries; if 'SDML', return a RowTable; if 'list' or omitted, return a list of lists of values."
    },
]


def _gen_navbar(active, email = None):
  def gen_link(link, active):
    class_val = 'active' if link[1] == active else 'inactive'
    return {"link": f"/services/gdp/ui/{link[1]}", "text": link[0], "class": class_val}
  
  base_links = [
    ('Home', ''),
    ('View Tables', 'view_tables')
  ]
  unloggedin_links = [
    ('Login', 'login')
  ]
  loggedin_links = [
    ('Upload Table', 'upload_table')
  ]
  links = base_links + (unloggedin_links if email is None else loggedin_links)
  result  = [gen_link(link, active) for link in links]
  return result

@ui_bp.route('/')
def root():
    user_agent = request.user_agent

    if user_agent.string.startswith('Mozilla'): #browser
        return redirect(url_for('ui.greeting'))
    return 'OK', 200

@ui_bp.route('/ui/')
@authenticated
def greeting(user):
  """Landing page: shows greeting and links to View Tables, Upload Table, etc."""
  # TODO: render greeting.html, pass navbar and email
  email = _get_email(user)
  return render_template('greeting.html', navbar_contents = _gen_navbar('greeting', email), routes=API_ROUTES, email=email, uuid=str(uuid.uuid4()))


def _make_link(kind, table):
    return f'/services/gdp/ui/{kind}/{table}'

def _add_to_link_dict(table, link_dict, existing):
    result = existing.copy()
    for (kind, url) in link_dict.items():
        result[kind] = _make_link(url, table)
    return result

def other_links(table):
    links = {
        'detail': 'view_table', 
        'download':  'download',
        'remotespec': 'remote_table_spec',
    }
    return _add_to_link_dict(table, links, {'table': table})

def owner_links(table):
    owner_kinds = {
    'share':  'share_table',
    'delete':  'delete_table'
    }
    table_name = table.split('/')[1] # defensive code needed here
    return _add_to_link_dict(table_name, owner_kinds, other_links(table))
          
    
@ui_bp.route('/ui/view_tables/')
@authenticated
def ui_view_tables(user):
    """List all tables available to user. Links: View Detail, Share, Delete, RemoteTable Spec."""
    # TODO: render tables.html, fetch tables for user
    email = _get_email(user)
    manager = current_app.table_manager  # type: ignore[attr-defined]
    print(f'Showing tables for {email}')
    tables = manager.all_user_tables(email, email is not None)
    def owned(table):
       return email is not None and owner(table) == email
    
    
    owned_tables = [table for table in tables if owned(table)] 
    other_tables = list(set(tables) - set(owned_tables))

    owned_tables = [owner_links(table) for table in owned_tables]
    other_tables = [other_links(table) for table in other_tables]

    return render_template(
       'view_tables.html',
       navbar_contents = _gen_navbar('view_tables', email),
       owned = owned_tables,
       other = other_tables,
       email=email, uuid=str(uuid.uuid4())
    )


@ui_bp.route('/ui/view_table/<owner>/<name>/')
@authenticated
def table_detail(user, owner, name):
    """View details of a table: schema, preview rows, actions (download, filter, share, spec, delete)."""
    manager = current_app.table_manager  # type: ignore[attr-defined]
    email  = _get_email(user)
    table_name = f'{owner}/{name}'
    links = owner_links(table_name) if email == owner else other_links(table_name)
    try:
      table  = manager.get_table_if_permitted(table_name, email, email is not None)
      num_columns = len(table.schema)
      rows = table.get_filtered_rows()
      if len(rows) > 10:
        first_rows = rows[:5]
        last_rows = rows[-5:]
        middle = ['...' for i in range(num_columns)]
        rows = first_rows + [middle] + last_rows
      return render_template(
        'view_table.html', 
        navbar_contents = _gen_navbar('view_table', email),
        schema = table.schema,
        table_name = table_name,
        rows = rows,
        uuid=str(uuid.uuid4()),
        num_columns = num_columns,
        links = links
      )
    except Exception as e:
       flash(str(e))
       return redirect('/services/gdp/view_tables')


def _delete_error_check(user, name):
    result = {
        "email": _get_email(user),
        "manager": current_app.table_manager,  # type: ignore[attr-defined]
        "error": False
    }
    if result["email"] is None:
        result["message"] = 'login required for /delete'
        result["error"] = True
    else:
        result["table_name"] = f'{result["email"]}/{name}'
        if not result["manager"].table_exists(result["table_name"]):
            result["message"] = 'table {result["table_name"]} does not exist'
            result["error"] = True
    return result



@ui_bp.route('/ui/delete_table/<name>/')
@authenticated
def ui_delete_table(user, name):
    """Delete a table (confirmation)."""
    # TODO: delete table, then redirect/flash message
    delete_detail = _delete_error_check(user, name)
    if delete_detail["error"]:
        flash(delete_detail["message"])
        return redirect(url_for('ui.ui_view_tables'))
    return render_template(
        'delete.html',
        delete_completion_url = url_for('ui.confirm_delete', name=name),
        table_name =  delete_detail["table_name"],
        navbar_contents = _gen_navbar('view_tables', delete_detail["email"]),
        email=delete_detail["email"], uuid=str(uuid.uuid4())
    )


@ui_bp.route('/ui/delete_table_confirm/<name>/', methods=['POST'])
@authenticated
def confirm_delete(user, name):
    delete_detail = _delete_error_check(user, name)
    if delete_detail["error"]:
        flash(delete_detail["message"])
    try:
        delete_detail["manager"].delete_table(delete_detail["table_name"])
        flash(f'{delete_detail["table_name"]} deleted')
    except Exception as e:
        flash(f'Error {repr(e)} in deleting delete_detail["table_name"]')
    return redirect(url_for('ui.ui_view_tables'))

                                            

@ui_bp.route('/ui/share_table/<name>/')
@authenticated
def share_table(user, name):
    """Share a table (e.g., generate link, send invite, etc.)."""
    
    email  = _get_email(user)
    if email == None:
        flash('Login required for /ui/share_table')
        redirect('/ui/view_tables/')
    manager = current_app.table_manager  # type: ignore[attr-defined]
    table_name = f'{email}/{name}'
    try:
        user_list = manager.get_user_access(table_name, email)
        emails = list(set(user_list) - {'HUB', 'PUBLIC'})
        return render_template(
            'share_table.html',
            navbar_contents = _gen_navbar('view_tables', email),
            share_list = emails,
            table_name = table_name,
            hub_shared = 'HUB' in user_list,
            public_shared = 'PUBLIC' in user_list,
            back_url = url_for('ui.table_detail', user=user, owner=email, name=name),
            share_action_url=url_for('ui.share_table_post', owner=email, name=name),
            email=email, uuid=str(uuid.uuid4()),
            
        )
    except GDPNotFoundException:
        flash(f"Couldn't find table {table_name}")
    except GDPNotOwnerException:
        flash(f"Only the owner can change the share of {table_name}")
    return redirect('/ui/view_tables/')

@ui_bp.route('/ui/share_table_post/<owner>/<name>', methods=['POST'])
@authenticated
def share_table_post(user, owner, name):
    email = _get_email(user)
    table_name = f"{owner}/{name}"
    manager = current_app.table_manager  # type: ignore[attr-defined]

    # Grab data from the form
    share_list_json = request.form.get('share_list', '[]')
    try:
        share_list = json.loads(share_list_json)
    except Exception:
        flash('Bad share list sent to share_table_post')
        return redirect(url_for(f'ui.share_table/{table_name}'))
    if bool(request.form.get('hub_shared')):
        share_list.append('HUB')
    if bool(request.form.get('public_shared')):
        share_list.append('PUBLIC')
    
    # (Optional) You may also want to process removed/added emails separately

    # Update sharing settings in your backend
    try:
        manager.update_access(table_name, email, share_list, replace=True)
        flash('Sharing updated!')
    except Exception as e:
        flash(f"Error updating share: {e}")

    # Redirect back to table detail (or view tables)
    return redirect(url_for('ui.table_detail',  owner=owner, name=name))


@ui_bp.route('/ui/download/<owner>/<name>')
@authenticated
def download_table(user, owner, name):
    manager = current_app.table_manager  # type: ignore[attr-defined]
    email = _get_email(user)
    table_name = f"{owner}/{name}"
    try:
        table = manager.get_table_if_permitted(table_name, email, email is not None)
        
        data = table.to_json()  # Or whatever serialization you use
        return (
            data,
            200,
            {
                "Content-Type": "application/json",
                "Content-Disposition": f"attachment; filename={name}"
            }
        )
    except GDPNotFoundException:
        flash(f'table {table_name} does not exist')
    except GDPNotPermittedException:
        flash(f'User {email} does not have access rights to {table_name}')
    return redirect(url_for('ui.ui_view_tables'))

@ui_bp.route('/ui/remote_table_spec/<owner>/<name>')
@authenticated
def remotetable_spec(user, owner, name):
    manager = current_app.table_manager # type: ignore[attr-defined]
    table_name = f"{owner}/{name}"
    try:
        table = manager._get_table(table_name)
    except GDPNotFoundException:
        flash(f"Couldn't find table {table_name}")
        return redirect(url_for('ui.ui_view_tables'))
    schema = table.schema
    # You can use current_app.config, or hardcode, or build from request
    base_url = current_app.config.get("GDP_BASE_URL", "http://localhost:5000/services/gdp")
    # If this app serves SDTP, you might just build a direct URL:
    remote_url = f"{base_url}/table/{table_name}"
    # Optionally include auth reference
    spec = {
        "type": "RemoteSDMLTable",
        "url": remote_url,
        "table": table_name,
        "schema": schema,
        "auth": {
            "type": "env",
            "variable": current_app.config.get('GDP_AUTH_TOKEN_VAR', "JUPYTER_HUB_TOKEN")
        }
    }
    # If you want to skip auth for now, just comment/remove that section
    response = current_app.response_class(
        response=json.dumps(spec, indent=2),
        status=200,
        mimetype='application/json'
    )
    # Make it downloadable (optional)
    base, ext = os.path.splitext(name)
    remote_spec_filename = f"{base}_remote{ext}"
    response.headers['Content-Disposition'] = f'attachment; filename="{remote_spec_filename}"'
    return response


@ui_bp.route('/ui/upload_table', methods=['GET', 'POST'])
@authenticated
def upload_table(user):
    email = _get_email(user)
    if email is None:
        flash('login required for /show_upload_form')
        return redirect(url_for('ui.ui_view_tables'))
    manager = current_app.table_manager  # type: ignore[attr-defined]
    if request.method == 'POST':
        table_name = request.form['table_name']
        if not table_name.endswith('.sdml'):
            flash("Table name must end with '.sdml'")
            return redirect(url_for('ui.upload_table'))
        file = request.files['table_file']
        sdml_str = file.read().decode('utf-8')
        key = f'{email}/{table_name}'
        # You might want to validate table_name, check for collisions, etc.
        # Save the file (parse as SDML if needed), set permissions, etc.
        manager.publish_table(key, sdml_str)
        flash('Table uploaded successfully!')
        return redirect(url_for('ui.ui_view_tables'))
    return render_template(
        'upload_table.html',
        upload_url = url_for('ui.upload_table'),
        navbar_contents = _gen_navbar('view_tables', email),
        email=email, uuid=str(uuid.uuid4())
    )



# ...add any additional routes as needed...


#-------------- Test Routes -----------------#

@ui_bp.route("/ui/test")
@authenticated
def ui_home_test(user):
    email = _get_email(user)
    navbar = _gen_navbar('/ui/greeting', email)
    if not email:
        navbar.append({"text": "Login", "link": "/hub/login", "class": "inactive"})
    else:
        navbar.append({"text": "Logout", "link": "/hub/logout", "class": "inactive"})
    return jsonify({
        "routes": API_ROUTES,
        "navbar_contents": navbar,
        "email": email,
        "uuid": "landing",
    })