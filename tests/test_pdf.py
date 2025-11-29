import utils
import pandas as pd
from datetime import date
import os

def test_pdf_generation():
    print("Testing PDF Generation...")
    
    emp = "PDF User"
    utils.save_employee(emp)
    
    # Add some data
    entries = [
        {"datum": date(2026, 1, 15), "mitarbeiter": emp, "projekt": "Proj A", "stunden": 5.0, "beschreibung": "Test", "typ": "Arbeit"},
        {"datum": date(2026, 2, 20), "mitarbeiter": emp, "projekt": "Proj A", "stunden": 3.0, "beschreibung": "Test", "typ": "Arbeit"},
        {"datum": date(2026, 1, 10), "mitarbeiter": emp, "projekt": "Proj B", "stunden": 2.0, "beschreibung": "Test", "typ": "Arbeit"},
    ]
    utils.save_month_entries(emp, 2026, 1, [entries[0], entries[2]])
    utils.save_month_entries(emp, 2026, 2, [entries[1]])
    
    filename = "test_report_2026.pdf"
    if os.path.exists(filename):
        os.remove(filename)
        
    success = utils.generate_pdf_report(2026, filename)
    assert success
    assert os.path.exists(filename)
    print("PDF Generated: OK")

if __name__ == "__main__":
    test_pdf_generation()
