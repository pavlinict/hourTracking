import utils
import pandas as pd
from datetime import date
import time

def test_project_management_and_validation():
    print("Testing Project Management & Validation...")
    
    # 1. Add Project
    p_name = "Test Project X"
    utils.add_project(p_name)
    all_projs = utils.get_projects()
    assert p_name in all_projs
    print("Project Addition: OK")
    
    # 2. Assign Project
    emp = "Test User Y"
    utils.save_employee(emp)
    utils.update_assigned_projects(emp, [p_name])
    assigned = utils.get_assigned_projects(emp)
    assert p_name in assigned
    assert len(assigned) == 1
    print("Project Assignment: OK")
    
    # 3. Strict Validation (via save_matrix_entries)
    # Create matrix with invalid input
    rows = [p_name, "Kommentar"]
    cols = list(range(1, 32))
    df_matrix = pd.DataFrame(index=rows, columns=cols)
    
    # Valid
    df_matrix.at[p_name, 1] = 8.0
    df_matrix.at[p_name, 2] = "U"
    
    # Invalid
    df_matrix.at[p_name, 3] = "Invalid"
    
    # Save
    # The function prints error but continues saving valid ones? 
    # Or does it reject?
    # My implementation prints "Skipping invalid value" and continues.
    # The user wanted "ensure that we can only enter number or F, KK, U, /".
    # If it skips, it means it's not saved. That effectively rejects it.
    # Let's verify it's NOT saved.
    
    utils.save_matrix_entries(emp, 2026, 7, df_matrix)
    
    # Verify
    df = utils.load_data()
    df['datum'] = pd.to_datetime(df['datum']).dt.date
    user_df = df[(df['mitarbeiter'] == emp) & (df['datum'].apply(lambda x: x.month) == 7)]
    
    # Day 1 (8.0) -> Should exist
    d1 = user_df[user_df['datum'] == date(2026, 7, 1)]
    assert not d1.empty
    
    # Day 2 (U) -> Should exist
    d2 = user_df[user_df['datum'] == date(2026, 7, 2)]
    assert not d2.empty
    
    # Day 3 (Invalid) -> Should NOT exist
    d3 = user_df[user_df['datum'] == date(2026, 7, 3)]
    assert d3.empty
    
    print("Validation: OK (Invalid entries skipped)")

if __name__ == "__main__":
    test_project_management_and_validation()
