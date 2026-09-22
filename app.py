import streamlit as st
import pandas as pd
import os
import io
import socket
import random
import smtplib
import urllib.parse
from datetime import datetime, timedelta
from supabase import create_client, Client

# Page Configuration
st.set_page_config(
    page_title="Dry1 Laundry & Saree Care CRM", 
    layout="wide", 
    page_icon="💧",
    initial_sidebar_state="auto"
)

# --- SUPABASE CLOUD DATABASE CONFIGURATION ---
SUPABASE_URL = "https://vvnbwnhmkicoydojubxs.supabase.co"
SUPABASE_KEY = "sb_publishable__fF3R7bDO-2DuEZKvYklvA_zWwrF9RP"

@st.cache_resource
def init_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# --- OPTIMIZED FAST DATABASE HELPER FUNCTIONS WITH CACHING ---
@st.cache_data(ttl=3)
def load_data(table_name):
    try:
        response = supabase.table(table_name).select("*").execute()
        df = pd.DataFrame(response.data)
        return df
    except Exception:
        return pd.DataFrame()

def save_record(table_name, record_dict):
    try:
        supabase.table(table_name).insert(record_dict).execute()
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Database Save Error: {e}")
        return False

def update_record(table_name, record_dict, match_col, match_val):
    try:
        supabase.table(table_name).update(record_dict).eq(match_col, match_val).execute()
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Database Update Error: {e}")
        return False

# --- EMAIL CONFIGURATION FOR AUTO OTP ---
GMAIL_SENDER = "kavincivil112@gmail.com"
GMAIL_APP_PASSWORD = "spjo ppvc cfir ivns"

def send_email_otp(target_email, otp_code):
    subject = "🔑 Dry1 CRM — Admin 2FA Login Verification Code"
    body = f"Hello Admin,\n\nYour 2FA Login Security OTP Code for Dry1 Laundry & Saree Care CRM is: {otp_code}\n\nThis code is generated for secure access. Do not share this OTP with anyone.\n\nRegards,\nDry1 Care Security Team"
    
    email_message = f"From: {GMAIL_SENDER}\nTo: {target_email}\nSubject: {subject}\n\n{body}"
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_SENDER, target_email, email_message.encode('utf-8'))
        return True
    except Exception:
        return False

# --- HELPER FUNCTIONS & CONFIG ---
ADMIN_MOBILE = "8056166017"
ADMIN_EMAIL = "kavincivil112@gmail.com"
STORE_UPI_ID = "praveenvp888-2@okaxis"

SERVICES_LIST = [
    "Washing",
    "Ironing",
    "Saree Polish",
    "Steam & Starch Ironing",
    "Shoe Cleaning"
]

def mask_mobile(mobile_str):
    m_str = str(mobile_str).strip() if mobile_str else ""
    if len(m_str) >= 10:
        return "*******" + m_str[-3:]
    return m_str

def get_device_info():
    hostname = socket.gethostname()
    try:
        local_ip = socket.gethostbyname(hostname)
    except Exception:
        local_ip = "127.0.0.1"
    return hostname, local_ip

# --- SESSION STATES ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "user_role" not in st.session_state: st.session_state.user_role = None
if "otp_sent" not in st.session_state: st.session_state.otp_sent = False
if "generated_otp" not in st.session_state: st.session_state.generated_otp = None
if "session_id" not in st.session_state: st.session_state.session_id = None
if "last_updated_ready_id" not in st.session_state: st.session_state.last_updated_ready_id = None

# --- MODERN STYLING ---
STYLING = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    * { font-family: 'Plus Jakarta Sans', sans-serif !important; }
    
    header[data-testid="stHeader"] { display: none !important; }
    .stApp { background: #F1F5F9 !important; color: #0F172A !important; }
    
    [data-testid="stSidebarCollapseButton"] span,
    [data-testid="stSidebarNav"] span[data-testid="stHeaderActionElements"],
    button[aria-label="Collapse sidebar"] span {
        font-size: 0px !important;
        color: transparent !important;
    }
    
    [data-testid="stSidebar"] { 
        background: linear-gradient(180deg, #0F172A 0%, #1E293B 100%) !important; 
        border-right: 1px solid #334155; 
        padding: 16px 12px !important;
    }
    [data-testid="stSidebar"] * { color: #FFFFFF !important; }
    
    .sidebar-brand-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 18px 14px;
        text-align: center;
        margin-bottom: 22px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.25);
    }
    
    .role-badge {
        display: inline-block;
        background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
        color: #FFFFFF !important;
        font-weight: 700;
        font-size: 0.8rem;
        padding: 4px 14px;
        border-radius: 20px;
        margin-top: 8px;
    }
    
    [data-testid="stSidebar"] div[role="radiogroup"] > label {
        background: rgba(255, 255, 255, 0.04) !important;
        border: 1px solid rgba(255, 255, 255, 0.09) !important;
        border-radius: 12px !important;
        padding: 10px 14px !important;
        margin: 0 !important;
        min-height: 48px !important;
        display: flex !important;
        align-items: center !important;
        width: 100% !important;
        box-sizing: border-box !important;
        transition: all 0.25s ease-in-out !important;
        cursor: pointer !important;
    }
    
    [data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child { display: none !important; }
    [data-testid="stSidebar"] div[role="radiogroup"] > label:hover { background: rgba(37, 99, 235, 0.25) !important; border-color: #3B82F6 !important; }
    [data-testid="stSidebar"] div[role="radiogroup"] > label[data-checked="true"] {
        background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
        border-color: #60A5FA !important;
        box-shadow: 0 4px 14px rgba(37, 99, 235, 0.4) !important;
    }

    div[data-testid="stForm"] {
        background: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 24px !important;
        padding: 35px !important;
        box-shadow: 0 20px 50px rgba(15, 23, 42, 0.09) !important;
    }
    
    div[data-testid="stForm"] label p { 
        color: #334155 !important; 
        font-weight: 700 !important; 
        font-size: 0.88rem !important;
    }
    
    div[data-testid="stForm"] input, div[data-testid="stForm"] div[role="combobox"] {
        background-color: #F8FAFC !important;
        color: #0F172A !important;
        border: 1.5px solid #CBD5E1 !important;
        border-radius: 12px !important;
        padding: 10px 14px !important;
    }

    .stButton > button {
        background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        border-radius: 12px !important;
        padding: 12px 20px !important;
        border: none !important;
        width: 100% !important;
    }

    .alert-today { background:#FEF3C7; border-left:5px solid #F59E0B; padding:12px; border-radius:10px; margin-bottom:10px; color:#92400E; font-weight:600; }
    .alert-delay { background:#FFEDD5; border-left:5px solid #EA580C; padding:12px; border-radius:10px; margin-bottom:10px; color:#9A3412; font-weight:600; }
    .alert-red { background:#FEE2E2; border-left:5px solid #DC2626; padding:12px; border-radius:10px; margin-bottom:10px; color:#991B1B; font-weight:bold; }
    
    .wa-link-btn {
        display: block; width: 100%; background: #22C55E; color: white !important;
        text-align: center; padding: 10px; border-radius: 10px; font-weight: 700;
        text-decoration: none !important; box-shadow: 0 4px 14px rgba(34, 197, 94, 0.35); margin-top: 8px;
    }
</style>
"""
st.markdown(STYLING, unsafe_allow_html=True)

# --- REAL-TIME SESSION LOGOUT CHECK ---
if st.session_state.logged_in and st.session_state.session_id:
    sessions_df = load_data("active_sessions")
    if not sessions_df.empty:
        my_session = sessions_df[sessions_df["session_id"] == st.session_state.session_id]
        if not my_session.empty and my_session.iloc[0]["status"] == "Logged Out":
            st.session_state.logged_in = False
            st.session_state.session_id = None
            st.error("🚨 Your session has been remotely terminated by the Administrator.")
            st.rerun()

# ==================== LOGIN AUTHENTICATION ====================
if not st.session_state.logged_in:
    _, lcol, _ = st.columns([1, 1.3, 1])
    with lcol:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="text-align: center; margin-bottom: 25px;">
            <div style="background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%); width: 76px; height: 76px; border-radius: 22px; display: flex; align-items: center; justify-content: center; margin: 0 auto 16px auto; box-shadow: 0 12px 30px rgba(37, 99, 235, 0.38);">
                <span style="font-size: 2.5rem;">💧</span>
            </div>
            <h1 style="color: #0F172A; font-weight: 800; font-size: 1.8rem; margin: 0;">Dry1 Laundry & Saree Care CRM</h1>
            <p style="color: #64748B; font-size: 0.9rem; font-weight: 600; margin-top: 6px;">Role-Based Authentication Portal</p>
        </div>
        """, unsafe_allow_html=True)
        
        if not st.session_state.otp_sent:
            with st.form("login_form"):
                role = st.selectbox("Select Department Role", ["👑 Admin", "👩‍💼 Reception", "🛵 Delivery Boy", "📢 Marketing Team"])
                username = st.text_input("Username", placeholder="Enter username")
                password = st.text_input("Password", type="password", placeholder="••••••••")
                
                CREDENTIALS = {
                    "👑 Admin": ("admin", "dry1@123"),
                    "👩‍💼 Reception": ("reception", "recep123"),
                    "🛵 Delivery Boy": ("delivery", "deliv123"),
                    "📢 Marketing Team": ("marketing", "mkt123")
                }
                
                st.markdown("<br>", unsafe_allow_html=True)
                submit = st.form_submit_button("🔓 Authenticate & Access")
                
                if submit:
                    clean_username = username.strip().lower()
                    clean_password = password.strip()
                    
                    req_user, req_pass = CREDENTIALS[role]
                    if clean_username == req_user and clean_password == req_pass:
                        if role == "👑 Admin":
                            otp = str(random.randint(100000, 999999))
                            st.session_state.generated_otp = otp
                            st.session_state.otp_sent = True
                            
                            sent_status = send_email_otp(ADMIN_EMAIL, otp)
                            if not sent_status:
                                st.warning("⚠️ Email send failed. Check internet connectivity.")
                            st.rerun()
                        else:
                            dev_name, dev_ip = get_device_info()
                            sess_id = f"SESS-{random.randint(10000,99999)}"
                            st.session_state.session_id = sess_id
                            st.session_state.logged_in = True
                            st.session_state.user_role = role
                            
                            save_record("active_sessions", {
                                "session_id": sess_id, "device_name": dev_name, "ip_address": dev_ip,
                                "role": role, "login_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "status": "Active"
                            })
                            st.rerun()
                    else:
                        st.error("❌ Invalid Username or Password")
                        
        else:
            with st.container():
                st.subheader("🔐 Admin 2FA Verification")
                st.info(f"📧 An OTP has been sent to Admin Email: **{ADMIN_EMAIL}**")
                
                user_otp = st.text_input("Enter 6-Digit OTP Code", max_chars=6, placeholder="••••••")
                
                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    if st.button("Verify OTP & Login", type="primary"):
                        if user_otp.strip() == st.session_state.generated_otp:
                            dev_name, dev_ip = get_device_info()
                            sess_id = f"SESS-{random.randint(10000,99999)}"
                            st.session_state.session_id = sess_id
                            st.session_state.logged_in = True
                            st.session_state.user_role = "👑 Admin"
                            st.session_state.otp_sent = False
                            
                            save_record("active_sessions", {
                                "session_id": sess_id, "device_name": dev_name, "ip_address": dev_ip,
                                "role": "👑 Admin", "login_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "status": "Active"
                            })
                            st.rerun()
                        else:
                            st.error("❌ Invalid OTP Code")
                with col_b2:
                    if st.button("⬅️ Back"):
                        st.session_state.otp_sent = False
                        st.rerun()
    st.stop()

# ==================== MAIN DASHBOARD APPLICATION ====================

st.sidebar.markdown(f"""
<div class="sidebar-brand-card">
    <h2 style="margin:0; font-weight:800; font-size:1.25rem; color:#FFFFFF;">💧 Dry1 Laundry</h2>
    <p style="margin:3px 0 0 0; color:#94A3B8 !important; font-size:0.75rem;">Saree Care & CRM</p>
    <div class="role-badge">{st.session_state.user_role}</div>
</div>
""", unsafe_allow_html=True)

user_role = st.session_state.user_role

orders_df = load_data("orders")
customers_df = load_data("customers")
expenses_df = load_data("expenses")
leads_df = load_data("marketing_leads")
sessions_df = load_data("active_sessions")
vendors_df = load_data("vendor_purchases")
shift_logs_df = load_data("delivery_shift_logs")

# --- ROLE-BASED NAVIGATION MENU ---
menu_options = []
if user_role == "👑 Admin":
    menu_options = [
        "📊 Master Operations", 
        "📜 Orders History & Reports",
        "📈 Financial Analytics", 
        "🚚 Vendor & Chemical Purchases",
        "🛵 Delivery Shift Logs",
        "👤 Customer Master DB", 
        "💸 Store Expenses Entry", 
        "🔒 Active Device Control", 
        "🎯 Converted Leads"
    ]
elif user_role == "👩‍💼 Reception":
    menu_options = [
        "📝 New Billing & Order", 
        "📊 Operations Dashboard", 
        "📜 Monthly Orders History",
        "📈 Financial Analytics", 
        "💸 Store Expenses Entry", 
        "🎯 Converted Leads"
    ]
elif user_role == "🛵 Delivery Boy":
    menu_options = ["🛵 Delivery Portal", "📜 Delivery History"]
elif user_role == "📢 Marketing Team":
    menu_options = ["📢 Marketing Tracker"]

st.sidebar.markdown("<p style='font-size:0.75rem; font-weight:800; color:#94A3B8 !important; letter-spacing:1px; margin-bottom:10px; padding-left:4px;'>NAVIGATION MENU</p>", unsafe_allow_html=True)
nav_selection = st.sidebar.radio("", menu_options, label_visibility="collapsed")

st.sidebar.markdown("<br>", unsafe_allow_html=True)
if st.sidebar.button("🚪 Logout Session"):
    if st.session_state.session_id:
        update_record("active_sessions", {"status": "Logged Out"}, "session_id", st.session_state.session_id)
    st.session_state.logged_in = False
    st.session_state.session_id = None
    st.session_state.otp_sent = False
    st.rerun()

# --- PROMISED DATE & MARKETING FOLLOWUP ALERTS ---
today = datetime.now().date()

if user_role in ["👑 Admin", "👩‍💼 Reception", "🛵 Delivery Boy"] and not orders_df.empty:
    active_orders = orders_df[orders_df["order_status"] != "Delivered"].copy()
    if not active_orders.empty:
        st.markdown("### 🚨 Promised Delivery Alerts")
        for _, ord_row in active_orders.iterrows():
            try:
                prom_date = datetime.strptime(str(ord_row["promised_date"]), "%Y-%m-%d").date()
                diff = (today - prom_date).days
                
                if user_role == "🛵 Delivery Boy" and ord_row["customer_type"] != "Delivery":
                    continue
                
                disp_mob = ord_row['mobile'] if user_role in ["👑 Admin", "👩‍💼 Reception"] else mask_mobile(ord_row['mobile'])
                status_txt = f"Order ID: <b>{ord_row['order_id']}</b> | Customer: <b>{ord_row['customer_name']}</b> (📞 <b>{disp_mob}</b>) | Stage: <code>{ord_row['order_status']}</code>"
                
                if diff == 0:
                    st.markdown(f'<div class="alert-today">⚠️ <b>DUE TODAY:</b> {status_txt} | Promised Date: Today</div>', unsafe_allow_html=True)
                elif diff == 1:
                    st.markdown(f'<div class="alert-delay">🟧 <b>DELAYED (+1 Day):</b> {status_txt} | Promised Date: {ord_row["promised_date"]}</div>', unsafe_allow_html=True)
                elif diff >= 2:
                    st.markdown(f'<div class="alert-red">🚨 <b>RED ALERT (+{diff} Days Delay):</b> {status_txt} | Promised Date: {ord_row["promised_date"]}</div>', unsafe_allow_html=True)
                    
                    alert_wa_msg = f"🚨 *RED ALERT: Order Delivery Delayed*\n\nOrder ID: {ord_row['order_id']}\nCustomer: {ord_row['customer_name']} ({ord_row['mobile']})\nPromised Date: {ord_row['promised_date']} (+{diff} Days Delay)\nStage: {ord_row['order_status']}"
                    wa_admin_url = f"https://api.whatsapp.com/send?phone=91{ADMIN_MOBILE}&text={urllib.parse.quote(alert_wa_msg)}"
                    st.markdown(f'<a href="{wa_admin_url}" target="_blank" class="wa-link-btn" style="background:#DC2626 !important;">📲 Send Red Alert to Admin WhatsApp</a>', unsafe_allow_html=True)
            except Exception: pass

if user_role in ["👑 Admin", "📢 Marketing Team"] and not leads_df.empty:
    pending_leads = leads_df[leads_df["status"] == "Pending Followup"].copy()
    if not pending_leads.empty:
        st.markdown("### 📢 Marketing Follow-up Reminders & Alerts")
        for _, lead_row in pending_leads.iterrows():
            try:
                f_date = datetime.strptime(str(lead_row["followup_date"]), "%Y-%m-%d").date()
                f_diff = (today - f_date).days
                
                disp_lead_mob = lead_row['mobile'] if user_role in ["👑 Admin", "📢 Marketing Team"] else mask_mobile(lead_row['mobile'])
                lead_txt = f"Lead ID: <b>{lead_row['lead_id']}</b> | Client Name: <b>{lead_row['customer_name']}</b> (📞 <b>{disp_lead_mob}</b>) | Notes: <i>{lead_row['notes']}</i>"
                
                if f_diff == 0:
                    st.markdown(f'<div class="alert-today">📞 <b>FOLLOW-UP TODAY:</b> {lead_txt}</div>', unsafe_allow_html=True)
                elif f_diff == 1:
                    st.markdown(f'<div class="alert-delay">🟧 <b>FOLLOW-UP OVERDUE (+1 Day):</b> {lead_txt} | Scheduled Date: {lead_row["followup_date"]}</div>', unsafe_allow_html=True)
                elif f_diff >= 2:
                    st.markdown(f'<div class="alert-red">🚨 <b>RED ALERT: OVERDUE (+{f_diff} Days):</b> {lead_txt} | Scheduled Date: {lead_row["followup_date"]}</div>', unsafe_allow_html=True)
                    
                    mkt_wa_msg = f"🚨 *RED ALERT: Marketing Lead Overdue*\n\nLead ID: {lead_row['lead_id']}\nClient Name: {lead_row['customer_name']} ({lead_row['mobile']})\nScheduled Date: {lead_row['followup_date']} (+{f_diff} Days Overdue)"
                    wa_admin_mkt_url = f"https://api.whatsapp.com/send?phone=91{ADMIN_MOBILE}&text={urllib.parse.quote(mkt_wa_msg)}"
                    st.markdown(f'<a href="{wa_admin_mkt_url}" target="_blank" class="wa-link-btn" style="background:#DC2626 !important;">📲 Send Marketing Delay Alert to Admin WhatsApp</a>', unsafe_allow_html=True)
            except Exception: pass

# ==================== MODULE: DELIVERY SHIFT LOGS (ADMIN VIEW) ====================
if nav_selection == "🛵 Delivery Shift Logs":
    if user_role != "👑 Admin":
        st.error("🔒 Access Restricted: Delivery Shift Logs can only be accessed by Admin.")
    else:
        st.subheader("🛵 Delivery Boy EV Shift Logs & Odometer / Charge History")
        if not shift_logs_df.empty:
            st.dataframe(shift_logs_df, use_container_width=True)
        else:
            st.info("No EV shift entries logged yet.")

# ==================== MODULE: VENDOR & CHEMICAL PURCHASES ====================
elif nav_selection == "🚚 Vendor & Chemical Purchases":
    if user_role != "👑 Admin":
        st.error("🔒 Access Restricted: Vendor Details can only be accessed by Admin.")
    else:
        st.subheader("🚚 Vendor Details & Laundry Chemical Purchases")
        with st.container(border=True):
            vcol1, vcol2 = st.columns(2)
            with vcol1:
                v_name = st.text_input("Vendor Company Name", placeholder="e.g., ABC Chemical Industries")
                v_contact = st.text_input("Contact Person Name", placeholder="e.g., Suresh Kumar")
                v_mobile = st.text_input("Vendor Mobile Number", placeholder="10-digit number")
            with vcol2:
                v_pdate = st.date_input("Purchase Date", value=today)
                v_chem = st.text_input("Chemicals Purchased", placeholder="e.g., Stain Remover, Washing Powder")
                v_specs = st.text_input("Quantity / Package Specs", placeholder="e.g., 25 KG Drum / 5 Ltr Can")
            
            v_cost = st.number_input("Total Purchase Cost (₹)", min_value=0.0, step=100.0)
            
            if st.button("💾 Save Purchase & Auto-Add to Expenses", type="primary"):
                if not v_name or not v_chem or v_cost <= 0:
                    st.error("Please fill Vendor Name, Chemicals Purchased, and Valid Cost Amount.")
                else:
                    save_record("vendor_purchases", {
                        "purchase_date": str(v_pdate), "vendor_name": v_name,
                        "contact_person": v_contact, "mobile": str(v_mobile),
                        "chemicals_items": v_chem, "quantity_specs": v_specs, "total_cost": float(v_cost)
                    })
                    save_record("expenses", {
                        "date": str(v_pdate), "expense_category": "Chemical & Detergent",
                        "description": f"Chemical Purchase from {v_name} ({v_chem})", "amount": float(v_cost)
                    })
                    st.success(f"✅ Purchase Recorded & Auto-calculated into Expenses (₹{v_cost:,.2f})!")
                    st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("📋 Chemical Purchase & Vendor History")
        if not vendors_df.empty:
            st.dataframe(vendors_df, use_container_width=True)

# ==================== MODULE: DELIVERY PORTAL (WITH EV SHIFT TRACKING) ====================
elif nav_selection == "🛵 Delivery Portal":
    st.subheader("🛵 Delivery Portal — Assigned Pickups & EV Shift Tracker")
    d_tab1, d_tab2, d_tab3 = st.tabs(["📝 New Doorstep Pickup Billing", "📦 Active Delivery Orders", "⚡ EV Shift Tracking (Start / End Shift)"])
    
    with d_tab1:
        with st.form("delivery_pickup_form"):
            dmobile = st.text_input("Customer Mobile Number", placeholder="10-digit number")
            dcust_name = st.text_input("Customer Name")
            dservice = st.selectbox("Service Offered", SERVICES_LIST)
            
            dcol1, dcol2 = st.columns(2)
            with dcol1: ditems = st.number_input("Items Count", min_value=1, value=1)
            with dcol2: dweight_kg = st.number_input("Weight (KG)", min_value=0.0, step=0.5, value=0.0)
            
            dpromised_date = st.date_input("Promised Delivery Date")
            pcol1, pcol2 = st.columns(2)
            with pcol1: dtotal = st.number_input("Total Amount (₹)", min_value=0.0, step=50.0)
            with pcol2: dpaid = st.number_input("Paid Amount (₹)", min_value=0.0, step=50.0)
            
            dbal = max(0.0, dtotal - dpaid)
            st.write(f"**Pending Balance:** ₹{dbal}")

            dsubmit = st.form_submit_button("🚀 Confirm Pickup & Generate Receipt")
            if dsubmit:
                if not dmobile or not dcust_name or dtotal <= 0:
                    st.error("Please enter Mobile, Name, and Total Amount.")
                else:
                    new_id = f"DRY1-2026-{len(orders_df)+1:06d}"
                    curr_month_yr = today.strftime("%B %Y")
                    
                    save_record("customers", {
                        "mobile": str(dmobile), "name": dcust_name, "type": "Delivery",
                        "total_orders": 1, "total_spent": float(dtotal), "notes": "Created via Delivery Boy Portal"
                    })
                    save_record("orders", {
                        "order_id": new_id, "customer_name": dcust_name, "mobile": str(dmobile),
                        "customer_type": "Delivery", "service": dservice, "items_count": int(ditems),
                        "weight_kg": float(dweight_kg), "total_amount": float(dtotal), "paid_amount": float(dpaid),
                        "balance_amount": float(dbal), "payment_status": "PAID" if dbal == 0 else "PENDING",
                        "order_status": "Order Created", "promised_date": str(dpromised_date),
                        "created_date": str(today), "month_year": curr_month_yr,
                        "special_instructions": "Doorstep Pickup", "assigned_delivery": "Delivery Boy"
                    })
                    st.success(f"Pickup Order Created: {new_id}")
                    
                    dwa_msg = f"✨ *DRY1 Laundry & Saree Care Pickup Receipt*\n\nDear {dcust_name},\nYour pickup order is booked!\n\n📋 Order ID: {new_id}\n🧼 Service: {dservice}\n⚖️ Weight: {dweight_kg} KG\n💰 Total: ₹{dtotal:.2f}\n💵 Paid: ₹{dpaid:.2f}\n🔴 Balance: ₹{dbal:.2f}\n📅 Promised Date: {dpromised_date}\n\nThank you!"
                    dwa_url = f"https://api.whatsapp.com/send?phone=91{dmobile}&text={urllib.parse.quote(dwa_msg)}"
                    st.markdown(f'<a href="{dwa_url}" target="_blank" class="wa-link-btn">📲 Send WhatsApp Receipt</a>', unsafe_allow_html=True)

    with d_tab2:
        delivery_orders = orders_df[orders_df["customer_type"] == "Delivery"].copy() if not orders_df.empty else pd.DataFrame()
        if not delivery_orders.empty:
            for _, drow in delivery_orders.iterrows():
                with st.container():
                    st.markdown(f"""
                    <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:16px; padding:16px; margin-bottom:14px; box-shadow:0 4px 12px rgba(0,0,0,0.03);">
                        <div style="font-size:1.1rem; font-weight:800; color:#0F172A;">📦 Order #{drow['order_id']}</div>
                        <div style="color:#475569; font-size:0.9rem; margin-top:4px;">
                            👤 <b>Customer:</b> {drow['customer_name']}<br>
                            📱 <b>Mobile:</b> {mask_mobile(drow['mobile'])}<br>
                            🧼 <b>Service:</b> {drow['service']} ({drow['weight_kg']} KG)<br>
                            💰 <b>Balance Due:</b> ₹{drow['balance_amount']}<br>
                            📅 <b>Promised Date:</b> {drow['promised_date']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    with d_tab3:
        st.markdown("### ⚡ Electric Vehicle (EV) Shift Start & End Logging")
        driver_name = st.text_input("Delivery Boy Name", value="Delivery Staff")
        
        today_str = str(today)
        active_shift = pd.DataFrame()
        if not shift_logs_df.empty:
            active_shift = shift_logs_df[(shift_logs_df["driver_name"] == driver_name) & 
                                         (shift_logs_df["shift_date"] == today_str) & 
                                         (shift_logs_df["status"] == "Ongoing Shift")]

        col_s1, col_s2 = st.columns(2)
        
        with col_s1:
            st.markdown("#### 🟢 Start Shift (Morning / Entry)")
            if active_shift.empty:
                with st.form("start_shift_form"):
                    s_km = st.number_input("Start Odometer Reading (KM)", min_value=0.0, step=1.0)
                    s_bat = st.slider("Start Battery Charge (%)", min_value=0, max_value=100, value=100)
                    
                    if st.form_submit_button("🚀 Start Shift"):
                        save_record("delivery_shift_logs", {
                            "driver_name": driver_name,
                            "shift_date": today_str,
                            "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "start_km": float(s_km),
                            "start_battery_pct": int(s_bat),
                            "status": "Ongoing Shift"
                        })
                        st.success("🟢 Shift Started & Logged Successfully!")
                        st.rerun()
            else:
                s_row = active_shift.iloc[0]
                st.info(f"✅ **Shift Already Active!**\n\n* **Start Time:** {s_row['start_time']}\n* **Start KM:** {s_row['start_km']} KM\n* **Start Battery:** {s_row['start_battery_pct']}%")

        with col_s2:
            st.markdown("#### 🔴 End Shift (Evening / Exit)")
            if not active_shift.empty:
                s_row = active_shift.iloc[0]
                with st.form("end_shift_form"):
                    e_km = st.number_input("End Odometer Reading (KM)", min_value=float(s_row['start_km']), step=1.0)
                    e_bat = st.slider("End Battery Charge (%)", min_value=0, max_value=100, value=s_row['start_battery_pct'])
                    
                    if st.form_submit_button("🏁 End Shift & Calculate Run"):
                        tot_run = float(e_km) - float(s_row['start_km'])
                        update_record("delivery_shift_logs", {
                            "end_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "end_km": float(e_km),
                            "total_km": tot_run,
                            "end_battery_pct": int(e_bat),
                            "status": "Completed"
                        }, "id", int(s_row['id']))
                        
                        st.success(f"🏁 Shift Completed!\n\n🛵 **Total Distance Run:** {tot_run} KM\n🔋 **Battery Used:** {s_row['start_battery_pct'] - e_bat}%")
                        st.rerun()
            else:
                st.warning("Start your shift first to unlock End Shift logging.")

# ==================== MODULE: BILLING (RECEPTION ONLY) ====================
elif nav_selection == "📝 New Billing & Order":
    st.subheader("📝 New Order Creation & Billing")
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            mobile = st.text_input("Customer Mobile Number", placeholder="10-digit number")
            cust_name = st.text_input("Customer Name")
            cust_type = st.selectbox("Customer Type", ["Walk-in", "Delivery"])
        with col2:
            service = st.selectbox("Select Service Offered", SERVICES_LIST)
            bcol1, bcol2 = st.columns(2)
            with bcol1: items = st.number_input("Items Count", min_value=1, value=1)
            with bcol2: weight_kg = st.number_input("Weight (KG)", min_value=0.0, step=0.5, value=0.0)
            promised_date = st.date_input("Promised Delivery Date")
        
        pcol1, pcol2 = st.columns(2)
        with pcol1: total = st.number_input("Total Amount (₹)", min_value=0.0, step=50.0)
        with pcol2: paid = st.number_input("Paid Amount (₹)", min_value=0.0, step=50.0)
        
        bal = max(0.0, total - paid)
        st.write(f"**Pending Balance:** ₹{bal}")

        if st.button("🚀 Confirm Order & Save", type="primary"):
            if not mobile or not cust_name or total <= 0:
                st.error("Please enter Mobile, Name, and Total Amount.")
            else:
                new_id = f"DRY1-2026-{len(orders_df)+1:06d}"
                curr_month_yr = today.strftime("%B %Y")
                
                save_record("customers", {
                    "mobile": str(mobile), "name": cust_name, "type": cust_type,
                    "total_orders": 1, "total_spent": float(total), "notes": ""
                })
                save_record("orders", {
                    "order_id": new_id, "customer_name": cust_name, "mobile": str(mobile),
                    "customer_type": cust_type, "service": service, "items_count": int(items),
                    "weight_kg": float(weight_kg), "total_amount": float(total), "paid_amount": float(paid),
                    "balance_amount": float(bal), "payment_status": "PAID" if bal == 0 else "PENDING",
                    "order_status": "Order Created", "promised_date": str(promised_date),
                    "created_date": str(today), "month_year": curr_month_yr,
                    "special_instructions": "", "assigned_delivery": "Unassigned"
                })
                st.success(f"Order Registered: {new_id}")
                
                wa_msg = f"✨ *DRY1 Laundry & Saree Care Receipt*\n\nDear {cust_name},\nYour order has been booked!\n\n📋 Order ID: {new_id}\n🧼 Service: {service}\n⚖️ Weight: {weight_kg} KG\n💰 Total: ₹{total:.2f}\n💵 Paid: ₹{paid:.2f}\n🔴 Balance: ₹{bal:.2f}\n📅 Promised Date: {promised_date}\n\nThank you!"
                wa_url = f"https://api.whatsapp.com/send?phone=91{mobile}&text={urllib.parse.quote(wa_msg)}"
                st.markdown(f'<a href="{wa_url}" target="_blank" class="wa-link-btn">📲 Send WhatsApp Receipt</a>', unsafe_allow_html=True)

# ==================== MODULE: OPERATIONS ====================
elif nav_selection in ["📊 Operations Dashboard", "📊 Master Operations"]:
    st.subheader("📊 Operational Workflow")
    if not orders_df.empty:
        with st.container(border=True):
            sel_id = st.selectbox("Select Order ID", orders_df["order_id"].values)
            target = orders_df[orders_df["order_id"] == sel_id].iloc[0]
            
            cust_mob_disp = target['mobile'] if user_role == "👑 Admin" else mask_mobile(target['mobile'])
            st.write(f"**Customer:** {target['customer_name']} ({cust_mob_disp}) | **Status:** `{target['order_status']}`")
            
            WORKFLOW_STAGES = ["Order Created", "Ready", "Delivered"]
            curr_idx = WORKFLOW_STAGES.index(target["order_status"]) if target["order_status"] in WORKFLOW_STAGES else 0
            
            new_st = st.selectbox("Update Status Stage", WORKFLOW_STAGES, index=curr_idx)
            
            if st.button("Update Order Stage", type="primary"):
                update_record("orders", {"order_status": new_st}, "order_id", sel_id)
                st.session_state.last_updated_ready_id = sel_id if new_st == "Ready" else None
                st.success(f"Order {sel_id} updated to {new_st}!")
                st.rerun()

            current_order_status = target["order_status"]
            if current_order_status == "Ready" or st.session_state.last_updated_ready_id == sel_id:
                upi_qr = f"upi://pay?pa={STORE_UPI_ID}&am={target['balance_amount']}&tn={sel_id}"
                wa_ready = f"✨ *DRY1 Laundry Order Ready*\n\nDear {target['customer_name']},\nYour garments for Order *{sel_id}* are READY for collection/delivery! 🧼\n\n💵 Balance Due: ₹{target['balance_amount']}\n📲 Pay via UPI: {upi_qr}\n\nThank you for choosing Dry1 Care!"
                wa_ready_url = f"https://api.whatsapp.com/send?phone=91{target['mobile']}&text={urllib.parse.quote(wa_ready)}"
                st.markdown(f'<a href="{wa_ready_url}" target="_blank" class="wa-link-btn" style="background:#0284C7 !important;">📲 Send "Garments Ready" WhatsApp Confirmation</a>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        disp_df = orders_df.copy()
        if user_role != "👑 Admin":
            disp_df["mobile"] = disp_df["mobile"].apply(mask_mobile)
        st.dataframe(disp_df, use_container_width=True)

# ==================== MODULE: MONTHLY HISTORY ====================
elif nav_selection in ["📜 Monthly Orders History", "📜 Orders History & Reports", "📜 Delivery History"]:
    st.subheader("📜 Monthly Orders History & Records")
    if not orders_df.empty:
        history_df = orders_df.copy()
        available_months = history_df["month_year"].dropna().unique().tolist() if "month_year" in history_df.columns else []
        if not available_months: available_months = [today.strftime("%B %Y")]
            
        selected_month = st.selectbox("📅 Select Month Filter", ["All Months"] + available_months)
        if selected_month != "All Months" and "month_year" in history_df.columns:
            history_df = history_df[history_df["month_year"] == selected_month]
            
        if user_role == "🛵 Delivery Boy":
            history_df = history_df[history_df["customer_type"] == "Delivery"]
        if user_role != "👑 Admin":
            history_df["mobile"] = history_df["mobile"].apply(mask_mobile)
            
        st.dataframe(history_df, use_container_width=True)

# ==================== MODULE: FINANCIAL ANALYTICS & GRAPH ====================
elif nav_selection == "📈 Financial Analytics":
    if user_role not in ["👑 Admin", "👩‍💼 Reception"]:
        st.error("🔒 Access Restricted to Admin and Reception Only.")
    else:
        st.subheader("📈 Financial Analytics & Weekly Performance")
        rev = orders_df["total_amount"].sum() if not orders_df.empty else 0.0
        exp = expenses_df["amount"].sum() if not expenses_df.empty else 0.0
        profit = rev - exp
        
        pcol1, pcol2, pcol3 = st.columns(3)
        pcol1.metric("Total Revenue Booked", f"₹{rev:,.2f}")
        pcol2.metric("Total Store Expenses", f"₹{exp:,.2f}")
        pcol3.metric("Net Profit", f"₹{profit:,.2f}", delta=f"₹{profit:,.2f}")
        
        st.markdown("---")
        st.subheader("📊 Weekly Order Analytics (Walk-in vs Delivery)")
        if not orders_df.empty:
            orders_df['created_date'] = pd.to_datetime(orders_df['created_date'], errors='coerce')
            last_7_days = today - timedelta(days=7)
            recent_orders = orders_df[orders_df['created_date'] >= pd.to_datetime(last_7_days)].copy()
            
            if not recent_orders.empty:
                recent_orders['Day'] = recent_orders['created_date'].dt.strftime('%a (%d %b)')
                weekly_summary = recent_orders.groupby(['Day', 'customer_type'])['total_amount'].sum().unstack().fillna(0)
                st.bar_chart(weekly_summary)
            else:
                st.info("No orders in last 7 days to display graph.")

# ==================== MODULE: CUSTOMER MASTER DB ====================
elif nav_selection == "👤 Customer Master DB":
    if user_role != "👑 Admin":
        st.error("🔒 Access Restricted: Customer Master Database can only be accessed by Admin.")
    else:
        st.subheader("👤 Customer Master Database (Admin View)")
        type_filter = st.radio("🔍 Filter Customer Type:", ["All Customers", "Walk-in Only", "Delivery Only"], horizontal=True)
        
        filtered_cust = customers_df.copy() if not customers_df.empty else pd.DataFrame()
        if not filtered_cust.empty:
            if type_filter == "Walk-in Only":
                filtered_cust = filtered_cust[filtered_cust["type"] == "Walk-in"]
            elif type_filter == "Delivery Only":
                filtered_cust = filtered_cust[filtered_cust["type"] == "Delivery"]
            st.dataframe(filtered_cust, use_container_width=True)

# ==================== MODULE: STORE EXPENSES ENTRY ====================
elif nav_selection == "💸 Store Expenses Entry":
    if user_role not in ["👑 Admin", "👩‍💼 Reception"]:
        st.error("🔒 Access Restricted to Admin and Reception Only.")
    else:
        st.subheader("💸 Daily Store Expenses Entry")
        
        if user_role == "👩‍💼 Reception":
            EXPENSE_CATEGORIES = ["Chemical & Detergent", "Repair", "Covers", "Ironing", "Petrol", "Water"]
        else:
            EXPENSE_CATEGORIES = ["Shop Rent", "Staff Salary", "Electricity", "Chemical & Detergent", "Repair", "Covers", "Ironing", "Petrol", "Water", "Miscellaneous"]
            
        with st.container(border=True):
            col1, col2 = st.columns(2)
            with col1:
                exp_date = st.date_input("Expense Date", value=today)
                exp_cat = st.selectbox("Expense Category", EXPENSE_CATEGORIES)
            with col2:
                exp_amt = st.number_input("Expense Amount (₹)", min_value=0.0, step=50.0)
                exp_desc = st.text_input("Expense Description / Notes")
                
            if st.button("➕ Add Expense Entry", type="primary"):
                if exp_amt <= 0:
                    st.error("Please enter a valid expense amount.")
                else:
                    save_record("expenses", {
                        "date": str(exp_date), "expense_category": exp_cat,
                        "description": exp_desc, "amount": float(exp_amt)
                    })
                    st.success("Store Expense Recorded Successfully!")
                    st.rerun()

# ==================== MODULE: ACTIVE DEVICE CONTROL ====================
elif nav_selection == "🔒 Active Device Control":
    if user_role != "👑 Admin":
        st.error("🔒 Access Restricted to Admin Only.")
    else:
        st.subheader("🔒 Active Device & Remote Session Manager")
        if not sessions_df.empty:
            active_sess = sessions_df[sessions_df["status"] == "Active"]
            st.dataframe(active_sess[["session_id", "device_name", "ip_address", "role", "login_time", "status"]], use_container_width=True)
            
            term_id = st.selectbox("Select Session ID to Terminate", active_sess["session_id"].values if not active_sess.empty else ["-- None --"])
            if term_id != "-- None --" and st.button("🔴 Force Logout Selected Device", type="primary"):
                update_record("active_sessions", {"status": "Logged Out"}, "session_id", term_id)
                st.success("Session Terminated!")
                st.rerun()

# ==================== MODULE: MARKETING TRACKER ====================
elif nav_selection == "📢 Marketing Tracker":
    st.subheader("📢 Marketing Lead Tracker & Reminders")
    with st.container(border=True):
        mcol1, mcol2 = st.columns(2)
        with mcol1:
            lead_name = st.text_input("Lead / Client Name")
            lead_mobile = st.text_input("Lead Mobile Number")
        with mcol2:
            follow_date = st.date_input("Follow-up Call Date")
            lead_notes = st.text_area("Call Notes / Discussion")
            
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("➕ Schedule Follow-up Call"):
                if lead_name and lead_mobile:
                    save_record("marketing_leads", {
                        "lead_id": f"LEAD-{len(leads_df)+1:04d}", "customer_name": lead_name,
                        "mobile": str(lead_mobile), "followup_date": str(follow_date),
                        "status": "Pending Followup", "notes": lead_notes
                    })
                    st.success("Follow-up Scheduled!")
                    st.rerun()
                    
        with btn_col2:
            if st.button("🎯 Converted Successfully", type="primary"):
                if lead_name and lead_mobile:
                    save_record("marketing_leads", {
                        "lead_id": f"LEAD-{len(leads_df)+1:04d}", "customer_name": lead_name,
                        "mobile": str(lead_mobile), "followup_date": str(today),
                        "status": "Converted", "notes": lead_notes if lead_notes else "Direct Conversion"
                    })
                    st.success("🎉 Client Converted Successfully!")
                    st.rerun()

    m_disp_df = leads_df.copy() if not leads_df.empty else pd.DataFrame()
    if not m_disp_df.empty:
        if user_role != "👑 Admin":
            m_disp_df["mobile"] = m_disp_df["mobile"].apply(mask_mobile)
        st.dataframe(m_disp_df, use_container_width=True)

# ==================== MODULE: CONVERTED LEADS ====================
elif nav_selection == "🎯 Converted Leads":
    st.subheader("🎯 Marketing Converted Leads")
    if not leads_df.empty:
        converted_leads = leads_df[leads_df["status"] == "Converted"].copy()
        if not converted_leads.empty:
            if user_role != "👑 Admin":
                converted_leads["mobile"] = converted_leads["mobile"].apply(mask_mobile)
            st.dataframe(converted_leads[["lead_id", "customer_name", "mobile", "followup_date", "notes"]], use_container_width=True)
