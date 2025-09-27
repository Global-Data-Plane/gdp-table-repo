from google.cloud import datastore
import sqlite3
import json
from google.cloud import storage


PUBLIC = 'PUBLIC'  # Access is open to everyone if this permission is set
HUB = 'HUB'        # Access is open to all hub users if this permission is set

from typing import List, Optional, TypedDict
from abc import ABC, abstractmethod

class PermissionRecord(TypedDict):
  key: str
  owner: str
  users: List[str]
  roles: List[str] # Currently unused

class PermissionManager(ABC):
  '''
  Manages the interface between  service and the permissions database.
  The schema is simple: a pair (object_key, list of users). The list of users
  is just simple userid's, or the special id's PUBLIC and HUB, which indicate 
  broad permissions.
  Note that the only permissions managed here are read permissions.
  The users are stored as a list.
  This is designed to be used only from the top level of the service, 
  which should check for all errors -- this does no error-checking.
  '''
  def __init__(self):
    pass

  @abstractmethod
  def _get(self, key: str) -> Optional[PermissionRecord]:
    '''
    Get the PermissionRecord for key, returning None if not found.
    Most implemenentations will only need to implement _get, _put, _delete
    '''
    raise NotImplementedError()
  
  @abstractmethod
  def _put(self, key: str, record:PermissionRecord) -> None:
    '''
    Store  the PermissionRecord under  key, returning None.
    Most implemenentations will only need to implement _get, _put, _delete
    '''
    raise NotImplementedError()
  
  @abstractmethod
  def _delete(self, key: str) -> None:
    '''
    Delete the PermissionRecord under  key, returning None.
    Most implemenentations will only need to implement _get, _put, _delete
    '''
    raise NotImplementedError()
  
  @abstractmethod
  def all_keys(self) -> List:
    '''
    Return all the keys for all objects
    '''
    raise NotImplementedError()
    
  
  def create_object(
    self, key: str, owner: str
  ) -> None:
    """Create or update a permissions record for a file/table path."""
    perm_record: PermissionRecord = {
      "key": key,
      "owner": owner,
      "users": [],
      "roles": []
    }
    existing = self._get(key)
    if existing is not None:
      return
    
    # ...store in datastore (pseudo-code)
    self._put(key, perm_record)

  def update_object(
    self, key: str, owner: str, users: List[str]
  ) -> None:
    """Create or update a permissions record for a file/table path."""
    perm_record: PermissionRecord = {
      "key": key,
      "owner": owner,
      "users": users,
      "roles": []
    }
    self._put(key, perm_record)

  def get_permission_record(self, key: str) -> Optional[PermissionRecord]:
    """Return the permission record for a given path (if exists)."""
    result = self._get(key)
    if result:
      return result  # Should be a dict with key, owner, users
    return None

  def delete_permission_record(self, key: str) -> None:
    """Delete the permissions record for a given path."""
    self._delete(key)

  def has_access(self, key: str, user: str, user_is_hub_user: bool) -> bool:
    """Check if a user has access to the object at path `key`."""
    perm_record = self.get_permission_record(key)
    if not perm_record:
      return False
    return user == perm_record["owner"] or \
      user in perm_record["users"] or \
      user == perm_record["owner"] or \
      PUBLIC in perm_record["users"] or \
      (user_is_hub_user and HUB in perm_record["users"])

  def add_user_access(self, key: str, user: str) -> None:
    """Add a user to the share list for a given path."""
    perm_record = self.get_permission_record(key)
    if perm_record and user not in perm_record["users"]:
      perm_record["users"].append(user)
      self._put(key, perm_record)

  def get_users(self, key: str)->List[str]:
    """Get the list of users with access to the obect with key"""
    perm_record = self.get_permission_record(key)
    return [] if perm_record is None else perm_record["users"].copy()

  def remove_user_access(self, key: str, user: str) -> None:
    """Remove a user from the share list for a given path."""
    perm_record = self.get_permission_record(key)
    if perm_record and user in perm_record["users"]:
      perm_record["users"].remove(user)
      self._put(key, perm_record)

  def get_owner(self, key: str) -> Optional[str]:
    """Get the owner of a given path."""
    perm_record = self.get_permission_record(key)
    return perm_record["owner"] if perm_record else None

  def get_share_list(self, key: str) -> Optional[List[str]]:
    """Get the share list of a given path."""
    perm_record = self.get_permission_record(key)
    return perm_record["users"] if perm_record else None



class DatastoreManager(PermissionManager):
  '''
  Manages the interface between the service and the permissions datastore.
  The schema is simple: a pair (object_key, list of users). The list of users
  is just simple userid's, or the special id's PUBLIC and HUB, which indicate 
  broad permissions.
  Note that the only permissions managed here are read permissions.
  The users are stored as a list, but read as sets.
  This is designed to be used only from the top level of the service, 
  which should check for all errors -- this does no error-checking.
  '''
  def __init__(self, project, database, permissions_table):
    '''
    Parameters:
      project: the google project
      database: the database used to store objects
      permissions_table: the kind for objects
    '''
    self.project = project
    self.database = database
    self.datastore_client = datastore.Client(project=project, database=database)
    self.kind = permissions_table

  def _put(self, key, perm_record):
    db_key = self.datastore_client.key(self.kind, key)
    entity = datastore.Entity(key=db_key)
    entity.update(perm_record)
    self.datastore_client.put(entity)


  def _get(self, key):
    db_key =  self.datastore_client.key(self.kind, key)
    return self.datastore_client.get(db_key)
  
  def _delete(self, key: str) -> None:
    """Delete the permissions record for a given path."""
    db_key =  self.datastore_client.key(self.kind, key)
    self.datastore_client.delete(db_key)

  def all_keys(self) -> List:
    query = self.datastore_client.query(kind=self.kind) # Need to set the kind from the end
    query.keys_only()
    result =  list(query.fetch())
    return [entry.key.name for entry in result]
  
class SQLitePermissionManager(PermissionManager):
  '''
  SQLite3 Permissions Manager.  There is one table with two fields, key and a JSONified PermissionsRecord
  '''
  def __init__(self, db_path: str):
    self.db_path = db_path
    self._init_db()

  def _init_db(self):
    '''
    Ensure the path exists, updating if it does not
    '''
    with sqlite3.connect(self.db_path) as conn:
      conn.execute('''
        CREATE TABLE IF NOT EXISTS permissions (
          key TEXT PRIMARY KEY,
          value TEXT NOT NULL
        )
      ''')

  def _put(self, key: str, perm_record: PermissionRecord):
    value = json.dumps(perm_record, indent=2)
    with sqlite3.connect(self.db_path) as conn:
      conn.execute(
        'REPLACE INTO permissions (key, value) VALUES (?, ?)',
        (key, value)
      )

  def _get(self, key: str) -> Optional[PermissionRecord]:
    with sqlite3.connect(self.db_path) as conn:
      cur = conn.execute(
        'SELECT value FROM permissions WHERE key = ?', (key,))
      row = cur.fetchone()
      if row is None:
        return None
      return json.loads(row[0])

  def _delete(self, key: str):
    with sqlite3.connect(self.db_path) as conn:
      conn.execute(
        'DELETE FROM permissions WHERE key = ?', (key,))

  def all_keys(self) -> List[str]:
    with sqlite3.connect(self.db_path) as conn:
      cur = conn.execute('SELECT key FROM permissions')
      return [row[0] for row in cur.fetchall()]


class CachedBucketPermissionManager(PermissionManager):
  def __init__(self, bucket_name: str):
    self.bucket_name = bucket_name
    self.client = storage.Client()
    self.bucket = self.client.bucket(bucket_name)
    self.records = {}
    self._load_all()

  def _perm_path(self, key: str) -> str:
    return f"{key}.perm"

  def _load_all(self):
    for blob in self.client.list_blobs(self.bucket_name):
      if blob.name.endswith('.perm'):
        key = blob.name[:-5]
        data = blob.download_as_text()
        self.records[key] = json.loads(data)

  def _get(self, key: str) -> Optional[PermissionRecord]:
    return self.records.get(key)

  def _put(self, key: str, perm_record: PermissionRecord) -> None:
    blob = self.bucket.blob(self._perm_path(key))
    blob.upload_from_string(json.dumps(perm_record, indent=2), content_type='application/json')
    self.records[key] = perm_record

  def _delete(self, key: str) -> None:
    blob = self.bucket.blob(self._perm_path(key))
    blob.delete()
    self.records.pop(key, None)

  def all_keys(self) -> List[str]:
    return list(self.records.keys())

class  InMemoryPermissionsManager(PermissionManager):
  '''
  InMemory Permissions Manager, for testing
  '''
  def __init__(self):
    self.records = {}

  def _put(self, key, perm_record):
    self.records[key] = perm_record

  def _get(self, key):
    record = self.records.get(key)
    return record.copy() if record else None
  
  def _delete(self, key: str) -> None:
    """Delete the permissions record for a given path."""
    if self.records.get(key):
      del self.records[key]
  
  def all_keys(self):
    return list(self.records.keys())