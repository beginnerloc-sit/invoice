"""Generate a small set of sample invoice PDFs with varied layouts and missing-data patterns.

Run from the project root (with the backend venv activated, plus reportlab installed):
    pip install reportlab
    python samples/generate_samples.py

PDFs land in samples/output/.
"""
from __future__ import annotations

import os
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

OUT = Path(__file__).resolve().parent / "output"
OUT.mkdir(exist_ok=True)

styles = getSampleStyleSheet()


def p(text, font="Helvetica", size=10, color=colors.black, align=TA_LEFT, leading=None, bold=False):
    f = font + "-Bold" if bold else font
    style = ParagraphStyle(
        "x", fontName=f, fontSize=size, leading=leading or size + 3, textColor=color, alignment=align,
    )
    return Paragraph(text, style)


# ---------------------------------------------------------------------------
# 1. Galaxy Pte Ltd — Singapore, classic blue corporate, ALL fields present
# ---------------------------------------------------------------------------
def invoice_galaxy():
    doc = SimpleDocTemplate(
        str(OUT / "01_galaxy_singapore.pdf"),
        pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm, bottomMargin=16 * mm,
    )
    BLUE = colors.HexColor("#1f4e8a")
    story = []

    header = Table(
        [[
            p("GALAXY PTE LTD", size=22, color=BLUE, bold=True),
            p("TAX INVOICE", size=20, color=colors.black, bold=True, align=TA_RIGHT),
        ]],
        colWidths=[100 * mm, 70 * mm],
    )
    header.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 2, BLUE), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
    story += [header, Spacer(1, 4 * mm)]

    story += [p("23 Tuas South Avenue 7, Singapore 637651", size=9, color=colors.grey)]
    story += [p("UEN: 200512345R   |   Tel: +65 6555 1234   |   accounts@galaxy.sg", size=9, color=colors.grey)]
    story += [Spacer(1, 6 * mm)]

    bill_to = Table(
        [[
            p("<b>Bill To:</b><br/>Stride Engineering Pte Ltd<br/>10 Anson Rd, #14-02<br/>International Plaza, Singapore 079903", size=10),
            p(
                "<b>Invoice No.:</b>  APP2600079<br/>"
                "<b>Invoice Date:</b>  03/03/2026<br/>"
                "<b>PO No.:</b>  K0094/26<br/>"
                "<b>DO No.:</b>  SH26000079<br/>"
                "<b>Project Code:</b>  Q/26/1010",
                size=10, align=TA_RIGHT,
            ),
        ]],
        colWidths=[90 * mm, 80 * mm],
    )
    bill_to.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story += [bill_to, Spacer(1, 8 * mm)]

    items = [
        ["#", "Description of Items / Works", "Qty", "Unit Price", "Amount (SGD)"],
        [
            "1",
            "Rack PDU 2G, Metered, ZeroU, 32A, 230V, (36) C13 & (6) C19\n"
            "AP8853; S/N: 0A2211G15414, 0A2210G11676",
            "1", "4,140.00", "4,140.00",
        ],
    ]
    t = Table(items, colWidths=[10 * mm, 90 * mm, 15 * mm, 25 * mm, 30 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BLUE),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cfd6e3")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))
    story += [t, Spacer(1, 4 * mm)]

    totals = Table(
        [
            ["Amount Before GST", "SGD 4,140.00"],
            ["GST 9%", "SGD 372.60"],
            ["Total Amount", "SGD 4,512.60"],
        ],
        colWidths=[130 * mm, 40 * mm],
    )
    totals.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
        ("FONTNAME", (0, 2), (-1, 2), "Helvetica-Bold"),
        ("BACKGROUND", (0, 2), (-1, 2), colors.HexColor("#eef2f8")),
        ("BOX", (0, 2), (-1, 2), 1, BLUE),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
    ]))
    story += [totals, Spacer(1, 8 * mm)]

    story += [p("<b>Currency:</b> SGD &nbsp;&nbsp;&nbsp;&nbsp; <b>Payment Terms:</b> 30D &nbsp;&nbsp;&nbsp;&nbsp; <b>Cost Code / Trade:</b> Electrical", size=10)]
    story += [Spacer(1, 6 * mm)]
    story += [p("Please make payment within 30 days. Thank you for your business.", size=9, color=colors.grey, align=TA_CENTER)]

    doc.build(story)


# ---------------------------------------------------------------------------
# 2. Acme Industrial Supplies — USA, no GST line at all
# ---------------------------------------------------------------------------
def invoice_acme():
    doc = SimpleDocTemplate(
        str(OUT / "02_acme_usa.pdf"),
        pagesize=LETTER,
        leftMargin=20 * mm, rightMargin=20 * mm, topMargin=18 * mm, bottomMargin=18 * mm,
    )
    story = []

    header = Table(
        [[
            p("ACME INDUSTRIAL<br/>SUPPLIES, INC.", size=18, bold=True, leading=22),
            p(
                "<b>INVOICE</b><br/>"
                "Invoice #: 11827<br/>"
                "Date: April 14, 2026<br/>"
                "Project: ACME-IND-2025-04",
                size=10, align=TA_RIGHT, leading=14,
            ),
        ]],
        colWidths=[100 * mm, 70 * mm],
    )
    header.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 1.5, colors.black), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
    story += [header, Spacer(1, 4 * mm)]

    story += [p("4421 Industrial Pkwy, Cleveland, OH 44135 &nbsp;|&nbsp; (216) 555-2900 &nbsp;|&nbsp; ar@acme-industrial.com", size=8, color=colors.grey)]
    story += [Spacer(1, 8 * mm)]

    addr = Table(
        [[
            p("<b>BILL TO</b><br/>Northshore Manufacturing<br/>1200 Lakefront Dr.<br/>Erie, PA 16505", size=10, leading=13),
            p("<b>SHIP TO / DO #</b><br/>Same as bill-to<br/>DO No.: DO-7732", size=10, leading=13),
            p("<b>P.O. NUMBER</b><br/>PO-44182", size=10, leading=13),
        ]],
        colWidths=[60 * mm, 55 * mm, 55 * mm],
    )
    addr.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("BOX", (0, 0), (-1, -1), 0.5, colors.grey), ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.lightgrey), ("LEFTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
    story += [addr, Spacer(1, 8 * mm)]

    items = [
        ["Item", "Description", "Qty", "Unit", "Total"],
        ["BR-6204-2RS", "SKF deep-groove ball bearings, sealed", "20", "$42.00", "$840.00"],
        ["GS-INDX-104",  "Industrial gasket set, replacement kit", "5", "$160.00", "$800.00"],
        ["LBR-3000",     "Heavy-duty machinery lubricant, 5gal pail", "12", "$100.00", "$1,200.00"],
    ]
    t = Table(items, colWidths=[30 * mm, 80 * mm, 15 * mm, 25 * mm, 25 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#222")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
        ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story += [t, Spacer(1, 4 * mm)]

    # No GST, just total — note: no line for tax
    totals = Table([["Total", "USD $2,840.00"]], colWidths=[145 * mm, 30 * mm])
    totals.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 12),
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f4f4f4")),
        ("LINEABOVE", (0, 0), (-1, -1), 1.2, colors.black),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story += [totals, Spacer(1, 8 * mm)]

    story += [p("<b>Payment Terms:</b> Net 45 &nbsp;&nbsp; <b>Trade / Cost Code:</b> Mechanical &nbsp;&nbsp; <b>Currency:</b> USD", size=10)]
    story += [Spacer(1, 4 * mm)]
    story += [p("Make checks payable to Acme Industrial Supplies, Inc. Wire instructions on file.", size=9, color=colors.grey)]

    doc.build(story)


# ---------------------------------------------------------------------------
# 3. NorthBeam Logistics — UK, minimalist; missing project_code, po_number, do_number
# ---------------------------------------------------------------------------
def invoice_northbeam():
    doc = SimpleDocTemplate(
        str(OUT / "03_northbeam_uk.pdf"),
        pagesize=A4,
        leftMargin=22 * mm, rightMargin=22 * mm, topMargin=22 * mm, bottomMargin=22 * mm,
    )
    story = []

    story += [p("NorthBeam Logistics Ltd", size=24, bold=True, leading=28)]
    story += [p("logistics that just keep moving.", size=10, color=colors.grey)]
    story += [Spacer(1, 12 * mm)]

    head = Table(
        [
            ["Invoice", "NB-2026-0455"],
            ["Date", "12 February 2026"],
            ["Currency", "GBP"],
        ],
        colWidths=[35 * mm, 60 * mm],
    )
    head.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.grey),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))
    story += [head, Spacer(1, 8 * mm)]

    story += [p("<b>Billed to</b><br/>Hartwell Distribution Ltd<br/>Unit 14, Coventry Logistics Park<br/>Coventry, CV6 6AA", size=10, leading=14)]
    story += [Spacer(1, 8 * mm)]

    items = [
        ["Service", "Period", "Amount"],
        ["Cross-dock handling — pallet inbound/outbound", "1–31 Jan 2026", "£780.00"],
        ["Bonded pallet storage (12 pallets × 31 days)", "1–31 Jan 2026", "£470.00"],
    ]
    t = Table(items, colWidths=[110 * mm, 30 * mm, 25 * mm])
    t.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, 0), 1, colors.black),
        ("LINEBELOW", (0, -1), (-1, -1), 0.3, colors.lightgrey),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))
    story += [t, Spacer(1, 4 * mm)]

    totals = Table(
        [
            ["Subtotal", "£1,250.00"],
            ["VAT 20%", "£250.00"],
            ["Total due", "£1,500.00"],
        ],
        colWidths=[140 * mm, 25 * mm],
    )
    totals.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("FONTNAME", (0, 2), (-1, 2), "Helvetica-Bold"),
        ("LINEABOVE", (0, 2), (-1, 2), 1, colors.black),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story += [totals, Spacer(1, 10 * mm)]

    story += [p("<b>Payment terms:</b> Net 14 &nbsp;&nbsp; <b>Trade:</b> Logistics", size=10)]
    story += [Spacer(1, 6 * mm)]
    story += [p("VAT Reg: GB 482 9183 04 &nbsp;|&nbsp; northbeam.co.uk", size=8, color=colors.grey)]


    doc.build(story)


# ---------------------------------------------------------------------------
# 4. Stahl Werke GmbH — Germany, EUR, missing payment_terms
# ---------------------------------------------------------------------------
def invoice_stahlwerke():
    doc = SimpleDocTemplate(
        str(OUT / "04_stahlwerke_de.pdf"),
        pagesize=A4,
        leftMargin=20 * mm, rightMargin=20 * mm, topMargin=18 * mm, bottomMargin=18 * mm,
    )
    GREEN = colors.HexColor("#2f6b3a")
    story = []

    top = Table(
        [[
            p("Stahl Werke GmbH", size=20, bold=True, color=GREEN),
            p("RECHNUNG / INVOICE", size=14, bold=True, align=TA_RIGHT),
        ]],
        colWidths=[110 * mm, 60 * mm],
    )
    story += [top]
    story += [p("Industriestraße 14, 40472 Düsseldorf, Deutschland", size=9, color=colors.grey)]
    story += [p("USt-IdNr.: DE298 442 117  ·  Tel.: +49 211 4477 0", size=9, color=colors.grey)]
    story += [Spacer(1, 8 * mm)]

    meta = Table(
        [
            ["Rechnungs-Nr. / Invoice No.", "2026-00342"],
            ["Datum / Date",                 "22.01.2026"],
            ["Projekt / Project Code",       "PRJ-DE-2026-0118"],
            ["Bestell-Nr. / PO No.",         "PO/DE/9921"],
            ["Lieferschein / DO No.",        "LS-DE-0301"],
            ["Kostenstelle / Cost Code",     "Structural"],
        ],
        colWidths=[70 * mm, 100 * mm],
    )
    meta.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#333")),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("LINEBELOW", (0, 0), (-1, -1), 0.3, colors.lightgrey),
    ]))
    story += [meta, Spacer(1, 6 * mm)]

    story += [p("<b>Kunde / Customer:</b> Bauwerk Konstruktion AG, Hafenstr. 8, 20097 Hamburg", size=10)]
    story += [Spacer(1, 6 * mm)]

    items = [
        ["Pos.", "Beschreibung / Description", "Menge", "Einzelpreis", "Gesamt (EUR)"],
        ["1", "Stahlträger I-Profil S355JR, 6.0 m (steel I-beams)", "20",  "€650.00",   "€13,000.00"],
        ["2", "Schweißarbeiten vor Ort (on-site welding services)", "55h", "€100.00",   "€5,500.00"],
    ]
    t = Table(items, colWidths=[12 * mm, 90 * mm, 18 * mm, 25 * mm, 30 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), GREEN),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c4d4c7")),
        ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))
    story += [t, Spacer(1, 4 * mm)]

    totals = Table(
        [
            ["Nettobetrag / Amount before VAT", "EUR 18,500.00"],
            ["MwSt. 19% / VAT 19%",             "EUR 3,515.00"],
            ["Gesamtbetrag / Total",            "EUR 22,015.00"],
        ],
        colWidths=[140 * mm, 35 * mm],
    )
    totals.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("FONTNAME", (0, 2), (-1, 2), "Helvetica-Bold"),
        ("BACKGROUND", (0, 2), (-1, 2), colors.HexColor("#eaf3ec")),
        ("BOX", (0, 2), (-1, 2), 1, GREEN),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
    ]))
    story += [totals, Spacer(1, 8 * mm)]

    # Note: NO payment-terms line — intentionally missing
    story += [p("Bitte überweisen Sie den Betrag auf das unten angegebene Konto.", size=9, color=colors.grey)]
    story += [p("IBAN: DE45 3007 0010 0123 4567 89  ·  BIC: DEUTDEDDXXX", size=9, color=colors.grey)]

    doc.build(story)


# ---------------------------------------------------------------------------
# 5. Sunrise Trading Sdn Bhd — Malaysia, simple typewriter, missing cost_code & do_number
# ---------------------------------------------------------------------------
def invoice_sunrise():
    doc = SimpleDocTemplate(
        str(OUT / "05_sunrise_malaysia.pdf"),
        pagesize=A4,
        leftMargin=22 * mm, rightMargin=22 * mm, topMargin=22 * mm, bottomMargin=22 * mm,
    )
    story = []

    story += [p("SUNRISE TRADING SDN BHD", font="Courier", size=16, bold=True)]
    story += [p("18, Jalan Industri 3/5, Taman Perindustrian, 47100 Puchong, Selangor", font="Courier", size=9)]
    story += [p("SST Reg: W10-1808-32000123  |  Tel: +60 3-8082 1199", font="Courier", size=9)]
    story += [Spacer(1, 6 * mm)]
    story += [p("=" * 92, font="Courier", size=9)]
    story += [p("INVOICE", font="Courier", size=14, bold=True, align=TA_CENTER)]
    story += [p("=" * 92, font="Courier", size=9)]
    story += [Spacer(1, 4 * mm)]

    meta = Table(
        [
            ["Invoice No.:", "SR-INV-2026-0089"],
            ["Date:",        "28-Jan-2026"],
            ["Project:",     "ST/PRJ/2026-15"],
            ["PO No.:",      "PO-MY-440"],
            ["Currency:",    "MYR"],
            ["Terms:",       "30 days"],
        ],
        colWidths=[40 * mm, 100 * mm],
    )
    meta.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Courier"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("FONTNAME", (0, 0), (0, -1), "Courier-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
    ]))
    story += [meta, Spacer(1, 6 * mm)]

    story += [p("Bill to:  Lim Trading Enterprise, No. 12 Jalan SS2/24, 47300 Petaling Jaya", font="Courier", size=10)]
    story += [Spacer(1, 6 * mm)]

    items = [
        ["No", "Item description",                                  "Qty",  "Price",     "Amount"],
        ["1",  "A4 copy paper 80gsm, 5 reams/box (bulk)",           "30",   "MYR 22.00",  "MYR 660.00"],
        ["2",  "Whiteboard markers, mixed colour, box of 12",       "40",   "MYR 18.00",  "MYR 720.00"],
        ["3",  "Manila folder F4, 100 pcs/pack",                    "25",   "MYR 14.00",  "MYR 350.00"],
        ["4",  "Office chair mat, anti-slip, 90x120cm",             "10",   "MYR 147.00", "MYR 1,470.00"],
    ]
    t = Table(items, colWidths=[10 * mm, 80 * mm, 15 * mm, 30 * mm, 30 * mm])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Courier"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, 0), (-1, 0), "Courier-Bold"),
        ("LINEABOVE", (0, 0), (-1, 0), 0.5, colors.black),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.black),
        ("LINEBELOW", (0, -1), (-1, -1), 0.5, colors.black),
        ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story += [t, Spacer(1, 4 * mm)]

    totals = Table(
        [
            ["Subtotal (Amount before SST):", "MYR 3,200.00"],
            ["SST 6%:",                       "MYR 192.00"],
            ["TOTAL AMOUNT:",                 "MYR 3,392.00"],
        ],
        colWidths=[140 * mm, 30 * mm],
    )
    totals.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Courier"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("FONTNAME", (0, 2), (-1, 2), "Courier-Bold"),
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
        ("LINEABOVE", (0, 2), (-1, 2), 0.8, colors.black),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story += [totals, Spacer(1, 8 * mm)]
    story += [p("Thank you for your purchase.", font="Courier", size=10, align=TA_CENTER)]

    doc.build(story)


def main():
    invoice_galaxy()
    invoice_acme()
    invoice_northbeam()
    invoice_stahlwerke()
    invoice_sunrise()
    print(f"Generated 5 invoices in: {OUT}")
    for f in sorted(OUT.iterdir()):
        print(f"  - {f.name}  ({f.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
