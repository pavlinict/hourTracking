import pandas as pd

def test_validation_logic():
    print("Testing Validation Logic...")
    
    # Mock Data
    rows = ["Proj A", "Kommentar"]
    cols = [1, 2, 3, 4]
    df = pd.DataFrame(index=rows, columns=cols)
    
    df.at["Proj A", 1] = "8"    # Valid Number
    df.at["Proj A", 2] = "U"    # Valid Code
    df.at["Proj A", 3] = "F"    # Valid Code
    df.at["Proj A", 4] = "Bad"  # Invalid
    
    validation_error = False
    for proj in df.index:
        if proj == "Kommentar": continue
        for day_col in df.columns:
            val = df.at[proj, day_col]
            if val is not None and str(val).strip() != "" and str(val).lower() != 'nan':
                is_valid = False
                try:
                    float(str(val).replace(',', '.'))
                    is_valid = True
                except ValueError:
                    if str(val).upper().strip() in ['U', 'KK', 'F', '/']:
                        is_valid = True
                
                if not is_valid:
                    print(f"Caught Invalid: {val}")
                    validation_error = True
                    
    assert validation_error == True
    print("Validation Logic: OK")

if __name__ == "__main__":
    test_validation_logic()
