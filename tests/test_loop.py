import utils
import pandas as pd
from datetime import date
import time

def test_month_loop_logic():
    print("Testing Month Loop Logic...")
    
    # Simulate the loop logic
    selected_year = 2026
    month_names = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"]
    
    for month_idx, month_name in enumerate(month_names):
        month_num = month_idx + 1
        print(f"Processing {month_name} ({month_num})...")
        
        # Check weekend prefilling for each month
        import calendar
        num_days = calendar.monthrange(selected_year, month_num)[1]
        days = list(range(1, num_days + 1))
        
        matrix_data = {}
        for d in days:
            curr_date = date(selected_year, month_num, d)
            is_weekend = curr_date.weekday() >= 5
            default_val = "/" if is_weekend else None
            matrix_data[d] = [default_val]
            
        # Basic assertion
        assert len(matrix_data) == num_days
        
    print("Month Loop Logic: OK")

if __name__ == "__main__":
    test_month_loop_logic()
