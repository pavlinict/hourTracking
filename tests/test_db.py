import utils
import pandas as pd
from datetime import date
import time

def test_db_operations():
    print("Testing Database Operations...")
    
    # 1. Init DB (Implicitly done on import, but good to check)
    # Wait a bit for DB to be ready if just started
    time.sleep(2)
    
    # 2. Employees
    print("Testing Employees...")
    utils.save_employee("DB User 1")
    emps = utils.get_employees()
    assert "DB User 1" in emps
    print("Employee Add: OK")
    
    # 3. Entries
    print("Testing Entries...")
    utils.save_entry(date(2026, 2, 1), "DB User 1", "DB Project", 4.5, "Test DB", "Arbeit")
    df = utils.load_data()
    assert not df.empty
    entry = df[df['mitarbeiter'] == "DB User 1"].iloc[0]
    assert entry['stunden'] == 4.5
    print("Entry Add: OK")
    
    # 4. Update Entry
    print("Testing Update...")
    entry_id = entry['id']
    utils.update_entry(entry_id, date(2026, 2, 1), "DB User 1", "DB Project", 8.0, "Updated DB", "Arbeit")
    df = utils.load_data()
    updated_entry = df[df['id'] == entry_id].iloc[0]
    assert updated_entry['stunden'] == 8.0
    assert updated_entry['beschreibung'] == "Updated DB"
    print("Entry Update: OK")
    
    print("Database Operations Test Passed!")

if __name__ == "__main__":
    test_db_operations()
