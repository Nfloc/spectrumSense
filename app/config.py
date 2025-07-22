from pathlib import Path

# Root of the project (2 levels up from this file)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Data paths
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "models"
APP_DIR = PROJECT_ROOT / "app"

# Output files
MONITOR_RAW_JSON = DATA_DIR / "monitor_raw_data.json"
BASELINE_RAW_JSON = DATA_DIR / "baseline.json"
TI3_OUTPUT = DATA_DIR / "monitor_patch_data.ti3"
COLOR_DATA = DATA_DIR / "color_data.json"

# ICC profiles and matrices
MACBETH_D65_PATH = MODELS_DIR / "mcbeth_D65_CIEXYZ_Values.json"
ICC_PROFILE_PATH = MODELS_DIR / "generated_profile.icc"
COLOR_MATRIX_PATH = MODELS_DIR / "conversion_matrix.json"
XYZ_BASELINE = MODELS_DIR / "XYZ_baseline.json"
XYZ_MONITOR = MODELS_DIR / "XYZ_monitor.json"

# App files
MATRIX_PATH = APP_DIR / "Matrix.py"

# Ensure required folders exist (optional safety)
DATA_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

def file_exists(file_path: Path) -> bool:
    """Check if a file exists."""
    return file_path.is_file()