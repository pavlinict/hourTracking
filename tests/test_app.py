import utils
import pandas as pd
import os
from datetime import date

def test_data_entry():
    print("Testing Data Entry...")
    # Clear data for testing
    if os.path.exists(utils.DATA_FILE):
        os.remove(utils.DATA_FILE)
    
    # Add Work
    utils.save_entry("2026-01-05", "Max Mustermann", "Project A", 8.0, "Development", "Arbeit")
    
    # Add Vacation
    utils.save_entry("2026-01-06", "Max Mustermann", "", 0.0, "Urlaub", "U")
    
    # Add Child Sick
    utils.save_entry("2026-01-07", "Max Mustermann", "", 0.0, "Kindkrank", "KK")
    
    df = utils.load_data()
    print(df)
    assert len(df) == 3
    assert df.iloc[0]['Typ'] == 'Arbeit'
    assert df.iloc[1]['Typ'] == 'U'
    assert df.iloc[2]['Typ'] == 'KK'
    print("Data Entry Test Passed!")

def test_holiday_entry():
    print("\nTesting Holiday Entry...")
    if os.path.exists(utils.HOLIDAY_FILE):
        os.remove(utils.HOLIDAY_FILE)
        
    utils.save_holiday("2026-01-01", "Neujahr")
    
    holidays = utils.load_holidays()
    print(holidays)
    assert len(holidays) == 1
    assert holidays[0] == date(2026, 1, 1)
    print("Holiday Entry Test Passed!")

def test_pdf_generation():
    print("\nTesting PDF Generation...")
    filename = "test_report_2026.pdf"
    if os.path.exists(filename):
        os.remove(filename)
        
    result = utils.generate_pdf_report(2026, filename)
    assert result == True
    assert os.path.exists(filename)
    print(f"PDF Generated: {filename}")
    print("PDF Generation Test Passed!")

if __name__ == "__main__":
    test_data_entry()
    test_holiday_entry()
    test_pdf_generation()
