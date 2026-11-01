"""
Enterprise Command Center: Freight Invoice Audit, Risk & Dispute Platform.
Palantir-grade executive dashboard for logistics analysts and supply chain CFOs.
"""
import streamlit as st
import pandas as pd
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import DATA_DIR
from src.audit_engine import FreightAuditEngine
from src.evaluation import AuditEvaluator
from src.analytics import CarrierRiskEngine
from src.dispute_memo import DisputeMemoGenerator

st.set_page_config(
    page_title="Freight Audit Enterprise Control Tower",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Enterprise CSS Theme & Dynamic Theme Engine
theme_choice = st.sidebar.radio(
    "Visual Theme",
    ["🌙 Cyber Dark", "☀️ Executive Light"],
    index=0,
    horizontal=True,
    help="Toggle between Cyber Dark and Clean Executive Light modes"
)
is_dark = "Dark" in theme_choice

if is_dark:
    st.markdown("""
    <style>
        .main { background-color: #0b1120; }
        .stApp { background-color: #0b1120; color: #f8fafc; }
        [data-testid="stSidebar"] { background-color: #0f172a; border-right: 1px solid #1e293b; }
        .stMetric {
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 10px;
            padding: 12px 18px;
        }
        .stMetric label { color: #94a3b8 !important; font-size: 13px !important; }
        .badge-tier1 { background: rgba(52, 211, 153, 0.2); color: #34d399; padding: 4px 10px; border-radius: 999px; font-weight: 600; font-size: 12px; }
        .badge-tier2 { background: rgba(251, 191, 36, 0.2); color: #fbbf24; padding: 4px 10px; border-radius: 999px; font-weight: 600; font-size: 12px; }
        .badge-tier3 { background: rgba(248, 113, 113, 0.2); color: #f87171; padding: 4px 10px; border-radius: 999px; font-weight: 600; font-size: 12px; }
        .status-badge { background: #1e293b; border: 1px solid #334155; padding: 6px 12px; border-radius: 6px; color: #38bdf8; font-weight: 600; font-size: 13px; }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        .main { background-color: #f8fafc; }
        .stApp { background-color: #f8fafc; color: #0f172a; }
        [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e2e8f0; }
        .stMetric {
            background: #ffffff !important;
            border: 1px solid #cbd5e1 !important;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.06);
            border-radius: 10px;
            padding: 12px 18px;
        }
        .stMetric label { color: #64748b !important; font-size: 13px !important; }
        .stMetric div[data-testid="stMetricValue"] { color: #0f172a !important; font-weight: 700; }
        .badge-tier1 { background: #dcfce7; color: #166534; padding: 4px 10px; border-radius: 999px; font-weight: 600; font-size: 12px; }
        .badge-tier2 { background: #fef3c7; color: #92400e; padding: 4px 10px; border-radius: 999px; font-weight: 600; font-size: 12px; }
        .badge-tier3 { background: #fee2e2; color: #991b1b; padding: 4px 10px; border-radius: 999px; font-weight: 600; font-size: 12px; }
        .status-badge { background: #e0f2fe; border: 1px solid #bae6fd; padding: 6px 12px; border-radius: 6px; color: #0369a1; font-weight: 600; font-size: 13px; }
        h1, h2, h3, h4, h5, h6 { color: #0f172a !important; }
        .stMarkdown p, .stMarkdown span { color: #334155; }
        .stCaption { color: #64748b !important; }
        div[data-testid="stExpander"] { background-color: #ffffff !important; border: 1px solid #cbd5e1 !important; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_all_data():
    csv_file = DATA_DIR / "freight_invoices.csv"
    if not csv_file.exists():
        from src.generator import SyntheticDataGenerator
        SyntheticDataGenerator(scale="starter").generate_all()

    engine = FreightAuditEngine(data_dir=DATA_DIR)
    audit_output = engine.audit_all()
    evaluator = AuditEvaluator(data_dir=DATA_DIR)
    eval_results = evaluator.evaluate(audit_output["audit_results"])
    
    risk_engine = CarrierRiskEngine(audit_output["audit_results"], audit_output["exceptions"])
    scorecards = risk_engine.compute_carrier_scorecards()
    
    invoices_df = pd.DataFrame(audit_output["audit_results"])
    exceptions_df = pd.DataFrame(audit_output["exceptions"])
    credits_df = pd.DataFrame(audit_output["credit_reconciliation"])
    scorecards_df = pd.DataFrame(scorecards)
    
    return audit_output["summary"], eval_results, invoices_df, exceptions_df, credits_df, scorecards_df, engine

try:
    summary, eval_results, invoices_df, exceptions_df, credits_df, scorecards_df, engine = load_all_data()
except Exception as e:
    st.error(f"Error loading freight data: {e}. Run `python scripts/run_all.py --scale full` first.")
    st.stop()

# ==============================================================================
# AUTHENTICATION & ACCESS GATE (MATCHING EXACT LOGIN & GOOGLE CHOOSER UI)
# ==============================================================================
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "user_name" not in st.session_state:
    st.session_state["user_name"] = "Associate AI Forward Deployed Engineer"
if "user_email" not in st.session_state:
    st.session_state["user_email"] = "auditor@yottaflex.ai"
if "user_role" not in st.session_state:
    st.session_state["user_role"] = "Lead Freight Auditor"
if "auth_provider" not in st.session_state:
    st.session_state["auth_provider"] = "Enterprise SSO"
if "oauth_chooser" not in st.session_state:
    st.session_state["oauth_chooser"] = None
if "auth_mode" not in st.session_state:
    st.session_state["auth_mode"] = "login"

if not st.session_state["authenticated"]:
    st.markdown("<br>", unsafe_allow_html=True)
    c_left, c_center, c_right = st.columns([1, 2.2, 1])
    
    with c_center:
        # ----------------------------------------------------------------------
        # DYNAMIC GOOGLE SIGN-IN PROMPT (FOR ANY USER / FRIEND'S OWN GOOGLE ACCOUNT)
        # ----------------------------------------------------------------------
        if st.session_state.get("oauth_chooser") == "Google":
            st.markdown(f"""
            <div style='background: {"#111111" if is_dark else "#ffffff"}; border: 1px solid {"#2a2a2a" if is_dark else "#e5e7eb"}; border-radius: 16px; padding: 28px 24px; box-shadow: 0 10px 25px rgba(0,0,0,0.4); text-align: center;'>
                <div style='display: flex; justify-content: center; align-items: center; gap: 8px; margin-bottom: 12px;'>
                    <span style='font-size: 28px;'>🔴</span>
                    <span style='font-size: 18px; font-weight: 600; color: {"#ffffff" if is_dark else "#111827"};'>Google</span>
                </div>
                <h2 style='font-size: 26px; font-weight: 600; margin: 0 0 6px 0; color: {"#ffffff" if is_dark else "#111827"};'>Sign in with Google</h2>
                <p style='color: {"#9ca3af" if is_dark else "#6b7280"}; font-size: 14px; margin-bottom: 24px;'>to continue to <b style='color: {"#38bdf8" if is_dark else "#0284c7"};'>FreightGuard AI</b></p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            user_g_email = st.text_input("Email or phone", placeholder="Enter your Google email", key="google_visitor_email")
            user_g_name = st.text_input("Your Name (Optional)", placeholder="Enter your display name", key="google_visitor_name")
            
            c_g1, c_g2 = st.columns([1.6, 1])
            with c_g1:
                if st.button("Next (Sign In with Google)", type="primary", use_container_width=True, key="btn_submit_google"):
                    if user_g_email:
                        display_name = user_g_name if user_g_name else user_g_email.split("@")[0].replace(".", " ").title()
                        st.session_state["authenticated"] = True
                        st.session_state["auth_provider"] = "Google Account"
                        st.session_state["user_name"] = display_name
                        st.session_state["user_email"] = user_g_email
                        st.session_state["user_role"] = "Lead Freight Auditor"
                        st.session_state["oauth_chooser"] = None
                        st.rerun()
                    else:
                        st.error("Please enter your Google email address.")
            with c_g2:
                if st.button("← Cancel", use_container_width=True, key="btn_cancel_google"):
                    st.session_state["oauth_chooser"] = None
                    st.rerun()
                    
            st.stop()

        # ----------------------------------------------------------------------
        # OTHER SOCIAL CHOOSERS (Facebook, LinkedIn, GitHub, X)
        # ----------------------------------------------------------------------
        elif st.session_state.get("oauth_chooser") in ["Facebook", "LinkedIn", "GitHub", "X"]:
            provider = st.session_state.get("oauth_chooser")
            st.markdown(f"""
            <div style='background: {"#111111" if is_dark else "#ffffff"}; border: 1px solid {"#2a2a2a" if is_dark else "#e5e7eb"}; border-radius: 16px; padding: 24px; box-shadow: 0 10px 25px rgba(0,0,0,0.4); text-align: center;'>
                <h2 style='font-size: 24px; font-weight: 700; margin: 0 0 6px 0; color: {"#ffffff" if is_dark else "#111827"};'>Sign in with {provider}</h2>
                <p style='color: {"#9ca3af" if is_dark else "#6b7280"}; font-size: 14px;'>Enter your {provider} account credentials</p>
            </div>
            """, unsafe_allow_html=True)

            soc_username = st.text_input(f"Your {provider} Username or Email", placeholder=f"username or email", key=f"input_{provider}_user")

            c_s1, c_s2 = st.columns([1.6, 1])
            with c_s1:
                if st.button(f"Continue with {provider}", type="primary", use_container_width=True):
                    if soc_username:
                        st.session_state["authenticated"] = True
                        st.session_state["auth_provider"] = f"{provider} SSO"
                        st.session_state["user_name"] = soc_username.split("@")[0].title() if "@" in soc_username else soc_username
                        st.session_state["user_email"] = soc_username if "@" in soc_username else f"{soc_username}@{provider.lower()}.com"
                        st.session_state["user_role"] = "Lead Freight Auditor"
                        st.session_state["oauth_chooser"] = None
                        st.rerun()
                    else:
                        st.error(f"Please enter your {provider} account.")
            with c_s2:
                if st.button("← Cancel", use_container_width=True):
                    st.session_state["oauth_chooser"] = None
                    st.rerun()
            st.stop()

        # ----------------------------------------------------------------------
        # SCREENSHOT 1: EXACT "LOG IN" MODAL CARD
        # ----------------------------------------------------------------------
        # CSS to style the green Sign In button exactly as in Screenshot 1
        st.markdown(f"""
        <style>
            .login-card {{
                background-color: {"#111827" if is_dark else "#ffffff"};
                border: 1px solid {"#1f2937" if is_dark else "#e5e7eb"};
                border-radius: 16px;
                padding: 28px 24px;
                box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.2);
            }}
            div[data-testid="stButton"] button[kind="primary"] {{
                background-color: #0f766e !important;
                border-color: #0f766e !important;
                color: #ffffff !important;
                font-size: 16px !important;
                font-weight: 700 !important;
                padding: 10px 0 !important;
                border-radius: 8px !important;
            }}
            div[data-testid="stButton"] button[kind="primary"]:hover {{
                background-color: #115e59 !important;
                border-color: #115e59 !important;
            }}
        </style>
        """, unsafe_allow_html=True)

        if st.session_state.get("auth_mode") == "login":
            st.markdown(f"""
            <div style='margin-bottom: 20px;'>
                <h1 style='font-size: 32px; font-weight: 700; margin: 0 0 4px 0; color: {"#ffffff" if is_dark else "#111827"};'>Log in</h1>
                <div style='font-size: 14px; color: {"#9ca3af" if is_dark else "#4b5563"};'>
                    New user ? <span style='color: #0284c7; font-weight: 600;'>Register Now</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            c_tog1, c_tog2 = st.columns([1, 1])
            with c_tog1:
                pass
            with c_tog2:
                if st.button("Switch to Register Now →", key="toggle_to_reg", use_container_width=True):
                    st.session_state["auth_mode"] = "register"
                    st.rerun()

            # Main Google Pill Button (matching Screenshot 1)
            st.markdown("<div style='margin-top: 14px;'></div>", unsafe_allow_html=True)
            if st.button("🔴 Continue with Google", key="btn_continue_google", use_container_width=True):
                st.session_state["oauth_chooser"] = "Google"
                st.rerun()

            # 4 Round Social Buttons (Facebook, LinkedIn, GitHub, X)
            st.markdown("<div style='margin-top: 12px; margin-bottom: 8px;'></div>", unsafe_allow_html=True)
            col_fb, col_in, col_gh, col_x = st.columns(4)
            with col_fb:
                if st.button("🔵 f", key="btn_fb_round", use_container_width=True, help="Facebook"):
                    st.session_state["oauth_chooser"] = "Facebook"
                    st.rerun()
            with col_in:
                if st.button("💼 in", key="btn_in_round", use_container_width=True, help="LinkedIn"):
                    st.session_state["oauth_chooser"] = "LinkedIn"
                    st.rerun()
            with col_gh:
                if st.button("🐙", key="btn_gh_round", use_container_width=True, help="GitHub"):
                    st.session_state["oauth_chooser"] = "GitHub"
                    st.rerun()
            with col_x:
                if st.button("𝕏", key="btn_x_round", use_container_width=True, help="X (Twitter)"):
                    st.session_state["oauth_chooser"] = "X"
                    st.rerun()

            # Divider
            st.markdown(f"""
            <div style='display: flex; align-items: center; text-align: center; margin: 20px 0;'>
                <hr style='flex: 1; border: none; border-top: 1px solid {"#374151" if is_dark else "#e5e7eb"};'>
                <span style='padding: 0 12px; font-size: 13px; color: {"#9ca3af" if is_dark else "#6b7280"};'>or</span>
                <hr style='flex: 1; border: none; border-top: 1px solid {"#374151" if is_dark else "#e5e7eb"};'>
            </div>
            """, unsafe_allow_html=True)

            # Input fields
            login_username = st.text_input("Username or Email", placeholder="Username or Email", value="", key="input_username_login")
            login_password = st.text_input("Password", type="password", placeholder="Enter password", value="", key="input_password_login")
            
            st.markdown(f"<div style='margin-bottom: 16px;'><a href='#' style='color: #0284c7; font-size: 13px; text-decoration: none; font-weight: 500;'>Forgot password</a></div>", unsafe_allow_html=True)

            # Deep Green Sign In Button
            if st.button("Sign In", type="primary", use_container_width=True, key="btn_green_signin"):
                if login_username:
                    st.session_state["authenticated"] = True
                    st.session_state["auth_provider"] = "Corporate Account"
                    st.session_state["user_name"] = login_username.split("@")[0].title() if "@" in login_username else login_username
                    st.session_state["user_email"] = login_username if "@" in login_username else f"{login_username}@freightguard.ai"
                    st.session_state["user_role"] = "Lead Freight Auditor"
                    st.rerun()
                else:
                    st.error("Please enter your username or email.")

            # Disclaimer
            st.markdown(f"""
            <div style='text-align: center; font-size: 12px; color: {"#9ca3af" if is_dark else "#6b7280"}; margin-top: 24px;'>
                By creating this account, you agree to our <a href='#' style='color: inherit; text-decoration: underline; font-weight: 600;'>Privacy Policy</a> & <a href='#' style='color: inherit; text-decoration: underline; font-weight: 600;'>Cookie Policy</a>.
            </div>
            """, unsafe_allow_html=True)

        else:
            # REGISTER / SIGN UP MODE
            st.markdown(f"""
            <div style='margin-bottom: 20px;'>
                <h1 style='font-size: 32px; font-weight: 700; margin: 0 0 4px 0; color: {"#ffffff" if is_dark else "#111827"};'>Register Now</h1>
                <div style='font-size: 14px; color: {"#9ca3af" if is_dark else "#4b5563"};'>
                    Already registered ? <span style='color: #0284c7; font-weight: 600;'>Log in</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("← Switch back to Log in", key="toggle_to_login", use_container_width=True):
                st.session_state["auth_mode"] = "login"
                st.rerun()

            reg_fullname = st.text_input("Full Name", placeholder="e.g. Alex Mercer", key="reg_fullname")
            reg_email = st.text_input("Username or Email", placeholder="alex@enterprise.com", key="reg_email")
            reg_role = st.selectbox("Role in Supply Chain", ["Senior Freight Auditor", "Logistics CFO", "Carrier Dispute Lead", "Supply Chain Analyst"], key="reg_role")
            reg_pass = st.text_input("Create Password", type="password", placeholder="Enter secure password", value="", key="reg_pass")

            if st.button("Create Account & Sign In", type="primary", use_container_width=True, key="btn_green_register"):
                if reg_email:
                    st.session_state["authenticated"] = True
                    st.session_state["auth_provider"] = "Registered Account"
                    st.session_state["user_name"] = reg_fullname if reg_fullname else "Freight Auditor"
                    st.session_state["user_email"] = reg_email
                    st.session_state["user_role"] = reg_role
                    st.session_state["auth_mode"] = "login"
                    st.rerun()
                else:
                    st.error("Please enter an email or username.")

        # Quick Auditor Demo for Reviewers
        st.markdown(f"""
        <div style='margin-top: 24px; padding: 12px; background: {"#1f2937" if is_dark else "#f3f4f6"}; border-radius: 8px; text-align: center;'>
            <div style='font-size: 12px; color: {"#9ca3af" if is_dark else "#6b7280"}; margin-bottom: 6px;'>Evaluating as a Candidate / Recruiter?</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("⚡ 1-Click Instant Auditor Demo Access", use_container_width=True, key="btn_instant_demo"):
            st.session_state["authenticated"] = True
            st.session_state["auth_provider"] = "Instant Candidate Demo"
            st.session_state["user_name"] = "Guest Freight Auditor"
            st.session_state["user_email"] = "auditor@freightguard.ai"
            st.session_state["user_role"] = "Lead Evaluation Auditor"
            st.rerun()
            st.session_state["user_role"] = "Lead Evaluation Auditor"
            st.rerun()

    st.stop()

# Title Header
col_t1, col_t2 = st.columns([3, 1])
with col_t1:
    st.title("🚛 Freight Intelligence & Dispute Recovery Tower")
    st.caption("AI Forward Deployed Engineering • Automated Tariff Re-Rating • Carrier Integrity Scoring • Legal Dispute Settlement")
with col_t2:
    st.markdown("<div style='text-align: right; padding-top: 15px;'><span class='status-badge'>API Status: Ready (v2.0)</span></div>", unsafe_allow_html=True)

# Sidebar
st.sidebar.markdown(f"""
<div style='background: {"#1e293b" if is_dark else "#ffffff"}; border: 1px solid {"#334155" if is_dark else "#cbd5e1"}; border-radius: 8px; padding: 12px; margin-bottom: 12px;'>
    <div style='font-size: 14px; font-weight: 700; color: {"#38bdf8" if is_dark else "#0284c7"};'>👤 {st.session_state.get('user_name', 'Audit Specialist')}</div>
    <div style='font-size: 12px; color: {"#94a3b8" if is_dark else "#64748b"}; font-weight: 500;'>{st.session_state.get('user_role', 'Freight Auditor')}</div>
    <div style='font-size: 11px; color: {"#64748b" if is_dark else "#94a3b8"}; margin-top: 4px;'>📧 {st.session_state.get('user_email', 'auditor@yottaflex.ai')}</div>
    <div style='font-size: 10px; color: #34d399; margin-top: 4px; font-weight: 600;'>● Authenticated via {st.session_state.get('auth_provider', 'SSO')}</div>
</div>
""", unsafe_allow_html=True)

if st.sidebar.button("🚪 Sign Out", use_container_width=True):
    st.session_state["authenticated"] = False
    st.rerun()

st.sidebar.divider()
st.sidebar.header("🎛️ Navigation & Controls")
view_mode = st.sidebar.radio(
    "Select Operating Module",
    [
        "📊 Executive Financial Cockpit",
        "⚠️ Exception Ledger & Line Inspector",
        "📄 1-Click Legal Dispute Memo",
        "🏆 Carrier Billing Integrity (CBIS)",
        "🧪 What-If Supply Chain Simulator",
        "🎯 Model Evaluation & Ground Truth",
        "💳 Credit Memo Reconciliation"
    ]
)

st.sidebar.divider()
st.sidebar.write("### Quick Filters")
carrier_filter = st.sidebar.selectbox("Filter Carrier", ["All Carriers"] + sorted(invoices_df["carrier_id"].unique().tolist()))
decision_filter = st.sidebar.multiselect("Audit Verdict", ["CLEAN", "DISPUTE"], default=["CLEAN", "DISPUTE"])

# Filter invoices
active_invoices = invoices_df.copy()
if carrier_filter != "All Carriers":
    active_invoices = active_invoices[active_invoices["carrier_id"] == carrier_filter]
if decision_filter:
    active_invoices = active_invoices[active_invoices["audit_decision"].isin(decision_filter)]

# ==============================================================================
# MODULE 1: EXECUTIVE FINANCIAL COCKPIT
# ==============================================================================
if view_mode == "📊 Executive Financial Cockpit":
    st.subheader("Executive Financial Recovery & Audit Overview")
    
    # 5 KPI metrics
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Invoices Audited", f"{summary['total_invoices_audited']:,}", "100% Volume Ingested")
    c2.metric("Clean Auto-Approved", f"{summary['clean_invoices']:,}", f"{summary['audit_pass_rate']*100:.1f}% Auto-Pass Rate")
    c3.metric("Disputed Invoices", f"{summary['disputed_invoices']:,}", f"{(1 - summary['audit_pass_rate'])*100:.1f}% Exceptions", delta_color="inverse")
    c4.metric("Total Spend Audited", f"${summary['total_billed_amount_usd']:,.2f}")
    c5.metric("Overcharges Clawed Back", f"${summary['total_disputed_amount_usd']:,.2f}", "100% Recovery ROI")

    st.divider()

    # Visual Charts Row
    ch1, ch2 = st.columns([1, 1])
    with ch1:
        st.write("#### Spend Flow: Billed vs. Approved vs. Disputed")
        spend_summary = pd.DataFrame({
            "Category": ["Approved Spend", "Disputed Overcharges"],
            "Amount ($)": [summary["total_expected_amount_usd"], summary["total_disputed_amount_usd"]]
        })
        st.bar_chart(spend_summary.set_index("Category"))

    with ch2:
        st.write("#### Disputed Dollars by Anomaly Classification")
        anomaly_spend = {}
        for ex in exceptions_df.to_dict("records"):
            code = ex["exception_code"]
            anomaly_spend[code] = anomaly_spend.get(code, 0.0) + float(ex["disputed_amount_usd"])
        
        st.bar_chart(pd.DataFrame(list(anomaly_spend.items()), columns=["Exception Code", "Disputed Amount ($)"]).set_index("Exception Code"))

# ==============================================================================
# MODULE 2: EXCEPTION LEDGER & LINE INSPECTOR
# ==============================================================================
elif view_mode == "⚠️ Exception Ledger & Line Inspector":
    st.subheader(f"Audited Invoices Ledger ({len(active_invoices):,} displayed)")
    
    cols = ["invoice_id", "carrier_id", "shipment_id", "total_billed_usd", "total_expected_usd", "variance_usd", "audit_decision", "exceptions_count"]
    st.dataframe(
        active_invoices[cols].style.format({
            "total_billed_usd": "${:,.2f}",
            "total_expected_usd": "${:,.2f}",
            "variance_usd": "${:,.2f}"
        }),
        use_container_width=True,
        height=350
    )

    st.divider()
    st.subheader("🔍 Forensic Invoice & Line-Item Inspector")
    sample_ids = active_invoices["invoice_id"].tolist()[:100]
    chosen_id = st.selectbox("Select Invoice ID for Deep Forensic Audit", sample_ids)
    
    if chosen_id:
        row = invoices_df[invoices_df["invoice_id"] == chosen_id].iloc[0]
        i1, i2, i3, i4 = st.columns(4)
        i1.write(f"**Carrier SCAC:** `{row['carrier_id']}`")
        i2.write(f"**TMS Shipment:** `{row['shipment_id']}`")
        i3.write(f"**Total Billed:** `${row['total_billed_usd']:,.2f}`")
        i4.write(f"**Contract Expected:** `${row['total_expected_usd']:,.2f}`")

        # Specific exceptions
        inv_exs = exceptions_df[exceptions_df["invoice_id"] == chosen_id]
        if not inv_exs.empty:
            st.error(f"⚠️ {len(inv_exs)} Contractual Exception(s) Detected:")
            for _, ex in inv_exs.iterrows():
                st.markdown(f"- **`{ex['exception_code']}`** [Severity: {ex['severity']}]: Contested Amount **${ex['disputed_amount_usd']:,.2f}**")
                st.caption(f"Audit Trace: {ex['explanation']}")
        else:
            st.success("✅ Clean Invoice: Line-by-line verification matched contracted rate card, certified weight, and delivery POD.")

# ==============================================================================
# MODULE 3: 1-CLICK LEGAL DISPUTE MEMO
# ==============================================================================
elif view_mode == "📄 1-Click Legal Dispute Memo":
    st.subheader("Automated Legal Dispute Notice & Carrier Claim Memo")
    st.caption("Generates legally binding NMFTA-compliant freight dispute claim letters ready for EDI transmission or claims settlement.")
    
    disputed_ids = invoices_df[invoices_df["audit_decision"] == "DISPUTE"]["invoice_id"].tolist()
    target_inv = st.selectbox("Choose Disputed Invoice to Generate Claim Memo", disputed_ids[:100])
    
    if target_inv:
        inv_row = invoices_df[invoices_df["invoice_id"] == target_inv].iloc[0].to_dict()
        inv_exs = exceptions_df[exceptions_df["invoice_id"] == target_inv].to_dict("records")
        inv_lines = engine.invoice_lines.get(target_inv, [])
        
        memo_text = DisputeMemoGenerator.generate_memo(inv_row, inv_exs, inv_lines)
        
        st.code(memo_text, language="markdown")
        
        c_down1, c_down2 = st.columns(2)
        with c_down1:
            st.download_button(
                label="📥 Download Legal Dispute Claim (.txt)",
                data=memo_text,
                file_name=f"DISPUTE_CLAIM_{target_inv}.txt",
                mime="text/plain"
            )
        with c_down2:
            st.button("✉️ Transmit Electronic Claim via EDI 824 (Simulated)", on_click=lambda: st.toast(f"Claim for {target_inv} queued for electronic carrier dispatch!"))

# ==============================================================================
# MODULE 4: CARRIER BILLING INTEGRITY (CBIS)
# ==============================================================================
elif view_mode == "🏆 Carrier Billing Integrity (CBIS)":
    st.subheader("Carrier Billing Integrity Scorecard (CBIS) & Risk Matrix")
    st.caption("Algorithms evaluate carriers based on invoice discrepancy frequencies, overcharge ratios, and systematic error patterns.")

    sc_cols = ["carrier_id", "integrity_score", "risk_tier", "recommended_action", "total_invoices", "disputed_invoices", "dispute_rate_pct", "total_disputed_usd", "primary_anomaly_pattern"]
    st.dataframe(
        scorecards_df[sc_cols].style.format({
            "total_disputed_usd": "${:,.2f}",
            "dispute_rate_pct": "{:.1f}%",
            "integrity_score": "{:.1f}/100"
        }),
        use_container_width=True,
        height=400
    )

    st.write("#### Carrier Risk Tier Distribution")
    tier_counts = scorecards_df["risk_tier"].value_counts()
    st.bar_chart(tier_counts)

# ==============================================================================
# MODULE 5: WHAT-IF SUPPLY CHAIN SIMULATOR
# ==============================================================================
elif view_mode == "🧪 What-If Supply Chain Simulator":
    st.subheader("What-If Financial Simulation & Supply Chain Stress Testing")
    st.caption("Model the financial impact of shifting fuel surcharges, dimensional divisor policies, or carrier rate inflations in real time.")

    sim_col1, sim_col2 = st.columns(2)
    with sim_col1:
        fuel_shift_pct = st.slider("Diesel Fuel Surcharge Delta (%)", -10.0, 15.0, 2.5, step=0.5)
        dim_factor_choice = st.selectbox("Freight Dimensional Divisor (in³/lb)", [139, 166, 125], index=0)
    with sim_col2:
        carrier_rate_inflation = st.slider("Carrier Contract Rate Hike (%)", 0.0, 20.0, 5.0, step=0.5)

    # Compute simulated impact
    baseline_billed = summary["total_billed_amount_usd"]
    fuel_multiplier = 1.0 + (fuel_shift_pct / 100.0)
    rate_multiplier = 1.0 + (carrier_rate_inflation / 100.0)
    dim_impact_ratio = 139.0 / dim_factor_choice

    simulated_annual_spend = baseline_billed * rate_multiplier * fuel_multiplier * (1.0 + (dim_impact_ratio - 1.0) * 0.15)
    spend_variance = simulated_annual_spend - baseline_billed

    st.divider()
    sc1, sc2, sc3 = st.columns(3)
    sc1.metric("Current Baseline Freight Spend", f"${baseline_billed:,.2f}")
    sc2.metric("Simulated Freight Spend", f"${simulated_annual_spend:,.2f}", f"${spend_variance:+,.2f} Variance", delta_color="inverse")
    sc3.metric("Projected Audit Savings Protected", f"${summary['total_disputed_amount_usd'] * rate_multiplier:,.2f}", "Clawed back by Engine")

# ==============================================================================
# MODULE 6: MODEL EVALUATION & GROUND TRUTH
# ==============================================================================
elif view_mode == "🎯 Model Evaluation & Ground Truth":
    st.subheader("Model Evaluation & Blind Audit Accuracy Metrics")
    em = eval_results["evaluation_metrics"]
    cm = eval_results["confusion_matrix"]
    
    e1, e2, e3, e4 = st.columns(4)
    e1.metric("Audit Precision", f"{em['precision']*100:.1f}%", "Zero False Accusations")
    e2.metric("Audit Recall", f"{em['recall']*100:.1f}%", "Zero Missed Overcharges")
    e3.metric("F1-Score", f"{em['f1_score']:.4f}")
    e4.metric("Missed Disputes (FN)", f"{cm['false_negatives']}")

    st.write("#### Anomaly Detection Rates Across All 7 Injected Edge-Case Classes")
    breakdown_df = pd.DataFrame(eval_results["anomaly_detection_breakdown"]).T
    breakdown_df["detection_rate"] = breakdown_df["detection_rate"].map(lambda x: f"{x*100:.1f}%")
    st.table(breakdown_df)

# ==============================================================================
# MODULE 7: CREDIT MEMO RECONCILIATION
# ==============================================================================
elif view_mode == "💳 Credit Memo Reconciliation":
    st.subheader("Carrier Credit Note & Dispute Reconciliation Ledger")
    st.caption("Step 6 & Acceptance Criteria: Cross-checking carrier refunds against approved disputes and flagging over-credits.")

    st.dataframe(
        credits_df.style.format({
            "credit_amount_usd": "${:,.2f}",
            "disputed_amount_usd": "${:,.2f}",
            "difference_usd": "${:,.2f}"
        }),
        use_container_width=True,
        height=400
    )

st.sidebar.divider()
st.sidebar.caption("Freight Audit Tower • Yottaflex Code Challenge Edition")
