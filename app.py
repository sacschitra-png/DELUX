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

# Custom Styling for Delux Blue & Green Theme + InfoSoft Layout
st.markdown("""
<style>
    /* Delux Premium Header Theme */
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
        font-size: 32px;
        font-weight: 800;
        letter-spacing: 2px;
        color: #00FF87;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.5);
    }
    .delux-subtext {
        font-size: 14px;
        color: #60EFFF;
        font-weight: 500;
    }
    
    /* InfoSoft Style Quick Navigation Bar */
    .quick-bar {
        background-color: #1e293b;
        padding: 10px;
        border-radius: 8px;
        color: #f8fafc;
        border-left: 5px solid #10b981;
        margin-bottom: 15px;
    }

    /* Buttons Styling */
    .stButton>button {
        background: linear-gradient(90deg, #059669 0%, #10b981 100%);
        color: white;
        font-weight: bold;
        border: none;
        border-radius: 6px;
        padding: 0.5rem 1rem;
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #047857 0%, #059669 100%);
        color: #ffffff;
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

# Session State Initialization
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.branch_code = None
    st.session_state.branch_name = None
    st.session_state.branch_id = None

# ---------------------------------------------------------
# ૩. PDF GENERATION UTILITIES
# ---------------------------------------------------------
def generate_awb_pdf(awb, sender, receiver, dest, weight, amount):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=(300, 400), rightMargin=10, leftMargin=10, topMargin=10, bottomMargin=10)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("<b>DELUX COURIER SERVICES</b>", styles['Title']))
    story.append(Spacer(1, 5))
    story.append(Paragraph(f"<b>AWB NO: {awb}</b>", styles['Heading2']))
    story.append(Spacer(1, 10))

    data = [
        ["Sender:", sender],
        ["Receiver:", receiver],
        ["Destination:", dest],
        ["Weight (Kg):", str(weight)],
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
    story.append(Spacer(1, 10))
    story.append(Paragraph("<i>Fast & Reliable Express Logistics</i>", styles['Italic']))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

def generate_runsheet_pdf(runsheet_id, branch, consignments):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(f"<b>DELUX COURIER - DELIVERY RUNSHEET (DRS)</b>", styles['Heading1']))
    story.append(Paragraph(f"<b>Runsheet ID:</b> {runsheet_id} | <b>Branch:</b> {branch}", styles['Normal']))
    story.append(Spacer(1, 15))

    table_data = [["AWB No", "Receiver Name", "Address", "Phone", "Signature"]]
    for item in consignments:
        table_data.append([
            item.get("awb_number", ""),
            item.get("receiver_name", ""),
            item.get("receiver_address", ""),
            item.get("receiver_phone", ""),
            ""
        ])

    t = Table(table_data, colWidths=[90, 110, 180, 90, 70])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0f2027")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
    ]))
    story.append(t)
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# ---------------------------------------------------------
# ૪. HEADER DISPLAY
# ---------------------------------------------------------
st.markdown("""
<div class="delux-header">
    <div class="delux-logo-text">⚡ DELUX COURIER SERVICES</div>
    <div class="delux-subtext">Express Cargo & Parcel Logistics Network | Digital Enterprise Portal</div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# ૫. PUBLIC TRACKING PANEL
# ---------------------------------------------------------
def render_public_tracking():
    st.subheader("🔍 TRACK YOUR DOCUMENTS / PARCELS")
    search_awb = st.text_input("અહીં AWB / Document નંબર દાખલ કરો:", placeholder="ઉદા. DEL100293")
    
    if st.button("Track Status Now"):
        if search_awb:
            res = supabase.table("consignments").select("*").eq("awb_number", search_awb).execute()
            if res.data:
                item = res.data[0]
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("AWB Number", item["awb_number"])
                c2.metric("Destination City", item["destination_city"])
                c3.metric("Current Status", item["status"])
                c4.metric("Booking Date", str(item["created_at"])[:10])
                
                st.success(f"📍 **મેળવનાર:** {item['receiver_name']} | **સરનામું:** {item['receiver_address']} | **મોબાઈલ:** {item['receiver_phone']}")
            else:
                st.error("❌ આ AWB નંબરનો કોઈ રેકોર્ડ મળ્યો નથી!")
        else:
            st.warning("કૃપા કરીને AWB નંબર દાખલ કરો.")

# ---------------------------------------------------------
# ૬. LOGIN & ROUTING LOGIC
# ---------------------------------------------------------
if not st.session_state.logged_in:
    col_left, col_right = st.columns([1, 1.2])
    
    with col_left:
        st.subheader("🔐 DELUX SYSTEM LOGIN")
        b_code = st.text_input("User ID / Branch Code", placeholder="ઉદા. HO001 અથવા BHAVNAGAR")
        pwd = st.text_input("Password", type="password", placeholder="તમારો પાસવર્ડ")
        
        if st.button("Login To System"):
            res = supabase.table("branches").select("*").eq("branch_code", b_code).execute()
            if res.data:
                user = res.data[0]
                st.session_state.logged_in = True
                st.session_state.role = user["role"]
                st.session_state.branch_code = user["branch_code"]
                st.session_state.branch_name = user["branch_name"]
                st.session_state.branch_id = user["id"]
                st.success(f"જી આયા ને! બ્રાન્ચ {user['branch_name']} લોગિન થઈ ગઈ છે.")
                st.rerun()
            else:
                st.error("❌ ખોટો બ્રાન્ચ કોડ અથવા યુઝર આઈડી!")

    with col_right:
        render_public_tracking()

else:
    # Top Information Bar (InfoSoft Style)
    st.markdown(f"""
    <div class="quick-bar">
        🟢 <b>Welcome:</b> {st.session_state.branch_name} ({st.session_state.branch_code}) | 
        🛡️ <b>Role:</b> {st.session_state.role.upper()} | 
        📅 <b>System Date:</b> {pd.Timestamp.now().strftime('%Y-%m-%d')}
    </div>
    """, unsafe_allow_html=True)
    
    if st.sidebar.button("🚪 Logout (બહાર નીકળો)"):
        st.session_state.logged_in = False
        st.rerun()

    # ---------------------------------------------------------
    # ૭. ADMIN CONTROL PANEL (Head Office)
    # ---------------------------------------------------------
    if st.session_state.role == "admin":
        st.sidebar.title("📌 Head Office Navigation")
        ho_menu = st.sidebar.radio("મેનુ પસંદ કરો", [
            "🏠 Master Entries (બ્રાન્ચ સેટઅપ)",
            "📦 Transactions & Multi Booking",
            "📊 Outgoing & Incoming Manifax",
            "🚚 DRS Voucher Entry",
            "🔎 Track & Audit Reports"
        ])

        if ho_menu == "🏠 Master Entries (બ્રાન્ચ સેટઅપ)":
            st.subheader("🏭 નવી બ્રાન્ચ / ફ્રેન્ચાઈઝી માસ્ટર બનાવટ")
            with st.form("add_branch_form"):
                col1, col2 = st.columns(2)
                with col1:
                    nb_code = st.text_input("New Branch Code", placeholder="ઉદા. BR_AHMEDABAD")
                    nb_name = st.text_input("Branch Name", placeholder="ઉદા. Ahmedabad Main Franchise")
                with col2:
                    nb_city = st.text_input("City Name", placeholder="Ahmedabad")
                    nb_phone = st.text_input("Contact Phone", placeholder="9876543210")
                
                submit_b = st.form_submit_button("Register New Branch")
                if submit_b:
                    if nb_code and nb_name:
                        supabase.table("branches").insert({
                            "branch_code": nb_code,
                            "branch_name": nb_name,
                            "city": nb_city,
                            "contact_number": nb_phone,
                            "role": "branch"
                        }).execute()
                        st.success(f"✅ નવી બ્રાન્ચ [{nb_code} - {nb_name}] સફળતાપૂર્વક સિસ્ટમમાં ઉમેરાઈ ગઈ!")
                    else:
                        st.error("બ્રાન્ચ કોડ અને નામ જરૂરી છે.")

            st.divider()
            st.subheader("📋 તમામ રજિસ્ટર્ડ બ્રાન્ચનું લિસ્ટ")
            all_b = supabase.table("branches").select("*").execute()
            if all_b.data:
                st.dataframe(pd.DataFrame(all_b.data), use_container_width=True)

        elif ho_menu == "📦 Transactions & Multi Booking":
            st.subheader("📦 હેડ ઓફિસ ઓલ-ઓવર બુકિંગ મેનેજર")
            res = supabase.table("consignments").select("*").execute()
            if res.data:
                df = pd.DataFrame(res.data)
                st.dataframe(df, use_container_width=True)
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Excel / CSV રિપોર્ટ ડાઉનલોડ", csv, "delux_all_bookings.csv", "text/csv")
            else:
                st.info("કોઈ બુકિંગ એન્ટ્રીઓ ઉપલબ્ધ નથી.")

        elif ho_menu == "📊 Outgoing & Incoming Manifax":
            st.subheader("📑 Manifax (મેનિફેસ્ટ) કન્ટ્રોલર")
            m_city = st.text_input("સિટી મુજબ આઉટગોઇંગ મેનિફેસ્ટ ફિલ્ટર કરો:")
            if st.button("Generate Outgoing Manifax List"):
                data = supabase.table("consignments").select("*").eq("destination_city", m_city).execute()
                if data.data:
                    st.dataframe(pd.DataFrame(data.data), use_container_width=True)
                else:
                    st.warning("આ સિટી માટે કોઈ કન્સાઈનમેન્ટ મળ્યા નથી.")

        elif ho_menu == "🚚 DRS Voucher Entry":
            st.subheader("📜 Delivery Runsheet (DRS) Generator")
            drs_city = st.text_input("જે સિટી માટે DRS બનાવવું હોય તે:")
            if st.button("Generate DRS PDF"):
                items = supabase.table("consignments").select("*").eq("destination_city", drs_city).execute()
                if items.data:
                    pdf = generate_runsheet_pdf(f"DRS-{drs_city}", st.session_state.branch_code, items.data)
                    st.download_button("📥 DRS Printable PDF ડાઉનલોડ કરો", pdf, f"DRS_{drs_city}.pdf", "application/pdf")
                else:
                    st.warning("આ સિટી માટે કોઈ પેન્ડિંગ પેકેટ મળ્યા નથી.")

        elif ho_menu == "🔎 Track & Audit Reports":
            render_public_tracking()

    # ---------------------------------------------------------
    # ૮. FRANCHISE / BRANCH PANEL
    # ---------------------------------------------------------
    else:
        st.sidebar.title(f"🚚 {st.session_state.branch_code} Panel")
        br_menu = st.sidebar.radio("મેનુ પસંદ કરો", [
            "📝 Cash Booking Entry",
            "📦 Incoming / Outgoing Manifax",
            "📄 Local DRS Printouts",
            "🔎 Quick Track"
        ])

        if br_menu == "📝 Cash Booking Entry":
            st.subheader("📝 નવું કન્સાઈનમેન્ટ બુકિંગ & લેબલ પ્રિન્ટ")
            with st.form("cash_booking_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    awb_no = st.text_input("AWB / Document No.", placeholder="ઉદા. DEL998877")
                    sender_name = st.text_input("Sender Name (મોકલનારનું નામ)")
                    sender_phone = st.text_input("Sender Mobile")
                    dest_city = st.text_input("Destination City (ગંતવ્ય સ્થળ)")
                with c2:
                    rec_name = st.text_input("Receiver Name (મેળવનારનું નામ)")
                    rec_phone = st.text_input("Receiver Mobile")
                    rec_addr = st.text_area("Receiver Full Address")
                    weight = st.number_input("Weight (Kg)", min_value=0.1, value=0.5, step=0.1)
                    amount = st.number_input("Booking Amount (₹)", min_value=0.0, value=100.0)

                submit_book = st.form_submit_button("Book Shipment & Generate Label")

            if submit_book:
                if awb_no and dest_city:
                    supabase.table("consignments").insert({
                        "awb_number": awb_no,
                        "origin_branch_id": st.session_state.branch_id,
                        "destination_city": dest_city,
                        "sender_name": sender_name,
                        "sender_phone": sender_phone,
                        "receiver_name": rec_name,
                        "receiver_address": rec_addr,
                        "receiver_phone": rec_phone,
                        "weight_kg": weight,
                        "charge_amount": amount,
                        "status": "In Transit"
                    }).execute()
                    
                    st.success(f"✅ બુકિંગ સફળતાપૂર્વક થઈ ગયું છે! AWB: {awb_no}")
                    
                    pdf_bytes = generate_awb_pdf(awb_no, sender_name, rec_name, dest_city, weight, amount)
                    st.download_button(
                        label="🖨️ Delux Print Slip PDF ડાઉનલોડ કરો",
                        data=pdf_bytes,
                        file_name=f"Delux_Label_{awb_no}.pdf",
                        mime="application/pdf"
                    )
                else:
                    st.error("AWB નંબર અને Destination City દાખલ કરવું ફરજિયાત છે.")

        elif br_menu == "📦 Incoming / Outgoing Manifax":
            st.subheader("📦 બ્રાન્ચ મેનિફેસ્ટ રજિસ્ટર")
            inward = supabase.table("consignments").select("*").eq("destination_city", st.session_state.branch_name).execute()
            if inward.data:
                st.write("📥 **તમારી બ્રાન્ચમાં આવતા ઇનવર્ડ પાર્સલ:**")
                st.dataframe(pd.DataFrame(inward.data), use_container_width=True)
            else:
                st.info("તમારી બ્રાન્ચ માટે કોઈ ઈનવર્ડ પાર્સલ મળ્યા નથી.")

        elif br_menu == "📄 Local DRS Printouts":
            st.subheader("📜 લોકલ ડીલિવરી રનશીટ (DRS)")
            if st.button("Generate Today's Delivery Runsheet"):
                my_parcels = supabase.table("consignments").select("*").eq("destination_city", st.session_state.branch_name).execute()
                if my_parcels.data:
                    pdf_drs = generate_runsheet_pdf(f"DRS-{st.session_state.branch_code}", st.session_state.branch_code, my_parcels.data)
                    st.download_button("📥 DRS PDF ડાઉનલોડ કરો", pdf_drs, "Delux_Local_DRS.pdf", "application/pdf")
                else:
                    st.warning("ડીલિવરી માટે કોઈ ડેટા મળ્યો નથી.")

        elif br_menu == "🔎 Quick Track":
            render_public_tracking()
