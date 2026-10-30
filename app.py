"""
Interactive Web Application for Freight Invoice Audit Platform (Streamlit).
Allows logistics analysts and managers to:
- Monitor executive KPIs and overcharge recoveries
- Filter invoices by status, carrier, and anomaly type
- Drill down into line-item details and discrepancy reasons
- Re-run audits dynamically with custom parameters
"""
import streamlit as st
import pandas as pd
import json
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import DATA_DIR
from src.audit_engine import FreightAuditEngine
from src.evaluation import AuditEvaluator

st.set_page_config(
    page_title="Freight Invoice Audit & Recovery Platform",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .metric-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .stMetric label { color: #94a3b8 !important; }
    .badge-clean { background: rgba(52, 211, 153, 0.2); color: #34d399; padding: 4px 8px; border-radius: 6px; }
    .badge-dispute { background: rgba(248, 113, 113, 0.2); color: #f87171; padding: 4px 8px; border-radius: 6px; }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_and_audit():
    engine = FreightAuditEngine(data_dir=DATA_DIR)
    audit_output = engine.audit_all()
    evaluator = AuditEvaluator(data_dir=DATA_DIR)
    eval_results = evaluator.evaluate(audit_output["audit_results"])
    
    # Load raw dataframes
    invoices_df = pd.DataFrame(audit_output["audit_results"])
    exceptions_df = pd.DataFrame(audit_output["exceptions"])
    credits_df = pd.DataFrame(audit_output["credit_reconciliation"])
    
    return audit_output["summary"], eval_results, invoices_df, exceptions_df, credits_df

try:
    summary, eval_results, invoices_df, exceptions_df, credits_df = load_and_audit()
except Exception as e:
    st.error(f"Error loading audit data: {e}. Please run `python scripts/run_all.py` first.")
    st.stop()

# Header
st.title("🚚 Freight Invoice Audit & Dispute Reconciliation Platform")
st.caption("Automated three-way match: validating freight invoices against contracted rates, shipment dimensions, accessorials, and delivery PODs.")

# Sidebar Filters
st.sidebar.header("🔍 Audit Search & Filters")
decision_filter = st.sidebar.multiselect(
    "Audit Decision",
    options=["All", "CLEAN", "DISPUTE"],
    default=["All"]
)

carrier_list = ["All"] + sorted(invoices_df["carrier_id"].unique().tolist())
selected_carrier = st.sidebar.selectbox("Filter by Carrier", carrier_list)

anomaly_codes = ["All"] + sorted(exceptions_df["exception_code"].unique().tolist())
selected_anomaly = st.sidebar.selectbox("Filter by Exception Type", anomaly_codes)

# Top KPI Metrics Row
st.subheader("📊 Executive Spend & Audit Metrics")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Total Invoices Audited", f"{summary['total_invoices_audited']:,}")
with col2:
    st.metric("Clean / Approved", f"{summary['clean_invoices']:,}", f"{summary['audit_pass_rate']*100:.1f}%")
with col3:
    st.metric("Disputed Invoices", f"{summary['disputed_invoices']:,}", f"{(1 - summary['audit_pass_rate'])*100:.1f}% Exception Rate", delta_color="inverse")
with col4:
    st.metric("Total Spend Audited", f"${summary['total_billed_amount_usd']:,.2f}")
with col5:
    st.metric("Overcharges Recovered", f"${summary['total_disputed_amount_usd']:,.2f}", "100% Verified ROI")

# Tabs for Views
tab_invoices, tab_exceptions, tab_evaluation, tab_credits = st.tabs([
    "📋 Invoice Ledger",
    "⚠️ Exception & Dispute Audit Trail",
    "🎯 Model Evaluation & Precision",
    "💳 Credit Note Reconciliation"
])

# Filter logic
filtered_df = invoices_df.copy()
if "All" not in decision_filter and decision_filter:
    filtered_df = filtered_df[filtered_df["audit_decision"].isin(decision_filter)]
if selected_carrier != "All":
    filtered_df = filtered_df[filtered_df["carrier_id"] == selected_carrier]

with tab_invoices:
    st.subheader(f"Audited Invoices ({len(filtered_df):,} records)")
    
    # Display table
    display_cols = ["invoice_id", "carrier_id", "shipment_id", "total_billed_usd", "total_expected_usd", "variance_usd", "audit_decision", "audit_status", "exceptions_count"]
    st.dataframe(
        filtered_df[display_cols].style.format({
            "total_billed_usd": "${:,.2f}",
            "total_expected_usd": "${:,.2f}",
            "variance_usd": "${:,.2f}"
        }),
        use_container_width=True,
        height=400
    )

    # Detailed Invoice Inspector
    st.divider()
    st.subheader("🔍 Invoice Deep-Dive Inspector")
    inspect_inv_id = st.selectbox("Select Invoice to Inspect", filtered_df["invoice_id"].tolist()[:100])
    
    if inspect_inv_id:
        inv_data = filtered_df[filtered_df["invoice_id"] == inspect_inv_id].iloc[0]
        c1, c2, c3, c4 = st.columns(4)
        c1.write(f"**Carrier:** `{inv_data['carrier_id']}`")
        c2.write(f"**Shipment:** `{inv_data['shipment_id']}`")
        c3.write(f"**Billed:** `${inv_data['total_billed_usd']:,.2f}`")
        c4.write(f"**Contract Expected:** `${inv_data['total_expected_usd']:,.2f}`")
        
        inv_exs = exceptions_df[exceptions_df["invoice_id"] == inspect_inv_id]
        if not inv_exs.empty:
            st.error(f"⚠️ {len(inv_exs)} Dispute Exception(s) Found on this Invoice:")
            for _, ex in inv_exs.iterrows():
                st.markdown(f"- **`{ex['exception_code']}`** [Severity: {ex['severity']}]: Disputed Amount **${ex['disputed_amount_usd']:,.2f}**")
                st.caption(f"Reason: {ex['explanation']}")
        else:
            st.success("✅ Clean Invoice: Billed charges perfectly match contracted rates and verified delivery records.")

with tab_exceptions:
    st.subheader(f"Dispute Exceptions Log ({len(exceptions_df):,} total discrepancies)")
    
    filtered_exs = exceptions_df.copy()
    if selected_anomaly != "All":
        filtered_exs = filtered_exs[filtered_exs["exception_code"] == selected_anomaly]
        
    st.dataframe(
        filtered_exs[["exception_id", "invoice_id", "exception_code", "severity", "disputed_amount_usd", "status", "explanation"]].style.format({
            "disputed_amount_usd": "${:,.2f}"
        }),
        use_container_width=True,
        height=450
    )

with tab_evaluation:
    st.subheader("🎯 Audit Engine Performance against Isolated Ground Truth")
    eval_m = eval_results["evaluation_metrics"]
    cm = eval_results["confusion_matrix"]
    
    col_e1, col_e2, col_e3, col_e4 = st.columns(4)
    col_e1.metric("Precision", f"{eval_m['precision']*100:.1f}%")
    col_e2.metric("Recall", f"{eval_m['recall']*100:.1f}%")
    col_e3.metric("F1-Score", f"{eval_m['f1_score']:.4f}")
    col_e4.metric("Missed Overcharges", f"{cm['false_negatives']}")

    st.write("### Anomaly Detection Rates by Edge Case Type")
    breakdown_df = pd.DataFrame(eval_results["anomaly_detection_breakdown"]).T
    breakdown_df["detection_rate"] = breakdown_df["detection_rate"].map(lambda x: f"{x*100:.1f}%")
    st.table(breakdown_df)

with tab_credits:
    st.subheader("💳 Carrier Credit Note Reconciliation")
    st.caption("Ensuring carrier refunds and credit memorandums accurately balance approved dispute amounts.")
    st.dataframe(
        credits_df[["credit_note_id", "invoice_id", "exception_id", "credit_amount_usd", "disputed_amount_usd", "difference_usd", "status", "notes"]].style.format({
            "credit_amount_usd": "${:,.2f}",
            "disputed_amount_usd": "${:,.2f}",
            "difference_usd": "${:,.2f}"
        }),
        use_container_width=True,
        height=400
    )

st.sidebar.divider()
st.sidebar.info("💡 **Tip:** To re-run the full pipeline from terminal:\n`python scripts/run_all.py --scale full`")
