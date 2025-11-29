import utils
import pandas as pd
from datetime import date
import time

def test_weekend_prefilling():
    print("Testing Weekend Prefilling Logic...")
    
    # Simulate the logic used in app.py
    selected_year = 2026
    selected_month = 6 # June 2026
    
    import calendar
    num_days = calendar.monthrange(selected_year, selected_month)[1]
    days = list(range(1, num_days + 1))
    all_projects = ["Proj A"]
    
    matrix_data = {}
    for d in days:
        curr_date = date(selected_year, selected_month, d)
        is_weekend = curr_date.weekday() >= 5
        default_val = "/" if is_weekend else None
        matrix_data[d] = [default_val]*(len(all_projects) + 1)
        
    df_matrix = pd.DataFrame(matrix_data, index=all_projects + ["Kommentar"])
    
    # Check a known weekend
    # June 6, 2026 is a Saturday
    assert df_matrix.at["Proj A", 6] == "/"
    assert df_matrix.at["Kommentar", 6] == "/"
    
    # Check a known weekday
    # June 1, 2026 is a Monday
    assert df_matrix.at["Proj A", 1] is None
    
    print("Weekend Prefilling: OK")

if __name__ == "__main__":
    test_weekend_prefilling()
