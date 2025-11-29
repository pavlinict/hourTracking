import utils
import pandas as pd
from datetime import date
import time

def test_calendar_entry():
    print("Testing Calendar Entry...")
    
    emp = "Calendar User"
    utils.save_employee(emp)
    
    # 1. Save Month Data
    entries = [
        {"datum": date(2026, 3, 1), "mitarbeiter": emp, "projekt": "Proj A", "stunden": 8.0, "beschreibung": "Work", "typ": "Arbeit"},
        {"datum": date(2026, 3, 2), "mitarbeiter": emp, "projekt": "", "stunden": 0.0, "beschreibung": "Vacation", "typ": "U"},
    ]
    
    print("Saving month entries...")
    utils.save_month_entries(emp, 2026, 3, entries)
    
    # Verify
    df = utils.load_data()
    df['datum'] = pd.to_datetime(df['datum']).dt.date
    
    user_df = df[(df['mitarbeiter'] == emp) & (df['datum'].apply(lambda x: x.month) == 3)]
    assert len(user_df) == 2
    assert user_df[user_df['datum'] == date(2026, 3, 1)].iloc[0]['stunden'] == 8.0
    assert user_df[user_df['datum'] == date(2026, 3, 2)].iloc[0]['typ'] == "U"
    print("Save Month: OK")
    
    # 2. Overwrite Month (Simulate editing the grid and saving again)
    # Change 3/1 to 4 hours, Remove 3/2, Add 3/3
    new_entries = [
        {"datum": date(2026, 3, 1), "mitarbeiter": emp, "projekt": "Proj A", "stunden": 4.0, "beschreibung": "Half Day", "typ": "Arbeit"},
        {"datum": date(2026, 3, 3), "mitarbeiter": emp, "projekt": "Proj B", "stunden": 5.0, "beschreibung": "New", "typ": "Arbeit"},
    ]
    
    print("Overwriting month entries...")
    utils.save_month_entries(emp, 2026, 3, new_entries)
    
    df = utils.load_data()
    df['datum'] = pd.to_datetime(df['datum']).dt.date
    user_df = df[(df['mitarbeiter'] == emp) & (df['datum'].apply(lambda x: x.month) == 3)]
    
    assert len(user_df) == 2
    assert user_df[user_df['datum'] == date(2026, 3, 1)].iloc[0]['stunden'] == 4.0
    assert date(2026, 3, 2) not in user_df['datum'].values
    assert date(2026, 3, 3) in user_df['datum'].values
    print("Overwrite Month: OK")
    
    print("Calendar Entry Test Passed!")

if __name__ == "__main__":
    test_calendar_entry()
