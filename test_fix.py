import utils
from datetime import date

# Ensure DB is init
utils.init_db()

# Create test employee and project
emp = "TestUserFix"
proj = "TestProjectFix"

print(f"Adding employee {emp}: {utils.save_employee(emp)}")
print(f"Adding project {proj}: {utils.add_project(proj)}")

# Assign project
print(f"Assigning project: {utils.update_assigned_projects(emp, [proj])}")

# Try to save entries
entries = [{
    "datum": date(2024, 1, 1),
    "mitarbeiter": emp,
    "projekt": proj,
    "stunden": 8.0,
    "beschreibung": "Test",
    "typ": "Arbeit"
}]

print(f"Saving entries: {utils.save_month_entries(emp, 2024, 1, entries)}")

# Verify
df = utils.load_data()
row = df[(df['mitarbeiter'] == emp) & (df['projekt'] == proj)]
print(f"Entries found: {len(row)}")
if len(row) > 0:
    print("SUCCESS")
else:
    print("FAILURE")
