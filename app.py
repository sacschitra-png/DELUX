import io
import streamlit as st
import pandas as pd
from supabase import create_client, Client

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

st.set_page_config(page_title="DELUX COURIER SERVICES", layout="wide", page_icon="🚚")

st.markdown("""
<style>
    .delux-header {
        background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
        padding: 18px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 20px;
    }
    .delux-logo-text { font-size: 30px; font-weight: 800; color: #00FF87; }
    .quick-bar { background-color: #1e293b; padding: 10px; border-radius: 8px; color: #f8fafc; border-left: 5px solid #10b981; margin-bottom: 15px; }
    .stButton>button { background: linear-gradient(90deg, #059669 0%, #10b981 100%); color: white; font-weight: bold; border-radius: 6px; }
</style>
""", unsafe_allow_html=True)

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

st.markdown("""
<div class="delux-header">
    <div class="delux-logo-text">⚡ DELUX COURIER SERVICES</div>
    <div style="color: #60EFFF; font-size: 13px;">Express Cargo & Parcel Logistics Network</div>
</div>
""", unsafe_allow_html=True)

def render_public_tracking():
    st.subheader("🔍 Document / Consignment Tracking")
    search_awb = st.text_input("Enter Document Number:", placeholder="ઉદા. 1477307197")
    if st.button("Track Document"):
        if search_awb:
            res = supabase.table("consignments").select("*").eq("awb_number", search_awb).execute()
            if res.data:
                item = res.data[0]
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("AWB Number", item["awb_number"])
                c2.metric("Destination", item["destination_city"])
                c3.metric("Status", item["status"])
                c4.metric("Mode", item.get("payment_mode", "Cash"))
                st.success(f"📍 **Receiver:** {item['receiver_name']} | **Address:** {item['receiver_address']} | **Phone:** {item['receiver_phone']}")
            else:
                st.error("❌ No record found.")
        else:
            st.warning("Please enter AWB number.")

if not st.session_state.logged_in:
    c1, c2 = st.columns([1, 1.2])
    with c1:
        st.subheader("🔐 System Login")
        b_code = st.text_input("User ID / Branch Code", placeholder="HO001")
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
                st.rerun()
            else:
                st.error("Invalid Branch Code!")
    with c2:
        render_public_tracking()
else:
    st.markdown(f"""
    <div class="quick-bar">
        🟢 <b>Current Center:</b> {st.session_state.branch_name} ({st.session_state.branch_code}) | 
        🛡️ <b>Role:</b> {st.session_state.role.upper()}
    </div>
    """, unsafe_allow_html=True)
    
    if st.sidebar.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.rerun()

    if st.session_state.role == "admin":
        menu = st.sidebar.radio("Navigation", ["🏠 Center Master Setup", "📝 Cash Booking Entry", "📊 Account Booking Entry", "🔎 Track & Reports"])
    else:
        menu = st.sidebar.radio("Branch Menu", ["📝 Cash Booking Entry", "📊 Account Booking Entry", "🔎 Track Document"])

    if menu == "🏠 Center Master Setup":
        st.subheader("🏭 Center / Branch Master Setup")
        with st.form("branch_setup"):
            c1, c2 = st.columns(2)
            with c1:
                nc_code = st.text_input("Center Code", placeholder="CHITRA")
                nc_name = st.text_input("Center Name")
            with c2:
                nc_city = st.text_input("City")
                nc_phone = st.text_input("Contact Number")
            if st.form_submit_button("Save Center"):
                supabase.table("branches").insert({
                    "branch_code": nc_code, "branch_name": nc_name,
                    "city": nc_city, "contact_number": nc_phone, "role": "branch"
                }).execute()
                st.success("Center saved successfully!")
        
        res = supabase.table("branches").select("*").execute()
        if res.data:
            st.dataframe(pd.DataFrame(res.data), use_container_width=True)

    elif menu == "📝 Cash Booking Entry":
        st.subheader("📦 Cash Booking Entry & Receipt Print")
        
        # Session state to hold last booked AWB for PDF download
        if "last_cash_awb" not in st.session_state:
            st.session_state.last_cash_awb = None
            st.session_state.last_cash_data = None

        with st.form("cash_booking"):
            c1, c2, c3 = st.columns(3)
            with c1:
                awb = st.text_input("Document / Barcode Number")
                doc_type = st.selectbox("Document Type", ["Documents", "Parcel"])
                sender_name = st.text_input("Sender Name")
                sender_mob = st.text_input("Sender Mobile")
            with c2:
                dest_city = st.text_input("Destination City")
                receiver_name = st.text_input("Receiver Name")
                receiver_mob = st.text_input("Receiver Mobile")
                receiver_addr = st.text_area("Receiver Address")
            with c3:
                weight = st.number_input("Weight", value=100.0)
                pieces = st.number_input("Pcs", value=1)
                freight = st.number_input("Freight Amount (₹)", value=100.0)
                net_total = freight + (freight * 0.18)
                st.metric("Net Amount", f"₹ {net_total:.2f}")

            submitted = st.form_submit_button("💾 SAVE BOOKING")
            
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
                    
                    st.session_state.last_cash_awb = awb
                    st.session_state.last_cash_data = (sender_name, receiver_name, dest_city, weight, net_total)
                    st.success(f"✅ Cash Booking Saved! AWB: {awb}")
                else:
                    st.error("Fill mandatory fields!")

        # Download button outside form
        if st.session_state.last_cash_awb:
            pdf = generate_awb_pdf(
                st.session_state.last_cash_awb, "Cash Booking",
                st.session_state.last_cash_data[0], st.session_state.last_cash_data[1],
                st.session_state.last_cash_data[2], st.session_state.last_cash_data[3],
                st.session_state.last_cash_data[4]
            )
            st.download_button(
                "🖨️ Download Receipt PDF", pdf,
                f"Receipt_{st.session_state.last_cash_awb}.pdf", "application/pdf"
            )

    elif menu == "📊 Account Booking Entry":
        st.subheader("📊 Account Booking Entry")
        with st.form("acc_booking"):
            c1, c2, c3 = st.columns(3)
            with c1:
                party = st.selectbox("Party Name", ["Party A", "Party B"])
                awb = st.text_input("AWB Number")
                sender = st.text_input("Sender Name")
            with c2:
                dest = st.text_input("Destination City")
                rec_name = st.text_input("Receiver Name")
                rec_addr = st.text_area("Receiver Address")
            with c3:
                weight = st.number_input("Weight", value=100.0)
                freight = st.number_input("Freight Amount (₹)", value=150.0)

            if st.form_submit_button("💾 Save Account Booking"):
                supabase.table("consignments").insert({
                    "awb_number": awb, "origin_branch_id": st.session_state.branch_id,
                    "destination_city": dest, "sender_name": f"{party} - {sender}",
                    "receiver_name": rec_name, "receiver_address": rec_addr,
                    "weight_kg": weight, "charge_amount": freight,
                    "payment_mode": "Account", "status": "In Transit"
                }).execute()
                st.success(f"✅ Account Booking Saved! AWB: {awb}")

    elif menu in ["🔎 Track & Reports", "🔎 Track Document"]:
        render_public_tracking()
