"""
Schema definitions, Enums, Data Models, and SQL DDL generator for Freight Audit System.
"""
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Optional, List, Dict, Any

# ==========================================
# Enumerations
# ==========================================

class CarrierMode(str, Enum):
    FTL = "FTL"
    LTL = "LTL"
    PARCEL = "PARCEL"
    INTERMODAL = "INTERMODAL"

class CarrierStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    TERMINATED = "TERMINATED"

class ServiceLevel(str, Enum):
    STANDARD_GROUND = "STANDARD_GROUND"
    EXPEDITED = "EXPEDITED"
    NEXT_DAY_AIR = "NEXT_DAY_AIR"
    ECONOMY = "ECONOMY"

class RateCardStatus(str, Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    SUPERSEDED = "SUPERSEDED"

class ShipmentStatus(str, Enum):
    BOOKED = "BOOKED"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"
    EXCEPTION = "EXCEPTION"
    CANCELLED = "CANCELLED"

class LegStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    IN_TRANSIT = "IN_TRANSIT"
    COMPLETED = "COMPLETED"
    DELAYED = "DELAYED"

class WeighedBy(str, Enum):
    SCALE_TERMINAL = "SCALE_TERMINAL"
    WAREHOUSE_RECEIVING = "WAREHOUSE_RECEIVING"
    SHIPPER_DOCK = "SHIPPER_DOCK"

class AccessorialCode(str, Enum):
    LIFTGATE = "LIFTGATE"
    RESIDENTIAL = "RESIDENTIAL"
    INSIDE_PICKUP = "INSIDE_PICKUP"
    HAZMAT = "HAZMAT"
    DETENTION = "DETENTION"
    REDELIVERY = "REDELIVERY"
    STORAGE = "STORAGE"

class InvoiceAuditStatus(str, Enum):
    PENDING = "PENDING"
    AUDITED_CLEAN = "AUDITED_CLEAN"
    DISPUTED = "DISPUTED"
    AUTO_APPROVED = "AUTO_APPROVED"
    RESOLVED = "RESOLVED"

class InvoiceLineType(str, Enum):
    BASE_FREIGHT = "BASE_FREIGHT"
    FUEL_SURCHARGE = "FUEL_SURCHARGE"
    ACCESSORIAL = "ACCESSORIAL"
    DISCOUNT = "DISCOUNT"
    TAX = "TAX"

class LineStatus(str, Enum):
    VALIDATED = "VALIDATED"
    VARIANCE_DETECTED = "VARIANCE_DETECTED"
    DUPLICATE = "DUPLICATE"

class ExceptionCode(str, Enum):
    UNKNOWN_SHIPMENT = "UNKNOWN_SHIPMENT"
    EXPIRED_RATE_CARD = "EXPIRED_RATE_CARD"
    WEIGHT_TIER_MISMATCH = "WEIGHT_TIER_MISMATCH"
    DUPLICATE_SURCHARGE = "DUPLICATE_SURCHARGE"
    DUPLICATE_INVOICE = "DUPLICATE_INVOICE"
    UNAUTHORIZED_ACCESSORIAL = "UNAUTHORIZED_ACCESSORIAL"
    BASE_RATE_OVERCHARGE = "BASE_RATE_OVERCHARGE"
    CREDIT_OVER_EXCEPTION = "CREDIT_OVER_EXCEPTION"

class ExceptionSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class ExceptionStatus(str, Enum):
    DETECTED = "DETECTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED_DISPUTE = "APPROVED_DISPUTE"
    REJECTED_DISPUTE = "REJECTED_DISPUTE"
    RESOLVED = "RESOLVED"

class CreditReconciliationStatus(str, Enum):
    RECONCILED = "RECONCILED"
    OVER_CREDITED = "OVER_CREDITED"
    UNDER_CREDITED = "UNDER_CREDITED"
    DISPUTED = "DISPUTED"

# ==========================================
# Data Classes
# ==========================================

@dataclass
class Carrier:
    carrier_id: str
    name: str
    scac: str
    mode: str
    contact_email: str
    status: str
    created_at: str

@dataclass
class Lane:
    lane_id: str
    origin_city: str
    origin_state: str
    origin_zip: str
    destination_city: str
    destination_state: str
    destination_zip: str
    distance_miles: float
    transit_days: int

@dataclass
class RateCard:
    rate_card_id: str
    carrier_id: str
    lane_id: str
    service_level: str
    min_charge_usd: float
    weight_tier_min_lbs: float
    weight_tier_max_lbs: float
    rate_per_cwt_usd: float
    fuel_surcharge_percent: float
    dim_factor: int
    effective_date: str
    expiration_date: str
    status: str

@dataclass
class Shipment:
    shipment_id: str
    carrier_id: str
    lane_id: str
    service_level: str
    shipment_date: str
    delivery_date: Optional[str]
    pieces_count: int
    pallet_count: int
    declared_value_usd: float
    status: str
    created_at: str

@dataclass
class ShipmentLeg:
    leg_id: str
    shipment_id: str
    leg_sequence: int
    carrier_id: str
    origin_terminal: str
    dest_terminal: str
    departure_time: str
    arrival_time: Optional[str]
    pod_signature: Optional[str]
    status: str

@dataclass
class WeightMeasurement:
    measurement_id: str
    shipment_id: str
    length_in: float
    width_in: float
    height_in: float
    scale_weight_lbs: float
    dim_weight_lbs: float
    billable_weight_lbs: float
    weighed_by: str
    measured_at: str

@dataclass
class Accessorial:
    accessorial_id: str
    shipment_id: str
    service_code: str
    authorized: int  # 1 for True, 0 for False (SQLite friendly)
    contract_rate_usd: float
    performed_at: str
    notes: Optional[str]

@dataclass
class FreightInvoice:
    invoice_id: str
    carrier_id: str
    shipment_id: str
    invoice_date: str
    due_date: str
    total_billed_usd: float
    total_expected_usd: float
    variance_usd: float
    audit_status: str
    created_at: str

@dataclass
class InvoiceLine:
    line_id: str
    invoice_id: str
    line_number: int
    line_type: str
    charge_code: str
    description: str
    billed_rate: float
    billed_quantity: float
    billed_amount_usd: float
    expected_amount_usd: float
    variance_usd: float
    line_status: str

@dataclass
class AuditException:
    exception_id: str
    invoice_id: str
    line_id: Optional[str]
    exception_code: str
    severity: str
    disputed_amount_usd: float
    explanation: str
    status: str
    created_at: str
    resolved_at: Optional[str]

@dataclass
class CreditNote:
    credit_note_id: str
    carrier_id: str
    invoice_id: str
    exception_id: str
    credit_amount_usd: float
    credit_date: str
    reconciliation_status: str
    notes: Optional[str]
    created_at: str


# ==========================================
# SQL DDL Definition
# ==========================================

SQL_DDL = """
-- Freight Audit & Payment Relational Schema
-- Designed for SQLite & ANSI SQL-92 Compliance

CREATE TABLE IF NOT EXISTS carriers (
    carrier_id VARCHAR(32) PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    scac VARCHAR(4) NOT NULL UNIQUE,
    mode VARCHAR(16) NOT NULL,
    contact_email VARCHAR(128) NOT NULL,
    status VARCHAR(16) NOT NULL,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS lanes (
    lane_id VARCHAR(32) PRIMARY KEY,
    origin_city VARCHAR(64) NOT NULL,
    origin_state VARCHAR(2) NOT NULL,
    origin_zip VARCHAR(5) NOT NULL,
    destination_city VARCHAR(64) NOT NULL,
    destination_state VARCHAR(2) NOT NULL,
    destination_zip VARCHAR(5) NOT NULL,
    distance_miles DECIMAL(10,2) NOT NULL,
    transit_days INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS rate_cards (
    rate_card_id VARCHAR(64) PRIMARY KEY,
    carrier_id VARCHAR(32) NOT NULL,
    lane_id VARCHAR(32) NOT NULL,
    service_level VARCHAR(32) NOT NULL,
    min_charge_usd DECIMAL(10,2) NOT NULL,
    weight_tier_min_lbs DECIMAL(10,2) NOT NULL,
    weight_tier_max_lbs DECIMAL(10,2) NOT NULL,
    rate_per_cwt_usd DECIMAL(10,2) NOT NULL,
    fuel_surcharge_percent DECIMAL(5,4) NOT NULL,
    dim_factor INTEGER NOT NULL,
    effective_date DATE NOT NULL,
    expiration_date DATE NOT NULL,
    status VARCHAR(16) NOT NULL,
    FOREIGN KEY (carrier_id) REFERENCES carriers(carrier_id),
    FOREIGN KEY (lane_id) REFERENCES lanes(lane_id)
);

CREATE TABLE IF NOT EXISTS shipments (
    shipment_id VARCHAR(32) PRIMARY KEY,
    carrier_id VARCHAR(32) NOT NULL,
    lane_id VARCHAR(32) NOT NULL,
    service_level VARCHAR(32) NOT NULL,
    shipment_date DATE NOT NULL,
    delivery_date DATE,
    pieces_count INTEGER NOT NULL,
    pallet_count INTEGER NOT NULL,
    declared_value_usd DECIMAL(12,2) NOT NULL,
    status VARCHAR(16) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    FOREIGN KEY (carrier_id) REFERENCES carriers(carrier_id),
    FOREIGN KEY (lane_id) REFERENCES lanes(lane_id)
);

CREATE TABLE IF NOT EXISTS shipment_legs (
    leg_id VARCHAR(48) PRIMARY KEY,
    shipment_id VARCHAR(32) NOT NULL,
    leg_sequence INTEGER NOT NULL,
    carrier_id VARCHAR(32) NOT NULL,
    origin_terminal VARCHAR(64) NOT NULL,
    dest_terminal VARCHAR(64) NOT NULL,
    departure_time TIMESTAMP NOT NULL,
    arrival_time TIMESTAMP,
    pod_signature VARCHAR(64),
    status VARCHAR(16) NOT NULL,
    FOREIGN KEY (shipment_id) REFERENCES shipments(shipment_id),
    FOREIGN KEY (carrier_id) REFERENCES carriers(carrier_id)
);

CREATE TABLE IF NOT EXISTS weight_measurements (
    measurement_id VARCHAR(48) PRIMARY KEY,
    shipment_id VARCHAR(32) NOT NULL,
    length_in DECIMAL(8,2) NOT NULL,
    width_in DECIMAL(8,2) NOT NULL,
    height_in DECIMAL(8,2) NOT NULL,
    scale_weight_lbs DECIMAL(10,2) NOT NULL,
    dim_weight_lbs DECIMAL(10,2) NOT NULL,
    billable_weight_lbs DECIMAL(10,2) NOT NULL,
    weighed_by VARCHAR(32) NOT NULL,
    measured_at TIMESTAMP NOT NULL,
    FOREIGN KEY (shipment_id) REFERENCES shipments(shipment_id)
);

CREATE TABLE IF NOT EXISTS accessorials (
    accessorial_id VARCHAR(32) PRIMARY KEY,
    shipment_id VARCHAR(32) NOT NULL,
    service_code VARCHAR(32) NOT NULL,
    authorized INTEGER NOT NULL DEFAULT 1,
    contract_rate_usd DECIMAL(10,2) NOT NULL,
    performed_at TIMESTAMP NOT NULL,
    notes VARCHAR(255),
    FOREIGN KEY (shipment_id) REFERENCES shipments(shipment_id)
);

CREATE TABLE IF NOT EXISTS freight_invoices (
    invoice_id VARCHAR(32) PRIMARY KEY,
    carrier_id VARCHAR(32) NOT NULL,
    shipment_id VARCHAR(32) NOT NULL,
    invoice_date DATE NOT NULL,
    due_date DATE NOT NULL,
    total_billed_usd DECIMAL(12,2) NOT NULL,
    total_expected_usd DECIMAL(12,2) NOT NULL,
    variance_usd DECIMAL(12,2) NOT NULL,
    audit_status VARCHAR(16) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    FOREIGN KEY (carrier_id) REFERENCES carriers(carrier_id)
    -- Note: Foreign key to shipments is not strictly enforced in DDL 
    -- to accommodate injected negative test cases (UNKNOWN_SHIPMENT)
);

CREATE TABLE IF NOT EXISTS invoice_lines (
    line_id VARCHAR(48) PRIMARY KEY,
    invoice_id VARCHAR(32) NOT NULL,
    line_number INTEGER NOT NULL,
    line_type VARCHAR(32) NOT NULL,
    charge_code VARCHAR(32) NOT NULL,
    description VARCHAR(128) NOT NULL,
    billed_rate DECIMAL(10,2) NOT NULL,
    billed_quantity DECIMAL(10,2) NOT NULL,
    billed_amount_usd DECIMAL(12,2) NOT NULL,
    expected_amount_usd DECIMAL(12,2) NOT NULL,
    variance_usd DECIMAL(12,2) NOT NULL,
    line_status VARCHAR(32) NOT NULL,
    FOREIGN KEY (invoice_id) REFERENCES freight_invoices(invoice_id)
);

CREATE TABLE IF NOT EXISTS audit_exceptions (
    exception_id VARCHAR(32) PRIMARY KEY,
    invoice_id VARCHAR(32) NOT NULL,
    line_id VARCHAR(48),
    exception_code VARCHAR(32) NOT NULL,
    severity VARCHAR(16) NOT NULL,
    disputed_amount_usd DECIMAL(12,2) NOT NULL,
    explanation TEXT NOT NULL,
    status VARCHAR(32) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    resolved_at TIMESTAMP,
    FOREIGN KEY (invoice_id) REFERENCES freight_invoices(invoice_id),
    FOREIGN KEY (line_id) REFERENCES invoice_lines(line_id)
);

CREATE TABLE IF NOT EXISTS credit_notes (
    credit_note_id VARCHAR(32) PRIMARY KEY,
    carrier_id VARCHAR(32) NOT NULL,
    invoice_id VARCHAR(32) NOT NULL,
    exception_id VARCHAR(32) NOT NULL,
    credit_amount_usd DECIMAL(12,2) NOT NULL,
    credit_date DATE NOT NULL,
    reconciliation_status VARCHAR(32) NOT NULL,
    notes VARCHAR(255),
    created_at TIMESTAMP NOT NULL,
    FOREIGN KEY (carrier_id) REFERENCES carriers(carrier_id),
    FOREIGN KEY (invoice_id) REFERENCES freight_invoices(invoice_id),
    FOREIGN KEY (exception_id) REFERENCES audit_exceptions(exception_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_rate_lookup ON rate_cards(carrier_id, lane_id, service_level, status);
CREATE INDEX IF NOT EXISTS idx_shipments_carrier ON shipments(carrier_id);
CREATE INDEX IF NOT EXISTS idx_shipments_date ON shipments(shipment_date);
CREATE INDEX IF NOT EXISTS idx_invoices_shipment ON freight_invoices(shipment_id);
CREATE INDEX IF NOT EXISTS idx_invoices_carrier ON freight_invoices(carrier_id);
CREATE INDEX IF NOT EXISTS idx_lines_invoice ON invoice_lines(invoice_id);
CREATE INDEX IF NOT EXISTS idx_exceptions_invoice ON audit_exceptions(invoice_id);
"""

