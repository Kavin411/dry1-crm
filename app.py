import streamlit as st
import pandas as pd
import os
import io
import socket
import random
import smtplib
import urllib.parse
import html as html_lib
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

# --- OPTIMIZED DATABASE HELPER FUNCTIONS WITH SMART CACHING ---
@st.cache_data(ttl=15, show_spinner=False)
def load_data(table_name):
    try:
        response = supabase.table(table_name).select("*").execute()
        return pd.DataFrame(response.data)
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

def delete_record(table_name, match_col, match_val):
    try:
        supabase.table(table_name).delete().eq(match_col, match_val).execute()
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Database Delete Error: {e}")
        return False

# --- EMAIL CONFIGURATION FOR AUTO OTP ---
GMAIL_SENDER = "praveenvp888@gmail.com"
GMAIL_APP_PASSWORD = "xaet vfgx wkmc upza"

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
ADMIN_MOBILE = "9629373570"        # Admin WhatsApp / customer support number (+91 96293 73570)
ADMIN_EMAIL = "praveenvp888@gmail.com"   # 2FA OTP is sent to this email
ADMIN_2FA_MOBILE = "9629373570"    # Admin mobile linked with 2FA (+91 96293 73570)
STORE_UPI_ID = "praveenvp888-2@okaxis"

# ---- NEW CONFIG (change these numbers / URL) ----
MD_MOBILE = "9629373570"          # Managing Director WhatsApp (customer feedback goes here)
RECEPTION_MOBILE = "8056166017"   # Reception WhatsApp (for corporate pickup alerts)
DELIVERY_MOBILE = "8056166017"    # Delivery boy WhatsApp (for corporate pickup alerts)
APP_URL = "https://your-app-name.streamlit.app"   # your deployed Streamlit URL (used in feedback link)
DELIVERY_CHARGE_PER_ORDER = 30.0  # ₹ auto-added (internal only) for EVERY delivery order. Change this amount.
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# ---- STAFF SALARY CONFIG (fixed monthly salary) ----
STAFF_DETAILS = {
    "Deepak": {"role": "Delivery Associate", "salary": 13000.0},
    "Barath": {"role": "Reception",          "salary": 6000.0},
    "Lady":   {"role": "Reception",          "salary": 16000.0},
}

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

# --- WHATSAPP PROFESSIONAL MESSAGE TEMPLATES ---
STORE_NAME = "DRY1 LAUNDRY & SAREE CARE"
STORE_TAGLINE = "Premium Fabric Care Services"
STORE_CONTACT = ADMIN_MOBILE   # customer support number shown on receipts (change if needed)
WA_LINE = "━━━━━━━━━━━━━━━━━━"

def clean_mobile(mobile_val):
    """Keep digits only and use the last 10 digits (handles +91, spaces, dashes)."""
    digits = "".join(ch for ch in str(mobile_val) if ch.isdigit())
    return digits[-10:] if len(digits) >= 10 else digits

def build_wa_url(mobile_val, message):
    return f"https://api.whatsapp.com/send?phone=91{clean_mobile(mobile_val)}&text={urllib.parse.quote(message)}"

def fmt_date(d):
    try:
        if isinstance(d, str):
            d = datetime.strptime(d[:10], "%Y-%m-%d")
        return d.strftime("%d %b %Y (%a)")
    except Exception:
        return str(d)

def _wa_header(title):
    return [WA_LINE, f"💧 *{STORE_NAME}*", f"_{STORE_TAGLINE}_", WA_LINE, "", title, ""]

def build_receipt_message(order_id, customer_name, service, items, weight_kg,
                          total, paid, balance, promised_date, order_type="Walk-in"):
    """Professional WhatsApp order receipt."""
    total, paid, balance = float(total), float(paid), float(balance)
    is_paid = balance <= 0
    type_txt = "Doorstep Pickup & Delivery" if order_type == "Delivery" else "Walk-in"

    details = [
        f"Order ID : {order_id}",
        f"Date     : {datetime.now().strftime('%d %b %Y')}",
        f"Type     : {type_txt}",
        f"Service  : {service}",
        f"Items    : {int(items)} pcs",
    ]
    if weight_kg and float(weight_kg) > 0:
        details.append(f"Weight   : {float(weight_kg)} KG")
    details.append(f"Ready By : {fmt_date(promised_date)}")

    payment = [
        f"Total Amount : ₹{total:,.2f}",
        f"Amount Paid  : ₹{paid:,.2f}",
        f"Balance Due  : ₹{balance:,.2f}",
    ]

    lines = _wa_header("🧾 *ORDER RECEIPT*")
    lines += [
        f"Dear *{customer_name}*,",
        "Thank you for choosing us! Your order has been booked successfully. ✅",
        "",
        "📋 *ORDER DETAILS*",
        "```" + "\n".join(details) + "```",
        "",
        "💳 *PAYMENT SUMMARY*",
        "```" + "\n".join(payment) + "```",
        "",
        "Status: ✅ *PAID IN FULL*" if is_paid else "Status: ⏳ *PAYMENT PENDING*",
    ]
    if not is_paid:
        lines += [f"Pay via UPI: *{STORE_UPI_ID}*"]
    lines += [
        "",
        WA_LINE,
        "_Please keep this receipt for order collection._",
        f"📞 Support: {STORE_CONTACT}",
        "🙏 *Thank you for choosing Dry1!*",
    ]
    return "\n".join(lines)

def build_ready_message(order_id, customer_name, service, balance):
    """Professional 'garments ready' WhatsApp notification."""
    balance = float(balance)
    lines = _wa_header("✅ *YOUR ORDER IS READY!*")
    lines += [
        f"Dear *{customer_name}*,",
        "Your garments are freshly cleaned and ready for collection / delivery. 🧼",
        "",
        "📋 *ORDER DETAILS*",
        f"```Order ID : {order_id}\nService  : {service}```",
        "",
        "💳 *PAYMENT*",
    ]
    if balance > 0:
        lines += [f"```Balance Due : ₹{balance:,.2f}```", f"Pay via UPI: *{STORE_UPI_ID}*"]
    else:
        lines += ["✅ *No balance due — fully paid.*"]
    lines += [
        "",
        WA_LINE,
        f"📞 Support: {STORE_CONTACT}",
        "🙏 *Thank you for choosing Dry1!*",
    ]
    return "\n".join(lines)

def build_admin_alert_message(title, rows):
    """Structured WhatsApp alert for admin. rows = list of (label, value)."""
    lines = [WA_LINE, f"🚨 *{title}*", WA_LINE, ""]
    lines += [f"▪️ *{k}:* {v}" for k, v in rows]
    lines += ["", "_Please take immediate action._", f"— {STORE_NAME} CRM"]
    return "\n".join(lines)


def _num(v, default=0.0):
    try:
        f = float(v)
        return default if f != f else f
    except Exception:
        return default

# ---------------- FEEDBACK (goes to Managing Director) ----------------
def build_feedback_link(order_id):
    return f"{APP_URL.rstrip('/')}/?feedback={urllib.parse.quote(str(order_id))}"

# ---- GOOGLE REVIEW (simple message sent after delivery) ----
GOOGLE_REVIEW_URL = "https://share.google/012ttgewhJmJ2inmu"   # your Google review link
REVIEW_STORE_NAME = "IFB Point Selaiyur"                         # name shown in the review message

def build_feedback_request_message(order_id=None, customer_name=None):
    """Simple WhatsApp message asking the customer for a 5-star Google review."""
    return (
        "Dear Customer,\n\n"
        f"Thank you for choosing {REVIEW_STORE_NAME}.\n\n"
        "We hope you are happy with your purchase and our service. "
        "Your feedback means a lot to us. "
        "Kindly spare a minute to rate us with 5 stars if you had a great experience.\n\n"
        f"⭐ Leave your review here: {GOOGLE_REVIEW_URL}\n\n"
        "Thank you for your support.\n\n"
        f"{REVIEW_STORE_NAME}"
    )

def build_feedback_to_md_message(order_id, customer_name, overall, quality, delivery, comments):
    lines = [WA_LINE, "⭐ *CUSTOMER FEEDBACK*", WA_LINE, "",
             f"▪️ *Order ID:* {order_id}",
             f"▪️ *Customer:* {customer_name}",
             f"▪️ *Overall:* {'⭐' * int(overall)} ({overall}/5)",
             f"▪️ *Cleaning Quality:* {'⭐' * int(quality)} ({quality}/5)",
             f"▪️ *Pickup/Delivery:* {'⭐' * int(delivery)} ({delivery}/5)",
             f"▪️ *Comments:* {comments if comments else '-'}",
             "", f"— {STORE_NAME}"]
    return "\n".join(lines)

STAR_OPTIONS = ["⭐", "⭐⭐", "⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐⭐⭐"]

def render_feedback_page(order_id):
    """Public page opened by the client from the WhatsApp link (no login needed)."""
    orders = load_data("orders")
    row = None
    if not orders.empty and "order_id" in orders.columns:
        m = orders[orders["order_id"] == order_id]
        if not m.empty:
            row = m.iloc[0]
    _, c, _ = st.columns([1, 1.6, 1])
    with c:
        st.markdown(f"""
        <div style="text-align:center; margin:20px 0;">
            <div style="font-size:2.4rem;">💧</div>
            <h2 style="margin:0; color:#0F172A;">{STORE_NAME}</h2>
            <p style="color:#64748B; font-weight:600;">Customer Feedback Form</p>
        </div>""", unsafe_allow_html=True)
        if row is None:
            st.error("This feedback link is invalid or expired.")
            return
        cust = str(row["customer_name"])
        done_key = f"fb_done_{order_id}"

        if st.session_state.get(done_key):
            d = st.session_state[done_key]
            st.success("🙏 Thank you! Your feedback has been submitted.")
            st.info("👇 Tap below to send your feedback directly to our Managing Director on WhatsApp.")
            md_msg = build_feedback_to_md_message(order_id, cust, d["overall"], d["quality"], d["delivery"], d["comments"])
            st.markdown(f'<a href="{build_wa_url(MD_MOBILE, md_msg)}" target="_blank" class="wa-link-btn">📲 Send to Managing Director on WhatsApp</a>', unsafe_allow_html=True)
            return

        existing = load_data("customer_feedback")
        if not existing.empty and "order_id" in existing.columns and (existing["order_id"] == order_id).any():
            st.success("🙏 We have already received your feedback for this order. Thank you!")
            return

        st.markdown(f"Dear **{cust}**, thank you for choosing us! Order: `{order_id}`")
        st.info("🔒 Your feedback goes directly to our **Managing Director** on WhatsApp.")
        with st.form("customer_feedback_form"):
            overall = st.radio("Overall Experience", STAR_OPTIONS, index=4, horizontal=True)
            quality = st.radio("Cleaning / Ironing Quality", STAR_OPTIONS, index=4, horizontal=True)
            delivery = st.radio("Pickup & Delivery Service", STAR_OPTIONS, index=4, horizontal=True)
            comments = st.text_area("Your Comments / Suggestions (optional)")
            if st.form_submit_button("📨 Submit Feedback"):
                ov, ql, dl = len(overall), len(quality), len(delivery)
                ok = save_record("customer_feedback", {
                    "order_id": order_id, "customer_name": cust,
                    "overall_rating": ov, "quality_rating": ql, "delivery_rating": dl,
                    "comments": comments, "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                if ok:
                    st.session_state[done_key] = {"overall": ov, "quality": ql, "delivery": dl, "comments": comments}
                    st.rerun()

# ---------------- SHIFT HANDOVER (Morning 9-6 / Evening 6-10) ----------------
SHIFT_MORNING = "🌅 Morning (9 AM - 6 PM)"
SHIFT_EVENING = "🌆 Evening (6 PM - 10 PM)"
SHIFT_OPTIONS = [SHIFT_MORNING, SHIFT_EVENING]
SHIFT_MORNING_START_HOUR = 9     # change here if shift timing changes (also update the labels above)
SHIFT_EVENING_START_HOUR = 18
SHIFT_EVENING_END_HOUR = 22

HANDOVER_ISSUE_TYPES = [
    "Dress Missing / Not Found",
    "Customer Complaint",
    "Payment Pending / Cash Issue",
    "Pickup / Delivery Pending",
    "Machine / Equipment Issue",
    "Stain / Damage in Garment",
    "Stock / Chemical Shortage",
    "Other",
]
HANDOVER_PRIORITIES = ["🟢 Normal", "🟠 High", "🔴 Urgent"]

def get_current_shift(now=None):
    """Returns the running shift, or None when the store is closed (10 PM - 9 AM)."""
    h = (now or datetime.now()).hour
    if SHIFT_MORNING_START_HOUR <= h < SHIFT_EVENING_START_HOUR:
        return SHIFT_MORNING
    if SHIFT_EVENING_START_HOUR <= h < SHIFT_EVENING_END_HOUR:
        return SHIFT_EVENING
    return None

def get_next_shift(shift):
    return SHIFT_EVENING if shift == SHIFT_MORNING else SHIFT_MORNING

def _priority_rank(p):
    p = str(p)
    return 0 if "Urgent" in p else (1 if "High" in p else 2)

# ---------------- CORPORATE PICKUP SCHEDULE & ALERTS ----------------
def get_corporate_alerts(clients_df, pickups_df, today, lookback=7):
    """Every scheduled pickup day (today or up to `lookback` days back) that is not yet marked 'Picked Up'."""
    alerts = []
    if clients_df is None or clients_df.empty:
        return alerts
    done = set()
    if pickups_df is not None and not pickups_df.empty:
        for _, p in pickups_df.iterrows():
            if str(p.get("status")) == "Picked Up":
                done.add((str(p.get("client_id")), str(p.get("pickup_date"))[:10]))
    for _, c in clients_df.iterrows():
        if str(c.get("status", "Active")) != "Active":
            continue
        days = [d.strip() for d in str(c.get("pickup_days", "")).split(",") if d.strip()]
        try:
            start = datetime.strptime(str(c.get("created_date"))[:10], "%Y-%m-%d").date()
        except Exception:
            start = today - timedelta(days=lookback)
        for back in range(lookback + 1):
            d = today - timedelta(days=back)
            if d < start:
                continue
            if WEEKDAYS[d.weekday()] in days and (str(c["client_id"]), str(d)) not in done:
                alerts.append({"client": c, "date": d, "delay": back})
    return alerts

def build_corporate_alert_message(client, sched_date, delay):
    if delay == 0:
        title = "CORPORATE PICKUP DUE TODAY"
    elif delay == 1:
        title = "CORPORATE PICKUP DELAYED (+1 Day)"
    else:
        title = f"RED ALERT: CORPORATE PICKUP MISSED (+{delay} Days)"
    rows = [("Company", client["company_name"]),
            ("Contact", f"{client.get('contact_person', '')} ({client.get('mobile', '')})"),
            ("Address", client.get("address", "")),
            ("Scheduled Date", fmt_date(sched_date))]
    if delay > 0:
        rows.append(("Delay", f"+{delay} Day(s)"))
    return build_admin_alert_message(title, rows)

def render_corporate_alerts(alerts, user_role):
    if not alerts:
        return
    st.markdown("### 🏢 Corporate Pickup Alerts")
    for a in sorted(alerts, key=lambda x: -x["delay"]):
        c, d, delay = a["client"], a["date"], a["delay"]
        mob = c["mobile"] if user_role in ["👑 Admin", "👩‍💼 Reception"] else mask_mobile(c["mobile"])
        info = f"Client: <b>{c['company_name']}</b> | Contact: <b>{c.get('contact_person', '')}</b> (📞 <b>{mob}</b>) | Scheduled: <b>{fmt_date(d)}</b>"
        if delay == 0:
            st.markdown(f'<div class="alert-today">⚠️ <b>CORPORATE PICKUP TODAY:</b> {info}</div>', unsafe_allow_html=True)
        elif delay == 1:
            st.markdown(f'<div class="alert-delay">🟧 <b>PICKUP DELAYED (+1 Day):</b> {info}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="alert-red">🚨 <b>RED ALERT: PICKUP MISSED (+{delay} Days):</b> {info}</div>', unsafe_allow_html=True)
        msg = build_corporate_alert_message(c, d, delay)
        b1, b2, b3 = st.columns(3)
        for col, label, num, bg in [(b1, "Delivery Boy", DELIVERY_MOBILE, "#0284C7"),
                                    (b2, "Reception", RECEPTION_MOBILE, "#7C3AED"),
                                    (b3, "Admin", ADMIN_MOBILE, "#DC2626")]:
            col.markdown(f'<a href="{build_wa_url(num, msg)}" target="_blank" class="wa-link-btn" style="background:{bg} !important;">📲 Alert {label}</a>', unsafe_allow_html=True)

def build_bill_card_html(b, mobile_display):
    """Professional invoice card (used on screen and in the downloadable bill)."""
    is_paid = float(b["balance"]) <= 0
    badge_bg, badge_fg, badge_txt = ("#DCFCE7", "#166534", "✅ PAID IN FULL") if is_paid else ("#FEF3C7", "#92400E", "⏳ PAYMENT PENDING")
    type_txt = "Doorstep Pickup & Delivery" if b["order_type"] == "Delivery" else "Walk-in"
    rows = [
        ("Service", b["service"]),
        ("Items", f"{int(b['items'])} pcs"),
    ]
    if b.get("weight_kg") and float(b["weight_kg"]) > 0:
        rows.append(("Weight", f"{float(b['weight_kg'])} KG"))
    rows += [("Order Type", type_txt), ("Ready By", fmt_date(b["promised_date"]))]
    detail_rows = "".join(
        f'<tr><td style="padding:9px 0;color:#64748B;font-size:0.85rem;border-bottom:1px dashed #E2E8F0;">{k}</td>'
        f'<td style="padding:9px 0;color:#0F172A;font-weight:700;font-size:0.9rem;text-align:right;border-bottom:1px dashed #E2E8F0;">{v}</td></tr>'
        for k, v in rows
    )
    upi_html = "" if is_paid else (
        f'<div style="margin-top:10px;font-size:0.8rem;color:#475569;text-align:center;">Pay via UPI: <b>{STORE_UPI_ID}</b></div>'
    )
    return (
        '<div style="max-width:520px;margin:10px auto;background:#FFFFFF;border:1px solid #E2E8F0;border-radius:18px;overflow:hidden;box-shadow:0 10px 30px rgba(15,23,42,0.10);">'
        '<div style="background:linear-gradient(135deg,#2563EB 0%,#1D4ED8 100%);padding:22px;text-align:center;color:#FFFFFF;">'
        f'<div style="font-size:1.3rem;font-weight:800;letter-spacing:0.5px;">💧 {STORE_NAME}</div>'
        f'<div style="font-size:0.8rem;opacity:0.9;margin-top:4px;">{STORE_TAGLINE}</div>'
        '<div style="display:inline-block;margin-top:12px;background:rgba(255,255,255,0.18);padding:4px 16px;border-radius:20px;font-size:0.78rem;font-weight:700;letter-spacing:1px;">ORDER RECEIPT</div>'
        '</div>'
        '<div style="padding:20px 22px;">'
        '<div style="display:flex;justify-content:space-between;background:#F8FAFC;border-radius:12px;padding:12px 14px;margin-bottom:16px;">'
        f'<div><div style="font-size:0.7rem;color:#64748B;font-weight:700;">ORDER ID</div><div style="font-weight:800;color:#0F172A;">{b["order_id"]}</div></div>'
        f'<div style="text-align:right;"><div style="font-size:0.7rem;color:#64748B;font-weight:700;">DATE</div><div style="font-weight:800;color:#0F172A;">{datetime.now().strftime("%d %b %Y")}</div></div>'
        '</div>'
        '<div style="font-size:0.7rem;color:#64748B;font-weight:700;letter-spacing:1px;">BILLED TO</div>'
        f'<div style="font-size:1.05rem;font-weight:800;color:#0F172A;">{b["customer_name"]}</div>'
        f'<div style="font-size:0.85rem;color:#475569;margin-bottom:14px;">📞 {mobile_display}</div>'
        f'<table style="width:100%;border-collapse:collapse;">{detail_rows}</table>'
        '<div style="margin-top:16px;background:#F8FAFC;border-radius:12px;padding:14px;">'
        f'<div style="display:flex;justify-content:space-between;margin-bottom:6px;"><span style="color:#64748B;">Total Amount</span><b>₹{float(b["total"]):,.2f}</b></div>'
        f'<div style="display:flex;justify-content:space-between;margin-bottom:6px;"><span style="color:#64748B;">Amount Paid</span><b style="color:#16A34A;">₹{float(b["paid"]):,.2f}</b></div>'
        f'<div style="display:flex;justify-content:space-between;border-top:1px solid #CBD5E1;padding-top:8px;margin-top:8px;font-size:1.05rem;"><b>Balance Due</b><b style="color:#DC2626;">₹{float(b["balance"]):,.2f}</b></div>'
        '</div>'
        f'<div style="margin-top:14px;text-align:center;"><span style="background:{badge_bg};color:{badge_fg};padding:6px 18px;border-radius:20px;font-weight:800;font-size:0.8rem;">{badge_txt}</span></div>'
        f'{upi_html}'
        '</div>'
        '<div style="background:#F8FAFC;border-top:1px solid #E2E8F0;padding:14px;text-align:center;font-size:0.78rem;color:#64748B;">'
        f'Please keep this receipt for order collection.<br>📞 Support: {STORE_CONTACT}<br><b style="color:#0F172A;">🙏 Thank you for choosing Dry1!</b>'
        '</div>'
        '</div>'
    )

def build_bill_download_html(b, mobile_display):
    card = build_bill_card_html(b, mobile_display)
    return (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        f'<title>Bill {b["order_id"]}</title>'
        '<style>body{background:#F1F5F9;font-family:Arial,Helvetica,sans-serif;padding:20px;}'
        '.noprint{text-align:center;margin:16px;}'
        '.noprint button{background:#2563EB;color:#fff;border:none;padding:10px 24px;border-radius:10px;font-weight:700;cursor:pointer;}'
        '@media print{body{background:#fff;padding:0;}.noprint{display:none;}}</style></head><body>'
        f'{card}<div class="noprint"><button onclick="window.print()">🖨️ Print / Save as PDF</button></div></body></html>'
    )

def render_bill_section(bill, key_prefix, mask=False):
    """Shows invoice card + WhatsApp button + download + message preview."""
    mob_disp = mask_mobile(bill["mobile"]) if mask else clean_mobile(bill["mobile"])
    st.markdown("### 🧾 Customer Bill")
    st.markdown(build_bill_card_html(bill, mob_disp), unsafe_allow_html=True)

    wa_msg = build_receipt_message(bill["order_id"], bill["customer_name"], bill["service"], bill["items"],
                                   bill["weight_kg"], bill["total"], bill["paid"], bill["balance"],
                                   bill["promised_date"], order_type=bill["order_type"])
    wa_url = build_wa_url(bill["mobile"], wa_msg)
    st.markdown(f'<a href="{wa_url}" target="_blank" class="wa-link-btn">📲 Send WhatsApp Receipt</a>', unsafe_allow_html=True)
    st.download_button("🖨️ Download Bill (Print / Save as PDF)",
                       data=build_bill_download_html(bill, mob_disp).encode("utf-8"),
                       file_name=f"{bill['order_id']}_bill.html", mime="text/html",
                       key=f"{key_prefix}_dl_{bill['order_id']}")
    with st.expander("👁️ Preview WhatsApp Message"):
        st.code(wa_msg, language=None)

@st.cache_data(ttl=300)
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

# --- MODERN STYLING WITH HIDDEN PASSWORD VISIBILITY ICON ---
STYLING = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    * { font-family: 'Plus Jakarta Sans', sans-serif !important; }

    /* Keep Streamlit's icon font (fixes the "_arrow_right" text glitch on expanders) */
    [data-testid="stIconMaterial"],
    [data-testid="stExpanderToggleIcon"],
    [data-testid="stExpanderIcon"],
    .material-icons,
    .material-symbols-rounded,
    .material-symbols-outlined {
        font-family: "Material Symbols Rounded", "Material Symbols Outlined", "Material Icons" !important;
        font-weight: 400 !important;
        font-style: normal !important;
    }
    
    header[data-testid="stHeader"] { display: none !important; }
    .stApp { background: #F1F5F9 !important; color: #0F172A !important; }
    
    /* HIDE PASSWORD EYE VISIBILITY TOGGLE BUTTON & BROWSER ICONS */
    [data-testid="stTextInput"] button[aria-label="Show password"],
    [data-testid="stTextInput"] button[aria-label="Hide password"],
    [data-testid="stTextInput"] button {
        display: none !important;
    }
    input[type="password"]::-ms-reveal,
    input[type="password"]::-ms-clear {
        display: none !important;
    }

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

    .stDownloadButton > button {
        width: 100% !important;
        background: #FFFFFF !important;
        color: #1D4ED8 !important;
        font-weight: 700 !important;
        border: 1.5px solid #2563EB !important;
        border-radius: 12px !important;
        padding: 12px 20px !important;
        margin-top: 4px;
    }
    .stDownloadButton > button:hover { background: #EFF6FF !important; }

    [data-testid="stExpander"] {
        background: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 12px !important;
        margin-top: 10px;
    }
    [data-testid="stExpander"] summary { font-weight: 700 !important; padding: 10px 14px !important; }

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

# ==================== PUBLIC CUSTOMER FEEDBACK PAGE (opened from WhatsApp link) ====================
_fb_order = st.query_params.get("feedback")
if _fb_order:
    render_feedback_page(str(_fb_order))
    st.stop()

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
                            if send_email_otp(ADMIN_EMAIL, otp):
                                st.session_state.generated_otp = otp
                                st.session_state.otp_sent = True
                                st.rerun()
                            else:
                                st.error("❌ Could not send OTP email. Please check the Gmail sender / App Password in app.py and internet connection.")
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
                st.info(f"📧 An OTP has been sent to Admin Email: **{ADMIN_EMAIL}**  \n📱 Registered Admin Mobile: **+91 {ADMIN_2FA_MOBILE[:5]} {ADMIN_2FA_MOBILE[5:]}**")
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

# --- ROLE-BASED NAVIGATION MENU ---
menu_options = []
if user_role == "👑 Admin":
    menu_options = [
        "📊 Master Operations", 
        "📜 Orders History & Reports",
        "📈 Financial Analytics", 
        "🚚 Vendor & Chemical Purchases",
        "🛵 Delivery Shift Logs",
        "🏢 Corporate Clients",
        "💰 Delivery Boy Charges",
        "⭐ Customer Feedback",
        "👤 Customer Master DB", 
        "💸 Store Expenses Entry", 
        "👥 Staff Salary & Advances",
        "🔒 Active Device Control", 
        "🎯 Converted Leads"
    ]
elif user_role == "👩‍💼 Reception":
    menu_options = [
        "📝 New Billing & Order", 
        "📊 Operations Dashboard", 
        "🏢 Corporate Clients",
        "📜 Monthly Orders History",
        "📈 Financial Analytics", 
        "💸 Store Expenses Entry", 
        "🎯 Converted Leads"
    ]
elif user_role == "🛵 Delivery Boy":
    menu_options = ["🛵 Delivery Portal", "🏢 Corporate Clients", "📜 Delivery History"]
elif user_role == "📢 Marketing Team":
    menu_options = ["📢 Marketing Tracker"]

if user_role in ["👑 Admin", "👩‍💼 Reception", "🛵 Delivery Boy"]:
    menu_options.insert(1, "🔄 Shift Handover")

st.sidebar.markdown("<p style='font-size:0.75rem; font-weight:800; color:#94A3B8 !important; letter-spacing:1px; margin-bottom:10px; padding-left:4px;'>NAVIGATION MENU</p>", unsafe_allow_html=True)
nav_selection = st.sidebar.radio("", menu_options, label_visibility="collapsed")

st.sidebar.markdown("<br>", unsafe_allow_html=True)
if st.sidebar.button("🚪 Logout Session"):
    if st.session_state.session_id:
        update_record("active_sessions", {"status": "Logged Out"}, "session_id", st.session_state.session_id)
    st.session_state.logged_in = False
    st.session_state.session_id = None
    st.session_state.otp_sent = False
    st.session_state.last_bill_billing = None
    st.session_state.last_bill_delivery = None
    st.session_state.feedback_prompt_id = None
    st.rerun()

# --- OPTIMIZED LAZY DATA FETCHING ---
orders_df = load_data("orders")
today = datetime.now().date()

# --- PROMISED DATE & MARKETING FOLLOWUP ALERTS ---
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
                    
                    alert_wa_msg = build_admin_alert_message("RED ALERT: ORDER DELIVERY DELAYED", [("Order ID", ord_row['order_id']), ("Customer", f"{ord_row['customer_name']} ({ord_row['mobile']})"), ("Promised Date", ord_row['promised_date']), ("Delay", f"+{diff} Days"), ("Stage", ord_row['order_status'])])
                    wa_admin_url = build_wa_url(ADMIN_MOBILE, alert_wa_msg)
                    st.markdown(f'<a href="{wa_admin_url}" target="_blank" class="wa-link-btn" style="background:#DC2626 !important;">📲 Send Red Alert to Admin WhatsApp</a>', unsafe_allow_html=True)
            except Exception: pass

# --- CORPORATE PICKUP ALERTS (Admin + Reception + Delivery Boy) ---
if user_role in ["👑 Admin", "👩‍💼 Reception", "🛵 Delivery Boy"]:
    _corp_clients = load_data("corporate_clients")
    _corp_pickups = load_data("corporate_pickups")
    render_corporate_alerts(get_corporate_alerts(_corp_clients, _corp_pickups, today), user_role)

if user_role in ["👑 Admin", "📢 Marketing Team"]:
    leads_df = load_data("marketing_leads")
    if not leads_df.empty:
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
                        
                        mkt_wa_msg = build_admin_alert_message("RED ALERT: MARKETING LEAD OVERDUE", [("Lead ID", lead_row['lead_id']), ("Client Name", f"{lead_row['customer_name']} ({lead_row['mobile']})"), ("Scheduled Date", lead_row['followup_date']), ("Overdue", f"+{f_diff} Days")])
                        wa_admin_mkt_url = build_wa_url(ADMIN_MOBILE, mkt_wa_msg)
                        st.markdown(f'<a href="{wa_admin_mkt_url}" target="_blank" class="wa-link-btn" style="background:#DC2626 !important;">📲 Send Marketing Delay Alert to Admin WhatsApp</a>', unsafe_allow_html=True)
                except Exception: pass

# --- PENDING SHIFT HANDOVER BANNER ---
if user_role in ["👑 Admin", "👩‍💼 Reception", "🛵 Delivery Boy"]:
    _ho_all = load_data("shift_handover")
    if not _ho_all.empty and "status" in _ho_all.columns:
        _ho_open = int((_ho_all["status"] == "Open").sum())
        if _ho_open:
            st.markdown(f'<div class="alert-delay">🔄 <b>{_ho_open} pending shift handover note(s)</b> — open <b>🔄 Shift Handover</b> in the menu and check.</div>', unsafe_allow_html=True)

# ==================== MODULE: DELIVERY SHIFT LOGS ====================
if nav_selection == "🛵 Delivery Shift Logs":
    if user_role != "👑 Admin":
        st.error("🔒 Access Restricted: Delivery Shift Logs can only be accessed by Admin.")
    else:
        st.subheader("🛵 Delivery Boy EV Shift Logs & Odometer / Charge History")
        shift_logs_df = load_data("delivery_shift_logs")
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
        vendors_df = load_data("vendor_purchases")
        if not vendors_df.empty:
            st.dataframe(vendors_df, use_container_width=True)

# ==================== MODULE: DELIVERY PORTAL ====================
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

            dcharge = DELIVERY_CHARGE_PER_ORDER
            st.caption(f"🔒 Delivery charge ₹{DELIVERY_CHARGE_PER_ORDER:,.0f} is auto-recorded for every order. It will NOT appear on the client's bill or WhatsApp message.")

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
                        "special_instructions": "Doorstep Pickup", "assigned_delivery": "Delivery Boy",
                        "delivery_charge": float(dcharge)
                    })
                    st.success(f"Pickup Order Created: {new_id}")
                    
                    st.session_state.last_bill_delivery = {
                        "order_id": new_id, "customer_name": dcust_name, "mobile": str(dmobile),
                        "service": dservice, "items": int(ditems), "weight_kg": float(dweight_kg),
                        "total": float(dtotal), "paid": float(dpaid), "balance": float(dbal),
                        "promised_date": str(dpromised_date), "order_type": "Delivery"
                    }

        if st.session_state.get("last_bill_delivery"):
            st.markdown("---")
            render_bill_section(st.session_state.last_bill_delivery, "delivery")

    with d_tab2:
        delivery_all = orders_df[orders_df["customer_type"] == "Delivery"].copy() if not orders_df.empty else pd.DataFrame()

        # Feedback prompt right after marking an order as Delivered
        _fb_id = st.session_state.get("feedback_prompt_id")
        if _fb_id and not delivery_all.empty:
            _m = delivery_all[delivery_all["order_id"] == _fb_id]
            if not _m.empty:
                _r = _m.iloc[0]
                st.success(f"✅ Order {_fb_id} delivered! Now send the review request to the client 👇")
                _fb_url = build_wa_url(_r["mobile"], build_feedback_request_message(_fb_id, _r["customer_name"]))
                st.markdown(f'<a href="{_fb_url}" target="_blank" class="wa-link-btn" style="background:#7C3AED !important;">⭐ Send Review Request to Client (WhatsApp)</a>', unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)

        delivery_orders = delivery_all[delivery_all["order_status"] != "Delivered"].copy() if not delivery_all.empty else pd.DataFrame()
        if delivery_orders.empty:
            st.info("No active delivery orders.")
        else:
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
                    if st.button("✅ Mark as Delivered", key=f"deliv_{drow['order_id']}"):
                        update_record("orders", {"order_status": "Delivered"}, "order_id", drow["order_id"])
                        st.session_state.feedback_prompt_id = drow["order_id"]
                        st.rerun()

    with d_tab3:
        st.markdown("### ⚡ Electric Vehicle (EV) Shift Start & End Logging")
        driver_name = st.text_input("Delivery Boy Name", value="Delivery Staff")
        
        shift_logs_df = load_data("delivery_shift_logs")
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

# ==================== MODULE: SHIFT HANDOVER ====================
elif nav_selection == "🔄 Shift Handover":
    st.subheader("🔄 Shift Handover Notes")
    _cur_shift = get_current_shift()
    if _cur_shift:
        st.info(f"🕘 **Current Shift:** {_cur_shift}   ➜   **Next Shift:** {get_next_shift(_cur_shift)}")
    else:
        st.info("🌙 Store is closed now (10 PM - 9 AM). Notes added now will be seen by the Morning shift.")

    ho_df = load_data("shift_handover")
    h_tab1, h_tab2, h_tab3 = st.tabs(["📥 Pending Notes (Next Shift Must Check)", "➕ Add Handover Note", "📚 Handover History"])

    # ---------- TAB 1: PENDING NOTES ----------
    with h_tab1:
        open_notes = pd.DataFrame()
        if not ho_df.empty and "status" in ho_df.columns:
            open_notes = ho_df[ho_df["status"] == "Open"].copy()

        if open_notes.empty:
            st.success("✅ No pending handover notes. All clear!")
        else:
            open_notes["_rank"] = open_notes["priority"].apply(_priority_rank)
            open_notes = open_notes.sort_values(["_rank", "created_at"], ascending=[True, False])
            for _, n in open_notes.iterrows():
                nid = str(n["note_id"])
                css = ["alert-red", "alert-delay", "alert-today"][_priority_rank(n["priority"])]
                order_txt = f" | Order: <b>{html_lib.escape(str(n['order_id']))}</b>" if str(n.get("order_id", "")) not in ["", "None", "nan"] else ""
                st.markdown(
                    f'<div class="{css}">{html_lib.escape(str(n["priority"]))} &nbsp;<b>{html_lib.escape(str(n["issue_type"]))}</b>{order_txt}<br>'
                    f'📝 {html_lib.escape(str(n["details"]))}<br>'
                    f'<span style="font-weight:500;font-size:0.85rem;">From: {html_lib.escape(str(n["from_shift"]))} | {html_lib.escape(str(n["shift_date"]))} | '
                    f'By: {html_lib.escape(str(n["reported_by"]))} ({html_lib.escape(str(n["role"]))})</span></div>',
                    unsafe_allow_html=True
                )
                res_note = st.text_input("What was done? (optional)", key=f"hres_{nid}", placeholder="e.g., Dress found in rack 3, given to customer")
                if st.button("✅ Mark as Done / Resolved", key=f"hbtn_{nid}"):
                    update_record("shift_handover", {
                        "status": "Resolved", "resolved_by": user_role,
                        "resolved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "resolution_note": res_note
                    }, "note_id", nid)
                    st.success("Note marked as resolved!")
                    st.rerun()
                if _priority_rank(n["priority"]) <= 1:
                    _wa = build_admin_alert_message("SHIFT HANDOVER ISSUE", [
                        ("Issue", n["issue_type"]), ("Priority", n["priority"]),
                        ("Order ID", n.get("order_id", "-")), ("Details", n["details"]),
                        ("Shift", n["from_shift"]), ("Reported By", n["reported_by"])
                    ])
                    st.markdown(f'<a href="{build_wa_url(ADMIN_MOBILE, _wa)}" target="_blank" class="wa-link-btn" style="background:#DC2626 !important;">📲 Send to Admin WhatsApp</a>', unsafe_allow_html=True)
                st.markdown("<hr style='margin:14px 0;'>", unsafe_allow_html=True)

    # ---------- TAB 2: ADD NOTE ----------
    with h_tab2:
        _order_ids = orders_df["order_id"].tolist()[::-1][:200] if not orders_df.empty else []
        with st.form("handover_form", clear_on_submit=True):
            hc1, hc2 = st.columns(2)
            with hc1:
                h_shift = st.selectbox("Your Shift (now ending)", SHIFT_OPTIONS,
                                       index=SHIFT_OPTIONS.index(_cur_shift) if _cur_shift else 1)
                h_issue = st.selectbox("Issue Type", HANDOVER_ISSUE_TYPES)
                h_priority = st.selectbox("Priority", HANDOVER_PRIORITIES)
            with hc2:
                h_order = st.selectbox("Related Order ID (optional)", ["-- None --"] + _order_ids)
                h_name = st.text_input("Your Name", placeholder="Who is handing over?")
            h_details = st.text_area("Details — what should the next shift do?",
                                     placeholder="e.g., Blue saree of customer Priya not found. Please check rack 3 and call her.")
            if st.form_submit_button("📨 Save Handover Note"):
                if not h_details.strip():
                    st.error("Please enter the details of the issue.")
                else:
                    ok = save_record("shift_handover", {
                        "note_id": datetime.now().strftime("HND-%Y%m%d%H%M%S"),
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "shift_date": str(today),
                        "from_shift": h_shift,
                        "to_shift": get_next_shift(h_shift),
                        "issue_type": h_issue,
                        "order_id": "" if h_order == "-- None --" else str(h_order),
                        "priority": h_priority,
                        "details": h_details.strip(),
                        "reported_by": h_name.strip() if h_name.strip() else user_role,
                        "role": user_role,
                        "status": "Open",
                    })
                    if ok:
                        st.success("✅ Handover note saved. Next shift will see it.")
                        st.rerun()
                    else:
                        st.warning("Note not saved. Please make sure the 'shift_handover' table exists in Supabase.")

    # ---------- TAB 3: HISTORY ----------
    with h_tab3:
        if ho_df.empty:
            st.info("No handover notes yet.")
        else:
            hist_filter = st.radio("Show:", ["All", "Open", "Resolved"], horizontal=True)
            hist_df = ho_df.copy()
            if hist_filter != "All" and "status" in hist_df.columns:
                hist_df = hist_df[hist_df["status"] == hist_filter]
            if "created_at" in hist_df.columns:
                hist_df = hist_df.sort_values("created_at", ascending=False)
            st.dataframe(hist_df.drop(columns=["id"], errors="ignore"), use_container_width=True)

# ==================== MODULE: CORPORATE CLIENTS ====================
elif nav_selection == "🏢 Corporate Clients":
    st.subheader("🏢 Corporate Clients — Weekly Pickup Schedule")
    corp_clients_df = load_data("corporate_clients")
    corp_pickups_df = load_data("corporate_pickups")
    c_tab1, c_tab2, c_tab3 = st.tabs(["📅 Pickups To Do (Mark Picked Up)", "➕ Register Corporate Client", "📋 Clients & Pickup History"])

    with c_tab1:
        pending = get_corporate_alerts(corp_clients_df, corp_pickups_df, today)
        if not pending:
            st.success("✅ No pending corporate pickups. All scheduled pickups are completed.")
        for a in sorted(pending, key=lambda x: -x["delay"]):
            c, d, delay = a["client"], a["date"], a["delay"]
            key = f"{c['client_id']}_{d}"
            tag = "Due Today" if delay == 0 else f"Delayed +{delay} Day(s)"
            with st.container(border=True):
                st.markdown(f"**🏢 {c['company_name']}** — {fmt_date(d)} — `{tag}`")
                st.caption(f"👤 {c.get('contact_person', '')} | 📍 {c.get('address', '')}")
                k1, k2, k3 = st.columns(3)
                with k1: p_items = st.number_input("Items Count", min_value=0, value=0, key=f"pi_{key}")
                with k2: p_wt = st.number_input("Weight (KG)", min_value=0.0, step=0.5, key=f"pw_{key}")
                with k3: p_chg = st.number_input("Extra Pickup Charge (₹) 🔒 internal", min_value=0.0, step=10.0,
                                                 value=_num(c.get("pickup_charge")), key=f"pc_{key}")
                p_note = st.text_input("Notes", key=f"pn_{key}")
                if st.button("✅ Mark Picked Up", key=f"pb_{key}", type="primary"):
                    save_record("corporate_pickups", {
                        "pickup_id": f"PICK-{len(corp_pickups_df)+1:05d}",
                        "client_id": str(c["client_id"]), "company_name": c["company_name"],
                        "pickup_date": str(d), "status": "Picked Up", "picked_by": user_role,
                        "picked_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "items_count": int(p_items), "weight_kg": float(p_wt),
                        "extra_charge": float(p_chg), "notes": p_note
                    })
                    st.success("Pickup marked as completed!")
                    st.rerun()

        st.markdown("#### 📆 Weekly Schedule")
        if not corp_clients_df.empty:
            sch = corp_clients_df[corp_clients_df["status"] == "Active"][["client_id", "company_name", "contact_person", "pickup_days", "address"]]
            st.dataframe(sch, use_container_width=True)

    with c_tab2:
        if user_role not in ["👑 Admin", "👩‍💼 Reception"]:
            st.info("🔒 Only Admin and Reception can register corporate clients.")
        else:
            with st.form("corp_register_form"):
                r1, r2 = st.columns(2)
                with r1:
                    co_name = st.text_input("Company Name")
                    co_contact = st.text_input("Contact Person")
                    co_mobile = st.text_input("Contact Mobile Number")
                with r2:
                    co_addr = st.text_area("Pickup Address")
                    co_days = st.multiselect("Weekly Pickup Days (3 days)", WEEKDAYS, default=["Mon", "Wed", "Fri"])
                    co_charge = st.number_input("Extra Pickup Charge per Visit (₹) 🔒 internal, not shown to client", min_value=0.0, step=10.0)
                if st.form_submit_button("💾 Register Corporate Client"):
                    if not co_name or not co_mobile or not co_days:
                        st.error("Please enter Company Name, Mobile and at least one pickup day.")
                    else:
                        if len(co_days) != 3:
                            st.warning(f"Note: {len(co_days)} pickup day(s) selected (normally 3 per week). Saved anyway.")
                        save_record("corporate_clients", {
                            "client_id": f"CORP-{len(corp_clients_df)+1:03d}", "company_name": co_name,
                            "contact_person": co_contact, "mobile": str(co_mobile), "address": co_addr,
                            "pickup_days": ",".join(co_days), "pickup_charge": float(co_charge),
                            "status": "Active", "created_date": str(today)
                        })
                        st.success("✅ Corporate client registered! Pickup alerts will start on the scheduled days.")
                        st.rerun()

    with c_tab3:
        st.markdown("#### 🏢 Registered Clients")
        if not corp_clients_df.empty:
            cl_disp = corp_clients_df.copy()
            if user_role != "👑 Admin":
                cl_disp = cl_disp.drop(columns=["pickup_charge"], errors="ignore")
            if user_role == "🛵 Delivery Boy":
                cl_disp["mobile"] = cl_disp["mobile"].apply(mask_mobile)
            st.dataframe(cl_disp, use_container_width=True)
            if user_role in ["👑 Admin", "👩‍💼 Reception"]:
                active_ids = corp_clients_df[corp_clients_df["status"] == "Active"]["client_id"].tolist()
                if active_ids:
                    deact = st.selectbox("Deactivate a client (stops alerts)", ["-- None --"] + active_ids)
                    if deact != "-- None --" and st.button("⛔ Deactivate Client"):
                        update_record("corporate_clients", {"status": "Inactive"}, "client_id", deact)
                        st.success("Client deactivated.")
                        st.rerun()
        else:
            st.info("No corporate clients registered yet.")
        st.markdown("#### 📦 Pickup History")
        if not corp_pickups_df.empty:
            pk_disp = corp_pickups_df.copy()
            if user_role != "👑 Admin":
                pk_disp = pk_disp.drop(columns=["extra_charge"], errors="ignore")
            st.dataframe(pk_disp, use_container_width=True)

# ==================== MODULE: DELIVERY BOY CHARGES (ADMIN ONLY, INTERNAL) ====================
elif nav_selection == "💰 Delivery Boy Charges":
    if user_role != "👑 Admin":
        st.error("🔒 Access Restricted to Admin Only.")
    else:
        st.subheader("💰 Delivery Boy Extra Charges (Internal — not visible on client bills)")
        corp_pk = load_data("corporate_pickups")
        rows = []
        if not orders_df.empty and "delivery_charge" in orders_df.columns:
            o = orders_df[pd.to_numeric(orders_df["delivery_charge"], errors="coerce").fillna(0) > 0]
            for _, r in o.iterrows():
                rows.append({"Type": "Delivery Order", "Ref": r["order_id"], "Name": r["customer_name"],
                             "Date": str(r.get("created_date"))[:10], "Charge": _num(r["delivery_charge"])})
        if not corp_pk.empty and "extra_charge" in corp_pk.columns:
            cp = corp_pk[pd.to_numeric(corp_pk["extra_charge"], errors="coerce").fillna(0) > 0]
            for _, r in cp.iterrows():
                rows.append({"Type": "Corporate Pickup", "Ref": r.get("pickup_id", ""), "Name": r["company_name"],
                             "Date": str(r.get("pickup_date"))[:10], "Charge": _num(r["extra_charge"])})
        if rows:
            ch_df = pd.DataFrame(rows)
            ch_df["Month"] = pd.to_datetime(ch_df["Date"], errors="coerce").dt.strftime("%B %Y")
            months = ["All Months"] + sorted(ch_df["Month"].dropna().unique().tolist())
            sel_m = st.selectbox("📅 Month", months)
            if sel_m != "All Months":
                ch_df = ch_df[ch_df["Month"] == sel_m]
            m1, m2, m3 = st.columns(3)
            m1.metric("Delivery Orders Charges", f"₹{ch_df[ch_df['Type']=='Delivery Order']['Charge'].sum():,.2f}")
            m2.metric("Corporate Pickup Charges", f"₹{ch_df[ch_df['Type']=='Corporate Pickup']['Charge'].sum():,.2f}")
            m3.metric("Total Delivery Boy Charges", f"₹{ch_df['Charge'].sum():,.2f}")
            st.dataframe(ch_df.sort_values("Date", ascending=False), use_container_width=True)
        else:
            st.info("No delivery boy extra charges recorded yet.")

# ==================== MODULE: CUSTOMER FEEDBACK (ADMIN) ====================
elif nav_selection == "⭐ Customer Feedback":
    if user_role != "👑 Admin":
        st.error("🔒 Access Restricted to Admin Only.")
    else:
        st.subheader("⭐ Customer Feedback Received")
        fb_df = load_data("customer_feedback")
        if fb_df.empty:
            st.info("No feedback received yet.")
        else:
            f1, f2, f3, f4 = st.columns(4)
            f1.metric("Total Responses", len(fb_df))
            f2.metric("Avg Overall", f"{pd.to_numeric(fb_df['overall_rating'], errors='coerce').mean():.1f} / 5")
            f3.metric("Avg Quality", f"{pd.to_numeric(fb_df['quality_rating'], errors='coerce').mean():.1f} / 5")
            f4.metric("Avg Delivery", f"{pd.to_numeric(fb_df['delivery_rating'], errors='coerce').mean():.1f} / 5")
            low = fb_df[pd.to_numeric(fb_df["overall_rating"], errors="coerce") <= 2]
            if not low.empty:
                st.markdown(f'<div class="alert-red">🚨 {len(low)} low-rating feedback(s) (2★ or below) need attention!</div>', unsafe_allow_html=True)
            st.dataframe(fb_df.sort_values("submitted_at", ascending=False), use_container_width=True)

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

        dc_charge = DELIVERY_CHARGE_PER_ORDER if cust_type == "Delivery" else 0.0
        if cust_type == "Delivery":
            st.caption(f"🔒 Delivery boy charge ₹{DELIVERY_CHARGE_PER_ORDER:,.0f} will be auto-recorded for this order (internal only, NOT shown on client bill).")

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
                    "special_instructions": "", "assigned_delivery": "Unassigned",
                    "delivery_charge": float(dc_charge)
                })
                st.success(f"Order Registered: {new_id}")
                
                st.session_state.last_bill_billing = {
                    "order_id": new_id, "customer_name": cust_name, "mobile": str(mobile),
                    "service": service, "items": int(items), "weight_kg": float(weight_kg),
                    "total": float(total), "paid": float(paid), "balance": float(bal),
                    "promised_date": str(promised_date), "order_type": cust_type
                }

    if st.session_state.get("last_bill_billing"):
        st.markdown("---")
        render_bill_section(st.session_state.last_bill_billing, "billing")

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
                st.session_state.last_delivered_id = sel_id if new_st == "Delivered" else None
                st.success(f"Order {sel_id} updated to {new_st}!")
                st.rerun()

            current_order_status = target["order_status"]
            # DIRECT WHATSAPP READY NOTIFICATION BUTTON (Auto triggers when stage is Ready)
            if current_order_status == "Ready" or st.session_state.last_updated_ready_id == sel_id:
                wa_ready = build_ready_message(sel_id, target['customer_name'], target['service'], target['balance_amount'])
                wa_ready_url = build_wa_url(target['mobile'], wa_ready)
                st.markdown(f'<a href="{wa_ready_url}" target="_blank" class="wa-link-btn" style="background:#0284C7 !important;">📲 Send "Garments Ready" WhatsApp Confirmation</a>', unsafe_allow_html=True)

            # FEEDBACK FORM TO CLIENT AFTER FINAL DELIVERY
            if current_order_status == "Delivered" or st.session_state.get("last_delivered_id") == sel_id:
                wa_fb = build_feedback_request_message(sel_id, target['customer_name'])
                wa_fb_url = build_wa_url(target['mobile'], wa_fb)
                st.markdown(f'<a href="{wa_fb_url}" target="_blank" class="wa-link-btn" style="background:#7C3AED !important;">⭐ Send Review Request to Client (WhatsApp)</a>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        disp_df = orders_df.copy()
        if user_role != "👑 Admin":
            disp_df["mobile"] = disp_df["mobile"].apply(mask_mobile)
            disp_df = disp_df.drop(columns=["delivery_charge"], errors="ignore")
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
            history_df = history_df.drop(columns=["delivery_charge"], errors="ignore")
            
        st.dataframe(history_df, use_container_width=True)

# ==================== MODULE: FINANCIAL ANALYTICS & GRAPH ====================
elif nav_selection == "📈 Financial Analytics":
    if user_role not in ["👑 Admin", "👩‍💼 Reception"]:
        st.error("🔒 Access Restricted to Admin and Reception Only.")
    else:
        st.subheader("📈 Financial Analytics & Weekly Performance")
        expenses_df = load_data("expenses")
        
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
        
        customers_df = load_data("customers")
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

# ==================== MODULE: STAFF SALARY & ADVANCES ====================
elif nav_selection == "👥 Staff Salary & Advances":
    if user_role != "👑 Admin":
        st.error("🔒 Access Restricted to Admin Only.")
    else:
        st.subheader("👥 Staff Salary & Advance Manager")
        st.caption("Month-la staff advance vanguna, antha amount salary-la irundhu auto-deduct aagum. Balance mattum pay pannanum.")

        adv_df = load_data("staff_advances")
        pay_df = load_data("staff_salary_payments")
        if adv_df.empty:
            adv_df = pd.DataFrame(columns=["id", "date", "month", "staff_name", "amount", "note"])
        if pay_df.empty:
            pay_df = pd.DataFrame(columns=["id", "month", "staff_name", "gross_salary", "advance_deducted", "net_paid", "paid_date", "note"])
        adv_df["amount"] = pd.to_numeric(adv_df["amount"], errors="coerce").fillna(0.0)

        # Last 12 months list (current month first)
        month_options = []
        _y, _m = today.year, today.month
        for _ in range(12):
            month_options.append(f"{_y}-{_m:02d}")
            _m -= 1
            if _m == 0:
                _m, _y = 12, _y - 1
        sel_month = st.selectbox("📅 Salary Month", month_options)

        def _month_advance(staff, month):
            if adv_df.empty:
                return 0.0
            mask = (adv_df["staff_name"] == staff) & (adv_df["month"].astype(str) == month)
            return float(adv_df.loc[mask, "amount"].sum())

        def _month_payment(staff, month):
            if pay_df.empty:
                return None
            m = pay_df[(pay_df["staff_name"] == staff) & (pay_df["month"].astype(str) == month)]
            return None if m.empty else m.iloc[0]

        s_tab1, s_tab2, s_tab3 = st.tabs(["💵 Salary Summary & Pay", "➕ Give Advance", "📚 Advance & Payment History"])

        # ---------- TAB 1: SUMMARY & PAY ----------
        with s_tab1:
            summary_rows = []
            total_sal = total_adv = total_bal = 0.0
            for s_name, s_info in STAFF_DETAILS.items():
                sal = s_info["salary"]
                adv = _month_advance(s_name, sel_month)
                bal = max(sal - adv, 0.0)
                paid = _month_payment(s_name, sel_month)
                total_sal += sal
                total_adv += adv
                total_bal += bal
                summary_rows.append({
                    "Staff": s_name, "Role": s_info["role"], "Salary (₹)": sal,
                    "Advance Taken (₹)": adv, "Balance To Pay (₹)": bal,
                    "Status": "✅ Paid" if paid is not None else "⏳ Pending"
                })
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Salary", f"₹{total_sal:,.0f}")
            m2.metric("Total Advance Given", f"₹{total_adv:,.0f}")
            m3.metric("Total Balance To Pay", f"₹{total_bal:,.0f}")
            st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)

            st.markdown("#### Pay Salary")
            for s_name, s_info in STAFF_DETAILS.items():
                sal = s_info["salary"]
                adv = _month_advance(s_name, sel_month)
                bal = max(sal - adv, 0.0)
                paid = _month_payment(s_name, sel_month)
                with st.container(border=True):
                    c1, c2 = st.columns([3, 2])
                    with c1:
                        st.markdown(f"**{s_name}** — {s_info['role']}")
                        st.markdown(f"Salary ₹{sal:,.0f} − Advance ₹{adv:,.0f} = **Balance ₹{bal:,.0f}**")
                        if adv > sal:
                            st.warning(f"⚠️ Advance (₹{adv:,.0f}) is more than salary. Excess ₹{adv - sal:,.0f} - next month-la recover pannunga.")
                    with c2:
                        if paid is not None:
                            st.success(f"✅ Paid ₹{float(paid['net_paid']):,.0f} on {paid['paid_date']}")
                        else:
                            if st.button(f"✅ Mark Paid ₹{bal:,.0f}", key=f"pay_{s_name}_{sel_month}"):
                                ok = save_record("staff_salary_payments", {
                                    "month": sel_month, "staff_name": s_name,
                                    "gross_salary": float(sal), "advance_deducted": float(adv),
                                    "net_paid": float(bal), "paid_date": str(today),
                                    "note": f"Salary {sel_month}"
                                })
                                if ok:
                                    # Full salary is booked as ONE expense (advance + balance) so there is no double counting
                                    save_record("expenses", {
                                        "date": str(today), "expense_category": "Staff Salary",
                                        "description": f"{s_name} salary {sel_month} (Advance ₹{adv:,.0f} + Paid ₹{bal:,.0f})",
                                        "amount": float(sal)
                                    })
                                    st.success(f"{s_name} salary marked as paid!")
                                    st.rerun()

        # ---------- TAB 2: GIVE ADVANCE ----------
        with s_tab2:
            with st.container(border=True):
                a1, a2 = st.columns(2)
                with a1:
                    adv_staff = st.selectbox("Staff Name", list(STAFF_DETAILS.keys()))
                    adv_date = st.date_input("Advance Date", value=today, key="adv_date")
                with a2:
                    adv_amt = st.number_input("Advance Amount (₹)", min_value=0.0, step=100.0, key="adv_amt")
                    adv_note = st.text_input("Note (optional)", key="adv_note")

                adv_month = adv_date.strftime("%Y-%m")
                cur_adv = _month_advance(adv_staff, adv_month)
                cur_sal = STAFF_DETAILS[adv_staff]["salary"]
                st.info(f"{adv_staff} - {adv_month}: Salary ₹{cur_sal:,.0f} | Advance already taken ₹{cur_adv:,.0f} | Remaining ₹{max(cur_sal - cur_adv, 0):,.0f}")

                if st.button("💾 Save Advance", type="primary"):
                    if adv_amt <= 0:
                        st.error("Please enter a valid advance amount.")
                    elif _month_payment(adv_staff, adv_month) is not None:
                        st.error(f"{adv_staff}-ku {adv_month} salary already paid. Next month date select pannunga.")
                    else:
                        if cur_adv + adv_amt > cur_sal:
                            st.warning("Total advance is more than salary for this month!")
                        if save_record("staff_advances", {
                            "date": str(adv_date), "month": adv_month, "staff_name": adv_staff,
                            "amount": float(adv_amt), "note": adv_note
                        }):
                            st.success(f"✅ ₹{adv_amt:,.0f} advance saved for {adv_staff}!")
                            st.rerun()

        # ---------- TAB 3: HISTORY ----------
        with s_tab3:
            st.markdown(f"#### Advances - {sel_month}")
            month_adv = adv_df[adv_df["month"].astype(str) == sel_month] if not adv_df.empty else adv_df
            if month_adv.empty:
                st.info("No advances recorded for this month.")
            else:
                st.dataframe(month_adv[["date", "staff_name", "amount", "note"]], use_container_width=True, hide_index=True)
                del_opts = {f"{r['date']} | {r['staff_name']} | ₹{r['amount']:,.0f}": r["id"] for _, r in month_adv.iterrows()}
                del_label = st.selectbox("Wrong entry delete panna select pannunga", ["-- None --"] + list(del_opts.keys()))
                if del_label != "-- None --" and st.button("🗑️ Delete Selected Advance"):
                    _row = month_adv[month_adv["id"] == del_opts[del_label]].iloc[0]
                    if _month_payment(_row["staff_name"], sel_month) is not None:
                        st.error("Salary already paid for this month - cannot delete this advance.")
                    elif delete_record("staff_advances", "id", int(del_opts[del_label])):
                        st.success("Advance deleted.")
                        st.rerun()

            st.markdown("#### Salary Payments (All Months)")
            if pay_df.empty:
                st.info("No salary payments recorded yet.")
            else:
                st.dataframe(pay_df[["month", "staff_name", "gross_salary", "advance_deducted", "net_paid", "paid_date"]].sort_values("month", ascending=False),
                             use_container_width=True, hide_index=True)

# ==================== MODULE: ACTIVE DEVICE CONTROL ====================
elif nav_selection == "🔒 Active Device Control":
    if user_role != "👑 Admin":
        st.error("🔒 Access Restricted to Admin Only.")
    else:
        st.subheader("🔒 Active Device & Remote Session Manager")
        sessions_df = load_data("active_sessions")
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
    leads_df = load_data("marketing_leads")
    
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
    leads_df = load_data("marketing_leads")
    if not leads_df.empty:
        converted_leads = leads_df[leads_df["status"] == "Converted"].copy()
        if not converted_leads.empty:
            if user_role != "👑 Admin":
                converted_leads["mobile"] = converted_leads["mobile"].apply(mask_mobile)
            st.dataframe(converted_leads[["lead_id", "customer_name", "mobile", "followup_date", "notes"]], use_container_width=True)
