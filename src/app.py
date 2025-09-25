from flask import Flask
import logging
import os
import sys
from src import permissions, gdp_storage
from src.config import GOOGLE_PROJECT, GDP_PERMISSIONS_DATABASE, GDP_PERMISSIONS_TABLE, BUCKET_NAME, CLOUD_ENVIRONMENT, FLASK_SECRET_KEY, FLASK_JINJA_TEMPLATE_DIR, FLASK_STATIC_ASSET_DIR, FLASK_STATIC_URL
from src.gdp_table_manager import GDPTableManager
from src.routes.sdtp_routes import sdtp_bp
from src.routes.repo import repo_bp
from src.routes.ui import ui_bp
from src.routes.debug import debug_bp
from src.auth_helpers import auth_bp

def _create_managers():
  if CLOUD_ENVIRONMENT == 'Google':
    return {
      "storage_manager": gdp_storage.GDPGoogleStorageManager(BUCKET_NAME),
      "permissions_manager": permissions.DatastoreManager(GOOGLE_PROJECT, GDP_PERMISSIONS_DATABASE, GDP_PERMISSIONS_TABLE)
    }
  else:
      return {
        "storage_manager": gdp_storage.InMemoryStorageManager(),
        "permissions_manager": permissions.InMemoryPermissionsManager()
      }
      

def create_app():
  app = Flask(
    __name__,
    template_folder=FLASK_JINJA_TEMPLATE_DIR,
    static_folder=FLASK_STATIC_ASSET_DIR,
    static_url_path=FLASK_STATIC_URL
  )

  managers = _create_managers()

  if app.logger.hasHandlers():
    app.logger.handlers.clear()

  handler = logging.StreamHandler(sys.stdout)
  handler.setLevel(logging.DEBUG)
  formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
  )
  handler.setFormatter(formatter)
  app.logger.addHandler(handler)
  app.logger.setLevel(logging.DEBUG)
  app.table_manager = GDPTableManager(managers["storage_manager"], managers["permissions_manager"])  # type: ignore[attr-defined]
  app.register_blueprint(sdtp_bp)
  app.register_blueprint(repo_bp)
  app.register_blueprint(ui_bp)
  app.register_blueprint(auth_bp)
  app.config['GDP_BASE_URL'] = os.environ.get('GDP_BASE_URL', 'http://localhost:5000/services/gdp')
  app.config['GDP_AUTH_TOKEN_VAR'] = os.environ.get('GDP_AUTH_TOKEN_VAR', 'JUPYTER_HUB_TOKEN')

  print("STATIC:", FLASK_STATIC_ASSET_DIR)
  print("TEMPLATE:", FLASK_JINJA_TEMPLATE_DIR)
  print("App static_folder:", app.static_folder)
  print("App template_folder:", app.template_folder)


  app.secret_key = FLASK_SECRET_KEY
  if os.getenv('DEBUG_GDP', 'false') == 'true':
    app.register_blueprint(debug_bp)
  return app

if __name__ == '__main__':
  app = create_app()
  app.run('0.0.0.0', port=5000, debug = True)