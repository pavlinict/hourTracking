import streamlit as st
import pandas as pd
import os
from datetime import date, datetime
import utils

st.set_page_config(page_title="Stundenerfassung", layout="wide")

st.title("⏱️ Stundenerfassung")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["Eingabe", "Übersicht", "Berichte", "Einstellungen"])

# --- Tab 1: Eingabe ---
with tab1:
    st.header("Neue Eintragung")
    
    col1, col2 = st.columns(2)
    
    with col1:
        datum = st.date_input("Datum", date.today())
        
        # Load existing employees or allow new one
        df = utils.load_data()
        employees = utils.get_employees(df)
        mitarbeiter = st.selectbox("Mitarbeiter", employees + ["Neu hinzufügen..."])
        if mitarbeiter == "Neu hinzufügen...":
            mitarbeiter = st.text_input("Name des Mitarbeiters")
            
        typ = st.radio("Typ", ["Arbeit", "Urlaub (U)", "Kindkrank (KK)"], horizontal=True)

    with col2:
        if typ == "Arbeit":
            projects = utils.get_projects(df)
            projekt = st.selectbox("Projekt", projects + ["Neu hinzufügen..."])
            if projekt == "Neu hinzufügen...":
                projekt = st.text_input("Projektname")
            
            stunden = st.number_input("Stunden", min_value=0.0, step=0.5, format="%.1f")
            beschreibung = st.text_area("Beschreibung")
        else:
            projekt = typ.split("(")[1].replace(")", "") # Extract U or KK
            stunden = 0.0 
            beschreibung = typ
            st.info(f"Für {typ} wird der Statuscode '{projekt}' gespeichert.")

    if st.button("Speichern"):
        if mitarbeiter:
            type_code = "Arbeit"
            if "Urlaub" in typ: type_code = "U"
            elif "Kindkrank" in typ: type_code = "KK"
            
            # For U and KK, we save the code in Project column as well for visibility if needed, 
            # or just rely on Type. Plan said Type column.
            # Let's keep Project empty for U/KK to avoid cluttering project list, 
            # but maybe useful to see in simple table. 
            # Let's follow plan: Type is U/KK.
            
            utils.save_entry(datum, mitarbeiter, projekt if typ == "Arbeit" else "", stunden, beschreibung, type_code)
            st.success("Eintrag gespeichert!")
        else:
            st.error("Bitte Mitarbeiter angeben.")

# --- Tab 2: Übersicht ---
with tab2:
    st.header("Übersicht")
    
    df = utils.load_data()
    if not df.empty:
        df['Datum'] = pd.to_datetime(df['Datum'])
        
        years = sorted(df['Datum'].dt.year.unique(), reverse=True)
        selected_year = st.selectbox("Jahr auswählen", years)
        
        df_year = df[df['Datum'].dt.year == selected_year]
        
        # Pivot Table: Employee vs Month (Hours)
        st.subheader("Stunden pro Mitarbeiter pro Monat")
        if not df_year.empty:
            df_year['Monat'] = df_year['Datum'].dt.month
            
            # Filter for Work hours only for the sum
            work_df = df_year[df_year['Typ'] == 'Arbeit']
            
            if not work_df.empty:
                pivot = work_df.pivot_table(
                    index='Mitarbeiter', 
                    columns='Monat', 
                    values='Stunden', 
                    aggfunc='sum', 
                    fill_value=0
                )
                # Rename columns to month names
                month_map = {1:'Jan', 2:'Feb', 3:'Mär', 4:'Apr', 5:'Mai', 6:'Jun', 7:'Jul', 8:'Aug', 9:'Sep', 10:'Okt', 11:'Nov', 12:'Dez'}
                pivot.columns = [month_map.get(c, c) for c in pivot.columns]
                
                st.dataframe(pivot)
            else:
                st.info("Keine Arbeitsstunden in diesem Jahr.")
            
            st.subheader("Detaillierte Daten")
            st.dataframe(df_year)
        else:
            st.info("Keine Daten für dieses Jahr.")
    else:
        st.info("Noch keine Daten vorhanden.")

# --- Tab 3: Berichte ---
with tab3:
    st.header("Berichte exportieren")
    
    df = utils.load_data()
    if not df.empty:
        df['Datum'] = pd.to_datetime(df['Datum'])
        years = sorted(df['Datum'].dt.year.unique(), reverse=True)
        report_year = st.selectbox("Jahr für Bericht", years, key="report_year")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # CSV Download
            csv_data = df[df['Datum'].dt.year == report_year].to_csv(index=False).encode('utf-8')
            st.download_button(
                label=f"📄 Download CSV {report_year}",
                data=csv_data,
                file_name=f"{report_year}_stunden.csv",
                mime='text/csv',
            )
            
        with col2:
            # PDF Generation
            if st.button(f"📄 Generiere PDF {report_year}"):
                filename = f"{report_year}_bericht.pdf"
                if utils.generate_pdf_report(report_year, filename):
                    with open(filename, "rb") as pdf_file:
                        st.download_button(
                            label="Download PDF",
                            data=pdf_file,
                            file_name=filename,
                            mime="application/pdf"
                        )
                else:
                    st.error("Fehler beim Generieren des PDFs oder keine Daten.")
    else:
        st.info("Keine Daten verfügbar.")

# --- Tab 4: Einstellungen (Feiertage) ---
with tab4:
    st.header("Einstellungen")
    st.subheader("Feiertage verwalten")
    
    col1, col2 = st.columns(2)
    with col1:
        h_date = st.date_input("Datum Feiertag", date.today())
        h_name = st.text_input("Name des Feiertags")
        if st.button("Feiertag speichern"):
            if h_name:
                utils.save_holiday(h_date, h_name)
                st.success(f"Feiertag '{h_name}' gespeichert.")
            else:
                st.error("Bitte Name eingeben.")
                
    with col2:
        st.write("Gespeicherte Feiertage:")
        if os.path.exists(utils.HOLIDAY_FILE):
            h_df = pd.read_csv(utils.HOLIDAY_FILE)
            st.dataframe(h_df)
        else:
            st.info("Keine Feiertage gespeichert.")
