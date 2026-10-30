"""
Configuration, constants, and deterministic seed definitions for Freight Invoice Audit System.
"""
from pathlib import Path

# Deterministic Seed as mandated by prompt
DEFAULT_SEED = 20261022

# Volume presets
SCALE_CONFIGS = {
    "starter": {
        "num_carriers": 10,
        "num_lanes": 20,
        "num_shipments": 200,
        "num_invoices": 150,
    },
    "medium": {
        "num_carriers": 25,
        "num_lanes": 50,
        "num_shipments": 2000,
        "num_invoices": 1500,
    },
    "full": {
        # Exactly as specified in prompt: 100 carriers, 20,000 shipments, 15,000 invoices
        "num_carriers": 100,
        "num_lanes": 150,
        "num_shipments": 20000,
        "num_invoices": 15000,
    }
}

# Directories
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DOCS_DIR = PROJECT_ROOT / "docs"
REPORTS_DIR = PROJECT_ROOT / "reports"

# ID Formatting templates
ID_CARRIER_FMT = "CAR-{:06d}"
ID_LANE_FMT = "LANE-{:06d}"
ID_RATE_CARD_FMT = "RATE-{}-{:04d}-{:02d}"  # RATE-<carrier-id>-YYYY-NN
ID_SHIPMENT_FMT = "SHP-2026-{:06d}"
ID_LEG_FMT = "LEG-{}-{:02d}"                 # LEG-<shipment-id>-NN
ID_WEIGHT_FMT = "WM-{}-{:02d}"               # WM-<shipment-id>-NN
ID_ACCESSORIAL_FMT = "ACC-{:06d}"
ID_INVOICE_FMT = "FINV-2026-{:06d}"
ID_INVOICE_LINE_FMT = "FLINE-{}-{:02d}"      # FLINE-<invoice-id>-NN
ID_EXCEPTION_FMT = "FEX-2026-{:06d}"
ID_CREDIT_NOTE_FMT = "CR-2026-{:06d}"

# Standard Freight Industry Dimensional Factors (Cubic inches per pound)
# Domestic freight standard is 139 or 166
DIM_FACTORS = [139, 166]

# Standard Weight Tiers in pounds (min_lbs, max_lbs)
WEIGHT_TIERS = [
    (0.0, 500.0),
    (500.0, 1000.0),
    (1000.0, 2000.0),
    (2000.0, 5000.0),
    (5000.0, 10000.0),
    (10000.0, 20000.0),
    (20000.0, 45000.0),  # Full Truckload max
]

# Standard Accessorial Base Tariffs
ACCESSORIAL_RATES = {
    "LIFTGATE": 75.00,
    "RESIDENTIAL": 65.00,
    "INSIDE_PICKUP": 85.00,
    "HAZMAT": 150.00,
    "DETENTION": 100.00,  # Per hour/event
    "REDELIVERY": 90.00,
    "STORAGE": 50.00,
}
