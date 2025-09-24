# tests/conftest.py

import sys

import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import types
import pytest
import logging


# --- Mock/Fake auth_helpers module ---
fake_auth_helpers = types.ModuleType("src.auth_helpers")

def authenticated(fn):
    from functools import wraps
    from flask import request, g
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user_key = request.headers.get("Authorization", "Garbage")
        USERS = {
            "userA": {"email": "aiko@ai"},
            "userB": {"email": "rick@ai"},
            "userC": {"email": "matt@ai"}
        }
        user = USERS.get(user_key, None)
        g.current_user = user
        return fn(user, *args, **kwargs)
    return wrapper

def _get_email(user):
    return user["email"] if user else None

fake_auth_helpers.authenticated = authenticated  # type: ignore[attr-defined]
fake_auth_helpers._get_email = _get_email        # type: ignore[attr-defined]

# Register with the correct full module name
sys.modules["src.auth_helpers"] = fake_auth_helpers

from src.app import create_app
from flask import current_app
# --- Test Tables Dictionary ---
tables = {
    "aiko@ai/table_1.sdml":{
        "owner": "aiko@ai",
        "table": {
            "type": "RowTable",
            "schema": [{"name": "id", "type": "number"}, {"name": "name", "type": "string"}],
            "rows": [[1, "Alice"], [2, "Bob"]]
        }
    },
    "aiko@ai/table_2.sdml":{
        "owner": "aiko@ai",
        "table": {
            "type": "RowTable",
            "schema": [{"name": "score", "type": "number"}, {"name": "passed", "type": "boolean"}],
            "rows": [[95, True], [70, False]]
        }
    },
    "rick@ai/table_3.sdml": {
        "owner": "rick@ai",
        "table": {
            "type": "RowTable",
            "schema": [{"name": "id1", "type": "number"}, {"name": "name", "type": "string"}],
            "rows": [[1, "Mary"], [2, "Bill"]]
        }
    },
    "rick@ai/table_4.sdml": {
        "owner": "rick@ai",
        "table": {
            "type": "RowTable",
            "schema": [{"name": "id2", "type": "number"}, {"name": "name", "type": "string"}],
            "rows": [[1, "Jack"], [2, "Jill"]]
        }
    }
}

# --- Shared table setup function ---
def setup_tables(manager):
    for (name, table_desc) in tables.items():
        manager.publish_table(name, table_desc["owner"], table_desc["table"])
    manager.update_access("aiko@ai/table_1.sdml", "aiko@ai", ["PUBLIC"])
    manager.update_access("aiko@ai/table_2.sdml",  "aiko@ai", ["rick@ai"])
    manager.update_access("rick@ai/table_3.sdml",  "rick@ai", ["HUB"])
    manager.update_access("rick@ai/table_4.sdml", "rick@ai", ["matt@ai"])

# --- Fixtures for use in tests ---
@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    yield app

@pytest.fixture
def client(app):

    with app.test_client() as client:
        yield client

@pytest.fixture
def tables_setup(app):
    with app.app_context():
        setup_tables(current_app.table_manager)  # type: ignore[attr-defined]
    yield
