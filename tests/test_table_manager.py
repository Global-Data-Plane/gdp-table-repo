import pytest
from src.gdp_table_manager import GDPTableManager, GDPNotPermittedException, GDPNotFoundException
from src.permissions import InMemoryPermissionsManager
from src.gdp_storage import InMemoryStorageManager
from sdtp import RowTable

@pytest.fixture
def managers():
    storage_mgr = InMemoryStorageManager()
    perm_mgr = InMemoryPermissionsManager()
    tm = GDPTableManager(storage_mgr, perm_mgr)
    return tm

@pytest.fixture
def sample_tables():
    table_1 = {
      "type": "RowTable",
      "schema": [{"name": "id", "type": "number"}, {"name": "name", "type": "string"}],
      "rows": [[1, "Alice"], [2, "Bob"]]
    }
    table_2 = {
      "type": "RowTable",
      "schema": [{"name": "score", "type": "number"}, {"name": "passed", "type": "boolean"}],
      "rows": [[95, True], [70, False]]
    }
    return table_1, table_2

def check_invariant(tm, expected_keys):
    key_mismatch = tm.consistency_errors()
    for (key, missing) in key_mismatch.items():
        assert len(missing) == 0, f'Keys {missing} missing for table {key}'
    assert set(expected_keys) == set(tm.storage_manager.all_keys_matching_pattern())

def test_publish_and_invariant(managers, sample_tables):
    tm = managers
    table_1, table_2 = sample_tables
    tm.publish_table("alice/table1.sdml", "alice", table_1)
    tm.publish_table("carol/table2.sdml", "carol", table_2)
    check_invariant(tm, ["alice/table1.sdml", "carol/table2.sdml"])

def test_update_access_and_invariant(managers, sample_tables):
    tm = managers
    table_1, table_2 = sample_tables
    tm.publish_table("alice/table1.sdml", "alice", table_1)
    tm.update_access("alice/table1.sdml", "alice", ["bob"])
    tm.update_access("alice/table1.sdml", "alice", ["alice", "carol"])
    perm_record = tm.permissions_manager._get("alice/table1.sdml")
    assert perm_record is not None
    assert set(perm_record["users"]) == {"alice", "bob", "carol"}

def test_access_permissions(managers, sample_tables):
    tm = managers
    table_1, table_2 = sample_tables
    tm.publish_table("alice/table1.sdml", "alice", table_1)
    tm.update_access("alice/table1.sdml", "alice", ["bob", "carol"])
    assert tm.table_access_permitted("alice/table1.sdml", "alice", True)
    assert tm.table_access_permitted("alice/table1.sdml", "bob", True)
    assert tm.table_access_permitted("alice/table1.sdml", "carol", True)
    assert not tm.table_access_permitted("alice/table1.sdml", "dave", True)

def test_get_table_and_exception_order(managers, sample_tables):
    tm = managers
    table_1, table_2 = sample_tables
    tm.publish_table("alice/table1.sdml", "alice", table_1)
    tbl = tm._get_table("alice/table1.sdml")
    assert isinstance(tbl, RowTable)

    with pytest.raises(GDPNotFoundException):
        tm.get_table_if_permitted("nonexistent_table.sdml", "anyuser", True)

def test_delete_table_and_consistency(managers, sample_tables):
    tm = managers
    table_1, table_2 = sample_tables
    tm.publish_table("alice/table1.sdml", "alice", table_1)
    tm.delete_table("alice/table1.sdml")
    check_invariant(tm, [])
    with pytest.raises(GDPNotFoundException):
        tm.get_table_if_permitted("alice/table1.sdml", "alice", True)

def test_clean_tables(managers, sample_tables):
    tm = managers
    table_1, table_2 = sample_tables
    tm.publish_table("carol/table2.sdml", "carol", table_2)
    tm.clean_tables("carol/*")
    check_invariant(tm, [])
    with pytest.raises(GDPNotFoundException):
        tm.get_table_if_permitted("carol/table2.sdml", "carol", True)

def test_get_table_info_and_final_consistency(managers, sample_tables):
    tm = managers
    table_1, table_2 = sample_tables
    tm.publish_table("alice/table1.sdml", "alice", table_1)
    tm.publish_table("carol/table2.sdml", "carol", table_2)
    info_bob = tm.get_table_info("bob", True)
    assert isinstance(info_bob, dict)
    check_invariant(tm, ["alice/table1.sdml", "carol/table2.sdml"])
    consistency_errors = tm.consistency_errors()
    for layer, missing in consistency_errors.items():
        assert not missing, f"Consistency errors in {layer}: {missing}"
