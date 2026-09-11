from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT / "demo_repo"

# Explicitly approved files for our controlled demo.
ALLOWED_FILES = (
    "README.md",
    "shop/__init__.py",
    "shop/coupons.py",
    "shop/pricing.py",
    "shop/checkout.py",
    "tests/test_checkout.py",
)

MAX_FILE_BYTES = 64_000