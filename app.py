import streamlit as st
import pandas as pd
import os
from datetime import date, datetime
import utils

st.set_page_config(page_title="Stundenerfassung", layout="wide")

st.title("⏱️ Stundenerfassung")

# Check database connection
db_success, db_error = utils.test_db_connection()
if not db_success:
    st.error(db_error)
    st.info("💡 **Quick Fix Options:**\n"
            "1. **If using Supabase:** Go to https://supabase.com/dashboard and resume your paused project\n"
            "2. **To use local database:** Comment out the Supabase line in `.streamlit/secrets.toml` and uncomment the local database line, then run `docker-compose up -d`")
    st.stop()

# Tabs
tab1, tab2_1, tab2_2, tab4 = st.tabs(["Übersicht", "Mitarbeiter", "Projekte", "Einstellungen"])

# --- Tab 1: Übersicht (Matrix View) ---
with tab1:
    st.header("Übersicht & Erfassung")
    
    # Filters
    col_filter1, col_filter2, col_filter3 = st.columns(3)
    
    df = utils.load_data()
    if not df.empty:
        df['datum'] = pd.to_datetime(df['datum']).dt.date
    
    with col_filter1:
        current_year = date.today().year
        # Always include current year and next year, plus any years from existing data
        data_years = df['datum'].apply(lambda x: x.year).unique().tolist() if not df.empty else []
        all_years = sorted(list(set(data_years + [current_year, current_year + 1])), reverse=True)
        selected_year = st.selectbox("Jahr", all_years)
        
    with col_filter2:
        employees = utils.get_employees()
        selected_emp_filter = st.selectbox("Mitarbeiter", ["Alle"] + employees)

    month_names = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"]
    
    # Loop through all months
    for month_idx, month_name in enumerate(month_names):
        month_num = month_idx + 1
        
        # Default expander state: Expanded if current month or has data? 
        # Let's just expand all or current. User said "one under another", maybe they want to see them.
        # Let's expand the current month by default, others collapsed? Or all collapsed?
        # "display all the months one under another" -> maybe all expanded?
    # --- VIEW 1: ALLE (Project -> Employee x Month) ---
    if selected_emp_filter == "Alle":
        st.subheader(f"Jahresübersicht {selected_year}")
        
        if not df.empty:
            # Filter Data by Year
            df_year = df[df['datum'].apply(lambda x: x.year) == selected_year]
            
            if not df_year.empty:
                # Calculate Grand Total (sum of all projects)
                grand_total = df_year['stunden'].sum()
                st.metric(label="Gesamt (Alle Projekte)", value=f"{grand_total:.2f} Std")
                st.divider()
                
                # Get all projects
                all_projects = utils.get_projects()
                
                for proj in all_projects:
                    with st.expander(f"Projekt: {proj}", expanded=True):
                        # Filter for project
                        df_proj = df_year[df_year['projekt'] == proj]
                        
                        if not df_proj.empty:
                            # Pivot: Index=Mitarbeiter, Columns=Month
                            df_proj['Monat'] = df_proj['datum'].apply(lambda x: x.month)
                            
                            pivot = df_proj.pivot_table(
                                index='mitarbeiter', 
                                columns='Monat', 
                                values='stunden', 
                                aggfunc='sum', 
                                fill_value=0
                            )
                            
                            # Ensure all months 1-12 are present
                            for m in range(1, 13):
                                if m not in pivot.columns:
                                    pivot[m] = 0
                            
                            # Sort columns
                            pivot = pivot.reindex(sorted(pivot.columns), axis=1)
                            
                            # Rename columns to Month Names
                            month_map = {i: month_names[i-1] for i in range(1, 13)}
                            pivot = pivot.rename(columns=month_map)
                            
                            # Add Total Column
                            pivot['Gesamt'] = pivot.sum(axis=1)
                            
                            # Add Total Row
                            pivot.loc['Gesamt'] = pivot.sum(axis=0)
                            
                            # Display Project Total (Sum of Sums)
                            project_total = pivot.at['Gesamt', 'Gesamt']
                            st.caption(f"**Projekt Gesamt: {project_total:.2f} Std**")
                            
                            # Styling
                            def highlight_total(s):
                                is_total_col = s.name == 'Gesamt'
                                return ['background-color: #2b2b2b; color: #ffffff; font-weight: bold' if is_total_col or s.name == 'Gesamt' else '' for i in s.index]

                            st.dataframe(pivot.style.apply(highlight_total, axis=0), use_container_width=True)
                        else:
                            st.info("Keine Stunden für dieses Projekt in diesem Jahr.")
            else:
                st.info("Keine Daten für dieses Jahr.")
        else:
            st.info("Keine Daten vorhanden.")

    # --- VIEW 2: SINGLE EMPLOYEE (Assigned Projects x Day) ---
    else:
        st.subheader(f"Erfassung: {selected_emp_filter} - {selected_year}")
        
        # Get Assigned Projects
        assigned_projects = utils.get_assigned_projects(selected_emp_filter)
        if not assigned_projects:
            st.warning("Diesem Mitarbeiter sind keine Projekte zugewiesen. Bitte unter 'Mitarbeiter' Projekte zuweisen.")
        
        # Loop through all months
        for month_idx, month_name in enumerate(month_names):
            month_num = month_idx + 1
            
            # Always expanded
            with st.expander(f"{month_name} {selected_year}", expanded=True):
                
                # 1. Prepare Matrix Structure
                import calendar
                num_days = calendar.monthrange(selected_year, month_num)[1]
                days = list(range(1, num_days + 1))
                
                # Filter data for this user/month
                user_data = pd.DataFrame()
                if not df.empty:
                    mask = (df['mitarbeiter'] == selected_emp_filter) & \
                           (df['datum'].apply(lambda x: x.year) == selected_year) & \
                           (df['datum'].apply(lambda x: x.month) == month_num)
                    user_data = df[mask]
                
                # Create Matrix DataFrame
                # Index: Assigned Projects only (no Kommentar)
                # Columns: Days (1..31)
                
                # Initialize
                # Load holidays and vacation days once for this month
                holidays = utils.load_holidays()
                vacation_days = utils.load_vacation_days()
                
                matrix_data = {}
                for d in days:
                    # Check weekend, holidays, and vacation days
                    curr_date = date(selected_year, month_num, d)
                    is_weekend = curr_date.weekday() >= 5 # 5=Sat, 6=Sun
                    is_holiday = curr_date in holidays
                    is_vacation = curr_date in vacation_days
                    
                    # Determine default value (priority: weekend > holiday > vacation)
                    if is_weekend:
                        default_val = "/"
                    elif is_holiday:
                        default_val = "F"
                    elif is_vacation:
                        default_val = "U"
                    else:
                        default_val = None
                    
                    # Only use assigned projects
                    matrix_data[d] = [default_val]*len(assigned_projects)
                
                # Row Index Mapping
                row_index = assigned_projects
                
                # Fill with existing data
                df_matrix = pd.DataFrame(matrix_data, index=row_index)
                
                if not user_data.empty:
                    for _, row in user_data.iterrows():
                        d = row['datum'].day
                        proj = row['projekt']
                        val = None
                        
                        if row['typ'] == 'Arbeit':
                            val = row['stunden']
                        else:
                            val = row['typ'] # Code
                        
                        # If project exists in index, update the cell
                        # But preserve holiday/weekend defaults if the DB value is None/empty
                        if proj in df_matrix.index:
                            # Only overwrite if we have actual data, not None
                            if val is not None and str(val).strip() != "" and str(val).lower() != 'nan':
                                df_matrix.at[proj, d] = val

                # Display Editor
                # Calculate Row Totals (Project Totals)
                def calculate_row_total(row):
                    total = 0.0
                    for val in row:
                        try:
                            if val and str(val).strip() != "" and str(val).lower() != 'nan':
                                total += float(str(val).replace(',', '.'))
                        except:
                            pass
                    return total

                # Add Gesamt column for display
                df_display = df_matrix.copy()
                df_display['Gesamt'] = df_display.apply(calculate_row_total, axis=1)
                
                # Add "Gesamt" Row (Grand Total of the "Gesamt" column)
                grand_total = df_display['Gesamt'].sum()
                
                # Display Grand Total as a Metric above or below
                st.metric("Gesamtstunden (Monat)", f"{grand_total:.2f}")

                edited_matrix = st.data_editor(
                    df_display,
                    use_container_width=True,
                    key=f"editor_{month_num}",
                    num_rows="fixed", # Prevent adding/deleting rows
                    disabled=["Gesamt"] # Make Total column read-only
                )
                
                col_add, col_save = st.columns([2, 1])
                with col_save:
                    st.write("") # Spacer
                    st.write("")
                    if st.button("💾 Monat speichern", type="primary", key=f"btn_save_{month_num}"):
                        # Pre-save Validation
                        validation_error = False
                        # Use the original df_matrix structure for validation logic, but get values from edited_matrix
                        # We need to ignore 'Gesamt' column
                        
                        for proj in edited_matrix.index:
                            for col in edited_matrix.columns:
                                if col == "Gesamt": continue # Skip Total Column
                                
                                val = edited_matrix.at[proj, col]
                                if val is not None and str(val).strip() != "" and str(val).lower() != 'nan':
                                    # Check if valid
                                    is_valid = False
                                    # 1. Number
                                    try:
                                        float(str(val).replace(',', '.'))
                                        is_valid = True
                                    except ValueError:
                                        # 2. Code
                                        if str(val).upper().strip() in ['U', 'KK', 'F', '/']:
                                            is_valid = True
                                    
                                    if not is_valid:
                                        st.error(f"Ungültiger Wert '{val}' bei {proj} am {col}. Erlaubt: Zahlen, U, KK, F.")
                                        validation_error = True
                        
                        if not validation_error:
                            # Drop 'Gesamt' row and column before saving
                            # We use errors='ignore' just in case
                            to_save = edited_matrix.drop(index=['Gesamt'], columns=['Gesamt'], errors='ignore')
                            if utils.save_matrix_entries(selected_emp_filter, selected_year, month_num, to_save):
                                st.success("Gespeichert!")
                                st.rerun()
                            else:
                                st.error("Fehler beim Speichern.")

    
# Sub-Tab: Mitarbeiter
with tab2_1:
    employees = utils.get_employees()
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Neuen Mitarbeiter anlegen")
        with st.form("add_employee_form"):
            new_emp = st.text_input("Name", placeholder="z. B. Max Mustermann")
            add_clicked = st.form_submit_button("Hinzufügen")
        if add_clicked:
            if new_emp:
                if utils.save_employee(new_emp.strip()):
                    st.success(f"Mitarbeiter '{new_emp}' hinzugefügt.")
                    st.rerun()
                else:
                    st.warning("Mitarbeiter existiert bereits.")
            else:
                st.error("Bitte Name eingeben.")
        
        st.write("---")
        st.caption("Aktuelle Mitarbeiter")
        if employees:
            for emp in employees:
                col_name, col_save, col_delete = st.columns([4, 2, 2])
                new_name = col_name.text_input("Name", value=emp, key=f"emp_edit_{emp}", label_visibility="collapsed")
                if col_save.button("Speichern", key=f"emp_save_{emp}"):
                    if new_name.strip() and new_name.strip() != emp:
                        utils.rename_employee(emp, new_name.strip())
                        st.success(f"'{emp}' in '{new_name}' umbenannt.")
                        st.rerun()
                    else:
                        st.warning("Bitte neuen Namen eingeben.")
                with col_delete.popover(f"🗑️ {emp}", use_container_width=True):
                    st.warning("Dieses Löschen entfernt alle Einträge dieses Mitarbeiters!")
                    if st.button("Löschen bestätigen", key=f"emp_delete_confirm_{emp}", type="primary"):
                        if utils.remove_employee(emp):
                            st.success(f"Mitarbeiter '{emp}' und alle Einträge gelöscht.")
                            st.rerun()
                        else:
                            st.error("Löschen fehlgeschlagen.")
        else:
            st.info("Noch keine Mitarbeiter angelegt.")
                
    with col2:
        st.subheader("Hinweis")
        st.write("Bearbeite oder lösche Mitarbeiter direkt in der Liste. Änderungen werden sofort übernommen.")

# Sub-Tab: Projekte & Zuweisung
with tab2_2:
    col_p1, col_p2 = st.columns(2)
    
    with col_p1:
        st.subheader("Projekte verwalten")
        all_projects = utils.get_projects()
        # Add Project
        with st.form("add_project_form"):
            new_proj_name = st.text_input("Neues Projekt", placeholder="z. B. Kundenprojekt A")
            add_project_clicked = st.form_submit_button("Projekt erstellen")
        if add_project_clicked:
            if new_proj_name:
                if utils.add_project(new_proj_name.strip()):
                    st.success(f"Projekt '{new_proj_name}' erstellt.")
                    st.rerun()
                else:
                    st.error("Projekt konnte nicht erstellt werden (ggf. bereits vorhanden).")
            else:
                st.error("Bitte einen Projektnamen eingeben.")
        
        # List / inline edit/delete
        st.write("---")
        st.caption("Aktuelle Projekte")
        if all_projects:
            for proj in all_projects:
                col_proj_name, col_proj_save, col_proj_delete = st.columns([4, 2, 2])
                edited_proj = col_proj_name.text_input("Projektname", value=proj, key=f"proj_edit_{proj}", label_visibility="collapsed")
                if col_proj_save.button("Speichern", key=f"proj_save_{proj}"):
                    if edited_proj.strip() and edited_proj.strip() != proj:
                        if utils.rename_project(proj, edited_proj.strip()):
                            st.success(f"Projekt '{proj}' in '{edited_proj}' umbenannt.")
                            st.rerun()
                        else:
                            st.error("Umbenennen fehlgeschlagen.")
                    else:
                        st.warning("Bitte neuen Projektnamen eingeben.")
                with col_proj_delete.popover(f"🗑️ {proj}", use_container_width=True):
                    st.warning("Dieses Löschen entfernt alle Einträge für dieses Projekt!")
                    if st.button("Projekt löschen", key=f"proj_delete_confirm_{proj}", type="primary"):
                        if utils.delete_project(proj):
                            st.success(f"Projekt '{proj}' und alle Einträge gelöscht.")
                            st.rerun()
                        else:
                            st.error("Löschen fehlgeschlagen.")
        else:
            st.info("Keine Projekte vorhanden.")
            
    with col_p2:
        st.subheader("Projekt-Zuweisung")
        employees = utils.get_employees()
        if employees:
            assign_emp = st.selectbox("Mitarbeiter für Zuweisung", employees, key="assign_emp")
            
            # Multi-select for projects
            all_projects = utils.get_projects()
            current_assigned = utils.get_assigned_projects(assign_emp)
            
            selected_projects = st.multiselect(
                "Zugewiesene Projekte",
                all_projects,
                default=current_assigned
            )
            
            if st.button("Zuweisung speichern"):
                if utils.update_assigned_projects(assign_emp, selected_projects):
                    st.success("Gespeichert!")
                    st.rerun()
                else:
                    st.error("Fehler beim Speichern.")
        else:
            st.info("Bitte erst Mitarbeiter anlegen.")

# --- Tab 3: Berichte ---
# with tab3:
#     st.header("Berichte exportieren")
    
#     df = utils.load_data()
#     if not df.empty:
#         df['datum'] = pd.to_datetime(df['datum'])
#         years = sorted(df['datum'].dt.year.unique(), reverse=True)
#         report_year = st.selectbox("Jahr für Bericht", years, key="report_year")
        
#         col1, col2 = st.columns(2)
        
#         with col1:
#             # CSV Download
#             csv_data = df[df['datum'].dt.year == report_year].to_csv(index=False).encode('utf-8')
#             st.download_button(
#                 label=f"📄 Download CSV {report_year}",
#                 data=csv_data,
#                 file_name=f"{report_year}_stunden.csv",
#                 mime='text/csv',
#             )
            
#         with col2:
#             # PDF Generation
#             if st.button(f"📄 Generiere PDF {report_year}"):
#                 filename = f"{report_year}_bericht.pdf"
#                 if utils.generate_pdf_report(report_year, filename):
#                     with open(filename, "rb") as pdf_file:
#                         st.download_button(
#                             label="Download PDF",
#                             data=pdf_file,
#                             file_name=filename,
#                             mime="application/pdf"
#                         )
#                 else:
#                     st.error("Fehler beim Generieren des PDFs oder keine Daten.")
#     else:
#         st.info("Keine Daten verfügbar.")

# --- Tab 4: Einstellungen (Feiertage) ---
with tab4:
    st.header("Einstellungen")
    
    # Year Management Section
    st.subheader("Jahre verwalten")
    
    # Display current years
    current_year = date.today().year
    data_years = df['datum'].apply(lambda x: x.year).unique().tolist() if not df.empty else []
    available_years = sorted(list(set(data_years + [current_year, current_year + 1])), reverse=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.write("**Verfügbare Jahre:**")
        if available_years:
            years_display = ", ".join([str(year) for year in available_years])
            st.markdown(years_display)
        else:
            st.info("Keine Jahre verfügbar")
    
    with col2:
        new_year = st.number_input("Neues Jahr", min_value=2020, max_value=2100, value=current_year + 1, step=1, key="new_year_input", label_visibility="collapsed")
        
        # Check if year already exists
        year_exists = new_year in available_years
        
        if year_exists:
            st.warning(f"⚠️ Jahr {new_year} existiert bereits!")
            button_disabled = True
        else:
            button_disabled = False
        
        if st.button("➕ Jahr hinzufügen", use_container_width=True, disabled=button_disabled):
            # Double-check that year doesn't exist (in case data changed)
            if new_year in available_years:
                st.error(f"Jahr {new_year} existiert bereits und kann nicht hinzugefügt werden.")
            else:
                # Ensure System employee and Platzhalter project exist
                utils.save_employee("System")
                utils.add_project("Platzhalter")
                
                # Create a dummy entry to make the year appear in the list
                dummy_date = date(new_year, 1, 1)
                success = utils.save_entry(dummy_date, "System", "Platzhalter", 0.0, f"Jahr {new_year} aktiviert", "System")
                if success:
                    st.success(f"Jahr {new_year} hinzugefügt!")
                    st.rerun()
                else:
                    st.error("Fehler beim Hinzufügen des Jahres.")
    
    st.divider()
    
    # Cleanup System and Platzhalter
    st.subheader("Aufräumen")
    st.write("Entferne System-Mitarbeiter und Platzhalter-Projekt (wird beim Hinzufügen von Jahren erstellt)")
    
    col_cleanup1, col_cleanup2 = st.columns([2, 1])
    with col_cleanup1:
        # Check if System or Platzhalter exist
        employees = utils.get_employees()
        projects = utils.get_projects()
        has_system = "System" in employees
        has_platzhalter = "Platzhalter" in projects
        
        if has_system or has_platzhalter:
            status_text = []
            if has_system:
                status_text.append("System")
            if has_platzhalter:
                status_text.append("Platzhalter")
            st.info(f"Gefunden: {', '.join(status_text)}")
        else:
            st.success("✅ Keine System/Platzhalter Einträge gefunden")
    
    with col_cleanup2:
        if st.button("🗑️ System & Platzhalter entfernen", use_container_width=True, 
                     disabled=not (has_system or has_platzhalter)):
            success, message, count_deleted = utils.cleanup_system_placeholders()
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)
    
    st.divider()
    
    # Holiday Management
    st.subheader("Feiertage verwalten")
    
    # Year selector for holiday management - use same logic as main view
    current_year = date.today().year
    data_years = df['datum'].apply(lambda x: x.year).unique().tolist() if not df.empty else []
    available_years = sorted(list(set(data_years + [current_year, current_year + 1])), reverse=True)
    
    st.write("### Jahr auswählen")
    holiday_year = st.selectbox("Jahr für Feiertage", 
                                 available_years,
                                 key="holiday_year")
    
    col_actions = st.columns([1, 1])
    
    # Auto-generate holidays
    with col_actions[0]:
        if st.button("🇩🇪 Feiertage generieren", type="primary", use_container_width=True):
            count, error = utils.populate_german_holidays(holiday_year)
            if error:
                st.error(error)
            elif count > 0:
                st.success(f"{count} Feiertage hinzugefügt!")
                st.rerun()
            else:
                st.info(f"Alle Feiertage für {holiday_year} bereits vorhanden.")
    
    st.divider()
    
    # Display holidays for selected year with edit and delete functionality
    st.write(f"### Feiertage {holiday_year}")
    h_df = utils.get_holidays_df(year=holiday_year)
    
    if not h_df.empty:
        # Display holidays with editable names and delete buttons
        for idx, row in h_df.iterrows():
            col1, col2, col3, col4 = st.columns([2, 4, 1, 1])
            with col1:
                st.write(f"**{row['Datum']}**")
            with col2:
                # Editable name field
                new_name = st.text_input("Name", value=row['Name'], key=f"h_edit_{row['Datum']}", label_visibility="collapsed")
                if new_name != row['Name']:
                    utils.update_holiday(row['Datum'], new_name)
            with col3:
                if st.button("�", key=f"save_h_{row['Datum']}", help="Änderungen speichern"):
                    st.rerun()
            with col4:
                if st.button("�🗑️", key=f"del_h_{row['Datum']}", help="Löschen"):
                    if utils.delete_holiday(row['Datum']):
                        st.success("Gelöscht!")
                        st.rerun()
    else:
        st.info(f"Keine Feiertage für {holiday_year} gespeichert.")
    
    st.divider()
    
    # Manual holiday entry
    st.write("### Neuer Feiertag")
    col1, col2 = st.columns([2, 1])
    with col1:
        h_date = st.date_input("Datum", date(holiday_year, 1, 1), key="new_holiday_date")
        h_name = st.text_input("Name", key="new_holiday_name")
    with col2:
        st.write("")
        st.write("")
        if st.button("➕ Hinzufügen", use_container_width=True, key="add_holiday_btn"):
            if h_name:
                if utils.save_holiday(h_date, h_name):
                    st.success("Gespeichert!")
                    st.rerun()
                else:
                    st.info("Feiertag existiert bereits.")
            else:
                st.error("Bitte Name eingeben.")
    
    st.divider()
    st.divider()
    
    # === VACATION DAYS MANAGEMENT ===
    st.subheader("Urlaubstage verwalten")
    st.write("Urlaubstage gelten für ALLE Mitarbeiter (werden mit 'U' vorgefüllt)")
    
    # Year selector for vacation days
    st.write("### Jahr auswählen")
    vacation_year = st.selectbox("Jahr für Urlaubstage", 
                                  available_years,
                                  key="vacation_year")
    
    # Display vacation days for selected year
    st.write(f"### Urlaubstage {vacation_year}")
    v_df = utils.get_vacation_days_df(year=vacation_year)
    
    if not v_df.empty:
        # Display vacation days with editable names and delete buttons
        for idx, row in v_df.iterrows():
            col1, col2, col3, col4 = st.columns([2, 4, 1, 1])
            with col1:
                st.write(f"**{row['Datum']}**")
            with col2:
                # Editable name field
                new_name = st.text_input("Name", value=row['Name'], key=f"v_edit_{row['Datum']}", label_visibility="collapsed")
                if new_name != row['Name']:
                    utils.update_vacation_day(row['Datum'], new_name)
            with col3:
                if st.button("💾", key=f"save_v_{row['Datum']}", help="Änderungen speichern"):
                    st.rerun()
            with col4:
                if st.button("🗑️", key=f"del_v_{row['Datum']}", help="Löschen"):
                    if utils.delete_vacation_day(row['Datum']):
                        st.success("Gelöscht!")
                        st.rerun()
    else:
        st.info(f"Keine Urlaubstage für {vacation_year} gespeichert.")
    
    st.divider()
    
    # Manual vacation day entry
    st.write("### Neuer Urlaubstag")
    col1, col2 = st.columns([2, 1])
    with col1:
        v_date = st.date_input("Datum", date(vacation_year, 1, 1), key="new_vacation_date")
        v_name = st.text_input("Name", key="new_vacation_name", placeholder="z.B. Betriebsurlaub")
    with col2:
        st.write("")
        st.write("")
        if st.button("➕ Hinzufügen", use_container_width=True, key="add_vacation_btn"):
            if v_name:
                if utils.save_vacation_day(v_date, v_name):
                    st.success("Gespeichert!")
                    st.rerun()
                else:
                    st.info("Urlaubstag existiert bereits.")
            else:
                st.error("Bitte Name eingeben.")
