import io
import streamlit as st
import pandas as pd
from supabase import create_client, Client

# PDF Generation Libraries (ReportLab)
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# ---------------------------------------------------------
# ૧. PAGE CONFIG & DELUX THEME STYLING
# ---------------------------------------------------------
st.set_page_config(
    page_title="DELUX COURIER SERVICES - Enterprise Portal", 
    layout="wide", 
    page_icon="🚚"
)

# Custom Styling for Delux Blue & Green Theme + InfoSoft Look
st.markdown("""
<style>
    .delux-header {
        background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
        padding: 18px;
        border-radius: 10px;
        color: white;
        text-align: center;
        box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.2);
        margin-bottom: 20px;
    }
    .delux-logo-text {
        font-size: 30px;
        font-weight: 800;
        letter-spacing: 2px;
        color: #00FF87;
    }
    .delux-subtext {
        font-size: 13px;
        color: #60EFFF;
    }
    .quick-bar {
        background-color: #1e293b;
        padding: 10px;
        border-radius: 8px;
        color: #f8fafc;
        border-left: 5px solid #10b981;
        margin-bottom: 15px;
    }
    .stButton>button {
        background: linear-gradient(90deg, #059669 0%, #10b981 100%);
        color: white;
        font-weight: bold;
        border-radius: 6px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# ૨. SUPABASE CONNECTIVITY
# ---------------------------------------------------------
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = init_supabase()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.branch_code = None
    st.session_state.branch_name = None
    st.session_state.branch_id = None

# ---------------------------------------------------------
# ૩. PDF UTILITIES
# ---------------------------------------------------------
def generate_awb_pdf(awb, mode, sender, receiver, dest, weight, amount):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=(300, 400), rightMargin=10, leftMargin=10, topMargin=10, bottomMargin=10)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("<b>DELUX COURIER SERVICES</b>", styles['Title']))
    story.append(Paragraph(f"<b>Booking Type: {mode}</b>", styles['Normal']))
    story.append(Spacer(1, 5))
    story.append(Paragraph(f"<b>AWB NO: {awb}</b>", styles['Heading2']))
    story.append(Spacer(1, 10))

    data = [
        ["Sender:", sender],
        ["Receiver:", receiver],
        ["Destination:", dest],
        ["Weight (Kg):", str(weight)],
        ["Total Amount:", f"INR {amount}"]
    ]
    
    t = Table(data, colWidths=[80, 190])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.whitesmoke),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
    ]))
    story.append(t)
    story.append(Spacer(1, 10))
    story.append(Paragraph("<i>Fast & Reliable Express Logistics</i>", styles['Italic']))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# ---------------------------------------------------------
# ૪. HEADER & TRACKING
# ---------------------------------------------------------
st.markdown("""
<div class="delux-header">
    <div class="delux-logo-text">⚡ DELUX COURIER SERVICES</div>
    <div class="delux-subtext">Express Cargo & Parcel Logistics Network | InfoSoft Modular Interface</div>
</div>
""", unsafe_allow_html=True)

def render_public_tracking():
    st.subheader("🔍 Document / Consignment Tracking")
    search_awb = st.text_input("Enter Document / Barcode Number:", placeholder="ઉદા. 1477307197")
    if st.button("Track Document"):
        if search_awb:
            res = supabase.table("consignments").select("*").eq("awb_number", search_awb).execute()
            if res.data:
                item = res.data[0]
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("AWB Number", item["awb_number"])
                c2.metric("Destination", item["destination_city"])
                c3.metric("Status", item["status"])
                c4.metric("Booking Mode", item.get("payment_mode", "Cash"))
                st.success(f"📍 **Receiver:** {item['receiver_name']} | **Address:** {item['receiver_address']} | **Phone:** {item['receiver_phone']}")
            else:
                st.error("❌ No record found for this AWB number.")
        else:
            st.warning("Please enter an AWB number.")

# ---------------------------------------------------------
# ૫. LOGIN & MAIN ROUTING
# ---------------------------------------------------------
if not st.session_state.logged_in:
    col1, col2 = st.columns([1, 1.2])
    with col1:
        st.subheader("🔐 System Login")
        b_code = st.text_input("User ID / Branch Code", placeholder="HO001 or BHAVNAGAR")
        pwd = st.text_input("Password", type="password")
        if st.button("Login"):
            res = supabase.table("branches").select("*").eq("branch_code", b_code).execute()
            if res.data:
                user = res.data[0]
                st.session_state.logged_in = True
                st.session_state.role = user["role"]
                st.session_state.branch_code = user["branch_code"]
                st.session_state.branch_name = user["branch_name"]
                st.session_state.branch_id = user["id"]
                st.success(f"Welcome, {user['branch_name']}!")
                st.rerun()
            else:
                st.error("Invalid Branch Code or User ID!")
    with col2:
        render_public_tracking()
else:
    st.markdown(f"""
    <div class="quick-bar">
        🟢 <b>Current Center:</b> {st.session_state.branch_name} ({st.session_state.branch_code}) | 
        🛡️ <b>Role:</b> {st.session_state.role.upper()} | 
        📅 <b>Date:</b> {pd.Timestamp.now().strftime('%Y-%m-%d')}
    </div>
    """, unsafe_allow_html=True)
    
    if st.sidebar.button("🚪 LogOff / Logout"):
        st.session_state.logged_in = False
        st.rerun()

    # ADMIN & BRANCH NAVIGATION
    if st.session_state.role == "admin":
        st.sidebar.title("📌 Master Entries & Transactions")
        menu = st.sidebar.radio("Navigation Menu", [
            "🏠 Center Master Setup",
            "📝 Cash Booking Entry",
            "📊 Account Booking Entry",
            "📦 Manifest / Outgoing",
            "🔎 Track & Reports"
        ])
    else:
        st.sidebar.title(f"🚚 {st.session_state.branch_code} Menu")
        menu = st.sidebar.radio("Branch Menu", [
            "📝 Cash Booking Entry",
            "📊 Account Booking Entry",
            "📦 Inward / Outward Manifest",
            "🔎 Track Document"
        ])

    # ---------------------------------------------------------
    # MODULE 1: CENTER MASTER SETUP (Admin Only)
    # ---------------------------------------------------------
    if menu == "🏠 Center Master Setup":
        st.subheader("🏭 Master Entries: Center / Branch Master Setup")
        with st.form("branch_setup"):
            c1, c2 = st.columns(2)
            with c1:
                nc_code = st.text_input("Center Code", placeholder="CHITRA")
                nc_name = st.text_input("Center Name", placeholder="Bhavnagar Chitra Branch")
            with c2:
                nc_city = st.text_input("City", placeholder="Bhavnagar")
                nc_phone = st.text_input("Contact Number")
            if st.form_submit_button("Save Center Master"):
                supabase.table("branches").insert({
                    "branch_code": nc_code,
                    "branch_name": nc_name,
                    "city": nc_city,
                    "contact_number": nc_phone,
                    "role": "branch"
                }).execute()
                st.success(f"Center [{nc_code}] saved successfully!")
        
        st.divider()
        st.subheader("📋 Registered Centers List")
        res = supabase.table("branches").select("*").execute()
        if res.data:
            st.dataframe(pd.DataFrame(res.data), use_container_width=True)

    # ---------------------------------------------------------
    # MODULE 2: CASH BOOKING ENTRY (InfoSoft Style)
    # ---------------------------------------------------------
    elif menu == "📝 Cash Booking Entry":
        st.subheader("📦 DOCUMENT TRANSIT BOOKING RECEIPT ENTRY (Cash Transaction)")
        
        with st.form("cash_booking", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                awb = st.text_input("Document / Barcode Number", placeholder="1477307197")
                doc_type = st.selectbox("Document Type", ["Documents", "Parcel", "Non-Doc"])
                sender_name = st.text_input("Sender Name")
                sender_mob = st.text_input("Sender Mobile")
            with col2:
                dest_city = st.text_input("Destination City / Area", placeholder="Ahmedabad")
                receiver_name = st.text_input("Receiver Name")
                receiver_mob = st.text_input("Receiver Mobile")
                receiver_addr = st.text_area("Receiver Full Address")
            with col3:
                weight = st.number_input("Weight (Gms / Kg)", value=100.0)
                pieces = st.number_input("No. of Pcs", value=1, min_value=1)
                freight = st.number_input("Freight Amount (₹)", value=100.0)
                tax_amt = freight * 0.18 # 18% GST calculation
                net_total = freight + tax_amt
                st.metric("Net Booking Amount (₹)", f"{net_total:.2f}")

            submitted = st.form_submit_button("💾 SAVE & PRINT AWB")
            
            if submitted:
                if awb and dest_city:
                    supabase.table("consignments").insert({
                        "awb_number": awb,
                        "origin_branch_id": st.session_state.branch_id,
                        "destination_city": dest_city,
                        "sender_name": sender_name,
                        "sender_phone": sender_mob,
                        "receiver_name": receiver_name,
                        "receiver_address": receiver_addr,
                        "receiver_phone": receiver_mob,
                        "weight_kg": weight,
                        "pieces": pieces,
                        "charge_amount": net_total,
                        "payment_mode": "Cash",
                        "status": "In Transit"
                    }).execute()
                    
                    st.success(f"✅ Cash Booking Saved Successfully! AWB: {awb}")
                    
                    pdf = generate_awb_pdf(awb, "Cash Booking", sender_name, receiver_name, dest_city, weight, net_total)
                    st.download_button("🖨️ Download Receipt PDF", pdf, f"Receipt_{awb}.pdf", "application/pdf")
                else:
                    st.error("Document Number and Destination are mandatory!")

    # ---------------------------------------------------------
    # MODULE 3: ACCOUNT BOOKING ENTRY (InfoSoft Style)
    # ---------------------------------------------------------
    elif menu == "📊 Account Booking Entry":
        st.subheader("📊 DOCUMENT TRANSIT BOOKING RECEIPT ENTRY (Account Transaction)")
        
        with st.form("account_booking", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                party_name = st.selectbox("Party Account Name / Code", ["Select Party", "Party A (Corporate)", "Party B (Regulog)"])
                awb = st.text_input("Document / Barcode Number", placeholder="1109244861")
                doc_type = st.selectbox("Document Type", ["Documents", "Parcel"])
                sender_name = st.text_input("Sender Name")
            with col2:
                dest_city = st.text_input("Destination City", placeholder="Surat")
                receiver_name = st.text_input("Receiver Name")
                receiver_mob = st.text_input("Receiver Mobile")
                receiver_addr = st.text_area("Receiver Address")
            with col3:
                weight = st.number_input("Weight (Kg)", value=100.0)
                pieces = st.number_input("No. of Pcs", value=1)
                freight = st.number_input("Freight Amount (₹)", value=150.0)
                st.metric("Account Billing Total", f"₹ {freight}")

            submitted_acc = st.form_submit_button("💾 SAVE ACCOUNT BOOKING")
            
            if submitted_acc:
                if awb and party_name != "Select Party":
                    supabase.table("consignments").insert({
                        "awb_number": awb,
                        "origin_branch_id": st.session_state.branch_id,
                        "destination_city": dest_city,
                        "sender_name": f"{party_name} - {sender_name}",
                        "receiver_name": receiver_name,
                        "receiver_address": receiver_addr,
                        "receiver_phone": receiver_mob,
                        "weight_kg": weight,
                        "pieces": pieces,
                        "charge_amount": freight,
                        "payment_mode": "Account",
                        "status": "In Transit"
                    }).execute()
                    st.success(f"✅ Account Booking Saved for [{party_name}]! AWB: {awb}")
                else:
                    st.error("Please select a valid Party and enter AWB number.")

    # ---------------------------------------------------------
    # MODULE 4: MANIFEST & REPORTS
    # ---------------------------------------------------------
    elif menu in ["📦 Manifest / Outgoing", "📦 Inward / Outward Manifest"]:
        st.subheader("📦 Manifest & Transit Management")
        city_f = st.text_input("Filter by Destination City:")
        if st.button("Load Manifest"):
            res = supabase.table("consignments").select("*").eq("destination_city", city_f).execute()
            if res.data:
                st.dataframe(pd.DataFrame(res.data), use_container_width=True)
            else:
                st.info("No consignments found for this destination.")

    elif menu in ["🔎 Track & Reports", "🔎 Track Document"]:
        render_public_tracking()
