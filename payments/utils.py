from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
from datetime import datetime
from django.conf import settings


def generate_invoice_pdf(payment, job, company):
    """
    Generate a professional PDF invoice for a payment.
    
    Args:
        payment: Payment object
        job: Job object
        company: Company object
    
    Returns:
        BytesIO object containing the PDF
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # Styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='Header',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#0b724d'),
        spaceAfter=0.5*cm,
        alignment=TA_CENTER
    ))
    styles.add(ParagraphStyle(
        name='SubHeader',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#333333'),
        spaceAfter=0.3*cm
    ))
    styles.add(ParagraphStyle(
        name='CompanyName',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#0b724d'),
        spaceAfter=0.2*cm
    ))
    
    # Build content
    content = []
    
    # Header
    content.append(Paragraph('CameroonTechJobs', styles['Header']))
    content.append(Paragraph('Professional Tech Job Platform', styles['Normal']))
    content.append(Spacer(1, 0.5*cm))
    
    # Invoice Title
    content.append(Paragraph('PAYMENT RECEIPT', styles['SubHeader']))
    content.append(Spacer(1, 0.3*cm))
    
    # Invoice Details Table
    invoice_data = [
        ['Invoice Number:', f'INV-{payment.id:06d}'],
        ['Date:', payment.created_at.strftime('%B %d, %Y at %I:%M %p')],
        ['Transaction ID:', payment.mch_transaction_ref or 'N/A'],
        ['Status:', payment.get_status_display().upper()],
    ]
    
    invoice_table = Table(invoice_data, colWidths=[5*cm, 9*cm])
    invoice_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#666666')),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#333333')),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0.15*cm),
    ]))
    content.append(invoice_table)
    content.append(Spacer(1, 0.5*cm))
    
    # Company Information
    content.append(Paragraph('BILL TO:', styles['SubHeader']))
    company_data = [
        [company.company_name],
        [company.email],
        [company.phone or 'Phone not provided'],
    ]
    
    company_table = Table(company_data, colWidths=[14*cm])
    company_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (0, 0), 12),
        ('FONTSIZE', (0, 1), (0, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, 0), colors.HexColor('#0b724d')),
        ('TEXTCOLOR', (0, 1), (0, -1), colors.HexColor('#666666')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0.1*cm),
    ]))
    content.append(company_table)
    content.append(Spacer(1, 0.5*cm))
    
    # Job Details
    content.append(Paragraph('JOB DETAILS:', styles['SubHeader']))
    job_data = [
        ['Job Title:', job.title],
        ['Plan:', job.get_plan_display()],
        ['Duration:', '30 days' if job.plan == 'basic' else '60 days'],
        ['Posted:', job.date_posted.strftime('%B %d, %Y')],
    ]
    
    job_table = Table(job_data, colWidths=[5*cm, 9*cm])
    job_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#666666')),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#333333')),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0.15*cm),
    ]))
    content.append(job_table)
    content.append(Spacer(1, 0.5*cm))
    
    # Payment Summary
    content.append(Paragraph('PAYMENT SUMMARY:', styles['SubHeader']))
    payment_data = [
        ['Description', 'Amount'],
        [f'{job.get_plan_display().title()} Job Posting Plan', f'{payment.amount:,.0f} {payment.currency}'],
        ['', ''],
        ['TOTAL', f'{payment.amount:,.0f} {payment.currency}'],
    ]
    
    payment_table = Table(payment_data, colWidths=[10*cm, 4*cm])
    payment_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#0b724d')),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0b724d')),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0.2*cm),
        ('TOPPADDING', (0, 0), (-1, -1), 0.2*cm),
        ('LINEBELOW', (0, -1), (-1, -1), 2, colors.HexColor('#0b724d')),
    ]))
    content.append(payment_table)
    content.append(Spacer(1, 1*cm))
    
    # Footer
    footer_text = '''Thank you for your payment! Your job listing is now active and visible to thousands of tech professionals in Cameroon.
    
For any questions or support, please contact us at support@cameroontechjobs.com or visit our website.'''
    
    content.append(Paragraph(footer_text, styles['Normal']))
    content.append(Spacer(1, 0.5*cm))
    
    # Copyright
    copyright_text = f'© {datetime.now().year} CameroonTechJobs. All rights reserved.'
    content.append(Paragraph(copyright_text, ParagraphStyle(
        name='Copyright',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#999999'),
        alignment=TA_CENTER
    )))
    
    # Build PDF
    doc.build(content)
    buffer.seek(0)
    
    return buffer