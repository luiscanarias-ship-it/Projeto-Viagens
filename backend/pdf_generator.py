"""
PDF Travel Guide Generator for 4Luis
Generates a clean, mobile-friendly offline travel guide PDF.
"""

import io
import math
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether, Image as RLImage, PageBreak
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from staticmap import StaticMap, CircleMarker

# 4Luis brand colors
PEACH = HexColor("#FFBE98")
DARK = HexColor("#2D2A26")
GREY = HexColor("#6B6661")
LIGHT_BG = HexColor("#FAF9F8")
BLUE = HexColor("#3B82F6")
AMBER = HexColor("#D97706")
EMERALD = HexColor("#059669")

DAY_COLORS = [
    "#E63946", "#2D9CDB", "#F2994A", "#27AE60",
    "#9B51E0", "#F2C94C", "#EB5757", "#219EBC"
]

# Styles
STYLES = {
    "title": ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=22, textColor=DARK, spaceAfter=2*mm, leading=26),
    "subtitle": ParagraphStyle("subtitle", fontName="Helvetica", fontSize=10, textColor=GREY, spaceAfter=4*mm),
    "h2": ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=13, textColor=DARK, spaceBefore=6*mm, spaceAfter=3*mm),
    "h3": ParagraphStyle("h3", fontName="Helvetica-Bold", fontSize=11, textColor=DARK, spaceBefore=3*mm, spaceAfter=2*mm),
    "body": ParagraphStyle("body", fontName="Helvetica", fontSize=9, textColor=GREY, leading=14, spaceAfter=1*mm),
    "body_bold": ParagraphStyle("body_bold", fontName="Helvetica-Bold", fontSize=9, textColor=DARK, leading=14, spaceAfter=1*mm),
    "small": ParagraphStyle("small", fontName="Helvetica", fontSize=8, textColor=GREY, leading=11),
    "small_bold": ParagraphStyle("small_bold", fontName="Helvetica-Bold", fontSize=8, textColor=DARK, leading=11),
    "day_title": ParagraphStyle("day_title", fontName="Helvetica-Bold", fontSize=11, textColor=PEACH, spaceBefore=4*mm, spaceAfter=1*mm),
    "activity": ParagraphStyle("activity", fontName="Helvetica", fontSize=9, textColor=DARK, leading=13, leftIndent=8*mm, spaceAfter=0.5*mm),
    "tip": ParagraphStyle("tip", fontName="Helvetica", fontSize=9, textColor=DARK, leading=13, leftIndent=6*mm, spaceAfter=1*mm),
    "footer": ParagraphStyle("footer", fontName="Helvetica", fontSize=7, textColor=GREY, alignment=TA_CENTER),
    "center": ParagraphStyle("center", fontName="Helvetica", fontSize=9, textColor=GREY, alignment=TA_CENTER),
}

def _clean_text(text):
    """Remove CTA markers and clean text for PDF"""
    if not text:
        return ""
    import re
    return re.sub(r'\[CTA:\w+:[^\]]+\]', '', str(text)).strip()


def _section_header(title, icon_char=""):
    """Create a styled section header"""
    prefix = f"{icon_char}  " if icon_char else ""
    return Paragraph(f"{prefix}{title}", STYLES["h2"])


def _build_flight_section(plan):
    """Build flight information section"""
    fi = plan.get("flight_info", {})
    if not fi:
        return []
    
    elements = [_section_header("Voos")]
    
    for key, label in [("outbound", "Ida"), ("return", "Volta")]:
        flight = fi.get(key)
        if not flight:
            continue
        
        data = [
            [Paragraph(f"<b>{label}</b>", STYLES["small_bold"]),
             Paragraph(flight.get("flight_number", ""), STYLES["small_bold"]),
             "", ""],
            [Paragraph("Partida", STYLES["small"]),
             Paragraph(flight.get("departure_airport", ""), STYLES["small"]),
             Paragraph("Chegada", STYLES["small"]),
             Paragraph(flight.get("arrival_airport", ""), STYLES["small"])],
            [Paragraph("Hora", STYLES["small"]),
             Paragraph(f"<b>{flight.get('departure_time', '')}</b>", STYLES["small_bold"]),
             Paragraph("Hora", STYLES["small"]),
             Paragraph(f"<b>{flight.get('arrival_time', '')}</b>", STYLES["small_bold"])],
        ]
        
        t = Table(data, colWidths=[22*mm, 55*mm, 22*mm, 55*mm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), HexColor("#F0F7FF") if key == "outbound" else HexColor("#FFFBEB")),
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 2*mm),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2*mm),
            ("LEFTPADDING", (0, 0), (-1, -1), 3*mm),
            ("BOX", (0, 0), (-1, -1), 0.5, HexColor("#E5E5E5")),
            ("LINEBELOW", (0, 0), (-1, 0), 0.5, HexColor("#E5E5E5")),
            ("ROUNDEDCORNERS", [3, 3, 3, 3]),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 2*mm))
    
    return elements


def _build_hotel_section(plan):
    """Build hotel information section"""
    hi = plan.get("hotel_info", {})
    if not hi or not hi.get("name"):
        return []
    
    elements = [_section_header("Alojamento")]
    
    lines = [f"<b>{hi['name']}</b>"]
    if hi.get("address"):
        lines.append(hi["address"])
    if hi.get("area"):
        lines.append(f"Zona: {hi['area']}")
    if hi.get("phone"):
        lines.append(f"Tel: {hi['phone']}")
    
    for line in lines:
        elements.append(Paragraph(line, STYLES["body"] if "<b>" not in line else STYLES["body_bold"]))
    
    return elements


def _build_transport_section(plan):
    """Build airport-to-hotel transport section"""
    ath = plan.get("airport_to_hotel", {})
    if not ath:
        return []
    
    elements = [_section_header("Aeroporto para o Hotel")]
    
    best = ath.get("best_option", {})
    alt = ath.get("alternative", {})
    tip = ath.get("tip", "")
    
    if best:
        elements.append(Paragraph(f"<b>Melhor opcao:</b> {best.get('mode', '')} — {best.get('duration', '')} — {best.get('cost', '')}", STYLES["body"]))
    if alt:
        elements.append(Paragraph(f"<b>Alternativa:</b> {alt.get('mode', '')} — {alt.get('duration', '')} — {alt.get('cost', '')}", STYLES["body"]))
    if tip:
        elements.append(Paragraph(f"<b>Dica:</b> {_clean_text(tip)}", STYLES["body"]))
    
    return elements


def _build_map_image(plan, geocode_data):
    """Generate static map image with pins"""
    if not geocode_data or not geocode_data.get("days"):
        return []
    
    try:
        m = StaticMap(600, 350, url_template="https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png")
        
        # Add day location pins
        for day_data in geocode_data.get("days", []):
            day_num = day_data.get("day", 1)
            color_hex = DAY_COLORS[(day_num - 1) % len(DAY_COLORS)]

            for loc in day_data.get("locations", []):
                if loc.get("lat") and loc.get("lng"):
                    marker = CircleMarker((loc["lng"], loc["lat"]), color=color_hex, width=10)
                    m.add_marker(marker)
        
        # Add special pins (airport / hotel)
        sp = geocode_data.get("special_pins", {})
        if sp.get("airport", {}).get("lat"):
            ap = sp["airport"]
            m.add_marker(CircleMarker((ap["lng"], ap["lat"]), color="#3B82F6", width=14))
        if sp.get("hotel", {}).get("lat"):
            ht = sp["hotel"]
            m.add_marker(CircleMarker((ht["lng"], ht["lat"]), color="#D97706", width=14))
        
        img_bytes = m.render()
        buf = io.BytesIO()
        img_bytes.save(buf, format="PNG")
        buf.seek(0)
        
        elements = [_section_header("Mapa")]
        elements.append(RLImage(buf, width=155*mm, height=90*mm))
        
        # Legend
        legend_text = "Azul = Aeroporto | Laranja = Hotel | Cores = Atividades por dia"
        elements.append(Paragraph(legend_text, STYLES["center"]))
        elements.append(Spacer(1, 2*mm))
        
        return elements
    except Exception:
        return []


def _build_itinerary_section(plan):
    """Build day-by-day itinerary"""
    itinerary = plan.get("itinerary", [])
    if not itinerary:
        return []
    
    elements = [_section_header("Roteiro Dia a Dia")]
    
    for day in itinerary:
        day_num = day.get("day", "?")
        title = day.get("title", "")
        activities = day.get("activities", [])
        
        color = DAY_COLORS[(int(day_num) - 1) % len(DAY_COLORS)] if str(day_num).isdigit() else "#FFBE98"
        
        day_elements = []
        style = ParagraphStyle("day_h", fontName="Helvetica-Bold", fontSize=11, textColor=HexColor(color), spaceBefore=4*mm, spaceAfter=1*mm)
        day_elements.append(Paragraph(f"Dia {day_num} — {title}", style))
        
        for a in activities:
            clean = _clean_text(a)
            if clean:
                day_elements.append(Paragraph(f"• {clean}", STYLES["activity"]))
        
        day_elements.append(Spacer(1, 2*mm))
        elements.append(KeepTogether(day_elements))
    
    return elements


def _build_tips_section(plan):
    """Build local tips and weather"""
    elements = []
    
    # Weather
    weather = plan.get("weather", "")
    if weather:
        elements.append(_section_header("Clima"))
        elements.append(Paragraph(_clean_text(weather), STYLES["body"]))
    
    # Packing
    packing = plan.get("packing", {})
    if packing:
        elements.append(_section_header("O que Levar"))
        for category, items in packing.items():
            if items:
                label = {"clothing": "Roupa", "essentials": "Essenciais"}.get(category, category.capitalize())
                elements.append(Paragraph(f"<b>{label}:</b>", STYLES["small_bold"]))
                for item in items:
                    clean = _clean_text(item)
                    if clean:
                        elements.append(Paragraph(f"  • {clean}", STYLES["small"]))
                elements.append(Spacer(1, 1*mm))
    
    # Local tips
    tips = plan.get("local_tips", [])
    if tips:
        elements.append(_section_header("Dicas Locais"))
        for tip in tips:
            clean = _clean_text(tip)
            if clean:
                elements.append(Paragraph(f"• {clean}", STYLES["tip"]))
    
    # Checklist
    checklist = plan.get("checklist", {})
    if checklist:
        elements.append(_section_header("Checklist de Viagem"))
        for category, items in checklist.items():
            if items:
                label = {"documents": "Documentos", "hygiene": "Higiene", "tech": "Tecnologia"}.get(category, category.capitalize())
                elements.append(Paragraph(f"<b>{label}:</b>", STYLES["small_bold"]))
                for item in items:
                    clean = _clean_text(item)
                    if clean:
                        elements.append(Paragraph(f"  ☐ {clean}", STYLES["small"]))
                elements.append(Spacer(1, 1*mm))
    
    return elements


def generate_travel_guide_pdf(plan, geocode_data=None, sections=None, affiliate_links=None, og_image_bytes=None):
    """
    Generate a complete offline travel guide PDF.
    
    Args:
        plan: dict - The AI-generated travel plan
        geocode_data: dict - Optional geocode data for static map
        sections: dict - Which sections to include {flights, hotel, map, itinerary, tips, transport}
        affiliate_links: dict - Optional affiliate link URLs {booking: {url}, skyscanner: {url}, ...}
        og_image_bytes: bytes - Optional OG image for PDF cover page
    
    Returns:
        BytesIO buffer containing the PDF
    """
    if sections is None:
        sections = {"flights": True, "hotel": True, "map": True, "itinerary": True, "tips": True, "transport": True}
    if affiliate_links is None:
        affiliate_links = {}
    
    buf = io.BytesIO()
    
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        topMargin=15*mm,
        bottomMargin=20*mm,
        leftMargin=18*mm,
        rightMargin=18*mm,
        title=f"Guia de Viagem - {plan.get('destination', '')}",
        author="4Luis AI Travel Planner"
    )
    
    elements = []
    
    # ─── Cover Page (using OG image) ───
    destination = plan.get("destination", "Viagem")
    dates = plan.get("dates", "")
    num_days = len(plan.get("itinerary", []))
    summary = plan.get("summary", "")
    
    if og_image_bytes:
        try:
            cover_buf = io.BytesIO(og_image_bytes)
            # Full-width cover image
            page_w = A4[0] - 36*mm  # account for margins
            img_ratio = 630 / 1200
            cover_h = page_w * img_ratio
            elements.append(RLImage(cover_buf, width=page_w, height=cover_h))
            elements.append(Spacer(1, 8*mm))
        except Exception:
            pass

    # Cover text
    elements.append(Paragraph(destination, ParagraphStyle("cover_title", fontName="Helvetica-Bold", fontSize=28, textColor=DARK, spaceAfter=2*mm, leading=34)))
    
    cover_subtitle = "Guia de viagem criado com IA"
    elements.append(Paragraph(cover_subtitle, ParagraphStyle("cover_sub", fontName="Helvetica", fontSize=12, textColor=PEACH, spaceAfter=4*mm)))

    subtitle_parts = []
    if num_days > 0:
        subtitle_parts.append(f"{num_days} dias")
    if dates:
        subtitle_parts.append(dates)
    if subtitle_parts:
        elements.append(Paragraph(" | ".join(subtitle_parts), STYLES["subtitle"]))
    
    if summary:
        elements.append(Paragraph(_clean_text(summary), STYLES["body"]))
    
    elements.append(Spacer(1, 6*mm))
    elements.append(Paragraph("4Luis", ParagraphStyle("cover_brand", fontName="Helvetica-Bold", fontSize=14, textColor=PEACH)))
    elements.append(Paragraph("4luis.com", STYLES["small"]))
    
    elements.append(PageBreak())
    
    # ─── Content Header ───
    elements.append(Paragraph("4Luis", ParagraphStyle("brand", fontName="Helvetica-Bold", fontSize=14, textColor=PEACH)))
    elements.append(Spacer(1, 1*mm))
    elements.append(HRFlowable(width="100%", thickness=2, color=PEACH, spaceAfter=4*mm))
    elements.append(Paragraph(destination, STYLES["title"]))
    if subtitle_parts:
        elements.append(Paragraph(" | ".join(subtitle_parts), STYLES["subtitle"]))

    elements.append(Spacer(1, 4*mm))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=HexColor("#E5E5E5"), spaceAfter=2*mm))
    
    # ─── Sections ───
    if sections.get("flights"):
        elements.extend(_build_flight_section(plan))
    
    if sections.get("hotel"):
        elements.extend(_build_hotel_section(plan))
    
    if sections.get("transport"):
        elements.extend(_build_transport_section(plan))
    
    if sections.get("map") and geocode_data:
        elements.extend(_build_map_image(plan, geocode_data))
    
    if sections.get("itinerary"):
        elements.extend(_build_itinerary_section(plan))
    
    if sections.get("tips"):
        elements.extend(_build_tips_section(plan))
    
    # ─── Affiliate Links (clickable in PDF) ───
    if affiliate_links:
        elements.append(_section_header("Links Uteis"))
        destination = plan.get("destination", "")
        link_items = [
            ("booking", f"Hoteis em {destination}", "Melhor localizacao · Cancelamento gratis"),
            ("skyscanner", "Comparar voos", "Melhor preco para estas datas"),
            ("getyourguide", f"Atividades em {destination}", "Evita filas · Cancelamento gratis"),
            ("insurance", "Seguro de viagem", "Protege a tua viagem"),
            ("airalo", "eSIM internacional", "Internet sem roaming"),
        ]
        for key, label, desc in link_items:
            url = affiliate_links.get(key, {}).get("url", "")
            if url:
                elements.append(Paragraph(
                    f'<b>{label}</b> — {desc}<br/>'
                    f'<a href="{url}" color="#FFBE98">{url[:60]}{"..." if len(url) > 60 else ""}</a>',
                    ParagraphStyle("link", fontName="Helvetica", fontSize=8, textColor=GREY, leading=12, spaceAfter=2*mm)
                ))
    
    # ─── Footer ───
    elements.append(Spacer(1, 8*mm))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=HexColor("#E5E5E5"), spaceAfter=3*mm))
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    elements.append(Paragraph(f"Guia gerado por 4Luis AI Travel Planner — {now}", STYLES["footer"]))
    elements.append(Paragraph("4luis.com — Sonha connosco", STYLES["footer"]))
    
    doc.build(elements)
    buf.seek(0)
    return buf
