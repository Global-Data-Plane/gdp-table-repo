from sdtp import TableServer, InvalidDataException
from json import loads, dumps
from typing import Dict, Optional, List
from src.gdp_storage import ObjectMeta
from pydantic import BaseModel, ValidationError

class PermissionRecord(BaseModel):
  key: str
  owner: str
  users: List[str]
  roles: List[str] # Currently unused


def load_permission(blob: str) -> Optional[PermissionRecord]:
  return PermissionRecord.model_validate_json(blob)
 

def dump_permission(perm: PermissionRecord) -> str:
  return perm.model_dump_json(indent=2)


def perm_key(table_key: str) -> str:
  if table_key.endswith('.sdml'):
    return table_key[:-5] + '.perm'
  raise ValueError("Table key does not end with '.sdml'")

def owner(key):
  return key.split('/')[0]

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
  def __init__(self, storage_manager):
    '''
    Initialize storage, permissions, and table server.
    Loads all tables at startup so they're available in memory.
    '''
    self.storage_manager = storage_manager
    self.table_server = TableServer()
    self._cache_meta = {}


  def get_table(self, key):
    if not self.storage_manager.key_exists(key):
      raise GDPNotFoundException(key)

    # 2. Is it cached and up to date?
    cache_meta = self._cache_meta.get(key)
    blob_meta = self.storage_manager.get_meta(key)
    if (
      cache_meta
      and cache_meta.etag == blob_meta.etag
      and key in self.table_server.servers
    ):
      return self.table_server.servers[key]

    # 3. Otherwise, load from storage and update cache
    obj = self.storage_manager.get_object(key)
    self.table_server.add_sdtp_table_from_dictionary(key, obj)
    self._cache_meta[key] = blob_meta
    return self.table_server.servers[key]

  def table_exists(self, key: str) -> bool:
    '''
    Return true iff the table exists
    '''
    return self.storage_manager.key_exists(key)
    
  def list_tables(self, user: Optional[str] = None) -> List[str]:
    '''
    Return the list of table paths stored under a user or all users.

    Parameters:
      user: If provided, list only tables for this user (tables whose key starts with 'user/').
            If None, returns tables for all users.

    Returns:
      List of strings (table paths)
    '''

    return self.storage_manager.all_keys_matching(prefix=user, suffix='.sdml')
  
  def get_permissions_record(self, key: str) -> PermissionRecord:
    '''
    Return the PermissionsRecord for the table at key.  The table is at <foo>.sdml,
    and the permission record is at <foo>.perm.  Returns the stored PermissionRecord if
    there is one and it's valid.  If not, it returns the default PermissionRecord for
    a table, which has the table key and the owner, and a blank user and role list
    Arguments:
      key: key for the table
    Returns:
      PermissionRecord for the table
    Raises:
      GDPNotFoundException if the key is not a valid table key
    '''
    try:
      permissions_key = perm_key(key)
    except ValueError:
      raise GDPNotFoundException(key)
    stored_permissions = self.storage_manager.get_object(permissions_key)
    new_permissions_record =  PermissionRecord(key=key, owner=owner(key), users=[], roles=[])
    if stored_permissions is None:
      return new_permissions_record
    try:
      if isinstance(stored_permissions, str):
        return PermissionRecord.model_validate_json(stored_permissions)
      elif isinstance(stored_permissions, dict):
         return PermissionRecord.model_validate(stored_permissions)
      else:
        return new_permissions_record
    except ValidationError:
      return new_permissions_record
    
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
    permissions_record = self.get_permissions_record(gdp_table_key)
    return user == permissions_record.owner or user in permissions_record.users or 'PUBLIC' in permissions_record.users or user_is_hub_user and 'HUB' in permissions_record.users
    
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
      table = self.get_table(key)
    except GDPNotFoundException:
      raise  # Propagate if table does not exist

    # Then check access
    if not self.table_access_permitted(key, user, user_is_hub_user):
      raise GDPNotPermittedException(key, user)

    return table

  def update_access(self, key: str, user: str, user_list: list, replace = False):
    """
    Incrementally update access for a table:
    - Adds users in user_list to existing access
    - Removes existing users if and only if replace is True (default False)
    """
    
    self.get_table(key)
    # Fetch current permissions record
    perm_record = self.get_permissions_record(key)

    if perm_record.owner != user:
      raise GDPNotOwnerException(key, perm_record.owner, user)

    # Incrementally add new users
    if replace:
      perm_record.users = user_list
    else:
      existing_users = set(perm_record.users)
      updated_users = existing_users.union(set(user_list))
      perm_record.users = list(updated_users)
    
    permissions_key = perm_key(key)
    # Save updated permission record
    self.storage_manager.put_object(permissions_key, dump_permission(perm_record))

  def get_user_access(self, key: str, user: str):
    perm_record =  self.get_permissions_record(key)
    
    if perm_record.owner != user:
      raise GDPNotOwnerException(key, perm_record.owner, user)
    return perm_record.users.copy()
    


  def _validate_table(self, sdml_table):
    '''
    Placeholder for future SDML table validation.
    '''
    pass


  def publish_table(self, key, table_data):
    '''
    Store a table in the repository and update permissions.
    Parameters:
      key: the table  to store (owner/name.sdml)
      table_data: a JSON string or dict (table data)
     
    '''
    table_to_write = table_data if type(table_data) == str else dumps(table_data, indent=2)
    table_to_load = loads(table_to_write)
    self._validate_table(table_to_load)
    self.table_server.add_sdtp_table_from_dictionary(key, table_to_load)
    self.storage_manager.put_object(key, table_to_write)
    self._cache_meta[key] = self.storage_manager.get_meta(key)

  def delete_table(self, key):
    '''
    Delete a table from storage, permissions, and in-memory server.
    Raises GDPNotFoundException if it doesn't exist.
    '''
    if not self.table_exists(key):
      raise GDPNotFoundException(f'table {key} does not exist')
    self.storage_manager.delete_object(key)
    permissions_key = perm_key(key)
    self.storage_manager.delete_object(permissions_key)
    if key in self.table_server.servers:
      del self.table_server.servers[key]
    if key in self._cache_meta:
      del self._cache_meta[key]


  def clean_tables(self, user = None):
    '''
    Delete all tables for user.  If user = None, cleans all tables.
    '''
    table_keys = self.list_tables(user)
   
    for key in table_keys:
      self.delete_table(key)

  def get_table_info(self, user, user_is_hub_user):
    '''
    Get URLs/schemas for all tables accessible to this user.
    Returns a dict mapping table name to schema.
    '''
    table_names = self.list_tables()
    accessible_tables = [name for name in table_names if self.table_access_permitted(name, user, user_is_hub_user)]
    result = {}
    for name in accessible_tables:
      table = self.get_table(name)
      result[name] = table.schema
    return result
