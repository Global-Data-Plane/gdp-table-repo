"""
auth_helpers.py -- All authentication logic, decorators, and helper functions for GDP Flask apps.
No routes are declared here! Import authenticated and helpers into blueprints as needed.
"""

import os
import re
import requests
import user_agents
from urllib.parse import urlparse
from functools import wraps
from flask import request, make_response, session, redirect, Blueprint
from src.config import HUB_API_URL, HUB_URL, OAUTH_CALLBACK_URL, SERVICE_API_TOKEN, GDP_CLIENT_ID
from jupyterhub.services.auth import HubOAuth, HubAuth
auth_bp = Blueprint('auth', __name__)

print(f"[DEBUG] HUB_URL: {HUB_URL}")
print(f"[DEBUG] OAUTH_CALLBACK_URL: {OAUTH_CALLBACK_URL}")

# def _sanitize_callback():
#   if HUB_URL.endswith('/') and OAUTH_CALLBACK_URL.startswith('/'):
#     result = HUB_URL[:-1] + OAUTH_CALLBACK_URL
#     print(f"[DEBUG] _sanitize_callback (case 1): {result}")
#     return result
#   if OAUTH_CALLBACK_URL.startswith('/'):
#     result = HUB_URL + OAUTH_CALLBACK_URL
#     print(f"[DEBUG] _sanitize_callback (case 2): {result}")
#     return result
#   result = f'{HUB_URL}/{OAUTH_CALLBACK_URL}'
#   print(f"[DEBUG] _sanitize_callback (case 3): {result}")
#   return result

# CALLBACK_URI = _sanitize_callback()
# CALLBACK_URI = "http://localhost:8080/services/gdp/callback"
# print(f"[DEBUG] CALLBACK_URI: {CALLBACK_URI}")


if not HUB_URL or not OAUTH_CALLBACK_URL:
  raise RuntimeError("Missing HUB_URL or OAUTH_CALLBACK_URL env vars.")

if OAUTH_CALLBACK_URL.startswith('http://') or OAUTH_CALLBACK_URL.startswith('https://'):
  CALLBACK_URI = OAUTH_CALLBACK_URL
else:
  CALLBACK_URI = f"{HUB_URL.rstrip('/')}/{OAUTH_CALLBACK_URL.lstrip('/')}"

print(f"[DEBUG] CALLBACK_URI: {CALLBACK_URI}")


auth = HubOAuth(
  api_url=HUB_API_URL,
  api_token=SERVICE_API_TOKEN,
  oauth_client_id=GDP_CLIENT_ID,
  oauth_redirect_uri=CALLBACK_URI,
  cache_max_age=60
)
print(f"[DEBUG] auth.oauth_redirect_uri: {auth.oauth_redirect_uri}")

token_auth = HubAuth(
  api_url=HUB_API_URL,
  api_token=SERVICE_API_TOKEN
)

def is_browser(user_agent):
  ua = user_agents.parse(user_agent)
  return ua.is_pc or ua.is_mobile or ua.is_tablet

def oauth_ok():
  requestor = request.headers.get('User-Agent')
  if requestor and is_browser(requestor):
    return True
  if request.headers.get('Referer') or request.headers.get('Origin'):
    return True
  accept_header = request.headers.get('Accept', '')
  if "text/html" in accept_header:
    return True
  return False




# ... (env var and HubOAuth logic as above) ...



CALLBACK_PATH = urlparse(CALLBACK_URI).path

@auth_bp.route(CALLBACK_PATH)
def oauth_callback():
  code = request.args.get('code', None)
  if code is None:
    return "Forbidden", 403

  arg_state = request.args.get('state', None)
  cookie_state = request.cookies.get(auth.state_cookie_name)
  if arg_state is None or arg_state != cookie_state:
    return "Forbidden", 403

  try:
    token = auth.token_for_code(code)
  except Exception as e:
    return f"Token exchange failed: {e}", 400

  session["token"] = token
  next_url = auth.get_next_url(cookie_state) or "/services/gdp/"
  response = make_response(redirect(next_url))
  return response


def _list_users():
  headers = {'Authorization': f'token {SERVICE_API_TOKEN}'}
  result = requests.get(f'{HUB_API_URL}/users', headers=headers)
  return result.json()

def get_user_from_token(user_token):
  headers = {"Authorization": f"token {user_token}"}
  response = requests.get(f"{HUB_API_URL}/user", headers=headers)
  if response.status_code == 200:
    return response.json()
  return None

class DebugUser:
  def __init__(self):
    self.debug_user_name = os.getenv("DEBUG_GDP_USER", "debug_user")
  def set_user(self, name):
    self.debug_user_name = name
  def get_user_structure(self):
    return {
      'name': self.debug_user_name
    }
  def __str__(self):
    return f"DebugUser({self.debug_user_name})"

DEBUG = os.getenv('DEBUG_GDP', 'false') == 'true'
DEBUG_USER = DebugUser()

def _get_bearer_token(auth_header):
  parts = auth_header.split(" ")
  parts = [part for part in parts if len(part) > 0 and part != "token"]
  return parts[0]

def _get_user_from_forwarded_path():
  forwarded_path = request.headers.get("X-Forwarded-Path", "")
  match = re.match(r"^/user/([^/]+)/", forwarded_path)
  if match:
    return match.group(1)
  return None

def _is_request_from_hub_proxy():
  forwarded_host = request.headers.get("X-Forwarded-Host", "")
  hub_host = urlparse(HUB_URL).netloc
  return forwarded_host == hub_host

def authenticated(f):
  @wraps(f)
  def decorated(*args, **kwargs):
    if "JupyterHub-User" in request.headers:
      username = request.headers.get("JupyterHub-User")
      return f({"name": username}, *args, **kwargs)
    if _is_request_from_hub_proxy():
      user_from_path = _get_user_from_forwarded_path()
      if user_from_path:
        return f({"name": user_from_path}, *args, **kwargs)
    if DEBUG:
      if "Debug-User" in request.headers:
        DEBUG_USER.set_user(request.headers.get("Debug-User"))
      return f(DEBUG_USER.get_user_structure(), *args, **kwargs)
    if "Authorization" in request.headers:
      auth_header = request.headers.get("Authorization")
      auth_header = auth_header.strip() if auth_header is not None else ''
      if auth_header.startswith("token "):
        user_token = _get_bearer_token(auth_header)
        user = get_user_from_token(user_token)
        if user:
          return f(user, *args, **kwargs)
    token = session.get("token")
    user = auth.user_for_token(token) if token else None
    if user:
      return f(user, *args, **kwargs)
    elif oauth_ok():
      state = auth.generate_state(next_url=request.path)
      print(f"[DEBUG] auth.login_url: {auth.login_url}")
      print(f"[DEBUG] state: {state}")
      response = make_response(redirect(auth.login_url + f'&state={state}'))
      response.set_cookie(auth.state_cookie_name, state)
      return response
    else:
      return f({}, *args, **kwargs)
  return decorated

def _get_email(user):
  try:
    return user['name'] if type(user) == dict else user if type(user) == str else None
  except Exception:
    return None
