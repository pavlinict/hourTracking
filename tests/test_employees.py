import utils
import pandas as pd
import os

def test_employee_management():
    print("Testing Employee Management...")
    # Clear employee file
    if os.path.exists('data/mitarbeiter.csv'):
        os.remove('data/mitarbeiter.csv')
        
    # 1. Add
    utils.save_employee("Test User 1")
    utils.save_employee("Test User 2")
    emps = utils.get_employees()
    assert "Test User 1" in emps
    assert "Test User 2" in emps
    assert len(emps) == 2
    print("Add: OK")
    
    # 2. Rename
    # Create dummy data first to check if it updates
    utils.save_entry("2026-01-01", "Test User 1", "Proj1", 5, "Desc", "Arbeit")
    
    utils.rename_employee("Test User 1", "Renamed User")
    emps = utils.get_employees()
    assert "Renamed User" in emps
    assert "Test User 1" not in emps
    
    df = utils.load_data()
    assert "Renamed User" in df['Mitarbeiter'].values
    print("Rename: OK")
    
    # 3. Remove
    utils.remove_employee("Test User 2")
    emps = utils.get_employees()
    assert "Test User 2" not in emps
    print("Remove: OK")
    
    print("Employee Management Test Passed!")

if __name__ == "__main__":
    test_employee_management()
