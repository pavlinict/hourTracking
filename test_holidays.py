import utils
from datetime import date

# Test load_holidays
holidays = utils.load_holidays()
print(f"Holidays loaded: {len(holidays)}")
print(f"Type of first holiday: {type(holidays[0]) if holidays else 'No holidays'}")
print(f"First 5 holidays: {holidays[:5]}")

# Test if Jan 1, 2025 is in there
jan1_2025 = date(2025, 1, 1)
print(f"\nJan 1, 2025 in holidays: {jan1_2025 in holidays}")
print(f"Jan 1, 2025 type: {type(jan1_2025)}")

# Show all January 2025 holidays
jan_holidays = [h for h in holidays if h.year == 2025 and h.month == 1]
print(f"\nJanuary 2025 holidays: {jan_holidays}")
