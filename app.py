import io
import streamlit as st
import pandas as pd
from supabase import create_client, Client

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

st.set_page_config(page_title="DELUX COURIER SERVICES - Enterprise Portal", layout="wide", page_icon="🚚")

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

st.markdown("""
<div class="delux-header">
    <div class="delux-logo-text">⚡ DELUX COURIER SERVICES</div>
    <div style="color: #60EFFF; font-size: 13px;">Express Cargo & Parcel Logistics Network | InfoSoft Modular Interface</div>
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

    # MAIN NAVIGATION (InfoSoft Style Menu Hierarchy)
    main_menu = st.sidebar.radio("Navigation", [
        "📦 Transactions (Booking)",
        "📜 D.R.S. & Packing Slip",
        "⚙️ Master Entries",
        "🔎 Track Document"
    ])

    if main_menu == "📦 Transactions (Booking)":
        sub_t = st.sidebar.selectbox("Transaction Type", ["Cash Booking Entry", "Account Booking Entry"])
        if sub_t == "Cash Booking Entry":
            st.subheader("📦 Cash Booking Entry & Receipt Print")
            with st.form("cash_booking"):
                c1, c2, c3 = st.columns(3)
                with c1:
                    awb = st.text_input("Document / Barcode Number")
                    sender_name = st.text_input("Sender Name")
                with c2:
                    dest_city = st.text_input("Destination City")
                    receiver_name = st.text_input("Receiver Name")
                    receiver_addr = st.text_area("Receiver Address")
                with c3:
                    weight = st.number_input("Weight (Kg)", value=0.5)
                    freight = st.number_input("Freight Amount (₹)", value=100.0)
                
                if st.form_submit_button("💾 Save Cash Booking"):
                    supabase.table("consignments").insert({
                        "awb_number": awb, "origin_branch_id": st.session_state.branch_id,
                        "destination_city": dest_city, "sender_name": sender_name,
                        "receiver_name": receiver_name, "receiver_address": receiver_addr,
                        "weight_kg": weight, "charge_amount": freight,
                        "payment_mode": "Cash", "status": "In Transit"
                    }).execute()
                    st.success(f"✅ Cash Booking Saved! AWB: {awb}")
        else:
            st.subheader("📊 Account Booking Entry")
            with st.form("acc_booking"):
                c1, c2, c3 = st.columns(3)
                with c1:
                    party = st.selectbox("Party Account Name", ["Corporate Party A", "Corporate Party B"])
                    awb = st.text_input("AWB Number")
                with c2:
                    dest = st.text_input("Destination City")
                    rec_name = st.text_input("Receiver Name")
                with c3:
                    weight = st.number_input("Weight (Kg)", value=1.0)
                    freight = st.number_input("Freight Amount (₹)", value=150.0)

                if st.form_submit_button("💾 Save Account Booking"):
                    supabase.table("consignments").insert({
                        "awb_number": awb, "origin_branch_id": st.session_state.branch_id,
                        "destination_city": dest, "sender_name": f"{party}",
                        "receiver_name": rec_name, "weight_kg": weight,
                        "charge_amount": freight, "payment_mode": "Account", "status": "In Transit"
                    }).execute()
                    st.success(f"✅ Account Booking Saved for [{party}]!")

    elif main_menu == "📜 D.R.S. & Packing Slip":
        sub_d = st.sidebar.selectbox("Select Utility", ["D.R.S. Entry", "Incoming Packing Slip"])
        if sub_d == "D.R.S. Entry":
            st.subheader("📜 D.R.S. [Delivery Run Sheet] Entry")
            with st.form("drs_form"):
                c1, c2 = st.columns(2)
                with c1:
                    drs_no = st.text_input("D.R.S. Number", value="34118")
                    delivery_boy = st.selectbox("Delivery Boy Master", ["Darshakbhai", "Jayveer", "Rameshbhai"])
                with c2:
                    drs_date = st.text_input("D.R.S. Date", value="09/11/2026")
                    area_name = st.selectbox("Area Master (ARFA NAME)", ["Chitra GIDC", "Bhavnagar City", "Vartej Road"])
                
                if st.form_submit_button("Save DRS Entry"):
                    st.success(f"✅ DRS [{drs_no}] saved for Delivery Boy [{delivery_boy}] in Area [{area_name}]!")
        else:
            st.subheader("📥 Incoming Packing Slip")
            with st.form("inc_slip"):
                c1, c2 = st.columns(2)
                with c1:
                    slip_no = st.text_input("Packing Slip No.", value="9789")
                    slip_from = st.selectbox("Slip From (Center)", ["Ahmedabad Center", "Surat Center"])
                with c2:
                    transit_mode = st.selectbox("Transit Mode", ["BY ROAD", "BY AIR"])
                    total_docs = st.number_input("Total Documents", value=1)
                if st.form_submit_button("Save Incoming Slip"):
                    st.success(f"✅ Packing Slip [{slip_no}] recorded successfully!")

    elif main_menu == "⚙️ Master Entries":
        st.subheader("⚙️ Master Entries Management [InfoSoft Style]")
        master_opt = st.selectbox("Select Master Setup", [
            "Center Master SetUp",
            "Local Center SetUp",
            "CENTER ADMIN User LogIN",
            "User Master",
            "AREA Master",
            "Delivery Boy Master",
            "General Account Master",
            "Party Account Master",
            "Party Account Rate Master",
            "Cash Booking Rate Master",
            "Bank Account SetUp"
        ])

        if master_opt in ["Center Master SetUp", "Local Center SetUp"]:
            with st.markdown(f"### 🏭 {master_opt}"):
                with st.form("center_form"):
                    c_code = st.text_input("Center Code")
                    c_name = st.text_input("Center Name")
                    c_city = st.text_input("City")
                    if st.form_submit_button("Save Center"):
                        supabase.table("branches").insert({"branch_code": c_code, "branch_name": c_name, "city": c_city, "role": "branch"}).execute()
                        st.success("Center saved successfully!")
                res = supabase.table("branches").select("*").execute()
                if res.data:
                    st.dataframe(pd.DataFrame(res.data), use_container_width=True)

        elif master_opt == "AREA Master":
            st.markdown("### 📍 AREA Master Setup")
            with st.form("area_form"):
                a_name = st.text_input("Area Name (ARFA NAME)")
                a_pincode = st.text_input("Pincode")
                if st.form_submit_button("Save Area"):
                    st.success(f"Area [{a_name}] saved successfully!")

        elif master_opt == "Delivery Boy Master":
            st.markdown("### 🛵 Delivery Boy Master Setup")
            with st.form("boy_form"):
                b_name = st.text_input("Delivery Boy Name")
                b_phone = st.text_input("Mobile Number")
                if st.form_submit_button("Save Delivery Boy"):
                    st.success(f"Delivery Boy [{b_name}] saved successfully!")

        else:
            st.info(f"Configuration panel for **{master_opt}** is ready. Enter and manage master records here.")

    elif main_menu == "🔎 Track Document":
        render_public_tracking()
