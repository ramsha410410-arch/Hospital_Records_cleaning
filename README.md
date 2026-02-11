🏥 Hospital Records Cleaning Pipeline 

This project is part of my Hospital Records Cleaning module that I taught in class. The goal of this exercise was to simulate a real-world healthcare dataset cleaning workflow using Python and Pandas — the same type of messy data we often face in industry (missing values, inconsistent formats, duplicates, invalid ages, wrong dates, noisy phone numbers, etc.).

Students learned how to:

load real CSV data safely,

standardize inconsistent columns,

detect and handle missing/dirty values,

clean important healthcare-related fields,

generate reports,

and export a final cleaned dataset ready for analysis.

🎯 Project Objective

Healthcare datasets are commonly messy because data comes from multiple sources (manual entry, different hospital systems, multiple departments). This project demonstrates how to build a reusable cleaning pipeline that:

✅ Loads raw data
✅ Cleans and standardizes formatting
✅ Fixes invalid or inconsistent values
✅ Produces missing-value reports (before & after)
✅ Saves a cleaned dataset for downstream analysis/ML

📁 Folder Structure

The code expects the following structure inside your project folder:

hospital-records-cleaning/
│
├── data/
│   ├── raw/
│   │   └── hospital_patients_real_world.csv
│   │
│   └── cleaned/
│       └── hospital_records_cleaned.csv
│
├── reports/
│   ├── missing_report_before.csv
│   └── missing_report_after.csv
│
├── clean_hospital_records.py
└── requirements.txt


✅ The script automatically creates:

data/cleaned/

reports/

if they don’t already exist.

⚙️ Tools & Libraries Used

This project uses:

Python 3

Pandas (data manipulation and cleaning)

NumPy (missing values & numeric operations)

No heavy dependencies are needed — it’s intentionally lightweight and beginner-friendly.

📦 Installation
1) Clone / Download the Project

Place the project folder in your Google Drive or local system.

2) Install requirements
pip install -r requirements.txt


requirements.txt

pandas>=2.0.0
numpy>=1.24.0

▶️ How to Run
✅ Running in Google Colab (Recommended)

Upload clean_hospital_records.py to Colab

Ensure your folder exists in Drive:

/content/drive/MyDrive/hospital-records-cleaning/

Run:

python clean_hospital_records.py


The script automatically mounts Google Drive when running in Colab.

✅ Running Locally (Optional)

If running locally, you can modify:

PROJECT_ROOT = Path("/content/drive/MyDrive/hospital-records-cleaning/")


to your local path, e.g.:

PROJECT_ROOT = Path(r"C:\Users\YourName\Documents\hospital-records-cleaning")


Then run:

python clean_hospital_records.py

🧹 Cleaning Steps Implemented
1) Safe CSV Loading

Reads CSV normally

If encoding fails, retries using latin1

2) Standardize Column Names

Prevents column mismatch issues due to:

spaces

uppercase/lowercase differences

special characters

Example:

"Patient Name " → patient_name

"DOB(Date)" → dobdate

3) Convert “Empty-like” Values to NaN

Converts messy placeholders to real missing values:

Examples:

n/a, na, none, null, ?, -, empty strings → NaN

4) Remove Duplicate Records

Drops duplicate rows and resets index.

5) Trim Text Columns

Removes extra spaces in string columns:

" Male " → "Male"

6) Auto-Detect Important Columns

The script prints possible columns for:

IDs

names

gender/sex

age

date fields

phone/contact

billing/cost fields

This helps in datasets where columns can be named differently.

7) Gender Cleaning

If gender or sex exists:

converts variations to a standard form:

M, male, man → male

F, female, woman → female

8) Age Cleaning

If age exists:

converts to numeric

invalid ranges are removed:

age < 0 or age > 120 → NaN

9) Date Parsing

Automatically detects columns containing:

date, admission, discharge, dob
and converts them using:

pd.to_datetime(..., errors="coerce")


Bad dates become NaT safely.

10) Phone Number Cleaning

For columns like phone, mobile, contact:

keeps digits only

invalid lengths are discarded:

< 10 digits or > 15 digits → NaN

11) Convert Numeric-looking Text Columns

If a text column is mostly numeric (≥ 70%), it is converted to numeric safely.

12) Outlier Capping (IQR Method)

For numeric columns (excluding ID columns), outliers are capped using IQR:

below: Q1 - 1.5*IQR

above: Q3 + 1.5*IQR

This prevents extreme values from breaking analysis.

13) Missing Value Imputation

Safe default imputation:

numeric columns → median

text columns → "unknown"

📊 Outputs

After running, you get:

✅ Cleaned Dataset

data/cleaned/hospital_records_cleaned.csv

✅ Missing Value Reports

reports/missing_report_before.csv

reports/missing_report_after.csv

These reports make it easy to compare how data quality improved.

🧠 Class Learning Outcomes

Students learned:

real-world data cleaning strategies

handling missing data properly

standardization best practices

building an end-to-end pipeline

saving reproducible outputs

preparing a dataset for analysis / ML

🔮 Future Improvements (Optional Enhancements)

Some upgrades we can add later:

command-line arguments (--project-root, --raw-file)

logging instead of print

unit tests for each cleaning function

data validation rules (schema checks)

exporting summary statistics report

👩‍🏫 Author

Created as part of a classroom teaching project on Data Cleaning & Preprocessing in Python.
