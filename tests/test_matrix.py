import utils
import pandas as pd
from datetime import date
import time

def test_matrix_saving():
    print("Testing Matrix Saving...")
    
    emp = "Matrix User"
    utils.save_employee(emp)
    
    # Create a Matrix DataFrame
    # Index: 1..31
    # Columns: Proj A, Proj B, Kommentar
    
    data = {
        "Proj A": [None]*31,
        "Proj B": [None]*31,
        "Kommentar": [""]*31
    }
    
    # Day 1: 8h on Proj A
    data["Proj A"][0] = 8.0
    data["Kommentar"][0] = "Work"
    
    # Day 2: 4h on Proj A, 4h on Proj B
    data["Proj A"][1] = 4.0
    data["Proj B"][1] = 4.0
    
    # Day 3: Vacation (U)
    data["Proj A"][2] = "U"
    
    df_matrix = pd.DataFrame(data, index=range(1, 32))
    
    print("Saving matrix...")
    utils.save_matrix_entries(emp, 2026, 5, df_matrix)
    
    # Verify
    df = utils.load_data()
    df['datum'] = pd.to_datetime(df['datum']).dt.date
    
    user_df = df[(df['mitarbeiter'] == emp) & (df['datum'].apply(lambda x: x.month) == 5)]
    
    # Check Day 1
    d1 = user_df[user_df['datum'] == date(2026, 5, 1)]
    assert len(d1) == 1
    assert d1.iloc[0]['stunden'] == 8.0
    assert d1.iloc[0]['projekt'] == "Proj A"
    
    # Check Day 2
    d2 = user_df[user_df['datum'] == date(2026, 5, 2)]
    assert len(d2) == 2
    assert d2[d2['projekt'] == "Proj A"].iloc[0]['stunden'] == 4.0
    assert d2[d2['projekt'] == "Proj B"].iloc[0]['stunden'] == 4.0
    
    # Check Day 3
    d3 = user_df[user_df['datum'] == date(2026, 5, 3)]
    assert len(d3) == 1
    assert d3.iloc[0]['typ'] == "U"
    
    print("Matrix Saving: OK")

if __name__ == "__main__":
    test_matrix_saving()
