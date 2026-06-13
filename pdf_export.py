import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generate_volunteers_pdf(volunteers, search_term="", skill_filter="", availability_filter=""):
    """
    Generates a PDF bytes buffer containing the formatted list of volunteers.
    Uses reportlab flowables to correctly wrap text in cells.
    """
    buffer = io.BytesIO()
    
    # 0.5 inch margins (36 pt)
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter, 
        rightMargin=36, 
        leftMargin=36, 
        topMargin=36, 
        bottomMargin=36
    )
    story = []
    
    # Setup custom styles matching the NGO theme
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#475569'),
        spaceAfter=15
    )
    
    header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.white
    )
    
    cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#1e293b')
    )
    
    # Document Header
    story.append(Paragraph("Kindred NGO — Volunteer Registry Report", title_style))
    
    # Render filter descriptions
    filters_list = []
    if search_term:
        filters_list.append(f"Search: '{search_term}'")
    if skill_filter:
        filters_list.append(f"Skill: {skill_filter}")
    if availability_filter:
        filters_list.append(f"Availability: {availability_filter}")
        
    filters_desc = ", ".join(filters_list) if filters_list else "None (Unfiltered)"
    story.append(Paragraph(f"Active Filters: {filters_desc}  |  Total Volunteers: {len(volunteers)}", subtitle_style))
    story.append(Spacer(1, 5))
    
    # Table Headings & Columns: Name, Email, Phone, Skills, Availability
    table_data = [[
        Paragraph("Volunteer Name", header_style),
        Paragraph("Email Address", header_style),
        Paragraph("Phone Number", header_style),
        Paragraph("Skills / Interests", header_style),
        Paragraph("Availability", header_style)
    ]]
    
    for v in volunteers:
        table_data.append([
            Paragraph(v.name, cell_style),
            Paragraph(v.email, cell_style),
            Paragraph(v.phone, cell_style),
            Paragraph(v.skills, cell_style),
            Paragraph(v.availability, cell_style)
        ])
    
    # Table Column Widths (total printable width: 612 - 72 = 540)
    col_widths = [110, 130, 85, 140, 75]
    
    volunteers_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    
    # Apply elegant clean spreadsheet table styling
    volunteers_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0f172a')), # NGO Primary Slate header
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#f8fafc'), colors.white]), # Alternating zebra rows
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')), # Light grey borders
    ]))
    
    story.append(volunteers_table)
    
    # Build document
    doc.build(story)
    buffer.seek(0)
    return buffer
