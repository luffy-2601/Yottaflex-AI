"""
Deterministic Synthetic Data Generator for Freight Invoice Audit.
Generates all 11 entities with relational integrity, realistic freight distributions,
and labeled edge cases according to challenge specification.
"""
import csv
import json
import random
import sqlite3
import datetime
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import (
    DEFAULT_SEED,
    SCALE_CONFIGS,
    DATA_DIR,
    DIM_FACTORS,
    WEIGHT_TIERS,
    ACCESSORIAL_RATES,
    ID_CARRIER_FMT,
    ID_LANE_FMT,
    ID_RATE_CARD_FMT,
    ID_SHIPMENT_FMT,
    ID_LEG_FMT,
    ID_WEIGHT_FMT,
    ID_ACCESSORIAL_FMT,
    ID_INVOICE_FMT,
    ID_INVOICE_LINE_FMT,
    ID_EXCEPTION_FMT,
    ID_CREDIT_NOTE_FMT,
)
from src.schema import (
    Carrier, Lane, RateCard, Shipment, ShipmentLeg,
    WeightMeasurement, Accessorial, FreightInvoice, InvoiceLine,
    AuditException, CreditNote, SQL_DDL,
    CarrierMode, CarrierStatus, ServiceLevel, RateCardStatus,
    ShipmentStatus, LegStatus, WeighedBy, AccessorialCode,
    InvoiceAuditStatus, InvoiceLineType, LineStatus,
    ExceptionCode, ExceptionSeverity, ExceptionStatus,
    CreditReconciliationStatus
)

# Reference data pools
US_CITIES = [
    ("Chicago", "IL", "60601"),
    ("Atlanta", "GA", "30301"),
    ("Dallas", "TX", "75201"),
    ("Los Angeles", "CA", "90001"),
    ("Newark", "NJ", "07101"),
    ("Memphis", "TN", "38101"),
    ("Columbus", "OH", "43201"),
    ("Indianapolis", "IN", "46201"),
    ("Kansas City", "MO", "64101"),
    ("Harrisburg", "PA", "17101"),
    ("Ontario", "CA", "91761"),
    ("Phoenix", "AZ", "85001"),
    ("Denver", "CO", "80201"),
    ("Seattle", "WA", "98101"),
    ("Charlotte", "NC", "28201"),
]

CARRIER_PREFIXES = [
    "Apex", "BlueLine", "Cardinal", "DirectFreight", "Eagle", "Frontier",
    "GlobalLink", "Horizon", "Interstate", "JetStream", "Keystone", "Logix",
    "Midwest", "National", "Omega", "Pacific", "Quality", "Rapid", "Summit",
    "TransContinental", "United", "Vanguard", "WestCoast", "Xpress", "Zenith"
]

class FreightDataGenerator:
    def __init__(self, seed: int = DEFAULT_SEED, scale: str = "starter"):
        self.seed = seed
        self.rng = random.Random(seed)
        self.scale = scale
        self.config = SCALE_CONFIGS.get(scale, SCALE_CONFIGS["starter"])
        
        # Entity collections
        self.carriers: List[Carrier] = []
        self.lanes: List[Lane] = []
        self.rate_cards: List[RateCard] = []
        self.shipments: List[Shipment] = []
        self.shipment_legs: List[ShipmentLeg] = []
        self.weight_measurements: List[WeightMeasurement] = []
        self.accessorials: List[Accessorial] = []
        self.freight_invoices: List[FreightInvoice] = []
        self.invoice_lines: List[InvoiceLine] = []
        self.audit_exceptions: List[AuditException] = []
        self.credit_notes: List[CreditNote] = []
        
        # Ground truth tracking (isolated from input features)
        self.ground_truth: List[Dict[str, Any]] = []
        
        # Lookups for relational fast access
        self.rate_card_lookup: Dict[Tuple[str, str, str], List[RateCard]] = {}
        self.carrier_lanes: Dict[str, List[Lane]] = {}

    def generate_all(self):
        """Execute full generation sequence: master data -> transactions -> events -> invoices -> edge cases."""
        self.generate_carriers()
        self.generate_lanes()
        self.generate_rate_cards()
        self.generate_shipments()
        self.generate_invoices()
        return self

    def generate_carriers(self):
        """Step 2: Generate Master Carriers."""
        num = self.config["num_carriers"]
        modes = [CarrierMode.LTL.value, CarrierMode.FTL.value, CarrierMode.PARCEL.value]
        
        for i in range(1, num + 1):
            carrier_id = ID_CARRIER_FMT.format(i)
            prefix = CARRIER_PREFIXES[(i - 1) % len(CARRIER_PREFIXES)]
            suffix = f"Logistics {((i - 1) // len(CARRIER_PREFIXES)) + 1}" if i > len(CARRIER_PREFIXES) else "Logistics"
            name = f"{prefix} {suffix}"
            scac = f"{prefix[:3].upper()}{chr(65 + ((i - 1) % 26))}"
            mode = modes[(i - 1) % len(modes)]
            email = f"billing@{prefix.lower()}-logistics.com"
            status = CarrierStatus.ACTIVE.value if i % 20 != 0 else CarrierStatus.SUSPENDED.value
            created_at = "2025-10-01T00:00:00Z"
            
            self.carriers.append(Carrier(
                carrier_id=carrier_id,
                name=name,
                scac=scac,
                mode=mode,
                contact_email=email,
                status=status,
                created_at=created_at
            ))

    def generate_lanes(self):
        """Step 2: Generate Master Lanes."""
        num = self.config["num_lanes"]
        lane_idx = 1
        
        for i, origin in enumerate(US_CITIES):
            for j, dest in enumerate(US_CITIES):
                if i != j:
                    lane_id = ID_LANE_FMT.format(lane_idx)
                    # Pseudo realistic distance based on index delta
                    distance = round(abs(i - j) * 165.5 + 240.0, 2)
                    transit_days = max(1, int(distance / 450.0) + 1)
                    
                    self.lanes.append(Lane(
                        lane_id=lane_id,
                        origin_city=origin[0],
                        origin_state=origin[1],
                        origin_zip=origin[2],
                        destination_city=dest[0],
                        destination_state=dest[1],
                        destination_zip=dest[2],
                        distance_miles=distance,
                        transit_days=transit_days
                    ))
                    lane_idx += 1
                    if lane_idx > num:
                        return

    def generate_rate_cards(self):
        """Step 2: Generate Rate Cards with Weight Tiers & Contract Terms."""
        rate_card_counter = 1
        services = [ServiceLevel.STANDARD_GROUND.value, ServiceLevel.EXPEDITED.value]
        
        for c_idx, carrier in enumerate(self.carriers):
            if carrier.status != CarrierStatus.ACTIVE.value:
                continue
                
            carrier_rc_idx = 1
            # Assign a regional network of lanes per carrier (e.g. 25 lanes with rotation)
            num_lanes_per_carrier = min(len(self.lanes), 25)
            start_offset = (c_idx * 5) % max(1, len(self.lanes) - num_lanes_per_carrier + 1)
            assigned_lanes = self.lanes[start_offset : start_offset + num_lanes_per_carrier]
            if len(assigned_lanes) < num_lanes_per_carrier:
                assigned_lanes = self.lanes[:num_lanes_per_carrier]
            self.carrier_lanes[carrier.carrier_id] = assigned_lanes
            
            for lane in assigned_lanes:
                for service in services:
                    dim_factor = 139
                    fuel_pct = round(0.18 + (self.rng.random() * 0.08), 4) # 18% to 26%
                    min_charge = round(65.00 + (lane.distance_miles * 0.04), 2)
                    
                    # Generate rate card for each weight tier
                    for tier_idx, (min_lbs, max_lbs) in enumerate(WEIGHT_TIERS):
                        rc_id = f"RATE-{carrier.carrier_id}-2026-{carrier_rc_idx:04d}"
                        carrier_rc_idx += 1
                        rate_card_counter += 1
                        
                        # Economies of scale: higher weight tier = lower cwt rate
                        base_cwt = max(8.50, round((80.00 / (tier_idx + 1.2)) + (lane.distance_miles * 0.015), 2))
                        if service == ServiceLevel.EXPEDITED.value:
                            base_cwt = round(base_cwt * 1.45, 2)
                            min_charge_val = round(min_charge * 1.35, 2)
                        else:
                            min_charge_val = min_charge
                            
                        # Standard active validity
                        eff_date = "2026-01-01"
                        exp_date = "2026-12-31"
                        status = RateCardStatus.ACTIVE.value
                        
                        rc = RateCard(
                            rate_card_id=rc_id,
                            carrier_id=carrier.carrier_id,
                            lane_id=lane.lane_id,
                            service_level=service,
                            min_charge_usd=min_charge_val,
                            weight_tier_min_lbs=min_lbs,
                            weight_tier_max_lbs=max_lbs,
                            rate_per_cwt_usd=base_cwt,
                            fuel_surcharge_percent=fuel_pct,
                            dim_factor=dim_factor,
                            effective_date=eff_date,
                            expiration_date=exp_date,
                            status=status
                        )
                        self.rate_cards.append(rc)
                        
                        key = (carrier.carrier_id, lane.lane_id, service)
                        if key not in self.rate_card_lookup:
                            self.rate_card_lookup[key] = []
                        self.rate_card_lookup[key].append(rc)

    def generate_shipments(self):
        """Step 2 & 4: Generate Shipments, Legs, WeightMeasurements, and Accessorials."""
        num = self.config["num_shipments"]
        active_carriers = [c for c in self.carriers if c.status == CarrierStatus.ACTIVE.value]
        
        base_date = datetime.date(2026, 5, 1)
        
        for i in range(1, num + 1):
            shipment_id = ID_SHIPMENT_FMT.format(i)
            carrier = active_carriers[(i - 1) % len(active_carriers)]
            c_lanes = self.carrier_lanes.get(carrier.carrier_id, self.lanes)
            lane = c_lanes[(i - 1) % len(c_lanes)]
            service = ServiceLevel.STANDARD_GROUND.value if i % 3 != 0 else ServiceLevel.EXPEDITED.value
            
            # Stagger shipment dates across 180 days in 2026
            day_offset = (i * 7) % 180
            ship_date = base_date + datetime.timedelta(days=day_offset)
            delivery_date = ship_date + datetime.timedelta(days=lane.transit_days)
            
            pieces = max(1, (i % 25) + 1)
            pallets = max(1, (pieces // 5) + 1)
            declared_val = round(float(pallets * 1250.00 + (pieces * 85.0)), 2)
            
            shipment = Shipment(
                shipment_id=shipment_id,
                carrier_id=carrier.carrier_id,
                lane_id=lane.lane_id,
                service_level=service,
                shipment_date=ship_date.isoformat(),
                delivery_date=delivery_date.isoformat(),
                pieces_count=pieces,
                pallet_count=pallets,
                declared_value_usd=declared_val,
                status=ShipmentStatus.DELIVERED.value,
                created_at=f"{ship_date.isoformat()}T08:00:00Z"
            )
            self.shipments.append(shipment)
            
            # Generate ShipmentLeg
            leg_id = ID_LEG_FMT.format(shipment_id, 1)
            self.shipment_legs.append(ShipmentLeg(
                leg_id=leg_id,
                shipment_id=shipment_id,
                leg_sequence=1,
                carrier_id=carrier.carrier_id,
                origin_terminal=f"{lane.origin_city} Hub",
                dest_terminal=f"{lane.destination_city} Terminal",
                departure_time=f"{ship_date.isoformat()}T10:00:00Z",
                arrival_time=f"{delivery_date.isoformat()}T16:00:00Z",
                pod_signature=f"POD-SIG-{shipment_id[-6:]}",
                status=LegStatus.COMPLETED.value
            ))
            
            # Generate WeightMeasurement (Dimensional vs Scale Weight)
            # Vary package characteristics: some dense, some bulky (dim weight > scale weight)
            is_bulky = (i % 4 == 0)
            if is_bulky:
                length, width, height = 48.0, 48.0, 60.0
                scale_wt = round(350.0 + (i % 200), 2)
            else:
                length, width, height = 40.0, 40.0, 40.0
                scale_wt = round(650.0 + (i % 1200), 2)
                
            dim_wt = round((length * width * height) / 139.0, 2)
            billable_wt = round(max(scale_wt, dim_wt), 2)
            
            wm_id = ID_WEIGHT_FMT.format(shipment_id, 1)
            self.weight_measurements.append(WeightMeasurement(
                measurement_id=wm_id,
                shipment_id=shipment_id,
                length_in=length,
                width_in=width,
                height_in=height,
                scale_weight_lbs=scale_wt,
                dim_weight_lbs=dim_wt,
                billable_weight_lbs=billable_wt,
                weighed_by=WeighedBy.SCALE_TERMINAL.value,
                measured_at=f"{ship_date.isoformat()}T10:30:00Z"
            ))
            
            # Generate Accessorials (e.g. 20% of shipments have liftgate, 10% residential)
            if i % 5 == 0:
                acc_code = AccessorialCode.LIFTGATE.value
                rate = ACCESSORIAL_RATES["LIFTGATE"]
                self.accessorials.append(Accessorial(
                    accessorial_id=ID_ACCESSORIAL_FMT.format(len(self.accessorials) + 1),
                    shipment_id=shipment_id,
                    service_code=acc_code,
                    authorized=1,
                    contract_rate_usd=rate,
                    performed_at=f"{delivery_date.isoformat()}T15:30:00Z",
                    notes="Authorized liftgate delivery required at destination"
                ))
            elif i % 7 == 0:
                acc_code = AccessorialCode.RESIDENTIAL.value
                rate = ACCESSORIAL_RATES["RESIDENTIAL"]
                self.accessorials.append(Accessorial(
                    accessorial_id=ID_ACCESSORIAL_FMT.format(len(self.accessorials) + 1),
                    shipment_id=shipment_id,
                    service_code=acc_code,
                    authorized=1,
                    contract_rate_usd=rate,
                    performed_at=f"{delivery_date.isoformat()}T15:45:00Z",
                    notes="Residential destination delivery verified"
                ))

    def _find_matching_rate_card(self, carrier_id: str, lane_id: str, service: str, weight: float, ship_date_str: str) -> Tuple[RateCard, str]:
        """Find matching rate card by lane, service level, weight tier, and date validity."""
        key = (carrier_id, lane_id, service)
        candidates = self.rate_card_lookup.get(key, [])
        if not candidates:
            # Fallback to any active card for carrier
            for c in self.rate_cards:
                if c.carrier_id == carrier_id and c.status == RateCardStatus.ACTIVE.value:
                    return c, "FALLBACK"
            return self.rate_cards[0], "GENERIC_FALLBACK"
            
        ship_date = datetime.date.fromisoformat(ship_date_str)
        
        # Check matching weight tier
        for rc in candidates:
            eff = datetime.date.fromisoformat(rc.effective_date)
            exp = datetime.date.fromisoformat(rc.expiration_date)
            if rc.weight_tier_min_lbs <= weight < rc.weight_tier_max_lbs:
                if eff <= ship_date <= exp:
                    return rc, "MATCH"
                else:
                    return rc, "EXPIRED_CARD"
                    
        # Return first candidate tier if outside boundary
        return candidates[0], "TIER_MISMATCH"

    def generate_invoices(self):
        """
        Step 3, 4, 5, 6, 7:
        Generate Freight Invoices, Lines, Injected Edge Cases, Derived Balances, and Ground Truth.
        """
        num_invoices = self.config["num_invoices"]
        exception_counter = 1
        credit_counter = 1
        
        # We index shipments and measurements for quick access
        shipments_by_id = {s.shipment_id: s for s in self.shipments}
        wm_by_shipment = {wm.shipment_id: wm for wm in self.weight_measurements}
        acc_by_shipment: Dict[str, List[Accessorial]] = {}
        for a in self.accessorials:
            if a.shipment_id not in acc_by_shipment:
                acc_by_shipment[a.shipment_id] = []
            acc_by_shipment[a.shipment_id].append(a)
            
        for inv_idx in range(1, num_invoices + 1):
            invoice_id = ID_INVOICE_FMT.format(inv_idx)
            
            # Assign shipment
            target_shp_idx = (inv_idx - 1) % len(self.shipments)
            shipment = self.shipments[target_shp_idx]
            wm = wm_by_shipment[shipment.shipment_id]
            ship_accessorials = acc_by_shipment.get(shipment.shipment_id, [])
            
            deliv_date = datetime.date.fromisoformat(shipment.delivery_date)
            inv_date = deliv_date + datetime.timedelta(days=3)
            due_date = inv_date + datetime.timedelta(days=30)
            
            # Determine expected contracted freight calculation
            matched_rc, match_status = self._find_matching_rate_card(
                shipment.carrier_id, shipment.lane_id, shipment.service_level,
                wm.billable_weight_lbs, shipment.shipment_date
            )
            
            # Expected calculations
            cwt_units = round(wm.billable_weight_lbs / 100.0, 2)
            calculated_base = round(cwt_units * matched_rc.rate_per_cwt_usd, 2)
            expected_base = max(matched_rc.min_charge_usd, calculated_base)
            expected_fuel = round(expected_base * matched_rc.fuel_surcharge_percent, 2)
            expected_acc_total = sum(a.contract_rate_usd for a in ship_accessorials if a.authorized)
            total_expected = round(expected_base + expected_fuel + expected_acc_total, 2)
            
            # Determine if this invoice should be an injected edge case (Step 5)
            # Cycle through edge cases systematically
            is_anomaly = False
            anomaly_type = None
            anomaly_explanation = None
            
            # Injection frequencies
            if inv_idx % 23 == 0:
                is_anomaly = True
                anomaly_type = ExceptionCode.UNKNOWN_SHIPMENT.value
            elif inv_idx % 31 == 0:
                is_anomaly = True
                anomaly_type = ExceptionCode.EXPIRED_RATE_CARD.value
            elif inv_idx % 19 == 0:
                is_anomaly = True
                anomaly_type = ExceptionCode.WEIGHT_TIER_MISMATCH.value
            elif inv_idx % 29 == 0:
                is_anomaly = True
                anomaly_type = ExceptionCode.DUPLICATE_SURCHARGE.value
            elif inv_idx % 37 == 0:
                is_anomaly = True
                anomaly_type = ExceptionCode.CREDIT_OVER_EXCEPTION.value
            elif inv_idx % 47 == 0:
                is_anomaly = True
                anomaly_type = ExceptionCode.UNAUTHORIZED_ACCESSORIAL.value
            elif inv_idx % 53 == 0:
                is_anomaly = True
                anomaly_type = ExceptionCode.DUPLICATE_INVOICE.value
                
            lines: List[InvoiceLine] = []
            line_num = 1
            
            # Generate lines based on anomaly injection or clean rating
            if not is_anomaly:
                # ----------------- CLEAN INVOICE -----------------
                # Base Freight line
                base_line_id = ID_INVOICE_LINE_FMT.format(invoice_id, line_num)
                lines.append(InvoiceLine(
                    line_id=base_line_id,
                    invoice_id=invoice_id,
                    line_number=line_num,
                    line_type=InvoiceLineType.BASE_FREIGHT.value,
                    charge_code="BASE",
                    description=f"Base Freight {cwt_units} cwt @ ${matched_rc.rate_per_cwt_usd:.2f}/cwt",
                    billed_rate=matched_rc.rate_per_cwt_usd,
                    billed_quantity=cwt_units,
                    billed_amount_usd=expected_base,
                    expected_amount_usd=expected_base,
                    variance_usd=0.00,
                    line_status=LineStatus.VALIDATED.value
                ))
                line_num += 1
                
                # Fuel Surcharge line
                fuel_line_id = ID_INVOICE_LINE_FMT.format(invoice_id, line_num)
                lines.append(InvoiceLine(
                    line_id=fuel_line_id,
                    invoice_id=invoice_id,
                    line_number=line_num,
                    line_type=InvoiceLineType.FUEL_SURCHARGE.value,
                    charge_code="FSC",
                    description=f"Fuel Surcharge ({matched_rc.fuel_surcharge_percent * 100:.2f}%)",
                    billed_rate=matched_rc.fuel_surcharge_percent,
                    billed_quantity=1.0,
                    billed_amount_usd=expected_fuel,
                    expected_amount_usd=expected_fuel,
                    variance_usd=0.00,
                    line_status=LineStatus.VALIDATED.value
                ))
                line_num += 1
                
                # Accessorial lines
                for acc in ship_accessorials:
                    if acc.authorized:
                        acc_line_id = ID_INVOICE_LINE_FMT.format(invoice_id, line_num)
                        lines.append(InvoiceLine(
                            line_id=acc_line_id,
                            invoice_id=invoice_id,
                            line_number=line_num,
                            line_type=InvoiceLineType.ACCESSORIAL.value,
                            charge_code=acc.service_code,
                            description=f"Accessorial Service: {acc.service_code}",
                            billed_rate=acc.contract_rate_usd,
                            billed_quantity=1.0,
                            billed_amount_usd=acc.contract_rate_usd,
                            expected_amount_usd=acc.contract_rate_usd,
                            variance_usd=0.00,
                            line_status=LineStatus.VALIDATED.value
                        ))
                        line_num += 1
                
                total_billed = sum(l.billed_amount_usd for l in lines)
                total_variance = 0.00
                audit_status = InvoiceAuditStatus.AUDITED_CLEAN.value
                inv_shipment_id = shipment.shipment_id
                
                # Ground truth clean label
                self.ground_truth.append({
                    "invoice_id": invoice_id,
                    "shipment_id": inv_shipment_id,
                    "carrier_id": shipment.carrier_id,
                    "is_anomaly": False,
                    "anomaly_type": "NONE",
                    "expected_decision": "CLEAN",
                    "expected_total_billed": total_billed,
                    "expected_total_approved": total_expected,
                    "expected_disputed_amount": 0.00,
                    "reason": "Matches contracted rates, billable weight, and verified accessorials."
                })
                
            else:
                # ----------------- INJECTED EDGE CASES (Step 5) -----------------
                inv_shipment_id = shipment.shipment_id
                disputed_amt = 0.00
                
                if anomaly_type == ExceptionCode.UNKNOWN_SHIPMENT.value:
                    # Edge Case 1: Invoice references unknown shipment
                    inv_shipment_id = f"SHP-2026-9{inv_idx:05d}"  # Non-existent ID
                    billed_base = expected_base
                    disputed_amt = round(expected_base + expected_fuel, 2)
                    anomaly_explanation = f"Referenced shipment {inv_shipment_id} does not exist in TMS/WMS shipment registry."
                    
                    lines.append(InvoiceLine(
                        line_id=ID_INVOICE_LINE_FMT.format(invoice_id, 1),
                        invoice_id=invoice_id,
                        line_number=1,
                        line_type=InvoiceLineType.BASE_FREIGHT.value,
                        charge_code="BASE",
                        description=f"Base Freight on Unregistered Shipment {inv_shipment_id}",
                        billed_rate=matched_rc.rate_per_cwt_usd,
                        billed_quantity=cwt_units,
                        billed_amount_usd=billed_base,
                        expected_amount_usd=0.00,
                        variance_usd=billed_base,
                        line_status=LineStatus.VARIANCE_DETECTED.value
                    ))
                    lines.append(InvoiceLine(
                        line_id=ID_INVOICE_LINE_FMT.format(invoice_id, 2),
                        invoice_id=invoice_id,
                        line_number=2,
                        line_type=InvoiceLineType.FUEL_SURCHARGE.value,
                        charge_code="FSC",
                        description="Fuel Surcharge on Unregistered Shipment",
                        billed_rate=matched_rc.fuel_surcharge_percent,
                        billed_quantity=1.0,
                        billed_amount_usd=expected_fuel,
                        expected_amount_usd=0.00,
                        variance_usd=expected_fuel,
                        line_status=LineStatus.VARIANCE_DETECTED.value
                    ))
                    
                elif anomaly_type == ExceptionCode.EXPIRED_RATE_CARD.value:
                    # Edge Case 2: Rate card expired
                    expired_cwt = round(matched_rc.rate_per_cwt_usd * 1.35, 2)
                    billed_base = round(cwt_units * expired_cwt, 2)
                    disputed_amt = round(billed_base - expected_base, 2)
                    anomaly_explanation = f"Carrier billed under expired rate schedule. Billed ${billed_base:.2f} vs contracted ${expected_base:.2f}."
                    
                    lines.append(InvoiceLine(
                        line_id=ID_INVOICE_LINE_FMT.format(invoice_id, 1),
                        invoice_id=invoice_id,
                        line_number=1,
                        line_type=InvoiceLineType.BASE_FREIGHT.value,
                        charge_code="BASE",
                        description=f"Base Freight under Expired Schedule (Rate ${expired_cwt:.2f}/cwt)",
                        billed_rate=expired_cwt,
                        billed_quantity=cwt_units,
                        billed_amount_usd=billed_base,
                        expected_amount_usd=expected_base,
                        variance_usd=disputed_amt,
                        line_status=LineStatus.VARIANCE_DETECTED.value
                    ))
                    lines.append(InvoiceLine(
                        line_id=ID_INVOICE_LINE_FMT.format(invoice_id, 2),
                        invoice_id=invoice_id,
                        line_number=2,
                        line_type=InvoiceLineType.FUEL_SURCHARGE.value,
                        charge_code="FSC",
                        description=f"Fuel Surcharge",
                        billed_rate=matched_rc.fuel_surcharge_percent,
                        billed_quantity=1.0,
                        billed_amount_usd=expected_fuel,
                        expected_amount_usd=expected_fuel,
                        variance_usd=0.00,
                        line_status=LineStatus.VALIDATED.value
                    ))
                    
                elif anomaly_type == ExceptionCode.WEIGHT_TIER_MISMATCH.value:
                    # Edge Case 3: Weight tier misapplied
                    # Carrier billed lower tier (higher rate/cwt) or ignored dim weight
                    wrong_tier_cwt = round(matched_rc.rate_per_cwt_usd * 1.50, 2)
                    billed_base = round(cwt_units * wrong_tier_cwt, 2)
                    disputed_amt = round(billed_base - expected_base, 2)
                    anomaly_explanation = f"Weight tier misapplied. Billable weight {wm.billable_weight_lbs} lbs qualifies for tier rate ${matched_rc.rate_per_cwt_usd:.2f}, carrier billed ${wrong_tier_cwt:.2f}."
                    
                    lines.append(InvoiceLine(
                        line_id=ID_INVOICE_LINE_FMT.format(invoice_id, 1),
                        invoice_id=invoice_id,
                        line_number=1,
                        line_type=InvoiceLineType.BASE_FREIGHT.value,
                        charge_code="BASE",
                        description=f"Base Freight - Incorrect Weight Bracket Applied",
                        billed_rate=wrong_tier_cwt,
                        billed_quantity=cwt_units,
                        billed_amount_usd=billed_base,
                        expected_amount_usd=expected_base,
                        variance_usd=disputed_amt,
                        line_status=LineStatus.VARIANCE_DETECTED.value
                    ))
                    lines.append(InvoiceLine(
                        line_id=ID_INVOICE_LINE_FMT.format(invoice_id, 2),
                        invoice_id=invoice_id,
                        line_number=2,
                        line_type=InvoiceLineType.FUEL_SURCHARGE.value,
                        charge_code="FSC",
                        description=f"Fuel Surcharge",
                        billed_rate=matched_rc.fuel_surcharge_percent,
                        billed_quantity=1.0,
                        billed_amount_usd=expected_fuel,
                        expected_amount_usd=expected_fuel,
                        variance_usd=0.00,
                        line_status=LineStatus.VALIDATED.value
                    ))
                    
                elif anomaly_type == ExceptionCode.DUPLICATE_SURCHARGE.value:
                    # Edge Case 4: Surcharge duplicated
                    disputed_amt = expected_fuel
                    anomaly_explanation = f"Duplicate fuel surcharge line detected on single invoice. Extra line amount: ${expected_fuel:.2f}."
                    
                    lines.append(InvoiceLine(
                        line_id=ID_INVOICE_LINE_FMT.format(invoice_id, 1),
                        invoice_id=invoice_id,
                        line_number=1,
                        line_type=InvoiceLineType.BASE_FREIGHT.value,
                        charge_code="BASE",
                        description="Base Freight",
                        billed_rate=matched_rc.rate_per_cwt_usd,
                        billed_quantity=cwt_units,
                        billed_amount_usd=expected_base,
                        expected_amount_usd=expected_base,
                        variance_usd=0.00,
                        line_status=LineStatus.VALIDATED.value
                    ))
                    lines.append(InvoiceLine(
                        line_id=ID_INVOICE_LINE_FMT.format(invoice_id, 2),
                        invoice_id=invoice_id,
                        line_number=2,
                        line_type=InvoiceLineType.FUEL_SURCHARGE.value,
                        charge_code="FSC",
                        description="Fuel Surcharge - Primary",
                        billed_rate=matched_rc.fuel_surcharge_percent,
                        billed_quantity=1.0,
                        billed_amount_usd=expected_fuel,
                        expected_amount_usd=expected_fuel,
                        variance_usd=0.00,
                        line_status=LineStatus.VALIDATED.value
                    ))
                    # Duplicate surcharge line
                    lines.append(InvoiceLine(
                        line_id=ID_INVOICE_LINE_FMT.format(invoice_id, 3),
                        invoice_id=invoice_id,
                        line_number=3,
                        line_type=InvoiceLineType.FUEL_SURCHARGE.value,
                        charge_code="FSC_DUP",
                        description="Fuel Surcharge - Secondary (Duplicate)",
                        billed_rate=matched_rc.fuel_surcharge_percent,
                        billed_quantity=1.0,
                        billed_amount_usd=expected_fuel,
                        expected_amount_usd=0.00,
                        variance_usd=expected_fuel,
                        line_status=LineStatus.DUPLICATE.value
                    ))
                    
                elif anomaly_type == ExceptionCode.CREDIT_OVER_EXCEPTION.value:
                    # Edge Case 5: Credit note exceeds exception amount
                    # We create an invoice with a small variance, and later issue an over-credit note
                    base_overcharge = 60.00
                    billed_base = round(expected_base + base_overcharge, 2)
                    disputed_amt = base_overcharge
                    anomaly_explanation = f"Carrier billed base overcharge of ${base_overcharge:.2f}, but issued credit note in excess of disputed amount."
                    
                    lines.append(InvoiceLine(
                        line_id=ID_INVOICE_LINE_FMT.format(invoice_id, 1),
                        invoice_id=invoice_id,
                        line_number=1,
                        line_type=InvoiceLineType.BASE_FREIGHT.value,
                        charge_code="BASE",
                        description="Base Freight with tariff variance",
                        billed_rate=matched_rc.rate_per_cwt_usd,
                        billed_quantity=cwt_units,
                        billed_amount_usd=billed_base,
                        expected_amount_usd=expected_base,
                        variance_usd=base_overcharge,
                        line_status=LineStatus.VARIANCE_DETECTED.value
                    ))
                    lines.append(InvoiceLine(
                        line_id=ID_INVOICE_LINE_FMT.format(invoice_id, 2),
                        invoice_id=invoice_id,
                        line_number=2,
                        line_type=InvoiceLineType.FUEL_SURCHARGE.value,
                        charge_code="FSC",
                        description="Fuel Surcharge",
                        billed_rate=matched_rc.fuel_surcharge_percent,
                        billed_quantity=1.0,
                        billed_amount_usd=expected_fuel,
                        expected_amount_usd=expected_fuel,
                        variance_usd=0.00,
                        line_status=LineStatus.VALIDATED.value
                    ))
                    
                elif anomaly_type == ExceptionCode.UNAUTHORIZED_ACCESSORIAL.value:
                    # Extra edge case: unauthorized accessorial
                    unauth_fee = 95.00
                    disputed_amt = unauth_fee
                    anomaly_explanation = "Accessorial charge for INSIDE_PICKUP not authorized or recorded in delivery receipt."
                    
                    lines.append(InvoiceLine(
                        line_id=ID_INVOICE_LINE_FMT.format(invoice_id, 1),
                        invoice_id=invoice_id,
                        line_number=1,
                        line_type=InvoiceLineType.BASE_FREIGHT.value,
                        charge_code="BASE",
                        description="Base Freight",
                        billed_rate=matched_rc.rate_per_cwt_usd,
                        billed_quantity=cwt_units,
                        billed_amount_usd=expected_base,
                        expected_amount_usd=expected_base,
                        variance_usd=0.00,
                        line_status=LineStatus.VALIDATED.value
                    ))
                    lines.append(InvoiceLine(
                        line_id=ID_INVOICE_LINE_FMT.format(invoice_id, 2),
                        invoice_id=invoice_id,
                        line_number=2,
                        line_type=InvoiceLineType.ACCESSORIAL.value,
                        charge_code="INSIDE_PICKUP",
                        description="Unauthorized Inside Pickup Fee",
                        billed_rate=unauth_fee,
                        billed_quantity=1.0,
                        billed_amount_usd=unauth_fee,
                        expected_amount_usd=0.00,
                        variance_usd=unauth_fee,
                        line_status=LineStatus.VARIANCE_DETECTED.value
                    ))
                    
                elif anomaly_type == ExceptionCode.DUPLICATE_INVOICE.value:
                    # Duplicate invoice: duplicate an invoice for an earlier shipment that was already invoiced!
                    prior_shp_idx = max(0, target_shp_idx - 4)
                    shipment = self.shipments[prior_shp_idx]
                    inv_shipment_id = shipment.shipment_id
                    wm = wm_by_shipment[inv_shipment_id]
                    cwt_units = round(wm.billable_weight_lbs / 100.0, 2)
                    disputed_amt = round(expected_base + expected_fuel, 2)
                    anomaly_explanation = f"Duplicate invoice submitted for shipment {shipment.shipment_id}."
                    
                    lines.append(InvoiceLine(
                        line_id=ID_INVOICE_LINE_FMT.format(invoice_id, 1),
                        invoice_id=invoice_id,
                        line_number=1,
                        line_type=InvoiceLineType.BASE_FREIGHT.value,
                        charge_code="BASE",
                        description="Duplicate Base Freight Billing",
                        billed_rate=matched_rc.rate_per_cwt_usd,
                        billed_quantity=cwt_units,
                        billed_amount_usd=expected_base,
                        expected_amount_usd=0.00,
                        variance_usd=expected_base,
                        line_status=LineStatus.DUPLICATE.value
                    ))
                    lines.append(InvoiceLine(
                        line_id=ID_INVOICE_LINE_FMT.format(invoice_id, 2),
                        invoice_id=invoice_id,
                        line_number=2,
                        line_type=InvoiceLineType.FUEL_SURCHARGE.value,
                        charge_code="FSC",
                        description="Duplicate Fuel Surcharge Billing",
                        billed_rate=matched_rc.fuel_surcharge_percent,
                        billed_quantity=1.0,
                        billed_amount_usd=expected_fuel,
                        expected_amount_usd=0.00,
                        variance_usd=expected_fuel,
                        line_status=LineStatus.DUPLICATE.value
                    ))
                    
                total_billed = round(sum(l.billed_amount_usd for l in lines), 2)
                total_variance = round(total_billed - total_expected, 2)
                audit_status = InvoiceAuditStatus.DISPUTED.value
                
                # Create AuditException record for the injected anomaly
                ex_id = ID_EXCEPTION_FMT.format(exception_counter)
                exception_counter += 1
                
                ex_severity = ExceptionSeverity.HIGH.value if disputed_amt > 100.0 else ExceptionSeverity.MEDIUM.value
                if anomaly_type == ExceptionCode.UNKNOWN_SHIPMENT.value:
                    ex_severity = ExceptionSeverity.CRITICAL.value
                    
                audit_ex = AuditException(
                    exception_id=ex_id,
                    invoice_id=invoice_id,
                    line_id=lines[0].line_id,
                    exception_code=anomaly_type,
                    severity=ex_severity,
                    disputed_amount_usd=disputed_amt,
                    explanation=anomaly_explanation,
                    status=ExceptionStatus.APPROVED_DISPUTE.value,
                    created_at=f"{inv_date.isoformat()}T12:00:00Z",
                    resolved_at=None
                )
                self.audit_exceptions.append(audit_ex)
                
                # If Edge Case 5: Credit note exceeds exception amount
                if anomaly_type == ExceptionCode.CREDIT_OVER_EXCEPTION.value:
                    # Issue credit note of $120 on a $60 dispute!
                    excess_credit = round(disputed_amt * 2.0, 2)
                    cr_id = ID_CREDIT_NOTE_FMT.format(credit_counter)
                    credit_counter += 1
                    
                    self.credit_notes.append(CreditNote(
                        credit_note_id=cr_id,
                        carrier_id=shipment.carrier_id,
                        invoice_id=invoice_id,
                        exception_id=ex_id,
                        credit_amount_usd=excess_credit,
                        credit_date=(inv_date + datetime.timedelta(days=7)).isoformat(),
                        reconciliation_status=CreditReconciliationStatus.OVER_CREDITED.value,
                        notes=f"Over-credit anomaly test: credit ${excess_credit:.2f} exceeds exception ${disputed_amt:.2f}",
                        created_at=f"{inv_date.isoformat()}T14:00:00Z"
                    ))
                elif inv_idx % 8 == 0:
                    # Normal reconciling credit note for other disputes
                    cr_id = ID_CREDIT_NOTE_FMT.format(credit_counter)
                    credit_counter += 1
                    self.credit_notes.append(CreditNote(
                        credit_note_id=cr_id,
                        carrier_id=shipment.carrier_id,
                        invoice_id=invoice_id,
                        exception_id=ex_id,
                        credit_amount_usd=disputed_amt,
                        credit_date=(inv_date + datetime.timedelta(days=7)).isoformat(),
                        reconciliation_status=CreditReconciliationStatus.RECONCILED.value,
                        notes=f"Carrier credit approved for exception dispute {ex_id}",
                        created_at=f"{inv_date.isoformat()}T14:00:00Z"
                    ))
                    
                # Ground truth anomaly label
                self.ground_truth.append({
                    "invoice_id": invoice_id,
                    "shipment_id": inv_shipment_id,
                    "carrier_id": shipment.carrier_id,
                    "is_anomaly": True,
                    "anomaly_type": anomaly_type,
                    "expected_decision": "DISPUTE",
                    "expected_total_billed": total_billed,
                    "expected_total_approved": total_expected,
                    "expected_disputed_amount": disputed_amt,
                    "reason": anomaly_explanation
                })

            # Append the parent invoice
            self.freight_invoices.append(FreightInvoice(
                invoice_id=invoice_id,
                carrier_id=shipment.carrier_id,
                shipment_id=inv_shipment_id,
                invoice_date=inv_date.isoformat(),
                due_date=due_date.isoformat(),
                total_billed_usd=total_billed,
                total_expected_usd=total_expected,
                variance_usd=total_variance,
                audit_status=audit_status,
                created_at=f"{inv_date.isoformat()}T10:00:00Z"
            ))
            
            self.invoice_lines.extend(lines)

    def export_all(self, target_dir: Path = DATA_DIR):
        """Step 9: Export dataset to CSV, JSON, and SQLite database."""
        target_dir.mkdir(parents=True, exist_ok=True)
        
        tables = [
            ("carriers", self.carriers),
            ("lanes", self.lanes),
            ("rate_cards", self.rate_cards),
            ("shipments", self.shipments),
            ("shipment_legs", self.shipment_legs),
            ("weight_measurements", self.weight_measurements),
            ("accessorials", self.accessorials),
            ("freight_invoices", self.freight_invoices),
            ("invoice_lines", self.invoice_lines),
            ("audit_exceptions", self.audit_exceptions),
            ("credit_notes", self.credit_notes),
        ]
        
        # 1. Export CSVs
        for table_name, records in tables:
            csv_path = target_dir / f"{table_name}.csv"
            if records:
                headers = list(records[0].__dict__.keys())
                with open(csv_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)
                    for r in records:
                        writer.writerow([getattr(r, h) for h in headers])
                        
        # 2. Export Ground Truth (Separated, isolated)
        gt_path = target_dir / "ground_truth.csv"
        if self.ground_truth:
            gt_headers = list(self.ground_truth[0].keys())
            with open(gt_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=gt_headers)
                writer.writeheader()
                writer.writerows(self.ground_truth)
                
        # Ground truth JSON
        with open(target_dir / "ground_truth.json", "w", encoding="utf-8") as f:
            json.dump(self.ground_truth, f, indent=2)

        # 3. Export SQLite Database
        db_path = target_dir / "freight_audit.db"
        if db_path.exists():
            db_path.unlink()
            
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.executescript(SQL_DDL)
        
        for table_name, records in tables:
            if records:
                headers = list(records[0].__dict__.keys())
                placeholders = ",".join(["?"] * len(headers))
                query = f"INSERT INTO {table_name} ({','.join(headers)}) VALUES ({placeholders})"
                data_tuples = [tuple(getattr(r, h) for h in headers) for r in records]
                cursor.executemany(query, data_tuples)
                
        conn.commit()
        conn.close()
        
        # 4. Export Source Manifest
        manifest = {
            "dataset_generation_seed": self.seed,
            "scale_profile": self.scale,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "table_counts": {t[0]: len(t[1]) for t in tables},
            "ground_truth_count": len(self.ground_truth),
            "edge_case_distribution": {}
        }
        for gt in self.ground_truth:
            atype = gt["anomaly_type"]
            manifest["edge_case_distribution"][atype] = manifest["edge_case_distribution"].get(atype, 0) + 1
            
        with open(target_dir / "source_manifest.json", "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
            
        return manifest

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Deterministic Freight Data Generator")
    parser.add_argument("--scale", choices=["starter", "medium", "full"], default="starter", help="Dataset scale")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Fixed deterministic seed")
    parser.add_argument("--out", type=str, default=str(DATA_DIR), help="Output directory")
    args = parser.parse_args()
    
    print(f"Generating synthetic freight dataset [Scale: {args.scale}, Seed: {args.seed}]...")
    gen = FreightDataGenerator(seed=args.seed, scale=args.scale)
    gen.generate_all()
    manifest = gen.export_all(Path(args.out))
    print(f"Generation complete! Table summary: {manifest['table_counts']}")
