import os

HUB_API_URL = os.environ.get('JUPYTERHUB_API_URL',' ')
SERVICE_API_TOKEN = os.environ.get('GDP_SERVICE_API_TOKEN','foo')
HUB_URL = os.environ.get('JUPYTERHUB_URL',' ')
GDP_CLIENT_ID = os.environ.get('GDP_CLIENT_ID','bar')
OAUTH_CALLBACK_URL = '/services/gdp/callback'
GDP_ROOT_URL = os.environ.get('GDP_ROOT_URL','')
GOOGLE_PROJECT = os.environ.get('GOOGLE_PROJECT','')
BUCKET_NAME = os.environ.get('BUCKET_NAME','')
JUPYTER_HUB_API_TOKEN = os.environ.get('JUPYTER_HUB_API_TOKEN','')
GDP_HOST = os.environ.get("GDP_HOST", "http://localhost")
GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
# if GOOGLE_APPLICATION_CREDENTIALS is None or not os.path.exists(GOOGLE_APPLICATION_CREDENTIALS):
#     print('Error!  GOOGLE_APPLICATION_CREDENTIALS is not set or does not exist')
#     exit(1)
STORAGE_ENVIRONMENT = os.getenv("STORAGE_ENVIRONMENT", "MEMORY")
#--- Flask Settings ----
FLASK_SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', 'super-secret-key')

FLASK_STATIC_ASSET_DIR = os.environ.get("FLASK_STATIC_ASSET_DIR", "../static")
FLASK_JINJA_TEMPLATE_DIR = os.environ.get("FLASK_JINJA_TEMPLATE_DIR", "../templates")
FLASK_STATIC_URL = os.environ.get("FLASK_STATIC_URL", "/static")
