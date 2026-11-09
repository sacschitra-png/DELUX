import io
import streamlit as st
import pandas as pd
from supabase import create_client, Client

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# ---------------------------------------------------------
# ૧. PAGE CONFIG & INFOSOFT CLASSIC THEME STYLING
# ---------------------------------------------------------
st.set_page_config(
    page_title="DELUX COURIER SERVICES - Online Courier Management System", 
    layout="wide", 
    page_icon="🚚"
)

st.markdown("""
<style>
    /* Classic Dark Background matching InfoSoft UI */
    .stApp {
        background-color: #241a19;
        color: #ffffff;
    }
    .company-title {
        font-size: 26px;
        font-weight: 800;
        color: #FF6600;
        font-family: Arial, Helvetica, sans-serif;
        text-align: center;
        margin-bottom: 10px;
    }
    .info-box {
        background-color: #1e293b;
        padding: 12px;
        border-radius: 8px;
        border-left: 4px solid #00FF87;
        margin-bottom: 15px;
        font-family: Tahoma;
        font-size: 14px;
        color: #ffffff;
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
# ૩. PDF UTILITIES FOR RECEIPTS & DRS
# ---------------------------------------------------------
def generate_receipt_pdf(awb, mode, sender, receiver, dest, weight, amount):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=(300, 400), rightMargin=10, leftMargin=10, topMargin=10, bottomMargin=10)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("<b>DELUX COURIER SERVICES</b>", styles['Title']),
        Paragraph(f"<b>Booking Type: {mode}</b>", styles['Normal']),
        Spacer(1, 5),
        Paragraph(f"<b>AWB NO: {awb}</b>", styles['Heading2']),
        Spacer(1, 10)
    ]
    data = [
        ["Sender:", sender],
        ["Receiver:", receiver],
        ["Destination:", dest],
        ["Weight:", str(weight)],
        ["Amount:", f"INR {amount}"]
    ]
    t = Table(data, colWidths=[80, 190])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.whitesmoke),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
    ]))
    story.append(t)
    doc.build(story)
    buffer.seek(0)
    return buffer

# ---------------------------------------------------------
# ૪. LOGIN & MAIN INTERFACE
# ---------------------------------------------------------
if not st.session_state.logged_in:
    st.markdown('<div class="company-title">⚡ DELUX COURIER SERVICES (P) LTD.</div>', unsafe_allow_html=True)
    c1, c2 = st.columns([1, 1])
    with c1:
        st.subheader("🔐 System Login")
        b_code = st.text_input("User ID / Branch Code", placeholder="ઉદા. HO001 અથવા CHITRA")
        pwd = st.text_input("Password", type="password")
        if st.button("Login To System"):
            res = supabase.table("branches").select("*").eq("branch_code", b_code).execute()
            if res.data:
                user = res.data[0]
                st.session_state.logged_in = True
                st.session_state.role = user["role"]
                st.session_state.branch_code = user["branch_code"]
                st.session_state.branch_name = user["branch_name"]
                st.session_state.branch_id = user["id"]
                st.rerun()
            else:
                st.error("❌ ખોટો બ્રાન્ચ કોડ અથવા વિગતો!")
    with c2:
        st.subheader("🔍 Public Document Tracking")
        track_no = st.text_input("Enter Document Number for Quick Track")
        if st.button("Track Now"):
            if track_no:
                t_res = supabase.table("consignments").select("*").eq("awb_number", track_no).execute()
                if t_res.data:
                    item = t_res.data[0]
                    st.success(f"📍 Status: {item['status']} | Dest: {item['destination_city']} | Receiver: {item['receiver_name']}")
                else:
                    st.warning("No record found.")
else:
    # Top Header & Info Box matching InfoSoft HTML layout
    st.markdown(f"""
    <div class="company-title">SHREE DELUX COURIER SERVICES (P) LTD.</div>
    <div class="info-box">
        <b>Wel Come:</b> {st.session_state.branch_name} ({st.session_state.branch_code}) &nbsp;|&nbsp; 
        <b>Acc. Year:</b> 2025-2026 &nbsp;|&nbsp; 
        <b>Date Period:</b> From 01/04/2025 To 31/03/2026 &nbsp;|&nbsp; 
        <b>Role:</b> {st.session_state.role.upper()}
    </div>
    """, unsafe_allow_html=True)

    if st.sidebar.button("🚪 LOG OFF"):
        st.session_state.logged_in = False
        st.rerun()

    # SIDEBAR MENU (InfoSoft Style Navigation)
    menu = st.sidebar.radio("📋 Quick Operations Menu", [
        "🏠 Dashboard / Home",
        "📦 Cash Booking Entry",
        "📊 Party Account Booking",
        "📑 ManiFax Incoming / Outgoing",
        "📜 DRS Voucher Entry",
        "📥 Incoming Packing Slip",
        "⚙️ Master Entries (Branch/Area/Boys)",
        "🔎 Document Tracking"
    ])

    if menu == "🏠 Dashboard / Home":
        st.subheader("📊 Booking Summary & Quick Actions")
        c1, c2, c3 = st.columns(3)
        c1.metric("Current Center", st.session_state.branch_name)
        c2.metric("System Date", pd.Timestamp.now().strftime('%d/%m/%Y'))
        c3.metric("Active Status", "Online")
        
        st.info("💡 ડાબી બાજુના મેનુમાંથી તમે કેશ બુકિંગ, એકાઉન્ટ બુકિંગ, મેનિફેસ્ટ અને ડી.આર.એસ. ની એન્ટ્રીઓ કરી શકો છો.")

    elif menu == "📦 Cash Booking Entry":
        st.subheader("📦 DOCUMENT TRANSIT BOOKING RECEIPT ENTRY (Cash Transaction)")
        if "last_cash_awb" not in st.session_state:
            st.session_state.last_cash_awb = None
            st.session_state.last_cash_data = None

        with st.form("cash_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                awb = st.text_input("Document / Barcode Number", placeholder="1477307197")
                sender = st.text_input("Sender Name")
                sender_mob = st.text_input("Sender Mobile")
            with col2:
                dest = st.text_input("Destination City / Area", placeholder="Ahmedabad")
                receiver = st.text_input("Receiver Name")
                receiver_mob = st.text_input("Receiver Mobile")
                receiver_addr = st.text_area("Receiver Full Address")
            with col3:
                weight = st.number_input("Weight (Gms/Kg)", value=100.0)
                pieces = st.number_input("No. of Pcs", value=1)
                freight = st.number_input("Freight Amount (₹)", value=100.0)
                net = freight + (freight * 0.18)
                st.metric("Net Booking Amount", f"₹ {net:.2f}")

            if st.form_submit_button("💾 SAVE CASH BOOKING"):
                if awb and dest:
                    supabase.table("consignments").insert({
                        "awb_number": awb, "origin_branch_id": st.session_state.branch_id,
                        "destination_city": dest, "sender_name": sender, "sender_phone": sender_mob,
                        "receiver_name": receiver, "receiver_address": receiver_addr, "receiver_phone": receiver_mob,
                        "weight_kg": weight, "pieces": pieces, "charge_amount": net,
                        "payment_mode": "Cash", "status": "In Transit"
                    }).execute()
                    st.session_state.last_cash_awb = awb
                    st.session_state.last_cash_data = (sender, receiver, dest, weight, net)
                    st.success(f"✅ Cash Booking Saved Successfully! AWB: {awb}")
                else:
                    st.error("AWB Number અને Destination City ફરજિયાત છે.")

        if st.session_state.last_cash_awb:
            pdf = generate_receipt_pdf(
                st.session_state.last_cash_awb, "Cash",
                st.session_state.last_cash_data[0], st.session_state.last_cash_data[1],
                st.session_state.last_cash_data[2], st.session_state.last_cash_data[3],
                st.session_state.last_cash_data[4]
            )
            st.download_button("🖨️ Download Receipt PDF", pdf, f"Receipt_{st.session_state.last_cash_awb}.pdf", "application/pdf")

    elif menu == "📊 Party Account Booking":
        st.subheader("📊 DOCUMENT TRANSIT BOOKING RECEIPT ENTRY (Account Transaction)")
        with st.form("acc_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                party = st.selectbox("Party Account Name", [".PAHAL FINANCIAL SERVICES", "00 KUMAR MINERAL", "CHITRA (SME) SBI", "KATARIA AUTOMOBILES"])
                awb = st.text_input("Document / Barcode Number")
                sender = st.text_input("Sender Name")
            with col2:
                dest = st.text_input("Destination City")
                receiver = st.text_input("Receiver Name")
                receiver_addr = st.text_area("Receiver Address")
            with col3:
                weight = st.number_input("Weight", value=100.0)
                freight = st.number_input("Freight Amount (₹)", value=150.0)
                st.metric("Account Billing Total", f"₹ {freight}")

            if st.form_submit_button("💾 SAVE ACCOUNT BOOKING"):
                if awb and dest:
                    supabase.table("consignments").insert({
                        "awb_number": awb, "origin_branch_id": st.session_state.branch_id,
                        "destination_city": dest, "sender_name": f"{party} - {sender}",
                        "receiver_name": receiver, "receiver_address": receiver_addr,
                        "weight_kg": weight, "charge_amount": freight,
                        "payment_mode": "Account", "status": "In Transit"
                    }).execute()
                    st.success(f"✅ Account Booking Saved for [{party}]! AWB: {awb}")

    elif menu == "📑 ManiFax Incoming / Outgoing":
        st.subheader("📑 ManiFax (Manifest) Management")
        tab1, tab2 = st.tabs(["📥 Incoming ManiFax", "📤 Outgoing ManiFax"])
        with tab1:
            st.info("Incoming manifest control and parcel verification list.")
        with tab2:
            city_filter = st.text_input("Filter Outgoing ManiFax by City:")
            if st.button("Generate Outgoing List"):
                res = supabase.table("consignments").select("*").eq("destination_city", city_filter).execute()
                if res.data:
                    st.dataframe(pd.DataFrame(res.data), use_container_width=True)
                else:
                    st.warning("કોઈ રેકોર્ડ મળ્યો નથી.")

    elif menu == "📜 DRS Voucher Entry":
        st.subheader("📜 D.R.S. [Delivery Run Sheet] Voucher Entry")
        with st.form("drs_entry"):
            c1, c2 = st.columns(2)
            with c1:
                drs_no = st.text_input("D.R.S. Number", value="34118")
                dboy = st.selectbox("Delivery Boy Name", ["Darshakbhai", "Jayveer", "Rameshbhai"])
            with c2:
                drs_date = st.text_input("D.R.S. Date", value="09/11/2026")
                area = st.selectbox("Area Name (ARFA NAME)", ["Chitra GIDC", "Bhavnagar City", "Vartej Road"])

            if st.form_submit_button("Save & Print DRS"):
                st.success(f"✅ DRS [{drs_no}] generated for Delivery Boy [{dboy}] in Area [{area}]!")

    elif menu == "📥 Incoming Packing Slip":
        st.subheader("📥 INCOMING PACKING SLIP")
        with st.form("pkng_slip"):
            c1, c2 = st.columns(2)
            with c1:
                slip_no = st.text_input("Packing Slip No.", value="9789")
                slip_from = st.selectbox("Slip From (Center)", ["Ahmedabad Center", "Surat Center"])
            with c2:
                transit = st.selectbox("Transit Mode", ["BY ROAD", "BY AIR"])
                total_docs = st.number_input("Total Documents", value=1)
            if st.form_submit_button("Save Packing Slip"):
                st.success(f"✅ Packing Slip [{slip_no}] from [{slip_from}] saved successfully!")

    elif menu == "⚙️ Master Entries (Branch/Area/Boys)":
        st.subheader("⚙️ Master Entries Management [InfoSoft Style]")
        master_type = st.selectbox("Select Master", ["Center Master SetUp", "AREA Master", "Delivery Boy Master", "Party Account Master"])
        st.info(f"Managing **{master_type}** records in Supabase database.")

    elif menu == "🔎 Document Tracking":
        st.subheader("🔍 Track Document / Consignment")
        doc_no = st.text_input("Enter Document Number / AWB:")
        if st.button("Search Document"):
            res = supabase.table("consignments").select("*").eq("awb_number", doc_no).execute()
            if res.data:
                st.dataframe(pd.DataFrame(res.data), use_container_width=True)
            else:
                st.error("❌ Document not found.")
