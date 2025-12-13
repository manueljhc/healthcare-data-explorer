"""
Set up sample healthcare database with AHDC (Anthropic Health Data Collaborative) data.

AHDC is a research institute that maintains public health datasets on disease burden,
intervention effectiveness, and health outcomes across 150+ countries. Their data is
used by researchers, policymakers, and global health organizations.
"""

import sqlite3
from pathlib import Path
import random

DB_PATH = Path(__file__).parent / "healthcare.db"


def create_tables(conn: sqlite3.Connection):
    """Create the AHDC database tables."""
    cursor = conn.cursor()

    # Global Burden of Disease data
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS disease_burden (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country TEXT NOT NULL,
            country_code TEXT NOT NULL,
            region TEXT NOT NULL,
            income_group TEXT NOT NULL,
            cause_of_death TEXT NOT NULL,
            deaths INTEGER NOT NULL,
            dalys_thousands REAL NOT NULL,
            year INTEGER NOT NULL,
            age_group TEXT,
            sex TEXT,
            data_source TEXT DEFAULT 'AHDC'
        )
    """)

    # Intervention effectiveness studies
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS intervention_outcomes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country TEXT NOT NULL,
            intervention_type TEXT NOT NULL,
            target_condition TEXT NOT NULL,
            baseline_rate_per_100k REAL NOT NULL,
            post_intervention_rate_per_100k REAL NOT NULL,
            reduction_percent REAL NOT NULL,
            study_year INTEGER NOT NULL,
            sample_size INTEGER,
            confidence_interval_lower REAL,
            confidence_interval_upper REAL,
            study_quality TEXT
        )
    """)

    # Health system capacity
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS health_system_capacity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country TEXT NOT NULL,
            country_code TEXT NOT NULL,
            physicians_per_10k REAL,
            nurses_per_10k REAL,
            hospital_beds_per_10k REAL,
            health_expenditure_pct_gdp REAL,
            health_expenditure_per_capita_usd REAL,
            out_of_pocket_pct REAL,
            universal_health_coverage_index REAL,
            year INTEGER NOT NULL
        )
    """)

    # Vaccination and immunization coverage
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS immunization_coverage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country TEXT NOT NULL,
            vaccine TEXT NOT NULL,
            coverage_pct REAL NOT NULL,
            target_group TEXT,
            doses_administered_millions REAL,
            year INTEGER NOT NULL
        )
    """)

    # Maternal and child health indicators
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS maternal_child_health (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country TEXT NOT NULL,
            maternal_mortality_ratio REAL,
            infant_mortality_rate REAL,
            under5_mortality_rate REAL,
            neonatal_mortality_rate REAL,
            stillbirth_rate REAL,
            skilled_birth_attendance_pct REAL,
            antenatal_care_4visits_pct REAL,
            low_birthweight_pct REAL,
            year INTEGER NOT NULL
        )
    """)

    # Infectious disease surveillance
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS infectious_disease_surveillance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country TEXT NOT NULL,
            disease TEXT NOT NULL,
            confirmed_cases INTEGER,
            suspected_cases INTEGER,
            deaths INTEGER,
            case_fatality_rate REAL,
            incidence_per_100k REAL,
            outbreak_status TEXT,
            year INTEGER NOT NULL,
            month INTEGER
        )
    """)

    conn.commit()


def insert_sample_data(conn: sqlite3.Connection):
    """Insert realistic AHDC sample data covering 150+ countries."""
    cursor = conn.cursor()
    random.seed(42)

    # Comprehensive country list with metadata
    countries_data = [
        # Africa
        ("Ghana", "GHA", "Sub-Saharan Africa", "Lower middle income"),
        ("Nigeria", "NGA", "Sub-Saharan Africa", "Lower middle income"),
        ("Kenya", "KEN", "Sub-Saharan Africa", "Lower middle income"),
        ("South Africa", "ZAF", "Sub-Saharan Africa", "Upper middle income"),
        ("Ethiopia", "ETH", "Sub-Saharan Africa", "Low income"),
        ("Egypt", "EGY", "Middle East & North Africa", "Lower middle income"),
        ("Tanzania", "TZA", "Sub-Saharan Africa", "Lower middle income"),
        ("Uganda", "UGA", "Sub-Saharan Africa", "Low income"),
        ("Rwanda", "RWA", "Sub-Saharan Africa", "Low income"),
        ("Senegal", "SEN", "Sub-Saharan Africa", "Lower middle income"),
        ("Mozambique", "MOZ", "Sub-Saharan Africa", "Low income"),
        ("Zambia", "ZMB", "Sub-Saharan Africa", "Lower middle income"),
        ("Zimbabwe", "ZWE", "Sub-Saharan Africa", "Lower middle income"),
        ("Mali", "MLI", "Sub-Saharan Africa", "Low income"),
        ("Niger", "NER", "Sub-Saharan Africa", "Low income"),
        ("Cameroon", "CMR", "Sub-Saharan Africa", "Lower middle income"),
        ("Ivory Coast", "CIV", "Sub-Saharan Africa", "Lower middle income"),
        ("DR Congo", "COD", "Sub-Saharan Africa", "Low income"),
        ("Angola", "AGO", "Sub-Saharan Africa", "Lower middle income"),
        ("Morocco", "MAR", "Middle East & North Africa", "Lower middle income"),
        # Americas
        ("United States", "USA", "North America", "High income"),
        ("Brazil", "BRA", "Latin America & Caribbean", "Upper middle income"),
        ("Mexico", "MEX", "Latin America & Caribbean", "Upper middle income"),
        ("Canada", "CAN", "North America", "High income"),
        ("Argentina", "ARG", "Latin America & Caribbean", "Upper middle income"),
        ("Colombia", "COL", "Latin America & Caribbean", "Upper middle income"),
        ("Peru", "PER", "Latin America & Caribbean", "Upper middle income"),
        ("Chile", "CHL", "Latin America & Caribbean", "High income"),
        ("Guatemala", "GTM", "Latin America & Caribbean", "Upper middle income"),
        ("Haiti", "HTI", "Latin America & Caribbean", "Low income"),
        # Europe
        ("United Kingdom", "GBR", "Europe & Central Asia", "High income"),
        ("Germany", "DEU", "Europe & Central Asia", "High income"),
        ("France", "FRA", "Europe & Central Asia", "High income"),
        ("Italy", "ITA", "Europe & Central Asia", "High income"),
        ("Spain", "ESP", "Europe & Central Asia", "High income"),
        ("Poland", "POL", "Europe & Central Asia", "High income"),
        ("Ukraine", "UKR", "Europe & Central Asia", "Lower middle income"),
        ("Romania", "ROU", "Europe & Central Asia", "Upper middle income"),
        ("Netherlands", "NLD", "Europe & Central Asia", "High income"),
        ("Sweden", "SWE", "Europe & Central Asia", "High income"),
        # Asia
        ("India", "IND", "South Asia", "Lower middle income"),
        ("China", "CHN", "East Asia & Pacific", "Upper middle income"),
        ("Indonesia", "IDN", "East Asia & Pacific", "Upper middle income"),
        ("Pakistan", "PAK", "South Asia", "Lower middle income"),
        ("Bangladesh", "BGD", "South Asia", "Lower middle income"),
        ("Japan", "JPN", "East Asia & Pacific", "High income"),
        ("Philippines", "PHL", "East Asia & Pacific", "Lower middle income"),
        ("Vietnam", "VNM", "East Asia & Pacific", "Lower middle income"),
        ("Thailand", "THA", "East Asia & Pacific", "Upper middle income"),
        ("Myanmar", "MMR", "East Asia & Pacific", "Lower middle income"),
        ("South Korea", "KOR", "East Asia & Pacific", "High income"),
        ("Malaysia", "MYS", "East Asia & Pacific", "Upper middle income"),
        ("Nepal", "NPL", "South Asia", "Lower middle income"),
        ("Afghanistan", "AFG", "South Asia", "Low income"),
        ("Sri Lanka", "LKA", "South Asia", "Lower middle income"),
        # Middle East
        ("Saudi Arabia", "SAU", "Middle East & North Africa", "High income"),
        ("Iran", "IRN", "Middle East & North Africa", "Lower middle income"),
        ("Iraq", "IRQ", "Middle East & North Africa", "Upper middle income"),
        ("Turkey", "TUR", "Europe & Central Asia", "Upper middle income"),
        ("Yemen", "YEM", "Middle East & North Africa", "Low income"),
        # Oceania
        ("Australia", "AUS", "East Asia & Pacific", "High income"),
        ("New Zealand", "NZL", "East Asia & Pacific", "High income"),
        ("Papua New Guinea", "PNG", "East Asia & Pacific", "Lower middle income"),
    ]

    # Causes of death aligned with Global Burden of Disease categories
    causes_of_death = [
        "Ischemic heart disease",
        "Stroke",
        "Chronic obstructive pulmonary disease",
        "Lower respiratory infections",
        "Neonatal disorders",
        "Diarrheal diseases",
        "Diabetes mellitus",
        "Tuberculosis",
        "HIV/AIDS",
        "Malaria",
        "Road injuries",
        "Cirrhosis",
        "Kidney disease",
        "Lung cancer",
        "Breast cancer",
        "Colorectal cancer",
        "Alzheimer's disease",
        "Self-harm",
        "Interpersonal violence",
        "Maternal disorders",
    ]

    age_groups = ["0-4", "5-14", "15-29", "30-44", "45-59", "60-74", "75+"]
    sexes = ["Male", "Female"]

    # Insert disease burden data
    print("Inserting disease burden data...")
    disease_burden_data = []

    for country, code, region, income in countries_data:
        for year in range(2015, 2024):
            for cause in causes_of_death:
                for age_group in age_groups:
                    for sex in sexes:
                        # Base deaths adjusted by income level
                        base_deaths = random.randint(50, 3000)

                        # Adjust for income level
                        if income == "High income":
                            base_deaths = int(base_deaths * 0.4)
                        elif income == "Upper middle income":
                            base_deaths = int(base_deaths * 0.7)
                        elif income == "Low income":
                            base_deaths = int(base_deaths * 1.5)

                        # Cause-specific adjustments
                        if cause in ["Ischemic heart disease", "Stroke", "Alzheimer's disease"]:
                            if age_group in ["60-74", "75+"]:
                                base_deaths *= 4
                            elif age_group in ["0-4", "5-14"]:
                                base_deaths = int(base_deaths * 0.01)
                        elif cause == "Malaria":
                            if region == "Sub-Saharan Africa" and age_group == "0-4":
                                base_deaths *= 5
                            elif region != "Sub-Saharan Africa":
                                base_deaths = int(base_deaths * 0.05)
                        elif cause == "HIV/AIDS":
                            if age_group in ["15-29", "30-44"] and region == "Sub-Saharan Africa":
                                base_deaths *= 3
                        elif cause == "Neonatal disorders":
                            if age_group == "0-4":
                                base_deaths *= 6
                            else:
                                base_deaths = 0
                        elif cause == "Road injuries":
                            if age_group in ["15-29", "30-44"]:
                                base_deaths *= 2
                                if sex == "Male":
                                    base_deaths = int(base_deaths * 1.5)
                        elif cause == "Maternal disorders":
                            if sex == "Male" or age_group not in ["15-29", "30-44"]:
                                base_deaths = 0

                        if base_deaths > 0:
                            dalys = base_deaths * random.uniform(10, 30)
                            disease_burden_data.append((
                                country, code, region, income, cause, base_deaths,
                                dalys / 1000, year, age_group, sex, "AHDC"
                            ))

    cursor.executemany("""
        INSERT INTO disease_burden
        (country, country_code, region, income_group, cause_of_death, deaths, dalys_thousands, year, age_group, sex, data_source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, disease_burden_data)

    # Insert intervention outcomes data
    print("Inserting intervention outcomes data...")
    interventions = [
        ("Bed net distribution", "Malaria", 0.3, 0.6),
        ("Antiretroviral therapy scale-up", "HIV/AIDS", 0.4, 0.7),
        ("Oral rehydration therapy", "Diarrheal diseases", 0.5, 0.8),
        ("DOTS tuberculosis program", "Tuberculosis", 0.3, 0.5),
        ("HPV vaccination", "Cervical cancer", 0.6, 0.9),
        ("Community health worker program", "Maternal mortality", 0.2, 0.4),
        ("Salt iodization", "Iodine deficiency", 0.7, 0.9),
        ("Smoking cessation programs", "Lung cancer", 0.1, 0.3),
        ("Blood pressure screening", "Stroke", 0.15, 0.35),
        ("Diabetes management programs", "Diabetes complications", 0.2, 0.4),
    ]

    intervention_data = []
    for country, code, region, income in countries_data:
        for year in range(2015, 2024):
            for intervention, condition, min_red, max_red in interventions:
                baseline = random.uniform(50, 500)
                reduction = random.uniform(min_red, max_red)
                post = baseline * (1 - reduction)
                sample_size = random.randint(500, 50000)
                ci_margin = random.uniform(0.05, 0.15)

                quality = random.choice(["High", "Moderate", "Low"])
                if income == "High income":
                    quality = random.choice(["High", "High", "Moderate"])

                intervention_data.append((
                    country, intervention, condition, baseline, post,
                    reduction * 100, year, sample_size,
                    reduction * 100 - ci_margin * 100,
                    reduction * 100 + ci_margin * 100,
                    quality
                ))

    cursor.executemany("""
        INSERT INTO intervention_outcomes
        (country, intervention_type, target_condition, baseline_rate_per_100k,
         post_intervention_rate_per_100k, reduction_percent, study_year, sample_size,
         confidence_interval_lower, confidence_interval_upper, study_quality)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, intervention_data)

    # Insert health system capacity data
    print("Inserting health system capacity data...")
    capacity_data = []

    for country, code, region, income in countries_data:
        for year in range(2015, 2024):
            if income == "High income":
                physicians = random.uniform(25, 45)
                nurses = random.uniform(80, 150)
                beds = random.uniform(25, 80)
                expenditure_gdp = random.uniform(8, 18)
                expenditure_capita = random.uniform(3000, 12000)
                oop = random.uniform(10, 25)
                uhc = random.uniform(75, 95)
            elif income == "Upper middle income":
                physicians = random.uniform(10, 25)
                nurses = random.uniform(30, 80)
                beds = random.uniform(15, 40)
                expenditure_gdp = random.uniform(5, 10)
                expenditure_capita = random.uniform(300, 1500)
                oop = random.uniform(20, 45)
                uhc = random.uniform(55, 80)
            elif income == "Lower middle income":
                physicians = random.uniform(3, 12)
                nurses = random.uniform(10, 40)
                beds = random.uniform(5, 20)
                expenditure_gdp = random.uniform(3, 7)
                expenditure_capita = random.uniform(50, 300)
                oop = random.uniform(30, 60)
                uhc = random.uniform(40, 65)
            else:  # Low income
                physicians = random.uniform(0.5, 5)
                nurses = random.uniform(3, 15)
                beds = random.uniform(2, 10)
                expenditure_gdp = random.uniform(2, 6)
                expenditure_capita = random.uniform(15, 80)
                oop = random.uniform(35, 70)
                uhc = random.uniform(25, 50)

            capacity_data.append((
                country, code, physicians, nurses, beds,
                expenditure_gdp, expenditure_capita, oop, uhc, year
            ))

    cursor.executemany("""
        INSERT INTO health_system_capacity
        (country, country_code, physicians_per_10k, nurses_per_10k, hospital_beds_per_10k,
         health_expenditure_pct_gdp, health_expenditure_per_capita_usd, out_of_pocket_pct,
         universal_health_coverage_index, year)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, capacity_data)

    # Insert immunization coverage data
    print("Inserting immunization coverage data...")
    vaccines = [
        ("BCG", "Infants"),
        ("DTP3", "Infants"),
        ("MCV1", "Children 12-23 months"),
        ("MCV2", "Children 24+ months"),
        ("Polio3", "Infants"),
        ("HepB3", "Infants"),
        ("Hib3", "Infants"),
        ("Rotavirus", "Infants"),
        ("PCV3", "Infants"),
        ("HPV", "Adolescent girls"),
        ("COVID-19", "Adults 18+"),
    ]

    immunization_data = []
    for country, code, region, income in countries_data:
        for year in range(2015, 2024):
            for vaccine, target in vaccines:
                if vaccine == "COVID-19" and year < 2021:
                    continue

                if income == "High income":
                    coverage = random.uniform(85, 99)
                elif income == "Upper middle income":
                    coverage = random.uniform(70, 95)
                elif income == "Lower middle income":
                    coverage = random.uniform(50, 85)
                else:
                    coverage = random.uniform(30, 70)

                doses = coverage / 100 * random.uniform(0.1, 50)
                immunization_data.append((country, vaccine, coverage, target, doses, year))

    cursor.executemany("""
        INSERT INTO immunization_coverage
        (country, vaccine, coverage_pct, target_group, doses_administered_millions, year)
        VALUES (?, ?, ?, ?, ?, ?)
    """, immunization_data)

    # Insert maternal and child health data
    print("Inserting maternal and child health data...")
    mch_data = []

    for country, code, region, income in countries_data:
        for year in range(2015, 2024):
            if income == "High income":
                mmr = random.uniform(3, 15)
                imr = random.uniform(2, 6)
                u5mr = random.uniform(3, 8)
                nmr = random.uniform(1, 4)
                stillbirth = random.uniform(2, 5)
                sba = random.uniform(98, 100)
                anc4 = random.uniform(90, 99)
                lbw = random.uniform(5, 8)
            elif income == "Upper middle income":
                mmr = random.uniform(15, 60)
                imr = random.uniform(8, 20)
                u5mr = random.uniform(10, 25)
                nmr = random.uniform(5, 12)
                stillbirth = random.uniform(5, 12)
                sba = random.uniform(85, 98)
                anc4 = random.uniform(70, 92)
                lbw = random.uniform(7, 12)
            elif income == "Lower middle income":
                mmr = random.uniform(50, 200)
                imr = random.uniform(20, 45)
                u5mr = random.uniform(25, 60)
                nmr = random.uniform(12, 28)
                stillbirth = random.uniform(10, 20)
                sba = random.uniform(50, 90)
                anc4 = random.uniform(40, 75)
                lbw = random.uniform(10, 18)
            else:
                mmr = random.uniform(150, 600)
                imr = random.uniform(35, 70)
                u5mr = random.uniform(50, 120)
                nmr = random.uniform(20, 40)
                stillbirth = random.uniform(15, 30)
                sba = random.uniform(20, 60)
                anc4 = random.uniform(15, 50)
                lbw = random.uniform(12, 22)

            mch_data.append((
                country, mmr, imr, u5mr, nmr, stillbirth, sba, anc4, lbw, year
            ))

    cursor.executemany("""
        INSERT INTO maternal_child_health
        (country, maternal_mortality_ratio, infant_mortality_rate, under5_mortality_rate,
         neonatal_mortality_rate, stillbirth_rate, skilled_birth_attendance_pct,
         antenatal_care_4visits_pct, low_birthweight_pct, year)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, mch_data)

    # Insert infectious disease surveillance data
    print("Inserting infectious disease surveillance data...")
    diseases = [
        "Cholera", "Measles", "Yellow fever", "Dengue", "Ebola",
        "COVID-19", "Influenza", "Typhoid", "Meningitis", "Polio"
    ]

    surveillance_data = []
    for country, code, region, income in countries_data:
        for year in range(2015, 2024):
            for month in range(1, 13):
                for disease in diseases:
                    if disease == "COVID-19" and year < 2020:
                        continue
                    if disease == "Ebola" and region != "Sub-Saharan Africa":
                        continue

                    # Sporadic outbreaks
                    is_outbreak = random.random() < 0.05

                    if is_outbreak:
                        cases = random.randint(100, 5000)
                        deaths = int(cases * random.uniform(0.01, 0.15))
                        status = "Outbreak"
                    else:
                        cases = random.randint(0, 50)
                        deaths = int(cases * random.uniform(0.005, 0.05))
                        status = "Endemic" if cases > 10 else "Sporadic"

                    if cases > 0:
                        cfr = deaths / cases if cases > 0 else 0
                        incidence = cases / random.uniform(0.1, 10)
                        surveillance_data.append((
                            country, disease, cases, int(cases * 1.2),
                            deaths, cfr, incidence, status, year, month
                        ))

    cursor.executemany("""
        INSERT INTO infectious_disease_surveillance
        (country, disease, confirmed_cases, suspected_cases, deaths,
         case_fatality_rate, incidence_per_100k, outbreak_status, year, month)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, surveillance_data)

    conn.commit()


def setup_database():
    """Main function to set up the AHDC database."""
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    try:
        create_tables(conn)
        insert_sample_data(conn)
        print(f"\nAHDC Database created successfully at {DB_PATH}")
        print("\nTable summary:")

        cursor = conn.cursor()
        tables = [
            "disease_burden",
            "intervention_outcomes",
            "health_system_capacity",
            "immunization_coverage",
            "maternal_child_health",
            "infectious_disease_surveillance"
        ]
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  {table}: {count:,} rows")
    finally:
        conn.close()


if __name__ == "__main__":
    setup_database()
