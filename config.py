from pathlib import Path

# ✅ Change this if your project folder name changes
PROJECT_ROOT = Path("/content/drive/MyDrive/hospital-records-cleaning")

RAW_DIR = PROJECT_ROOT / "data" / "raw"
CLEAN_DIR = PROJECT_ROOT / "data" / "cleaned"
REPORTS_DIR = PROJECT_ROOT / "reports"
FIG_DIR = REPORTS_DIR / "figures"

# Default raw file name (can be overridden in run script)
DEFAULT_RAW_FILE = "hospital_patients_real_world.csv"
DEFAULT_CLEAN_FILE = "hospital_records_cleaned.csv"


def ensure_folders() -> None:
    """Create output folders if they don't exist (safe to call multiple times)."""
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
