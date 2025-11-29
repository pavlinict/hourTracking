import pandas as pd
import os
from datetime import datetime, date
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from sqlalchemy import create_engine, text
import streamlit as st

# Database Connection
def get_db_url():
    try:
        if "db_url" in st.secrets:
            return st.secrets["db_url"]
    except FileNotFoundError:
        pass # No secrets file
    return os.environ.get("DATABASE_URL", "postgresql://user:password@localhost:5432/hourtracking")

DB_URL = get_db_url()
engine = create_engine(DB_URL)

def init_db():
    """Initializes the database tables."""
    try:
        with engine.connect() as conn:
            # 1. Create referenced tables first (Employees & Projects)
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS employees (
                    name TEXT PRIMARY KEY
                )
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS projects (
                    name TEXT PRIMARY KEY
                )
            """))
            
            # 2. Create Entries table with Foreign Keys
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS entries (
                    id SERIAL PRIMARY KEY,
                    datum DATE,
                    mitarbeiter TEXT REFERENCES employees(name) ON UPDATE CASCADE ON DELETE SET NULL,
                    projekt TEXT REFERENCES projects(name) ON UPDATE CASCADE ON DELETE SET NULL,
                    stunden FLOAT,
                    beschreibung TEXT,
                    typ TEXT
                )
            """))
            
            # 3. Create Employee-Projects table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS employee_projects (
                    employee TEXT REFERENCES employees(name) ON DELETE CASCADE,
                    project TEXT REFERENCES projects(name) ON DELETE CASCADE,
                    PRIMARY KEY (employee, project)
                )
            """))
            
            # 4. Create Holidays table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS holidays (
                    datum DATE PRIMARY KEY,
                    name TEXT
                )
            """))
            conn.commit()
            
            # 4. Auto-migration: Populate employees/projects from entries if empty
            # This ensures that if we have existing entries, we backfill the master tables
            # so that FK constraints (if applied) are satisfied.
            
            # Check/Migrate Employees
            res_emp = conn.execute(text("SELECT COUNT(*) FROM employees")).scalar()
            if res_emp == 0:
                print("Migrating employees from entries...")
                conn.execute(text("""
                    INSERT INTO employees (name)
                    SELECT DISTINCT mitarbeiter FROM entries 
                    WHERE mitarbeiter IS NOT NULL AND mitarbeiter != ''
                    ON CONFLICT DO NOTHING
                """))
                conn.commit()

            # Check/Migrate Projects
            res_proj = conn.execute(text("SELECT COUNT(*) FROM projects")).scalar()
            if res_proj == 0:
                print("Migrating projects from entries...")
                conn.execute(text("""
                    INSERT INTO projects (name)
                    SELECT DISTINCT projekt FROM entries 
                    WHERE projekt IS NOT NULL AND projekt != ''
                    ON CONFLICT DO NOTHING
                """))
                conn.commit()
                
            # Migrate Employee-Project Assignments
            # (Only if we just migrated data, or check if empty?)
            # Let's just run it safely with ON CONFLICT
            conn.execute(text("""
                INSERT INTO employee_projects (employee, project)
                SELECT DISTINCT mitarbeiter, projekt FROM entries
                WHERE mitarbeiter IS NOT NULL AND projekt IS NOT NULL AND projekt != ''
                ON CONFLICT DO NOTHING
            """))
            conn.commit()

            # 5. Attempt to add FK constraints to 'entries' if they don't exist (for existing DBs)
            # We do this AFTER migration to ensure data is consistent.
            try:
                conn.execute(text("""
                    ALTER TABLE entries 
                    ADD CONSTRAINT fk_entries_employees 
                    FOREIGN KEY (mitarbeiter) REFERENCES employees(name) 
                    ON UPDATE CASCADE ON DELETE SET NULL
                """))
                conn.commit()
            except Exception:
                conn.rollback() # Constraint likely exists or data violation

            try:
                conn.execute(text("""
                    ALTER TABLE entries 
                    ADD CONSTRAINT fk_entries_projects 
                    FOREIGN KEY (projekt) REFERENCES projects(name) 
                    ON UPDATE CASCADE ON DELETE SET NULL
                """))
                conn.commit()
            except Exception:
                conn.rollback() # Constraint likely exists or data violation
    except Exception as e:
        print(f"DB Init Error: {e}")

# Initialize on module load (or call explicitly)
init_db()

def load_data():
    """Loads data from the DB."""
    try:
        return pd.read_sql("SELECT * FROM entries", engine)
    except Exception as e:
        print(f"Error loading data: {e}")
        return pd.DataFrame(columns=['datum', 'mitarbeiter', 'projekt', 'stunden', 'beschreibung', 'typ'])

def save_entry(datum, mitarbeiter, projekt, stunden, beschreibung, typ):
    """Saves a new entry to the DB."""
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO entries (datum, mitarbeiter, projekt, stunden, beschreibung, typ)
                VALUES (:datum, :mitarbeiter, :projekt, :stunden, :beschreibung, :typ)
            """), {
                "datum": datum,
                "mitarbeiter": mitarbeiter.strip() if mitarbeiter else None,
                "projekt": projekt.strip() if projekt else None,
                "stunden": stunden,
                "beschreibung": beschreibung,
                "typ": typ
            })
            conn.commit()
            return True
    except Exception as e:
        print(f"Error saving entry: {e}")
        return False

def update_entry(id, datum, mitarbeiter, projekt, stunden, beschreibung, typ):
    """Updates an existing entry."""
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                UPDATE entries 
                SET datum=:datum, mitarbeiter=:mitarbeiter, projekt=:projekt, stunden=:stunden, beschreibung=:beschreibung, typ=:typ
                WHERE id=:id
            """), {
                "id": int(id),
                "datum": datum,
                "mitarbeiter": mitarbeiter.strip() if mitarbeiter else None,
                "projekt": projekt.strip() if projekt else None,
                "stunden": stunden,
                "beschreibung": beschreibung,
                "typ": typ
            })
            conn.commit()
            return True
    except Exception as e:
        print(f"Error updating entry: {e}")
        return False

def save_month_entries(mitarbeiter, year, month, entries):
    """
    Replaces all entries for a specific employee and month with the new list.
    entries: list of dicts {'datum': ..., 'projekt': ..., 'stunden': ..., 'beschreibung': ..., 'typ': ...}
    """
    try:
        # Clean data
        cleaned_entries = []
        for e in entries:
            e['mitarbeiter'] = e['mitarbeiter'].strip() if e['mitarbeiter'] else None
            e['projekt'] = e['projekt'].strip() if e['projekt'] else None
            cleaned_entries.append(e)
            
        with engine.connect() as conn:
            # 1. Delete existing entries for this user/month
            conn.execute(text("""
                DELETE FROM entries 
                WHERE mitarbeiter = :mitarbeiter 
                AND EXTRACT(YEAR FROM datum) = :year 
                AND EXTRACT(MONTH FROM datum) = :month
            """), {"mitarbeiter": mitarbeiter.strip(), "year": int(year), "month": int(month)})
            
            # 2. Insert new entries
            if cleaned_entries:
                conn.execute(text("""
                    INSERT INTO entries (datum, mitarbeiter, projekt, stunden, beschreibung, typ)
                    VALUES (:datum, :mitarbeiter, :projekt, :stunden, :beschreibung, :typ)
                """), cleaned_entries)
            
            conn.commit()
            return True
    except Exception as e:
        print(f"Error saving month entries: {e}")
        return False

def save_matrix_entries(mitarbeiter, year, month, df_matrix):
    """
    Parses the edited matrix DataFrame and saves it to the DB.
    df_matrix: Index=Projects, Columns=Days (1..31)
    """
    entries = []
    import calendar
    num_days = calendar.monthrange(year, month)[1]
    
    # Iterate over the matrix
    # df_matrix index is Projects
    # Columns are days (as strings or ints)
    
    for project in df_matrix.index:
        if project == "Kommentar": continue # Should not happen as row, but safety check
        
        for day_col in df_matrix.columns:
            try:
                day = int(day_col)
                if day < 1 or day > num_days: continue
                
                datum = date(year, month, day)
                value = df_matrix.at[project, day_col]
                
                # Check for None, empty string, or NaN
                if value is None or str(value).strip() == "" or str(value).lower() == 'nan':
                    continue
                
                # Parse value
                stunden = 0.0
                typ = "Arbeit"
                
                # Try float
                try:
                    stunden = float(str(value).replace(',', '.'))
                    typ = "Arbeit"
                except ValueError:
                    # Code
                    code = str(value).upper().strip()
                    if code in ['U', 'KK', 'F', '/']:
                        typ = code
                        stunden = 0.0
                    else:
                        print(f"Skipping invalid value '{value}' for {project} on {datum}")
                        continue
                
                # Description? In this view (Project x Day), we don't have a dedicated comment cell per entry easily.
                # Unless we have a "Kommentar" ROW.
                # Let's check if there is a "Kommentar" row.
                beschreibung = ""
                if "Kommentar" in df_matrix.index:
                    beschreibung = str(df_matrix.at["Kommentar", day_col] or "")
                
                entries.append({
                    "datum": datum,
                    "mitarbeiter": mitarbeiter,
                    "projekt": project,
                    "stunden": stunden,
                    "beschreibung": beschreibung,
                    "typ": typ
                })
                
            except Exception as e:
                print(f"Error parsing cell {project}/{day_col}: {e}")
                continue
            
    return save_month_entries(mitarbeiter, year, month, entries)

def get_employees():
    """Returns a list of unique employees."""
    try:
        df = pd.read_sql("SELECT name FROM employees ORDER BY name", engine)
        return df['name'].tolist()
    except:
        return []

def save_employee(name):
    """Adds a new employee."""
    try:
        with engine.connect() as conn:
            # Check if exists
            res = conn.execute(text("SELECT 1 FROM employees WHERE name = :name"), {"name": name}).fetchone()
            if not res:
                conn.execute(text("INSERT INTO employees (name) VALUES (:name)"), {"name": name})
                conn.commit()
                return True
    except Exception as e:
        print(f"Error saving employee: {e}")
    return False

def remove_employee(name):
    """Removes an employee."""
    try:
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM employees WHERE name = :name"), {"name": name})
            conn.commit()
            return True
    except:
        return False

def rename_employee(old_name, new_name):
    """Renames an employee and updates history."""
    try:
        with engine.connect() as conn:
            # Update employee table
            conn.execute(text("UPDATE employees SET name = :new_name WHERE name = :old_name"), 
                         {"new_name": new_name, "old_name": old_name})
            # Update entries table
            conn.execute(text("UPDATE entries SET mitarbeiter = :new_name WHERE mitarbeiter = :old_name"), 
                         {"new_name": new_name, "old_name": old_name})
            conn.commit()
            return True
    except Exception as e:
        print(f"Error renaming: {e}")
        return False

def get_projects():
    """Returns a list of all available projects."""
    try:
        df = pd.read_sql("SELECT name FROM projects ORDER BY name", engine)
        return df['name'].tolist()
    except:
        return []

def add_project(name):
    """Adds a new project."""
    try:
        with engine.connect() as conn:
            conn.execute(text("INSERT INTO projects (name) VALUES (:name) ON CONFLICT DO NOTHING"), {"name": name})
            conn.commit()
            return True
    except:
        return False

def delete_project(name):
    """Deletes a project."""
    try:
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM projects WHERE name = :name"), {"name": name})
            conn.commit()
            return True
    except:
        return False

def get_assigned_projects(employee):
    """Returns projects assigned to an employee."""
    try:
        df = pd.read_sql(text("SELECT project FROM employee_projects WHERE employee = :emp ORDER BY project"), 
                         engine, params={"emp": employee})
        return df['project'].tolist()
    except:
        return []

def update_assigned_projects(employee, projects):
    """Updates the list of projects assigned to an employee."""
    try:
        with engine.connect() as conn:
            # Clear existing
            conn.execute(text("DELETE FROM employee_projects WHERE employee = :emp"), {"emp": employee})
            # Insert new
            if projects:
                data = [{"emp": employee, "proj": p} for p in projects]
                conn.execute(text("INSERT INTO employee_projects (employee, project) VALUES (:emp, :proj)"), data)
            conn.commit()
            return True
    except Exception as e:
        print(f"Error updating assignments: {e}")
        return False

def load_holidays():
    """Loads holidays."""
    try:
        df = pd.read_sql("SELECT datum FROM holidays", engine)
        return pd.to_datetime(df['datum']).dt.date.tolist()
    except:
        return []

def get_holidays_df(year=None):
    """Returns holidays as a DataFrame, optionally filtered by year."""
    try:
        if year:
            query = "SELECT datum, name FROM holidays WHERE EXTRACT(YEAR FROM datum) = :year ORDER BY datum"
            df = pd.read_sql(text(query), engine, params={"year": year})
            df.columns = ['Datum', 'Name']  # Rename columns
            return df
        else:
            return pd.read_sql("SELECT datum as Datum, name as Name FROM holidays ORDER BY datum", engine)
    except:
        return pd.DataFrame(columns=['Datum', 'Name'])

def delete_holiday(datum):
    """Deletes a holiday by date."""
    try:
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM holidays WHERE datum = :datum"), {"datum": datum})
            conn.commit()
            return True
    except Exception as e:
        print(f"Error deleting holiday: {e}")
        return False

def save_holiday(datum, name):
    """Saves a holiday."""
    try:
        with engine.connect() as conn:
            # Check if exists
            res = conn.execute(text("SELECT 1 FROM holidays WHERE datum = :datum"), {"datum": datum}).fetchone()
            if not res:
                conn.execute(text("INSERT INTO holidays (datum, name) VALUES (:datum, :name)"), 
                             {"datum": datum, "name": name})
                conn.commit()
                return True
            return False
    except Exception as e:
        print(f"Error saving holiday: {e}")
        return False

def populate_german_holidays(year):
    """
    Auto-populates German holidays for Thuringia for the given year.
    Returns tuple: (count, error_message)
    """
    try:
        from workalendar.europe import Thuringia
        cal = Thuringia()
        holidays = cal.holidays(year)
        
        count = 0
        for holiday_date, holiday_name in holidays:
            if save_holiday(holiday_date, holiday_name):
                count += 1
        
        return (count, None)
    except ImportError as e:
        return (0, "workalendar library not installed. Will be available after deployment to Streamlit Cloud.")
    except Exception as e:
        return (0, f"Error: {str(e)}")

def generate_pdf_report(year, filename):
    """Generates a PDF report for the given year."""
    df = load_data()
    if df.empty: return False
    
    # Normalize columns to match old logic (lowercase from DB to Capitalized for report logic if needed, or adjust logic)
    # DB columns are lowercase: datum, mitarbeiter, projekt, stunden, beschreibung, typ
    # Let's rename for compatibility with existing report logic
    df = df.rename(columns={
        'datum': 'Datum', 
        'mitarbeiter': 'Mitarbeiter', 
        'projekt': 'Projekt', 
        'stunden': 'Stunden', 
        'beschreibung': 'Beschreibung', 
        'typ': 'Typ'
    })
    
    df['Datum'] = pd.to_datetime(df['Datum'])
    df_year = df[df['Datum'].dt.year == int(year)]

    if df_year.empty:
        return False

    doc = SimpleDocTemplate(filename, pagesize=landscape(A4))
    elements = []
    styles = getSampleStyleSheet()
    
    # Helper to add table
    def add_table(data, col_widths=None):
        t = Table(data, colWidths=col_widths)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 10))

    # Title
    elements.append(Paragraph(f"Stundenbericht {year}", styles['Title']))
    elements.append(Spacer(1, 20))

    # 1. Auswertung pro Mitarbeiter
    elements.append(Paragraph("1. Auswertung pro Mitarbeiter", styles['Heading1']))
    
    employees = sorted(df_year['Mitarbeiter'].unique())
    for emp in employees:
        elements.append(Paragraph(f"Mitarbeiter: {emp}", styles['Heading2']))
        
        emp_df = df_year[df_year['Mitarbeiter'] == emp]
        emp_df['Monat'] = emp_df['Datum'].dt.month
        
        work_df = emp_df[emp_df['Typ'] == 'Arbeit']
        
        if not work_df.empty:
            # Group by Project then Month
            grouped = work_df.groupby(['Projekt', 'Monat'])['Stunden'].sum().reset_index()
            grouped = grouped.sort_values(['Projekt', 'Monat'])
            
            data = [['Projekt', 'Monat', 'Stunden']]
            total_hours = 0
            
            current_proj = None
            
            for _, row in grouped.iterrows():
                month_map = {1:'Januar', 2:'Februar', 3:'März', 4:'April', 5:'Mai', 6:'Juni', 7:'Juli', 8:'August', 9:'September', 10:'Oktober', 11:'November', 12:'Dezember'}
                month_str = month_map.get(row['Monat'], str(row['Monat']))
                
                # Show project name only on change (cleaner look)
                proj_display = row['Projekt'] if row['Projekt'] != current_proj else ""
                current_proj = row['Projekt']
                
                data.append([proj_display, month_str, f"{row['Stunden']:.1f}"])
                total_hours += row['Stunden']
            
            data.append(['', 'Gesamt', f"{total_hours:.1f}"])
            add_table(data, col_widths=[200, 100, 100])
        else:
            elements.append(Paragraph("Keine Arbeitsstunden verzeichnet.", styles['Normal']))
        
        elements.append(Spacer(1, 10))

    # 2. Per Project -> Employee -> Month
    elements.append(Paragraph("2. Auswertung pro Projekt", styles['Heading1']))
    
    project_df_all = df_year[df_year['Typ'] == 'Arbeit']
    projects = sorted(project_df_all['Projekt'].unique())
    
    for proj in projects:
        elements.append(Paragraph(f"Projekt: {proj}", styles['Heading2']))
        
        proj_df = project_df_all[project_df_all['Projekt'] == proj]
        proj_df['Monat'] = proj_df['Datum'].dt.month
        
        grouped = proj_df.groupby(['Mitarbeiter', 'Monat'])['Stunden'].sum().reset_index()
        
        data = [['Mitarbeiter', 'Monat', 'Stunden']]
        total_hours = 0
        
        grouped = grouped.sort_values(['Mitarbeiter', 'Monat'])
        
        current_emp = None
        for _, row in grouped.iterrows():
            month_map = {1:'Januar', 2:'Februar', 3:'März', 4:'April', 5:'Mai', 6:'Juni', 7:'Juli', 8:'August', 9:'September', 10:'Oktober', 11:'November', 12:'Dezember'}
            month_str = month_map.get(row['Monat'], str(row['Monat']))
            
            emp_display = row['Mitarbeiter'] if row['Mitarbeiter'] != current_emp else ""
            current_emp = row['Mitarbeiter']
            
            data.append([emp_display, month_str, f"{row['Stunden']:.1f}"])
            total_hours += row['Stunden']
            
        data.append(['', 'Gesamt', f"{total_hours:.1f}"])
        add_table(data, col_widths=[200, 150, 100])
        elements.append(Spacer(1, 10))

    doc.build(elements)
    return True
