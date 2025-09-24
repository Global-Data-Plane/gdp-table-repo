from flask import Blueprint, request, session, redirect, make_response
from auth_helpers import auth  # import your configured HubOAuth instance
from config import OAUTH_CALLBACK_URL, GDP_ROOT_URL

auth_bp = Blueprint('auth', __name__, url_prefix='/services/gdp')

@auth_bp.route(OAUTH_CALLBACK_URL)
def oauth_callback():
  code = request.args.get('code', None)
  if code is None:
      return "Forbidden", 403
  arg_state = request.args.get('state', None)
  cookie_state = request.cookies.get(auth.state_cookie_name)
  if arg_state is None or arg_state != cookie_state:
      return "Forbidden", 403
  token = auth.token_for_code(code)
  session["token"] = token
  next_url = auth.get_next_url(cookie_state) or GDP_ROOT_URL
  response = make_response(redirect(next_url))
  return response
