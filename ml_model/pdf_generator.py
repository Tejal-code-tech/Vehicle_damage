

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.pdfgen import canvas
from datetime import datetime
import os

def generate_insurance_pdf(report_data, output_path):
    """
    Generate professional PDF insurance claim report
    
    Args:
        report_data: Dictionary with all report information
        output_path: Path where PDF should be saved
        
    Returns:
        str: Path to generated PDF file
    """
    
    # Create PDF document
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.75*inch,
        bottomMargin=0.5*inch
    )
    
    # Container for PDF elements
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a237e'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#0d47a1'),
        spaceAfter=12,
        fontName='Helvetica-Bold'
    )
    
    # ========================================================================
    # HEADER SECTION
    # ========================================================================
    
    # Title
    title = Paragraph("INSURANCE CLAIM REPORT", title_style)
    elements.append(title)
    
    # Report ID and Date
    info_data = [
        ['Report ID:', report_data['report_id'], 'Generated On:', report_data['generated_on']]
    ]
    info_table = Table(info_data, colWidths=[1.5*inch, 2*inch, 1.5*inch, 2*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#e3f2fd')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 20))
    
    # ========================================================================
    # USER & VEHICLE INFORMATION
    # ========================================================================
    
    elements.append(Paragraph("CLAIMANT INFORMATION", heading_style))
    
    user_data = [
        ['Name:', report_data['user_name'], 'Email:', report_data['user_email']],
        ['Phone:', report_data.get('user_phone', 'N/A'), '', '']
    ]
    user_table = Table(user_data, colWidths=[1.5*inch, 2*inch, 1.5*inch, 2*inch])
    user_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f5f5f5')),
        ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#f5f5f5')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    elements.append(user_table)
    elements.append(Spacer(1, 15))
    
    elements.append(Paragraph("VEHICLE INFORMATION", heading_style))
    
    vehicle_data = [
        ['Model:', report_data['vehicle_model'], 'Registration:', report_data['vehicle_registration']],
        ['Year:', report_data['vehicle_year'], '', '']
    ]
    vehicle_table = Table(vehicle_data, colWidths=[1.5*inch, 2*inch, 1.5*inch, 2*inch])
    vehicle_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f5f5f5')),
        ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#f5f5f5')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    elements.append(vehicle_table)
    elements.append(Spacer(1, 20))
    
    # ========================================================================
    # DAMAGE ASSESSMENT
    # ========================================================================
    
    elements.append(Paragraph("AI-BASED DAMAGE ASSESSMENT", heading_style))
    
    # Severity color coding
    severity_colors = {
        'MINOR': colors.green,
        'MODERATE': colors.orange,
        'SEVERE': colors.red,
        'NONE': colors.blue
    }
    severity_color = severity_colors.get(report_data['severity'], colors.grey)
    
    damage_data = [
        ['Damage Status:', 'YES' if report_data['is_damaged'] else 'NO'],
        ['Severity Level:', report_data['severity']],
        ['Detection Confidence:', f"{report_data['confidence']:.2%}"],
        ['Number of Damaged Parts:', str(len(report_data['damaged_parts']))]
    ]
    damage_table = Table(damage_data, colWidths=[2.5*inch, 4.5*inch])
    damage_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f5f5f5')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 1), (1, 1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (1, 1), (1, 1), severity_color),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    elements.append(damage_table)
    elements.append(Spacer(1, 15))
    
    # Damaged parts list
    if report_data['damaged_parts']:
        elements.append(Paragraph("DETECTED DAMAGED PARTS:", heading_style))
        
        parts_list_data = [['Part Name', 'Estimated Cost (₹)']]
        for part in report_data['damaged_parts']:
            cost = report_data['part_costs'].get(part, 0)
            parts_list_data.append([part.upper().replace('_', ' '), f"₹{cost:,}"])
        
        parts_table = Table(parts_list_data, colWidths=[3.5*inch, 3.5*inch])
        parts_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1976d2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')])
        ]))
        elements.append(parts_table)
        elements.append(Spacer(1, 20))
    
    # ========================================================================
    # COST BREAKDOWN
    # ========================================================================
    
    elements.append(Paragraph("REPAIR COST ESTIMATION", heading_style))
    
    cost_data = [
        ['Parts Cost:', f"₹{report_data['parts_total']:,}"],
        ['Labor Cost (20%):', f"₹{report_data['labor_cost']:,}"],
        ['TOTAL ESTIMATED COST:', f"₹{report_data['total_cost']:,}"]
    ]
    cost_table = Table(cost_data, colWidths=[3.5*inch, 3.5*inch])
    cost_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f5f5f5')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#1976d2')),
        ('TEXTCOLOR', (0, 2), (-1, 2), colors.whitesmoke),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('FONTSIZE', (0, 2), (-1, 2), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    elements.append(cost_table)
    elements.append(Spacer(1, 20))
    
    # ========================================================================
    # INSURANCE BREAKDOWN
    # ========================================================================
    
    elements.append(Paragraph("INSURANCE CLAIM BREAKDOWN", heading_style))
    
    insurance_data = [
        ['Policy Type:', report_data['policy_name']],
        ['Coverage:', f"{report_data['coverage_percentage']}%"],
        ['Deductible:', f"₹{report_data['deductible']:,}"],
        ['', ''],
        ['Insurance Payable:', f"₹{report_data['insurance_payable']:,}"],
        ['User Payable (Out-of-Pocket):', f"₹{report_data['user_payable']:,}"]
    ]
    insurance_table = Table(insurance_data, colWidths=[3.5*inch, 3.5*inch])
    insurance_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 3), colors.HexColor('#f5f5f5')),
        ('BACKGROUND', (0, 4), (-1, 4), colors.HexColor('#4caf50')),
        ('BACKGROUND', (0, 5), (-1, 5), colors.HexColor('#ff9800')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (0, 4), (-1, 5), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 4), (-1, 5), colors.white),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTSIZE', (0, 0), (-1, 3), 10),
        ('FONTSIZE', (0, 4), (-1, 5), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('LINEABOVE', (0, 4), (-1, 4), 2, colors.black)
    ]))
    elements.append(insurance_table)
    elements.append(Spacer(1, 20))
    
    # ========================================================================
    # CLAIM PROBABILITY
    # ========================================================================
    
    elements.append(Paragraph("CLAIM APPROVAL PROBABILITY", heading_style))
    
    prob_color = {
        'Strong': colors.green,
        'Moderate': colors.orange,
        'Weak': colors.orangered,
        'Very Weak': colors.red
    }.get(report_data['claim_strength'], colors.grey)
    
    probability_data = [
        ['Approval Probability:', f"{report_data['claim_probability']}%"],
        ['Claim Strength:', report_data['claim_strength']],
        ['Recommendation:', report_data['claim_recommendation']]
    ]
    prob_table = Table(probability_data, colWidths=[2.5*inch, 4.5*inch])
    prob_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f5f5f5')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, 1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (1, 1), (1, 1), prob_color),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    elements.append(prob_table)
    elements.append(Spacer(1, 30))
    
    # ========================================================================
    # FOOTER / DISCLAIMER
    # ========================================================================
    
    disclaimer_style = ParagraphStyle(
        'Disclaimer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    
    disclaimer_text = """
    <b>DISCLAIMER:</b> This is an AI-generated estimate based on image analysis. 
    Actual repair costs may vary. Final claim approval is subject to insurance company's assessment 
    and policy terms. This report should be used as a reference only.
    """
    elements.append(Paragraph(disclaimer_text, disclaimer_style))
    
    # Build PDF
    doc.build(elements)
    
    print(f"✅ PDF report generated: {output_path}")
    return output_path