from typing import Any, Optional, List, Dict
from google.cloud import storage
import json
import re
from abc import ABC, abstractmethod

class GDPStorageManager(ABC):
  '''
  Abstract class for storing SDML Tables.  A concrete implementation
  instantiates a StorageManager to read and write SDML Tables as dictionaries
  '''

  def __init__(self):
    pass

  @abstractmethod
  def get_object(self, key:str) -> Optional[Any]:
    '''
    Reads the object at the specified key (path).
    Returns the parsed JSON object, an SDML Table or None if not found.
    '''
    raise NotImplementedError()
  
  @abstractmethod
  def put_object(self, key: str, object_data: Dict) -> None:
    '''
    Stores the given object_data  as JSON under key.
    '''
    raise NotImplementedError()
  
  @abstractmethod
  def delete_object(self, key: str) -> None:
    '''
    Deletes  the object stored under  key.
    '''
    raise NotImplementedError()
  
  @abstractmethod
  def _all_keys(self):
    '''
    Return all the keys of stored objects
    '''
    raise NotImplementedError()
  
  def all_keys_matching_pattern(self, pattern: Optional[str] = None) -> List[str]:
    '''
    Returns a list of all keys in the bucket matching the optional regex pattern.
    If no pattern is given, returns all  keys.
    '''
    keys = self._all_keys()
    if pattern is None:
      return keys
    regex = re.compile(pattern)
    return [k for k in keys if regex.search(k)]
  
  
  def clean_objects(self, pattern: str) -> None:
    '''
    Deletes all blobs whose keys match the given regex pattern.
    '''
    for key in self.all_keys_matching_pattern(pattern):
      self.delete_object(key)

  def clean_all(self) -> None:
    '''
    Deletes *all* blobs in the bucket. USE WITH CAUTION.
    '''
    for key in self.all_keys_matching_pattern():
      self.delete_object(key)

class GDPGoogleStorageManager(GDPStorageManager):
  '''
  Storage manager for SDML tables in GCS buckets.
  All interfaces use string keys (paths), not GDPObject.
  Handles JSON-serializable objects as blobs. All keys are GCS paths (e.g., 'project/table.sdml').
  '''
  def __init__(self, bucket_name: str):
    self.bucket_name = bucket_name
    self.client = storage.Client()
    self.bucket = self.client.bucket(bucket_name)

  def get_object(self, key: str) -> Optional[Any]:
    '''
    Reads the object at the specified key (path) in the GCS bucket.
    Returns the parsed JSON object, or None if not found.
    '''
    blob = self.bucket.blob(key)
    if not blob.exists():
      return None
    data = blob.download_as_text()
    try:
      return json.loads(data)
    except Exception:
      # Fallback: treat as string if not JSON
      return data

  def put_object(self, key: str, object_data: Any) -> None:
    '''
    Stores the given object_data (dict or string) as JSON in the bucket under key.
    '''
    blob = self.bucket.blob(key)
    if isinstance(object_data, str):
      blob.upload_from_string(object_data)
    else:
      blob.upload_from_string(json.dumps(object_data))

  def delete_object(self, key: str) -> None:
    '''
    Deletes the object at key (path) in the bucket.
    '''
    blob = self.bucket.blob(key)
    blob.delete()

  def _all_keys(self,) -> List[str]:
    '''
    Returns a list of all  keys in the bucket 
    '''
    blobs = self.client.list_blobs(self.bucket_name)
    return  [blob.name for blob in blobs]
    
  
class InMemoryStorageManager(GDPStorageManager):
  '''
  Storage manager for SDML tables in memory.
  All interfaces use string keys (paths), not GDPObject.
  All keys are GCS paths (e.g., 'project/table.sdml').
  '''
  def __init__(self):
    self.tables = {}

  def get_object(self, key: str) -> Optional[str]:
    '''
    Reads the object at the specified key (path).
    Returns a JSON obejct
    '''
    return self.tables.get(key)

  def put_object(self, key: str, object_data: str) -> None:
    '''
    Stores the given object_data (dict or string) under key.
    '''
    self.tables[key] = object_data

  def delete_object(self, key: str) -> None:
    '''
    Deletes the object at key (path).
    '''
    if key in self.tables:
      del self.tables[key]
    

  def _all_keys(self) -> List[str]:
    '''
    Returns a list of all  keys of stored objects.
    '''
    return  list(self.tables.keys())
    


