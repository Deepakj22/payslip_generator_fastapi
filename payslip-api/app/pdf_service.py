
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
import calendar
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from app.models import PayslipRequest


# Colors inspired by the reference payslip
NAVY = colors.HexColor("#142F5B")
BLUE = colors.HexColor("#5278C2")
LIGHT_BLUE = colors.HexColor("#DCE8F2")
BORDER = colors.HexColor("#BECBD2")
TEXT = colors.HexColor("#222222")
WHITE = colors.white
MUTED = colors.HexColor("#667784")


def generate_payslip_pdf(data: PayslipRequest) -> BytesIO:
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=10 * mm,
        bottomMargin=12 * mm,
        title=f"Payslip - {data.employee.employee_name}",
        author=data.company.company_name or "Payslip Generator",
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "PayslipTitle",
        parent=styles["Title"],
        fontName="Helvetica",
        fontSize=25,
        leading=30,
        textColor=BORDER,
        alignment=TA_CENTER,
        spaceAfter=8 * mm,
    )

    company_style = ParagraphStyle(
        "CompanyName",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=17,
        leading=20,
        textColor=NAVY,
        spaceAfter=2 * mm,
    )

    statement_style = ParagraphStyle(
        "Statement",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=14,
        alignment=TA_RIGHT,
        textColor=NAVY,
    )

    normal_style = ParagraphStyle(
        "NormalSmall",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=12,
        textColor=TEXT,
    )

    section_style = ParagraphStyle(
        "SectionHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=11,
        textColor=WHITE,
    )

    table_header_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=10,
        alignment=TA_CENTER,
        textColor=NAVY,
    )

    amount_style = ParagraphStyle(
        "Amount",
        parent=normal_style,
        alignment=TA_RIGHT,
    )

    net_label_style = ParagraphStyle(
        "NetLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        alignment=TA_RIGHT,
        textColor=NAVY,
    )

    net_amount_style = ParagraphStyle(
        "NetAmount",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=19,
        alignment=TA_CENTER,
        textColor=WHITE,
    )

    def safe(value):
        return escape(str(value or ""))

    def money(value):
        return f"{value:,.2f}"

    def paragraph(value, style=normal_style):
        return Paragraph(str(value), style)

    def section_bar(title, width):
        table = Table(
            [[paragraph(safe(title), section_style)]],
            colWidths=[width],
        )
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), BLUE),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        return table

    def apply_grid(table, header_rows=0):
        commands = [
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]

        if header_rows:
            commands.extend([
                ("BACKGROUND", (0, 0), (-1, header_rows - 1), LIGHT_BLUE),
                ("FONTNAME", (0, 0), (-1, header_rows - 1), "Helvetica-Bold"),
            ])

        table.setStyle(TableStyle(commands))
        return table

    company = data.company
    employee = data.employee

    # Build the document
    elements = []

    elements.append(
        paragraph("PAYSLIP", title_style)
    )

    # Company header and statement heading
    company_lines = [
        paragraph(
            safe(company.company_name) or "COMPANY NAME",
            company_style,
        ),
        paragraph(safe(company.address), normal_style),
    ]

    identifiers = []
    if company.gstin:
        identifiers.append(f"GSTIN: {safe(company.gstin)}")
    if company.llpin:
        identifiers.append(f"LLPIN: {safe(company.llpin)}")

    if identifiers:
        company_lines.append(
            paragraph(" | ".join(identifiers), normal_style)
        )

    contacts = [
        safe(item)
        for item in (
            company.contact_number,
            company.email,
            company.website,
        )
        if item
    ]

    if contacts:
        company_lines.append(
            paragraph(" | ".join(contacts), normal_style)
        )

    statement_lines = [
        paragraph("Statement of Earnings", statement_style),
        Spacer(1, 2 * mm),
        # paragraph(
        #     f"<b>Pay Period:</b> "
        #     f"{calendar.month_name[data.month]} {data.year}",
        #     amount_style,
        # ),
    ]

    header = Table(
        [[company_lines, statement_lines]],
        colWidths=[112 * mm, 66 * mm],
    )
    header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))

    elements.append(header)
    elements.append(Spacer(1, 4 * mm))

    # Employee information
    elements.append(section_bar("Employee Information", 178 * mm))

    employee_rows = [
        [
            paragraph("<b>Employee Name:</b>", normal_style),
            paragraph(safe(employee.employee_name)),
            paragraph("<b>Pay Period:</b>", normal_style),
            paragraph(f"{calendar.month_name[data.month]} {data.year}"),
        ],
        [
            paragraph("<b>Designation:</b>", normal_style),
            paragraph(safe(employee.designation)),
            paragraph("<b>Income Tax PAN:</b>", normal_style),
            paragraph(safe(employee.income_tax_pan) or "N/A"),
        ],
    ]

    employee_table = Table(
        employee_rows,
        colWidths=[30 * mm, 57 * mm, 34 * mm, 57 * mm],
    )
    employee_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))

    elements.append(employee_table)
    elements.append(Spacer(1, 5 * mm))

    # Earnings: current values are available from the request.
    # YTD is deliberately shown as unavailable because no YTD
    # information exists in the current request model.
    earnings = [
        ("Basic Salary", data.basic_pay),
        ("House Rent Allowance", data.house_rent_allowance),
        ("Special Allowance", data.special_allowance),
        ("Conveyance Allowance", data.conveyance_allowance),
        ("Fuel Allowance", data.fuel_allowance),
    ]

    earnings_rows = [[
        paragraph("Earnings", table_header_style),
         paragraph("Amount (Rs.)", table_header_style),
       # paragraph("Year-to-Date", table_header_style),
    ]]

    for label, value in earnings:
        earnings_rows.append([
            paragraph(safe(label)),
            paragraph(money(value), amount_style),
           # paragraph("N/A", amount_style),
        ])

    earnings_rows.append([
        paragraph("<b>Gross Pay</b>"),
        paragraph(f"<b>{money(data.gross_pay)}</b>", amount_style),
       # paragraph("<b>N/A</b>", amount_style),
    ])

    earnings_table = Table(
        earnings_rows,
        colWidths=[89 * mm, 89 * mm],
    )
    apply_grid(earnings_table, header_rows=1)
    earnings_table.setStyle(TableStyle([
        ("BACKGROUND", (0, -1), (-1, -1), LIGHT_BLUE),
    ]))

    elements.append(earnings_table)
    elements.append(Spacer(1, 5 * mm))

    # Deductions
    deduction_rows = [[
        paragraph("Deductions", table_header_style),
        paragraph("Current", table_header_style),
       # paragraph("Year-to-Date", table_header_style),
    ]]

    deduction_rows.append([
        paragraph("Professional Tax"),
        paragraph(money(data.profession_tax), amount_style),
      # paragraph("N/A", amount_style),
    ])

    deduction_rows.append([
        paragraph("<b>Total Deductions</b>"),
        paragraph(f"<b>{money(data.total_deductions)}</b>", amount_style),
       # paragraph("<b>N/A</b>", amount_style),
    ])

    deduction_table = Table(
        deduction_rows,
        colWidths=[89 * mm, 89 * mm],
    )
    apply_grid(deduction_table, header_rows=1)
    deduction_table.setStyle(TableStyle([
        ("BACKGROUND", (0, -1), (-1, -1), LIGHT_BLUE),
    ]))

    elements.append(deduction_table)
    elements.append(Spacer(1, 5 * mm))

    # Prominent net pay box
    net_table = Table(
        [[
            paragraph("NET PAY", net_label_style),
            paragraph(money(data.net_pay), net_amount_style),
        ]],
        colWidths=[75 * mm, 75 * mm],
        hAlign="RIGHT"
    )
    net_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (0, 0), "RIGHT"),
        ("BACKGROUND", (1, 0), (1, 0), BLUE),
        ("BOX", (1, 0), (1, 0), 0.8, NAVY),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))

    elements.append(net_table)
    elements.append(Spacer(1, 10 * mm))

    # Direct deposit information is omitted until bank fields
    # are added to the request model.
    elements.append(
        paragraph(
            "This is a auto-generated salary slip.",
            ParagraphStyle(
                "Footer",
                parent=normal_style,
                alignment=TA_CENTER,
                textColor=MUTED,
                fontSize=10,
            ),
        )
    )

    # Outer frame around the printable payslip content
    def draw_border(canvas, document):
        canvas.saveState()
        canvas.setStrokeColor(BORDER)
        canvas.setLineWidth(1.5)
        canvas.rect(
            12 * mm,
            8 * mm,
            A4[0] - 24 * mm,
            A4[1] - 16 * mm,
            stroke=1,
            fill=0,
        )
        canvas.restoreState()

    doc.build(
        elements,
        onFirstPage=draw_border,
        onLaterPages=draw_border,
    )

    buffer.seek(0)
    return buffer

