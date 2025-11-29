import utils
import pandas as pd
from datetime import date
import time

def test_inverted_matrix_saving():
    print("Testing Inverted Matrix Saving...")
    
    emp = "Inverted User"
    utils.save_employee(emp)
    
    # Create a Matrix DataFrame
    # Index: Proj A, Proj B, Kommentar
    # Columns: 1..31
    
    rows = ["Proj A", "Proj B", "Kommentar"]
    cols = list(range(1, 32))
    
    df_matrix = pd.DataFrame(index=rows, columns=cols)
    
    # Day 1 (Col 1): 8h on Proj A
    df_matrix.at["Proj A", 1] = 8.0
    df_matrix.at["Kommentar", 1] = "Work"
    
    # Day 2 (Col 2): 4h on Proj A, 4h on Proj B
    df_matrix.at["Proj A", 2] = 4.0
    df_matrix.at["Proj B", 2] = 4.0
    
    # Day 3 (Col 3): Vacation (U)
    df_matrix.at["Proj A", 3] = "U"
    
    print("Saving inverted matrix...")
    utils.save_matrix_entries(emp, 2026, 6, df_matrix)
    
    # Verify
    df = utils.load_data()
    df['datum'] = pd.to_datetime(df['datum']).dt.date
    
    user_df = df[(df['mitarbeiter'] == emp) & (df['datum'].apply(lambda x: x.month) == 6)]
    
    # Check Day 1
    d1 = user_df[user_df['datum'] == date(2026, 6, 1)]
    assert len(d1) == 1
    assert d1.iloc[0]['stunden'] == 8.0
    assert d1.iloc[0]['projekt'] == "Proj A"
    assert d1.iloc[0]['beschreibung'] == "Work"
    
    # Check Day 2
    d2 = user_df[user_df['datum'] == date(2026, 6, 2)]
    assert len(d2) == 2
    assert d2[d2['projekt'] == "Proj A"].iloc[0]['stunden'] == 4.0
    assert d2[d2['projekt'] == "Proj B"].iloc[0]['stunden'] == 4.0
    
    # Check Day 3
    d3 = user_df[user_df['datum'] == date(2026, 6, 3)]
    assert len(d3) == 1
    assert d3.iloc[0]['typ'] == "U"
    
    print("Inverted Matrix Saving: OK")

if __name__ == "__main__":
    test_inverted_matrix_saving()
