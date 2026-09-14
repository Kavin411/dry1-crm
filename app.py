import streamlit as st
import pandas as pd
import os
import io
import socket
import random
import urllib.parse
import webbrowser
from datetime import datetime
from PIL import Image, ImageDraw
from cryptography.fernet import Fernet

# Page Configuration
st.set_page_config(
    page_title="Dry1 — Multi-Role Laundry CRM", 
    layout="wide", 
    page_icon="💧",
    initial_sidebar_state="auto"
)

# --- ENCRYPTION SETUP ---
KEY_FILE = "secret.key"

@st.cache_resource
def get_cached_cipher():
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as kf: 
            kf.write(key)
    else:
        with open(KEY_FILE, "rb") as kf: 
            key = kf.read()
    return Fernet(key)

cipher = get_cached_cipher()

def load_encrypted_csv(filepath, dtype=None):
    if not os.path.exists(filepath): 
        return pd.DataFrame()
    try:
        with open(filepath, "rb") as f: 
            data = f.read()
        if not data: 
            return pd.DataFrame()
        return pd.read_csv(io.BytesIO(cipher.decrypt(data)), dtype=dtype)
    except Exception: 
        return pd.DataFrame()

def save_encrypted_csv(df, filepath):
    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    with open(filepath, "wb") as f: 
        f.write(cipher.encrypt(buf.getvalue()))

# --- DATA FILE PATHS ---
CUSTOMERS_FILE = "customers.csv"
ORDERS_FILE = "orders.csv"
EXPENSES_FILE = "expenses.csv"
LEADS_FILE = "marketing_leads.csv"
SESSIONS_FILE = "active_sessions.csv"

def init_db():
    if not os.path.exists(CUSTOMERS_FILE):
        save_encrypted_csv(pd.DataFrame(columns=["Mobile", "Name", "Type", "Total Orders", "Total Spent", "Notes"]), CUSTOMERS_FILE)
    if not os.path.exists(ORDERS_FILE):
        save_encrypted_csv(pd.DataFrame(columns=[
            "Order ID", "Customer Name", "Mobile", "Customer Type", "Service", "Items Count", "Weight (KG)", 
            "Total Amount", "Paid Amount", "Balance Amount", "Payment Status", 
            "Order Status", "Promised Date", "Created Date", "Month-Year", "Special Instructions", "Assigned Delivery"
        ]), ORDERS_FILE)
    if not os.path.exists(EXPENSES_FILE):
        save_encrypted_csv(pd.DataFrame(columns=["Date", "Expense Category", "Description", "Amount"]), EXPENSES_FILE)
    if not os.path.exists(LEADS_FILE):
        save_encrypted_csv(pd.DataFrame(columns=["Lead ID", "Customer Name", "Mobile", "Followup Date", "Status", "Notes"]), LEADS_FILE)
    if not os.path.exists(SESSIONS_FILE):
        save_encrypted_csv(pd.DataFrame(columns=["Session ID", "Device Name", "IP Address", "Role", "Login Time", "Status"]), SESSIONS_FILE)

init_db()

# --- HELPER FUNCTIONS ---
ADMIN_MOBILE = "8056166017"
STORE_UPI_ID = "praveenvp888-2@okaxis"

def mask_mobile(mobile_str):
    m_str = str(mobile_str).strip()
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

# --- MODERN STYLING ---
STYLING = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    * { font-family: 'Plus Jakarta Sans', sans-serif !important; }
    
    header[data-testid="stHeader"] { display: none !important; }
    .stApp { background: #F1F5F9 !important; color: #0F172A !important; }
    
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

    button[aria-label="Show password"], button[aria-label="Hide password"], div[data-testid="stTextInput"] button {
        display: none !important;
        visibility: hidden !important;
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
        text-align: center; padding: 12px; border-radius: 10px; font-weight: 700;
        text-decoration: none !important; box-shadow: 0 4px 14px rgba(34, 197, 94, 0.35); margin-top: 10px;
    }
</style>
"""
st.markdown(STYLING, unsafe_allow_html=True)

# --- REAL-TIME SESSION LOGOUT CHECK ---
if st.session_state.logged_in and st.session_state.session_id:
    sessions_df = load_encrypted_csv(SESSIONS_FILE)
    if not sessions_df.empty:
        my_session = sessions_df[sessions_df["Session ID"] == st.session_state.session_id]
        if not my_session.empty and my_session.iloc[0]["Status"] == "Logged Out":
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
            <h1 style="color: #0F172A; font-weight: 800; font-size: 2rem; margin: 0;">Dry1 Care CRM</h1>
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
                    req_user, req_pass = CREDENTIALS[role]
                    if username == req_user and password == req_pass:
                        if role == "👑 Admin":
                            otp = str(random.randint(100000, 999999))
                            st.session_state.generated_otp = otp
                            st.session_state.otp_sent = True
                            
                            wa_otp_msg = f"🔑 Your Dry1 CRM Admin 2FA Login OTP is: *{otp}*"
                            wa_url = f"https://api.whatsapp.com/send?phone=91{ADMIN_MOBILE}&text={urllib.parse.quote(wa_otp_msg)}"
                            webbrowser.open(wa_url)
                            st.rerun()
                        else:
                            dev_name, dev_ip = get_device_info()
                            sess_id = f"SESS-{random.randint(10000,99999)}"
                            st.session_state.session_id = sess_id
                            st.session_state.logged_in = True
                            st.session_state.user_role = role
                            
                            sessions_df = load_encrypted_csv(SESSIONS_FILE)
                            new_sess = pd.DataFrame([{
                                "Session ID": sess_id, "Device Name": dev_name, "IP Address": dev_ip,
                                "Role": role, "Login Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Status": "Active"
                            }])
                            save_encrypted_csv(pd.concat([sessions_df, new_sess], ignore_index=True), SESSIONS_FILE)
                            st.rerun()
                    else:
                        st.error("❌ Invalid Username or Password")
                        
        else:
            with st.container():
                st.subheader("🔐 Admin 2FA Verification")
                st.info(f"📱 An OTP has been sent to **+91 ******{ADMIN_MOBILE[-4:]}** via WhatsApp.")
                
                user_otp = st.text_input("Enter 6-Digit OTP Code", max_chars=6, placeholder="••••••")
                
                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    if st.button("Verify OTP & Login"):
                        if user_otp == st.session_state.generated_otp:
                            dev_name, dev_ip = get_device_info()
                            sess_id = f"SESS-{random.randint(10000,99999)}"
                            st.session_state.session_id = sess_id
                            st.session_state.logged_in = True
                            st.session_state.user_role = "👑 Admin"
                            st.session_state.otp_sent = False
                            
                            sessions_df = load_encrypted_csv(SESSIONS_FILE)
                            new_sess = pd.DataFrame([{
                                "Session ID": sess_id, "Device Name": dev_name, "IP Address": dev_ip,
                                "Role": "👑 Admin", "Login Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Status": "Active"
                            }])
                            save_encrypted_csv(pd.concat([sessions_df, new_sess], ignore_index=True), SESSIONS_FILE)
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
    <h2 style="margin:0; font-weight:800; font-size:1.35rem; color:#FFFFFF;">💧 Dry1 Care</h2>
    <p style="margin:3px 0 0 0; color:#94A3B8 !important; font-size:0.75rem;">Saree Care & Laundry CRM</p>
    <div class="role-badge">{st.session_state.user_role}</div>
</div>
""", unsafe_allow_html=True)

user_role = st.session_state.user_role
orders_df = load_encrypted_csv(ORDERS_FILE, dtype={"Mobile": str})
customers_df = load_encrypted_csv(CUSTOMERS_FILE, dtype={"Mobile": str})
expenses_df = load_encrypted_csv(EXPENSES_FILE)
leads_df = load_encrypted_csv(LEADS_FILE, dtype={"Mobile": str})
sessions_df = load_encrypted_csv(SESSIONS_FILE)

# --- ROLE-BASED NAVIGATION MENU ---
menu_options = []
if user_role == "👑 Admin":
    menu_options = [
        "📊 Master Operations", 
        "📜 Orders History & Reports",
        "📈 Financial Analytics", 
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
        sessions_df = load_encrypted_csv(SESSIONS_FILE)
        if not sessions_df.empty:
            idx_list = sessions_df[sessions_df["Session ID"] == st.session_state.session_id].index
            if len(idx_list) > 0:
                sessions_df.at[idx_list[0], "Status"] = "Logged Out"
                save_encrypted_csv(sessions_df, SESSIONS_FILE)
    st.session_state.logged_in = False
    st.session_state.session_id = None
    st.session_state.otp_sent = False
    st.rerun()

# --- PROMISED DATE ALERTS ---
today = datetime.now().date()

if user_role in ["👑 Admin", "👩‍💼 Reception", "🛵 Delivery Boy"] and not orders_df.empty:
    active_orders = orders_df[orders_df["Order Status"] != "Delivered"].copy()
    if not active_orders.empty:
        st.markdown("### 🚨 Promised Delivery Alerts")
        for _, ord_row in active_orders.iterrows():
            try:
                prom_date = datetime.strptime(str(ord_row["Promised Date"]), "%Y-%m-%d").date()
                diff = (today - prom_date).days
                
                if user_role == "🛵 Delivery Boy" and ord_row["Customer Type"] != "Delivery":
                    continue
                    
                status_txt = f"Order ID: <b>{ord_row['Order ID']}</b> | Customer: <b>{ord_row['Customer Name']}</b> ({mask_mobile(ord_row['Mobile']) if user_role != '👑 Admin' else ord_row['Mobile']}) | Stage: <code>{ord_row['Order Status']}</code>"
                
                if diff == 0:
                    st.markdown(f'<div class="alert-today">⚠️ <b>DUE TODAY:</b> {status_txt} | Promised Date: Today</div>', unsafe_allow_html=True)
                elif diff == 1:
                    st.markdown(f'<div class="alert-delay">🟧 <b>DELAYED (+1 Day):</b> {status_txt} | Promised Date: {ord_row["Promised Date"]}</div>', unsafe_allow_html=True)
                elif diff >= 2:
                    st.markdown(f'<div class="alert-red">🚨 <b>RED ALERT (+{diff} Days Delay):</b> {status_txt} | Promised Date: {ord_row["Promised Date"]}</div>', unsafe_allow_html=True)
            except Exception: pass

# ==================== MODULE: DELIVERY PORTAL (WITH DIRECT MOBILE BILLING) ====================
if nav_selection == "🛵 Delivery Portal":
    st.subheader("🛵 Delivery Portal — Assigned Pickups & Direct Mobile Billing")
    
    # --- TAB SWITCH FOR DELIVERY BOY ---
    d_tab1, d_tab2 = st.tabs(["📝 New Doorstep Pickup Billing", "📦 Active Delivery Orders"])
    
    # TAB 1: DELIVERY BOY MOBILE BILLING FORM
    with d_tab1:
        st.markdown("##### 📝 Create Doorstep Pickup Order")
        with st.form("delivery_pickup_form"):
            dmobile = st.text_input("Customer Mobile Number", placeholder="10-digit number")
            dcust_name = st.text_input("Customer Name")
            dservice = st.selectbox("Service Offered", ["Saree Roll Polish Ironing", "Shoe Cleaning Service", "Stain Removal Service", "Washing Machines", "Steam & Starch Ironing"])
            
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
                    
                    # Save Customer Profile
                    existing_cust = customers_df[customers_df["Mobile"] == str(dmobile)] if not customers_df.empty else pd.DataFrame()
                    if existing_cust.empty:
                        new_cust = pd.DataFrame([{
                            "Mobile": str(dmobile), "Name": dcust_name, "Type": "Delivery",
                            "Total Orders": 1, "Total Spent": dtotal, "Notes": "Created via Delivery Boy Portal"
                        }])
                        customers_df = pd.concat([customers_df, new_cust], ignore_index=True)
                    else:
                        c_idx = customers_df[customers_df["Mobile"] == str(dmobile)].index[0]
                        customers_df.at[c_idx, "Name"] = dcust_name
                        customers_df.at[c_idx, "Type"] = "Delivery"
                        customers_df.at[c_idx, "Total Orders"] = int(customers_df.at[c_idx, "Total Orders"]) + 1
                        customers_df.at[c_idx, "Total Spent"] = float(customers_df.at[c_idx, "Total Spent"]) + dtotal
                    save_encrypted_csv(customers_df, CUSTOMERS_FILE)

                    # Save Order
                    new_ord = pd.DataFrame([{
                        "Order ID": new_id, "Customer Name": dcust_name, "Mobile": str(dmobile),
                        "Customer Type": "Delivery", "Service": dservice, "Items Count": ditems, "Weight (KG)": dweight_kg,
                        "Total Amount": dtotal, "Paid Amount": dpaid, "Balance Amount": dbal,
                        "Payment Status": "PAID" if dbal == 0 else "PENDING", "Order Status": "Order Created",
                        "Promised Date": str(dpromised_date), "Created Date": str(today), "Month-Year": curr_month_yr,
                        "Special Instructions": "Doorstep Pickup", "Assigned Delivery": "Delivery Boy"
                    }])
                    orders_df = pd.concat([orders_df, new_ord], ignore_index=True)
                    save_encrypted_csv(orders_df, ORDERS_FILE)
                    st.success(f"Pickup Order Created: {new_id}")
                    
                    dwa_msg = f"✨ *DRY1 Care Doorstep Pickup Receipt*\n\nDear {dcust_name},\nYour pickup order is booked!\n\n📋 Order ID: {new_id}\n🧼 Service: {dservice}\n⚖️ Weight: {dweight_kg} KG\n💰 Total: ₹{dtotal:.2f}\n💵 Paid: ₹{dpaid:.2f}\n🔴 Balance: ₹{dbal:.2f}\n📅 Promised Date: {dpromised_date}\n\nThank you!"
                    dwa_url = f"https://api.whatsapp.com/send?phone=91{dmobile}&text={urllib.parse.quote(dwa_msg)}"
                    st.markdown(f'<a href="{dwa_url}" target="_blank" class="wa-link-btn">📲 Send WhatsApp Receipt to Customer</a>', unsafe_allow_html=True)

    # TAB 2: ACTIVE DELIVERY ORDERS
    with d_tab2:
        delivery_orders = orders_df[orders_df["Customer Type"] == "Delivery"].copy()
        if not delivery_orders.empty:
            for _, drow in delivery_orders.iterrows():
                with st.container():
                    st.markdown(f"""
                    <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:16px; padding:16px; margin-bottom:14px; box-shadow:0 4px 12px rgba(0,0,0,0.03);">
                        <div style="font-size:1.1rem; font-weight:800; color:#0F172A;">📦 Order #{drow['Order ID']}</div>
                        <div style="color:#475569; font-size:0.9rem; margin-top:4px;">
                            👤 <b>Customer:</b> {drow['Customer Name']}<br>
                            📱 <b>Mobile:</b> {mask_mobile(drow['Mobile'])}<br>
                            🧼 <b>Service:</b> {drow['Service']} ({drow['Weight (KG)']} KG)<br>
                            💰 <b>Balance Due:</b> ₹{drow['Balance Amount']}<br>
                            📅 <b>Promised Date:</b> {drow['Promised Date']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    wa_call_msg = f"Hello {drow['Customer Name']}, I am reaching out from Dry1 Care regarding your order {drow['Order ID']} delivery."
                    wa_link = f"https://api.whatsapp.com/send?phone=91{drow['Mobile']}&text={urllib.parse.quote(wa_call_msg)}"
                    st.markdown(f'<a href="{wa_link}" target="_blank" class="wa-link-btn">💬 Chat / Contact Customer</a>', unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)
        else: 
            st.info("No active delivery orders assigned for today.")

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
            service = st.selectbox("Select Service Offered", ["Saree Roll Polish Ironing", "Shoe Cleaning Service", "Stain Removal Service", "Washing Machines", "Steam & Starch Ironing"])
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
                
                existing_cust = customers_df[customers_df["Mobile"] == str(mobile)] if not customers_df.empty else pd.DataFrame()
                if existing_cust.empty:
                    new_cust = pd.DataFrame([{
                        "Mobile": str(mobile), "Name": cust_name, "Type": cust_type,
                        "Total Orders": 1, "Total Spent": total, "Notes": ""
                    }])
                    customers_df = pd.concat([customers_df, new_cust], ignore_index=True)
                else:
                    c_idx = customers_df[customers_df["Mobile"] == str(mobile)].index[0]
                    customers_df.at[c_idx, "Name"] = cust_name
                    customers_df.at[c_idx, "Type"] = cust_type
                    customers_df.at[c_idx, "Total Orders"] = int(customers_df.at[c_idx, "Total Orders"]) + 1
                    customers_df.at[c_idx, "Total Spent"] = float(customers_df.at[c_idx, "Total Spent"]) + total
                save_encrypted_csv(customers_df, CUSTOMERS_FILE)

                new_ord = pd.DataFrame([{
                    "Order ID": new_id, "Customer Name": cust_name, "Mobile": str(mobile),
                    "Customer Type": cust_type, "Service": service, "Items Count": items, "Weight (KG)": weight_kg,
                    "Total Amount": total, "Paid Amount": paid, "Balance Amount": bal,
                    "Payment Status": "PAID" if bal == 0 else "PENDING", "Order Status": "Order Created",
                    "Promised Date": str(promised_date), "Created Date": str(today), "Month-Year": curr_month_yr,
                    "Special Instructions": "", "Assigned Delivery": "Unassigned"
                }])
                orders_df = pd.concat([orders_df, new_ord], ignore_index=True)
                save_encrypted_csv(orders_df, ORDERS_FILE)
                st.success(f"Order Registered: {new_id}")
                
                wa_msg = f"✨ *DRY1 Care Receipt*\n\nDear {cust_name},\nYour order has been booked!\n\n📋 Order ID: {new_id}\n🧼 Service: {service}\n⚖️ Weight: {weight_kg} KG\n💰 Total: ₹{total:.2f}\n💵 Paid: ₹{paid:.2f}\n🔴 Balance: ₹{bal:.2f}\n📅 Promised Date: {promised_date}\n\nThank you!"
                wa_url = f"https://api.whatsapp.com/send?phone=91{mobile}&text={urllib.parse.quote(wa_msg)}"
                st.markdown(f'<a href="{wa_url}" target="_blank" class="wa-link-btn">📲 Send WhatsApp Receipt</a>', unsafe_allow_html=True)

# ==================== MODULE: OPERATIONS ====================
elif nav_selection in ["📊 Operations Dashboard", "📊 Master Operations"]:
    st.subheader("📊 Operational Workflow")
    if not orders_df.empty:
        with st.container(border=True):
            sel_id = st.selectbox("Select Order ID", orders_df["Order ID"].values)
            target = orders_df[orders_df["Order ID"] == sel_id].iloc[0]
            
            cust_mob_disp = target['Mobile'] if user_role == "👑 Admin" else mask_mobile(target['Mobile'])
            st.write(f"**Customer:** {target['Customer Name']} ({cust_mob_disp}) | **Status:** `{target['Order Status']}`")
            
            WORKFLOW_STAGES = ["Order Created", "Ready", "Delivered"]
            curr_idx = WORKFLOW_STAGES.index(target["Order Status"]) if target["Order Status"] in WORKFLOW_STAGES else 0
            
            new_st = st.selectbox("Update Status Stage", WORKFLOW_STAGES, index=curr_idx)
            
            if st.button("Update Order Stage"):
                idx = orders_df[orders_df["Order ID"] == sel_id].index[0]
                orders_df.at[idx, "Order Status"] = new_st
                save_encrypted_csv(orders_df, ORDERS_FILE)
                st.success(f"Order {sel_id} updated to {new_st}!")
                
                if new_st == "Ready":
                    upi_qr = f"upi://pay?pa={STORE_UPI_ID}&am={target['Balance Amount']}&tn={sel_id}"
                    wa_ready = f"✨ *DRY1 Order Ready for Delivery*\n\nDear {target['Customer Name']},\nYour garments for Order {sel_id} are READY! 🧼\n\nBalance Due: ₹{target['Balance Amount']}\nPay via UPI: {upi_qr}\nOr pay upon pickup/delivery."
                    wa_url = f"https://api.whatsapp.com/send?phone=91{target['Mobile']}&text={urllib.parse.quote(wa_ready)}"
                    st.markdown(f'<a href="{wa_url}" target="_blank" class="wa-link-btn">📲 Send "Garments Ready" WhatsApp Message</a>', unsafe_allow_html=True)
                elif new_st == "Delivered":
                    wa_del = f"✨ *DRY1 Order Delivered*\n\nDear {target['Customer Name']},\nYour Order {sel_id} has been successfully delivered. Thank you for choosing Dry1 Care!"
                    wa_url = f"https://api.whatsapp.com/send?phone=91{target['Mobile']}&text={urllib.parse.quote(wa_del)}"
                    st.markdown(f'<a href="{wa_url}" target="_blank" class="wa-link-btn">📲 Send "Delivered" Confirmation Message</a>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        disp_df = orders_df.copy()
        if user_role != "👑 Admin":
            disp_df["Mobile"] = disp_df["Mobile"].apply(mask_mobile)
        st.dataframe(disp_df, use_container_width=True)

# ==================== MODULE: MONTHLY HISTORY ====================
elif nav_selection in ["📜 Monthly Orders History", "📜 Orders History & Reports", "📜 Delivery History"]:
    st.subheader("📜 Monthly Orders History & Records")
    if not orders_df.empty:
        history_df = orders_df.copy()
        available_months = history_df["Month-Year"].dropna().unique().tolist() if "Month-Year" in history_df.columns else []
        if not available_months: available_months = [today.strftime("%B %Y")]
            
        selected_month = st.selectbox("📅 Select Month Filter", ["All Months"] + available_months)
        if selected_month != "All Months" and "Month-Year" in history_df.columns:
            history_df = history_df[history_df["Month-Year"] == selected_month]
            
        if user_role == "🛵 Delivery Boy":
            history_df = history_df[history_df["Customer Type"] == "Delivery"]
        if user_role != "👑 Admin":
            history_df["Mobile"] = history_df["Mobile"].apply(mask_mobile)
            
        st.write(f"Showing `{len(history_df)}` records for **{selected_month}**")
        st.dataframe(history_df, use_container_width=True)
    else:
        st.info("No historical order records found.")

# ==================== MODULE: FINANCIAL ANALYTICS ====================
elif nav_selection == "📈 Financial Analytics":
    if user_role not in ["👑 Admin", "👩‍💼 Reception"]:
        st.error("🔒 Access Restricted to Admin and Reception Only.")
    else:
        st.subheader("📈 Financial Analytics & Monthly Profit Reports")
        rev = orders_df["Total Amount"].sum() if not orders_df.empty else 0.0
        exp = expenses_df["Amount"].sum() if not expenses_df.empty else 0.0
        profit = rev - exp
        
        pcol1, pcol2, pcol3 = st.columns(3)
        pcol1.metric("Total Revenue Booked", f"₹{rev:,.2f}")
        pcol2.metric("Total Store Expenses", f"₹{exp:,.2f}")
        pcol3.metric("Net Profit", f"₹{profit:,.2f}", delta=f"₹{profit:,.2f}")
        
        st.markdown("---")
        st.subheader("📋 Breakdown of Recorded Expenses")
        if not expenses_df.empty:
            st.dataframe(expenses_df, use_container_width=True)
        else:
            st.info("No expense entries recorded yet.")

# ==================== MODULE: CUSTOMER MASTER DB ====================
elif nav_selection == "👤 Customer Master DB":
    if user_role != "👑 Admin":
        st.error("🔒 Access Restricted: Customer Master Database can only be accessed by Admin.")
    else:
        st.subheader("👤 Customer Master Database (Admin Full View)")
        st.dataframe(customers_df, use_container_width=True)

# ==================== MODULE: STORE EXPENSES ENTRY ====================
elif nav_selection == "💸 Store Expenses Entry":
    if user_role not in ["👑 Admin", "👩‍💼 Reception"]:
        st.error("🔒 Access Restricted to Admin and Reception Only.")
    else:
        st.subheader("💸 Daily Store Expenses Entry")
        with st.container(border=True):
            col1, col2 = st.columns(2)
            with col1:
                exp_date = st.date_input("Expense Date", value=today)
                exp_cat = st.selectbox("Expense Category", ["Shop Rent", "Chemicals & Detergents", "Staff Salary", "Electricity / Utilities", "Equipment Repair", "Miscellaneous"])
            with col2:
                exp_amt = st.number_input("Expense Amount (₹)", min_value=0.0, step=100.0)
                exp_desc = st.text_input("Expense Description / Notes")
                
            if st.button("➕ Add Expense Entry", type="primary"):
                if exp_amt <= 0:
                    st.error("Please enter a valid expense amount.")
                else:
                    new_exp = pd.DataFrame([{
                        "Date": str(exp_date),
                        "Expense Category": exp_cat,
                        "Description": exp_desc,
                        "Amount": exp_amt
                    }])
                    expenses_df = pd.concat([expenses_df, new_exp], ignore_index=True)
                    save_encrypted_csv(expenses_df, EXPENSES_FILE)
                    st.success("Store Expense Recorded Successfully!")
                    st.rerun()

# ==================== MODULE: ACTIVE DEVICE CONTROL ====================
elif nav_selection == "🔒 Active Device Control":
    if user_role != "👑 Admin":
        st.error("🔒 Access Restricted to Admin Only.")
    else:
        st.subheader("🔒 Active Device & Remote Session Manager")
        if not sessions_df.empty:
            active_sess = sessions_df[sessions_df["Status"] == "Active"]
            st.write(f"**Total Active Connected Systems:** `{len(active_sess)}`")
            st.dataframe(active_sess[["Session ID", "Device Name", "IP Address", "Role", "Login Time", "Status"]], use_container_width=True)
            
            st.markdown("---")
            st.subheader("🔴 Terminate / Remote Logout Device")
            term_id = st.selectbox("Select Active Session ID to Terminate", active_sess["Session ID"].values if not active_sess.empty else ["-- None --"])
            if term_id != "-- None --":
                if st.button("🔴 Force Logout Selected Device", type="primary"):
                    term_idx = sessions_df[sessions_df["Session ID"] == term_id].index[0]
                    sessions_df.at[term_idx, "Status"] = "Logged Out"
                    save_encrypted_csv(sessions_df, SESSIONS_FILE)
                    st.success(f"Device Session {term_id} terminated successfully!")
                    st.rerun()
        else:
            st.info("No session logs recorded yet.")

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
            
        if st.button("➕ Schedule Follow-up Call"):
            new_lead = pd.DataFrame([{
                "Lead ID": f"LEAD-{len(leads_df)+1:04d}", "Customer Name": lead_name,
                "Mobile": str(lead_mobile), "Followup Date": str(follow_date),
                "Status": "Pending Followup", "Notes": lead_notes
            }])
            leads_df = pd.concat([leads_df, new_lead], ignore_index=True)
            save_encrypted_csv(leads_df, LEADS_FILE)
            st.success("Marketing Lead Follow-up Saved!")

    st.markdown("---")
    st.subheader("⚙️ Update Lead Status (Mark Converted)")
    if not leads_df.empty:
        lead_sel = st.selectbox("Select Lead ID to Update", leads_df["Lead ID"].values)
        lead_row_idx = leads_df[leads_df["Lead ID"] == lead_sel].index[0]
        
        status_choice = st.selectbox("Update Status", ["Pending Followup", "Converted", "Rejected"], index=["Pending Followup", "Converted", "Rejected"].index(leads_df.at[lead_row_idx, "Status"]))
        if st.button("Update Lead Status"):
            leads_df.at[lead_row_idx, "Status"] = status_choice
            save_encrypted_csv(leads_df, LEADS_FILE)
            st.success(f"Lead {lead_sel} updated to {status_choice}!")
            st.rerun()

    m_disp_df = leads_df.copy()
    if user_role != "👑 Admin":
        m_disp_df["Mobile"] = m_disp_df["Mobile"].apply(mask_mobile)
    st.dataframe(m_disp_df, use_container_width=True)

# ==================== MODULE: CONVERTED LEADS ====================
elif nav_selection == "🎯 Converted Leads":
    st.subheader("🎯 Marketing Converted Leads (Ready for Booking)")
    if not leads_df.empty:
        converted_leads = leads_df[leads_df["Status"] == "Converted"].copy()
        if not converted_leads.empty:
            if user_role != "👑 Admin":
                converted_leads["Mobile"] = converted_leads["Mobile"].apply(mask_mobile)
            st.success(f"Found {len(converted_leads)} successfully converted marketing leads!")
            st.dataframe(converted_leads[["Lead ID", "Customer Name", "Mobile", "Followup Date", "Notes"]], use_container_width=True)
        else:
            st.info("No converted leads found yet.")
    else:
        st.info("No marketing lead records found.")