from sdtp import TableServer, InvalidDataException
from json import loads, dumps
from google.cloud.exceptions import NotFound
import src.permissions
from typing import Dict
from sdtp import TableNotFoundException


class GDPNotFoundException(Exception):
  '''
  Raised when a GDP Object (table) has not been found.
  '''
  def __init__(self, url):
    self.message = f'Could not find table at URL {url}'
    self.url = url
    super().__init__(self.message)

class GDPNotPermittedException(Exception):
  '''
  Raised when the user doesn't have access to the requested table.
  '''
  def __init__(self, url, user):
    self.message = f'User {user} is not permitted to access table at {url}'
    self.url = url
    self.user = user
    super().__init__(self.message)

class GDPNotOwnerException(Exception):
  def __init__(self, key, owner, user):
    self.message = f'User {user} is not the owner of {key}.  The owner is {owner}'
    super().__init__(self.message)
    self.owner = owner
    self.key = key
    self.user = user


class GDPTableManager:
  '''
  Manages storage, retrieval, and permissions for GDP/SDML tables only.
  This is a thin overlay on the storage, permissions, and table server managers.
  Ensures the different layers remain consistent, especially for permissioning.
  '''
  def __init__(self, storage_manager, permissions_manager):
    '''
    Initialize storage, permissions, and table server.
    Loads all tables at startup so they're available in memory.
    '''
    self.storage_manager = storage_manager
    self.permissions_manager = permissions_manager
    self.table_server = TableServer()
    table_paths = self.list_tables()
    for path in table_paths:
      table_data = self.storage_manager.get_object(path)
      self.table_server.add_sdtp_table_from_dictionary(path, table_data)

  def table_exists(self, key: str) -> bool:
    '''
    Return true iff the table exists
    '''
    return key in self.permissions_manager.all_keys() #inefficient, we should do better


  def list_tables(self, user='[^/]+'):
    '''
    Return the list of table table paths stored under a user or all users.
    Parameters:
      user: user pattern (defaults to '[^/]+', i.e., all users)
    Returns:
      List of strings (table paths)
    '''

    table_paths = self.storage_manager.all_keys_matching_pattern(f'^{user}/[^/]+.sdml')
    return table_paths

  def table_access_permitted(self, gdp_table_key, user, user_is_hub_user):
    '''
    Check that the GDP table can be accessed by the user.
    Parameters:
      gdp_table_key: the key of the  requested table
      user: the user requesting access
      user_is_hub_user: True iff the user is an accredited hub user
    Returns: 
      True if permitted, False otherwise
    '''
                
    return self.permissions_manager.has_access(gdp_table_key, user, user_is_hub_user)

  def _get_table(self, key):
    '''
    Get the table with key  from the in-memory table server.
    Raises GDPNotFoundException if the table cannot be found.
    '''
    try:
      return self.table_server.get_table(key)
    except (NotFound, InvalidDataException, TableNotFoundException):
      raise GDPNotFoundException(key)
    
  def all_user_tables(self, user, is_hub_user):
    '''
    Get all of the keys of the tables this user can access
    '''
    tables = self.list_tables()
    return [key for key in tables if self.table_access_permitted(key, user, is_hub_user)]

  def get_table_if_permitted(self, key, user, user_is_hub_user):
    '''
    Check existence first, then access, and return table if allowed.
    Raises GDPNotFoundException or GDPNotPermittedException as appropriate.
    '''
    # Check existence first
    try:
      table = self._get_table(key)
    except GDPNotFoundException:
      raise  # Propagate if table does not exist

    # Then check access
    if not self.table_access_permitted(key, user, user_is_hub_user):
      raise GDPNotPermittedException(key, user)

    return table

  def update_access(self, key: str, email: str, user_list: list, replace = False):
    """
    Incrementally update access for a table:
    - Adds users in user_list to existing access
    - Removes existing users if and only if replace is True (default False)
    """
    try:
      self._get_table(key)  # Ensure table exists first
    except (NotFound, InvalidDataException):
      raise GDPNotFoundException(key)

    # Fetch current permissions record
    perm_record = self.permissions_manager._get(key)
    if perm_record is None:
      raise GDPNotFoundException(key)

    # Incrementally add new users
    if replace:
      perm_record["users"] = user_list
    else:
      existing_users = set(perm_record.get("users", []))
      updated_users = existing_users.union(set(user_list))
      perm_record["users"] = list(updated_users)

    # Save updated permission record
    self.permissions_manager._put(key, perm_record)

  def get_user_access(self, key: str, user: str):
    perm_record = self.permissions_manager._get(key)
    if perm_record is None:
      raise GDPNotFoundException(key)
    if perm_record["owner"] != user:
      raise GDPNotOwnerException(key, perm_record["owner"], user)
    return perm_record["users"].copy()
    


  def _validate_table(self, sdml_table):
    '''
    Placeholder for future SDML table validation.
    '''
    pass

  def consistency_errors(self)->Dict:
    key_sets = {
      "server": set(self.table_server.servers.keys()),
      "permissions": set(self.permissions_manager.all_keys()),
      "storage": set(self.storage_manager.all_keys_matching_pattern())
    }
    master = key_sets["server"].union(key_sets["permissions"]).union(key_sets["storage"])
    result = {}
    for key_type in key_sets.keys():
      result[key_type] = master - key_sets[key_type]
    return result


  def publish_table(self, key, owner, table_data):
    '''
    Store a table in the repository and update permissions.
    Parameters:
      key: the GDPTable to store
      table_data: a JSON string or dict (table data)
      share_set: set of users to share the table with (includes owner automatically)
    '''
    table_to_write = table_data if type(table_data) == str else dumps(table_data, indent=2)
    table_to_load = loads(table_to_write)
    self._validate_table(table_to_load)
    self.table_server.add_sdtp_table_from_dictionary(key, table_to_load)
    self.storage_manager.put_object(key, table_to_write)
    self.permissions_manager.create_object(key, owner)

  def delete_table(self, key):
    '''
    Delete a table from storage, permissions, and in-memory server.
    Raises GDPNotFoundException if it doesn't exist.
    '''
    if not key in self.table_server.servers.keys():
      raise GDPNotFoundException(f'table {key} does not exist')
    try:
      self.storage_manager.delete_object(key)
      self.permissions_manager.delete_permission_record(key)
      if key in self.table_server.servers:
        del self.table_server.servers[key]
    except NotFound:
      raise GDPNotFoundException(f'table {key} does not exist')

  def clean_tables(self, user_pattern='*'):
    '''
    Delete all tables for users matching the pattern.
    '''
    table_keys = self.list_tables(user_pattern)
   
    for key in table_keys:
      self.delete_table(key)

  def get_table_info(self, user, user_is_hub_user):
    '''
    Get URLs/schemas for all tables accessible to this user.
    Returns a dict mapping table name to schema.
    '''
    table_names = self.table_server.servers.keys()
    table_names = [name for name in table_names if self.table_access_permitted(name, user, user_is_hub_user)]
    result = {}
    for name in table_names:
      result[name] = self.table_server.servers[name].schema
    return result
