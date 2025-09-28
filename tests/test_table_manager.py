import pytest
from src.gdp_table_manager import GDPTableManager, GDPNotFoundException
from src.gdp_storage import InMemoryStorageManager
from sdtp import RowTable

@pytest.fixture
def managers():
    storage_mgr = InMemoryStorageManager()
    tm = GDPTableManager(storage_mgr)
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


    

def test_update_access_and_invariant(managers, sample_tables):
    tm = managers
    table_1, table_2 = sample_tables
    tm.publish_table("alice/table1.sdml",  table_1)
    tm.update_access("alice/table1.sdml", "alice", ["bob"])
    tm.update_access("alice/table1.sdml", "alice", ["alice", "carol"])
    perm_record = tm.get_permissions_record('alice/table1.sdml')
    assert perm_record is not None
    assert set(perm_record.users) == {"alice", "bob", "carol"}

def test_access_permissions(managers, sample_tables):
    tm = managers
    table_1, table__2 = sample_tables
    tm.publish_table("alice/table1.sdml", table_1)
    tm.update_access("alice/table1.sdml", "alice", ["bob", "carol"])
    assert tm.table_access_permitted("alice/table1.sdml", "alice", True)
    assert tm.table_access_permitted("alice/table1.sdml", "bob", True)
    assert tm.table_access_permitted("alice/table1.sdml", "carol", True)
    assert not tm.table_access_permitted("alice/table1.sdml", "dave", True)

def test_get_table_and_exception_order(managers, sample_tables):
    tm = managers
    table_1, table_2 = sample_tables
    tm.publish_table("alice/table1.sdml", table_1)
    tbl = tm.get_table("alice/table1.sdml")
    assert isinstance(tbl, RowTable)

    with pytest.raises(GDPNotFoundException):
        tm.get_table_if_permitted("nonexistent_table.sdml", "anyuser", True)

def test_delete_table_and_consistency(managers, sample_tables):
    tm = managers
    table_1, table_2 = sample_tables
    tm.publish_table("alice/table1.sdml", table_1)
    tm.delete_table("alice/table1.sdml")
    with pytest.raises(GDPNotFoundException):
        tm.get_table_if_permitted("alice/table1.sdml", "alice", True)

def test_clean_tables(managers, sample_tables):
    tm = managers
    table_1, table_2 = sample_tables
    tm.publish_table("carol/table2.sdml", table_2)
    tm.clean_tables("carol")
    with pytest.raises(GDPNotFoundException):
        tm.get_table_if_permitted("carol/table2.sdml", "carol", True)

def test_get_table_info(managers, sample_tables):
    tm = managers
    table_1, table_2 = sample_tables
    tm.publish_table("alice/table1.sdml",  table_1)
    tm.publish_table("carol/table2.sdml",  table_2)
    info_bob = tm.get_table_info("bob", True)
    assert isinstance(info_bob, dict)
    
