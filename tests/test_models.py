import pytest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))

import models

@pytest.fixture
def db_setup():
    models.DB_PATH = ":memory:"
    models.init_db(force=True)
    yield
    
def test_insert_and_query_department(db_setup):
    models.insert_row("department", {"name": "Test Dept", "code": "TD01"})
    dept = models.query("SELECT * FROM department WHERE code = 'TD01'", one=True)
    assert dept is not None
    assert dept["name"] == "Test Dept"

def test_table_all(db_setup):
    models.insert_row("category", {"name": "Volunteering", "type": "CSR Activity"})
    models.insert_row("category", {"name": "Recycling", "type": "Challenge"})
    categories = models.table_all("category")
    assert len(categories) >= 2
