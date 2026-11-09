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
# ૧. SUPABASE CONNECTIVITY
# ---------------------------------------------------------
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "YOUR_SUPABASE_URL")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "YOUR_SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Express Courier Logistics System", layout="wide", page_icon="📦")

# સેશન સ્ટેટ હેન્ડલર
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.branch_code = None
    st.session_state.branch_id = None

# ---------------------------------------------------------
# ૨. PDF GENERATION UTILITIES
# ---------------------------------------------------------
def generate_awb_pdf(awb, sender, receiver, dest, weight, amount):
    """કન્સાઈનમેન્ટ બુકિંગ લેબલ/પ્રિન્ટ સ્લિપ જનરેટર"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=(300, 400), rightMargin=10, leftMargin=10, topMargin=10, bottomMargin=10)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(f"<b>EXPRESS COURIER SERVICES</b>", styles['Title']))
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"<b>AWB NO: {awb}</b>", styles['Heading2']))
    story.append(Spacer(1, 10))

    data = [
        ["Sender:", sender],
        ["Receiver:", receiver],
        ["Destination:", dest],
        ["Weight (Kg):", str(weight)],
        ["Total Amount:", f"INR {amount}"]
    ]
    
    t = Table(data, colWidths=[90, 180])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.whitesmoke),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
    ]))
    story.append(t)
    story.append(Spacer(1, 15))
    story.append(Paragraph("<i>Thank you for routing with us!</i>", styles['Italic']))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

def generate_runsheet_pdf(runsheet_id, branch, consignments):
    """લાઈવ રનશીટ/DRS PDF જનરેટર"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(f"<b>DELIVERY RUNSHEET (DRS) - {runsheet_id}</b>", styles['Heading1']))
    story.append(Paragraph(f"<b>Branch:</b> {branch}", styles['Normal']))
    story.append(Spacer(1, 15))

    table_data = [["AWB No", "Receiver Name", "Address", "Phone", "Sign"]]
    for item in consignments:
        table_data.append([
            item.get("awb_number", ""),
            item.get("receiver_name", ""),
            item.get("receiver_address", ""),
            item.get("receiver_phone", ""),
            ""
        ])

    t = Table(table_data, colWidths=[100, 110, 180, 90, 70])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.navy),
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
# ૩. PUBLIC TRACKING PAGE
# ---------------------------------------------------------
def render_public_tracking():
    st.subheader("🔍 લાઈવ કન્સાઈનમેન્ટ ટ્રેકિંગ (Tracking Panel)")
    search_awb = st.text_input("તમારો AWB / Consignment Number દાખલ કરો:", placeholder="EXP123456")
    
    if st.button("Track Status"):
        if search_awb:
            res = supabase.table("consignments").select("*").eq("awb_number", search_awb).execute()
            if res.data:
                item = res.data[0]
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("AWB Number", item["awb_number"])
                col2.metric("Destination", item["destination_city"])
                col3.metric("Current Status", item["status"])
                col4.metric("Booking Date", str(item["created_at"])[:10])
                
                st.info(f"📍 **મેળવનારનું નામ:** {item['receiver_name']} | **સરનામું:** {item['receiver_address']}")
            else:
                st.error("❌ આ AWB નંબરનો કોઈ રેકોર્ડ મળ્યો નથી!")
        else:
            st.warning("કૃપા કરીને AWB નંબર દાખલ કરો.")

# ---------------------------------------------------------
# ૪. MAIN APP ROUTING & LOGIN
# ---------------------------------------------------------
st.sidebar.title("📦 Courier Portal")

if not st.session_state.logged_in:
    menu = st.sidebar.radio("મેનુ પસંદ કરો", ["સિસ્ટમ લોગિન", "જાહેર ટ્રેકિંગ (Public Track)"])
    
    if menu == "જાહેર ટ્રેકિંગ (Public Track)":
        render_public_tracking()
    else:
        st.title("🔐 કુરિયર સોફ્ટવેર પોર્ટલ લોગિન")
        b_code = st.text_input("Branch Code (ઉદાహરણ: HO001)")
        pwd = st.text_input("Password", type="password")
        
        if st.button("Login"):
            res = supabase.table("branches").select("*").eq("branch_code", b_code).execute()
            if res.data:
                user = res.data[0]
                st.session_state.logged_in = True
                st.session_state.role = user["role"]
                st.session_state.branch_code = user["branch_code"]
                st.session_state.branch_id = user["id"]
                st.success("સફળતાપૂર્વક લોગિન થયા છો!")
                st.rerun()
            else:
                st.error("ખોટો બ્રાન્ચ કોડ અથવા વિગતો!")

else:
    st.sidebar.write(f"👤 Logged in: **{st.session_state.branch_code}** ({st.session_state.role.upper()})")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    st.sidebar.divider()
    
    # HEAD OFFICE (HO) DASHBOARD
    if st.session_state.role == "admin":
        st.title("👑 Head Office (HO) Control Center")
        ho_tabs = st.tabs(["📊 ઓલ-ઓવર ટ્રાન્ઝિટ", "🏭 બ્રાન્ચ મેનેજમેન્ટ", "🔍 AWB ચેક", "📄 રનશીટ જનરેશન"])

        with ho_tabs[0]:
            st.subheader("તમામ બ્રાન્ચનું લાઈવ બુકિંગ રજિસ્ટર")
            res = supabase.table("consignments").select("*").execute()
            if res.data:
                df = pd.DataFrame(res.data)
                st.dataframe(df, use_container_width=True)
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Excel/CSV ડાઉનલોડ", csv, "all_consignments.csv", "text/csv")
            else:
                st.info("હજુ સુધી કોઈ કન્સાઈનમેન્ટ બુક થયું નથી.")

        with ho_tabs[1]:
            st.subheader("નવી ફ્રેન્ચાઈઝી બ્રાન્ચ રજિસ્ટર કરો")
            col1, col2 = st.columns(2)
            with col1:
                n_code = st.text_input("New Branch Code (ઉદાહરણ: BR_AHMEDABAD)")
                n_name = st.text_input("Branch Name / Owner")
            with col2:
                n_city = st.text_input("City")
                n_phone = st.text_input("Contact Phone")
            
            if st.button("Create Branch"):
                supabase.table("branches").insert({
                    "branch_code": n_code,
                    "branch_name": n_name,
                    "city": n_city,
                    "contact_number": n_phone,
                    "role": "branch"
                }).execute()
                st.success(f"બ્રાન્ચ {n_code} સફળતાપૂર્વક ઉમેરાઈ ગઈ!")

        with ho_tabs[2]:
            st.subheader("🔎 AWB કન્સાઈનમેન્ટ તપાસો")
            check_awb = st.text_input("AWB નંબર દાખલ કરો:")
            if check_awb:
                data = supabase.table("consignments").select("*").eq("awb_number", check_awb).execute()
                if data.data:
                    st.json(data.data[0])
                else:
                    st.warning("કોઈ ડેટા મળ્યો નથી.")

        with ho_tabs[3]:
            st.subheader("📄 લાઈવ રનશીટ (DRS) PDF જનરેશન")
            city_filter = st.text_input("જે સિટીની રનશીટ બનાવવી હોય તે સિટી:")
            if st.button("Generate Runsheet PDF"):
                items = supabase.table("consignments").select("*").eq("destination_city", city_filter).eq("status", "In Transit").execute()
                if items.data:
                    pdf_bytes = generate_runsheet_pdf(f"DRS-{city_filter}", st.session_state.branch_code, items.data)
                    st.download_button("📥 રનશીટ PDF ડાઉનલોડ કરો", pdf_bytes, f"Runsheet_{city_filter}.pdf", "application/pdf")
                else:
                    st.warning("આ સિટી માટે 'In Transit' સ્ટેટસ વાળા પેકેટ મળ્યા નથી.")

    # FRANCHISE (BR) DASHBOARD
    else:
        st.title(f"🚚 Franchise Outward & Booking Panel ({st.session_state.branch_code})")
        br_tabs = st.tabs(["📝 નવું કન્સાઈનમેન્ટ બુકિંગ", "📦 લાઈવ રનશીટ (Out for Delivery)", "🔎 AWB ટ્રેક"])

        with br_tabs[0]:
            st.subheader("નવું બુકિંગ અને લેબલ PDF જનરેશન")
            with st.form("booking_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    awb_no = st.text_input("AWB / Consignment No.", placeholder="ઉદા. 987654321")
                    sender_name = st.text_input("Sender Name")
                    sender_phone = st.text_input("Sender Phone")
                    dest_city = st.text_input("Destination City")
                with col2:
                    rec_name = st.text_input("Receiver Name")
                    rec_phone = st.text_input("Receiver Phone")
                    rec_addr = st.text_area("Receiver Full Address")
                    weight = st.number_input("Weight (Kg)", min_value=0.1, value=0.5, step=0.1)
                    amount = st.number_input("Total Amount (₹)", min_value=0.0, value=100.0)

                submit_booking = st.form_submit_button("Book Shipment & Generate PDF")

            if submit_booking:
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
                
                st.success(f"✅ બુકિંગ સફળ! AWB: {awb_no}")
                
                pdf_label = generate_awb_pdf(awb_no, sender_name, rec_name, dest_city, weight, amount)
                st.download_button(
                    label="🖨️ બુકિંગ લેબલ PDF ડાઉનલોડ કરો",
                    data=pdf_label,
                    file_name=f"Label_{awb_no}.pdf",
                    mime="application/pdf"
                )

        with br_tabs[1]:
            st.subheader("તમારી બ્રાન્ચની ઈનવર્ડ રનશીટ સેટઅપ")
            my_city = st.text_input("તમારું લોકલ સિટી સર્ચ કરો (Inward Deliveries માટે):")
            if my_city:
                inward_res = supabase.table("consignments").select("*").eq("destination_city", my_city).execute()
                if inward_res.data:
                    st.dataframe(pd.DataFrame(inward_res.data), use_container_width=True)
                    pdf_drs = generate_runsheet_pdf("LOCAL-DRS", st.session_state.branch_code, inward_res.data)
                    st.download_button("📥 ડીલિવરી બોય માટે રનશીટ PDF પ્રિન્ટ કરો", pdf_drs, "Delivery_Runsheet.pdf", "application/pdf")
                else:
                    st.info("કોઈ પેન્ડિંગ પાર્સલ મળ્યા નથી.")

        with br_tabs[2]:
            render_public_tracking()
