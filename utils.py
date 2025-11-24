import pandas as pd
import os
from datetime import datetime, date
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

DATA_FILE = 'data/stunden.csv'
HOLIDAY_FILE = 'data/feiertage.csv'
COLUMNS = ['Datum', 'Mitarbeiter', 'Projekt', 'Stunden', 'Beschreibung', 'Typ']

def load_data():
    """Loads data from the CSV file."""
    if not os.path.exists(DATA_FILE):
        return pd.DataFrame(columns=COLUMNS)
    try:
        df = pd.read_csv(DATA_FILE)
        # Ensure all columns exist
        for col in COLUMNS:
            if col not in df.columns:
                df[col] = ""
        return df
    except Exception as e:
        print(f"Error loading data: {e}")
        return pd.DataFrame(columns=COLUMNS)

def save_entry(datum, mitarbeiter, projekt, stunden, beschreibung, typ):
    """Saves a new entry to the CSV file."""
    df = load_data()
    new_entry = pd.DataFrame([{
        'Datum': datum,
        'Mitarbeiter': mitarbeiter,
        'Projekt': projekt,
        'Stunden': stunden,
        'Beschreibung': beschreibung,
        'Typ': typ
    }])
    df = pd.concat([df, new_entry], ignore_index=True)
    df.to_csv(DATA_FILE, index=False)

def get_employees(df):
    """Returns a list of unique employees."""
    if df.empty:
        return []
    return sorted(df['Mitarbeiter'].dropna().unique().tolist())

def get_projects(df):
    """Returns a list of unique projects."""
    if df.empty:
        return []
    return sorted(df['Projekt'].dropna().unique().tolist())

def load_holidays():
    """Loads holidays from CSV."""
    if not os.path.exists(HOLIDAY_FILE):
        return []
    try:
        df = pd.read_csv(HOLIDAY_FILE)
        return pd.to_datetime(df['Datum']).dt.date.tolist()
    except:
        return []

def save_holiday(datum, name):
    """Saves a holiday."""
    if not os.path.exists(HOLIDAY_FILE):
        df = pd.DataFrame(columns=['Datum', 'Name'])
    else:
        df = pd.read_csv(HOLIDAY_FILE)
    
    new_entry = pd.DataFrame([{'Datum': datum, 'Name': name}])
    df = pd.concat([df, new_entry], ignore_index=True)
    df.drop_duplicates(subset=['Datum'], inplace=True)
    df.to_csv(HOLIDAY_FILE, index=False)

def generate_pdf_report(year, filename):
    """Generates a PDF report for the given year."""
    df = load_data()
    if df.empty: return False
    
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

    # 1. Per Employee -> Month -> Project
    elements.append(Paragraph("1. Auswertung pro Mitarbeiter", styles['Heading1']))
    
    employees = sorted(df_year['Mitarbeiter'].unique())
    for emp in employees:
        elements.append(Paragraph(f"Mitarbeiter: {emp}", styles['Heading2']))
        
        emp_df = df_year[df_year['Mitarbeiter'] == emp]
        # Add Month column for sorting
        emp_df['Monat'] = emp_df['Datum'].dt.month
        
        # Group by Month and Project
        # We only care about 'Arbeit' for project hours usually, but let's show everything or filter?
        # User said "hours on different projects", implying work.
        work_df = emp_df[emp_df['Typ'] == 'Arbeit']
        
        if not work_df.empty:
            # Group by Month, Project
            grouped = work_df.groupby(['Monat', 'Projekt'])['Stunden'].sum().reset_index()
            
            data = [['Monat', 'Projekt', 'Stunden']]
            total_hours = 0
            
            for month in sorted(grouped['Monat'].unique()):
                month_name = date(int(year), month, 1).strftime('%B') # English month name by default, fine for now or map
                # Simple mapping for German
                month_map = {1:'Januar', 2:'Februar', 3:'März', 4:'April', 5:'Mai', 6:'Juni', 7:'Juli', 8:'August', 9:'September', 10:'Oktober', 11:'November', 12:'Dezember'}
                month_str = month_map.get(month, str(month))
                
                month_data = grouped[grouped['Monat'] == month]
                for _, row in month_data.iterrows():
                    data.append([month_str, row['Projekt'], f"{row['Stunden']:.1f}"])
                    total_hours += row['Stunden']
            
            data.append(['', 'Gesamt', f"{total_hours:.1f}"])
            add_table(data, col_widths=[100, 300, 100])
        else:
            elements.append(Paragraph("Keine Arbeitsstunden verzeichnet.", styles['Normal']))
        
        elements.append(Spacer(1, 10))

    # 2. Per Project -> Employee -> Month
    elements.append(Paragraph("2. Auswertung pro Projekt", styles['Heading1']))
    
    # Filter only work for projects
    project_df_all = df_year[df_year['Typ'] == 'Arbeit']
    projects = sorted(project_df_all['Projekt'].unique())
    
    for proj in projects:
        elements.append(Paragraph(f"Projekt: {proj}", styles['Heading2']))
        
        proj_df = project_df_all[project_df_all['Projekt'] == proj]
        proj_df['Monat'] = proj_df['Datum'].dt.month
        
        grouped = proj_df.groupby(['Mitarbeiter', 'Monat'])['Stunden'].sum().reset_index()
        
        data = [['Mitarbeiter', 'Monat', 'Stunden']]
        total_hours = 0
        
        # Sort by Employee then Month
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
