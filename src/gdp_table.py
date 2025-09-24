from urllib.parse import urlparse

class GDPTable:
  '''
  A GDP Table is a pair: owner, name.
  The table_key is 'owner/name' and is used for storage, retrieval, and permissions.
  Only SDML tables are supported (name must end with .sdml).
  '''
  def __init__(self, owner, name):
    '''
    Parameters:
      owner: the user who owns the table
      name: the name of the table (must end with .sdml)
    '''
    if not name.endswith('.sdml'):
      raise GDPBadTableException(f'{owner}/{name}', 'Table names must end with .sdml')
    self.owner = owner
    self.name = name
    self.table_key = f'{owner}/{name}'

  def eq(self, gdp_table):
    return (
      self.owner == gdp_table.owner and
      self.name == gdp_table.name
    )

class GDPBadTableException(Exception):
  '''
  Raised for invalid GDP table creation or bad keys.
  '''
  def __init__(self, key, reason):
    self.key = key
    self.reason = reason
    self.message = f'Bad table {key}: {reason}'
    super().__init__(self.message)

def make_table_from_key(table_key):
  '''
  Given an table key, make a GDPTable from it.
  Expects <owner>/<name>.sdml only.
  '''
  parts = table_key.split('/')
  if len(parts) != 2:
    raise GDPBadTableException(table_key, 'Table keys must be of the form <owner>/<name>.sdml')
  owner, name = parts
  if not name.endswith('.sdml'):
    raise GDPBadTableException(table_key, 'Table name must end with .sdml')
  return GDPTable(owner, name)

def make_table_from_url(url, gdp_root_url):
  '''
  Given a URL, make a GDPTable from it.
  Only supports: <gdp_root_url>/<owner>/<name>.sdml
  '''
  components = urlparse(url)
  if f'{components.scheme}://{components.netloc}' != gdp_root_url:
    raise GDPBadTableException(url, f'Table urls must start with {gdp_root_url}')
  parts = components.path.split('/')
  if len(parts) != 3:
    raise GDPBadTableException(url, f'Table urls must be of the form {gdp_root_url}/<owner>/<name>.sdml')
  owner, name = parts[1], parts[2]
  if not name.endswith('.sdml'):
    raise GDPBadTableException(url, 'Table name must end with .sdml')
  return GDPTable(owner, name)

def check_or_raise_exception(input, name):
  '''
  
  name must end with .sdml 
  Parameters:
    input: original string
    name: name of the table
  Returns:
    No return
  Raises:
    GalyleoBadTableException
  '''
  if not name.endswith('.sdml'):
    raise GDPBadTableException(input, f'Tables must end with .sdml and {name} does not')

