from typing import Any, Optional, List, Dict
import sys
from uuid import uuid4
from google.cloud import storage
import json
from abc import ABC, abstractmethod

from typing import Optional
from datetime import datetime

class ObjectMeta:
    def __init__(
        self,
        etag: str,
        last_modified: datetime,
        size: int,
        content_type: Optional[str] = None,
        version_id: Optional[str] = None
    ):
        self.etag = etag
        self.last_modified = last_modified
        self.size = size
        self.content_type = content_type
        self.version_id = version_id

    def __repr__(self):
        return (
            f"<BlobMeta etag={self.etag} last_modified={self.last_modified} "
            f"size={self.size} content_type={self.content_type} version_id={self.version_id}>"
        )


class GDPStorageManager(ABC):
  '''
  Abstract class for storing SDML Tables.  A concrete implementation
  instantiates a StorageManager to read and write SDML Tables as dictionaries
  '''

  def __init__(self):
    pass

  @abstractmethod
  def key_exists(self, key: str) -> bool:
    '''
    Returns true iff an object exists under key key
    '''

  @abstractmethod
  def get_meta(self, key: str) -> Optional[ObjectMeta]:
    '''
    Reads the metadata of the object at the specified key (path).
    Returns an ObjectMeta or  None if not found.
    '''
    raise NotImplementedError()
  

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
  
  def all_keys_matching(self, prefix: Optional[str] = None, suffix: Optional[str] = None) -> List[str]:
    '''
    Returns a list of all keys in the bucket matching the optional regex pattern.
    If no pattern is given, returns all  keys.
    '''
    keys = self._all_keys()
    if prefix is not None:
      keys = [key for key in keys if key.startswith(prefix)]
    if suffix is not None:
      keys = [key for key in keys if key.endswith(suffix)]
    return keys
  

  def clean_all(self) -> None:
    '''
    Deletes *all* blobs in the bucket. USE WITH CAUTION.
    '''
    for key in self.all_keys_matching():
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

  def key_exists(self, key: str) -> bool:
    blob = self.bucket.blob(key)
    return  blob.exists()

  def get_meta(self, key) -> Optional[ObjectMeta]:
    '''
    Get the metadata associated with a key.  Reads the blob and then returns the 
    metadata object assocated with it
    '''
    blob = self.bucket.blob(key)
    if not blob.exists():
      return None
    # `blob` is a google.cloud.storage.Blob object (after get_blob or list_blobs)
    if blob is  None:
      return None
    return ObjectMeta(
        etag=blob.etag if blob.etag else '',
        last_modified=blob.updated if blob.updated else datetime.now(),
        size=blob.size if blob.size is not None else 0,
        content_type=blob.content_type,
        version_id=getattr(blob, 'generation', None)
    )
  
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
    self.bucket.delete_blob(key)
      

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
    self.objects = {}
    self.meta:Dict[str, ObjectMeta] = {}

  def key_exists(self, key):
    return key in self.objects.keys()
  
  def get_meta(self, key):
    if self.key_exists(key):
      return self.meta[key]

  def get_object(self, key: str) -> Optional[str]:
    '''
    Reads the object at the specified key (path).
    Returns a JSON obejct
    '''
    return self.objects.get(key)

  def put_object(self, key: str, object_data) -> None:
    '''
    Stores the given object_data (dict or string) under key.
    '''
    self.objects[key] = object_data
    object_size = sys.getsizeof(object_data)
    version = str(uuid4())
    if key in self.meta.keys():
      meta = self.meta[key]
      meta.etag = version
      meta.version_id = version
      meta.last_modified = datetime.now()
      meta.content_type = 'application/dict'
      meta.size = object_size
    else:
      self.meta[key] = ObjectMeta(
        etag=version,
        last_modified=datetime.now(),
        size=object_size,
        content_type='application/dict',
        version_id=version
      )


  def delete_object(self, key: str) -> None:
    '''
    Deletes the object at key (path).
    '''
    if key in self.objects:
      del self.objects[key]
    if key in self.meta:
      del self.meta[key]
    

  def _all_keys(self) -> List[str]:
    '''
    Returns a list of all  keys of stored objects.
    '''
    return  list(self.objects.keys())
    


