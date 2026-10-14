import os
import json
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY


# ── Color palette ──────────────────────────────────────────────────────────────
BRAND_DARK   = colors.HexColor("#0A0E1A")
BRAND_ACCENT = colors.HexColor("#7C3AED")
BRAND_CYAN   = colors.HexColor("#06B6D4")
RISK_COLORS  = {
    "CRITICAL": colors.HexColor("#EF4444"),
    "HIGH":     colors.HexColor("#F97316"),
    "MEDIUM":   colors.HexColor("#EAB308"),
    "LOW":      colors.HexColor("#22C55E"),
}


def _risk_color(level: str):
    return RISK_COLORS.get(level.upper(), colors.gray)


def generate_pdf(analysis: dict, output_dir: str) -> str:
    """Generate a formatted PDF report and return the file path."""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename  = f"fraudshield_report_{analysis.get('id', 'X')}_{timestamp}.pdf"
    filepath  = os.path.join(output_dir, filename)

    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm,   bottomMargin=2*cm,
        title="FraudShield Analysis Report",
    )

    styles = getSampleStyleSheet()
    story  = []

    # ── Helper styles ──────────────────────────────────────────────────────────
    h1 = ParagraphStyle("H1", parent=styles["Title"],
                        fontSize=22, textColor=BRAND_ACCENT,
                        spaceAfter=4, fontName="Helvetica-Bold", alignment=TA_CENTER)
    h2 = ParagraphStyle("H2", parent=styles["Heading2"],
                        fontSize=13, textColor=BRAND_CYAN,
                        spaceBefore=14, spaceAfter=4, fontName="Helvetica-Bold")
    body = ParagraphStyle("Body", parent=styles["Normal"],
                          fontSize=10, leading=14, alignment=TA_JUSTIFY)
    small = ParagraphStyle("Small", parent=styles["Normal"],
                           fontSize=8, textColor=colors.grey)
    code  = ParagraphStyle("Code", parent=styles["Code"],
                           fontSize=8, backColor=colors.HexColor("#1E1E2E"),
                           textColor=colors.HexColor("#A6E3A1"), leading=12,
                           leftIndent=6, rightIndent=6, spaceBefore=4, spaceAfter=4)

    # ── Header ─────────────────────────────────────────────────────────────────
    story.append(Paragraph("🛡 FraudShield", h1))
    story.append(Paragraph("AI-Powered Fraud Detection Report", ParagraphStyle(
        "sub", parent=styles["Normal"], fontSize=11,
        textColor=colors.lightgrey, alignment=TA_CENTER)))
    story.append(Spacer(1, 0.3*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=BRAND_ACCENT))
    story.append(Spacer(1, 0.4*cm))

    # ── Risk Banner ────────────────────────────────────────────────────────────
    risk_level = analysis.get("risk_level", "LOW")
    risk_score = analysis.get("risk_score", 0)
    rc = _risk_color(risk_level)
    is_fraud = analysis.get("is_fraud", False)
    verdict_text = "⚠️  FRAUD DETECTED" if is_fraud else "✅  CLEAN — No Fraud Detected"
    verdict_color = colors.HexColor("#EF4444") if is_fraud else colors.HexColor("#22C55E")

    banner_data = [[
        Paragraph(f"<b>VERDICT</b><br/><font size=14>{verdict_text}</font>",
                  ParagraphStyle("v", parent=styles["Normal"],
                                 textColor=verdict_color, alignment=TA_CENTER)),
        Paragraph(f"<b>RISK SCORE</b><br/><font size=20 color='#{rc.hexval()[-6:]}'><b>{risk_score:.0f}/100</b></font>",
                  ParagraphStyle("rs", parent=styles["Normal"],
                                 textColor=rc, alignment=TA_CENTER)),
        Paragraph(f"<b>RISK LEVEL</b><br/><font size=16><b>{risk_level}</b></font>",
                  ParagraphStyle("rl", parent=styles["Normal"],
                                 textColor=rc, alignment=TA_CENTER)),
        Paragraph(f"<b>CONFIDENCE</b><br/><font size=14>{analysis.get('confidence', 0):.0f}%</font>",
                  ParagraphStyle("cf", parent=styles["Normal"],
                                 textColor=BRAND_CYAN, alignment=TA_CENTER)),
    ]]
    banner_table = Table(banner_data, colWidths=[4.2*cm, 3.8*cm, 3.8*cm, 3.8*cm])
    banner_table.setStyle(TableStyle([
        ("BACKGROUND",  (0,0), (-1,-1), colors.HexColor("#0F1629")),
        ("TEXTCOLOR",   (0,0), (-1,-1), colors.white),
        ("ALIGN",       (0,0), (-1,-1), "CENTER"),
        ("VALIGN",      (0,0), (-1,-1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [colors.HexColor("#0F1629")]),
        ("BOX",         (0,0), (-1,-1), 1, BRAND_ACCENT),
        ("INNERGRID",   (0,0), (-1,-1), 0.5, colors.HexColor("#2A2A4A")),
        ("TOPPADDING",  (0,0), (-1,-1), 10),
        ("BOTTOMPADDING",(0,0), (-1,-1), 10),
    ]))
    story.append(banner_table)
    story.append(Spacer(1, 0.5*cm))

    # ── Meta info ──────────────────────────────────────────────────────────────
    story.append(Paragraph("📋 Analysis Details", h2))
    ai_engine = analysis.get("ai_model") or analysis.get("evidence", {}).get("ai_model_used", "Google Gemini AI")
    meta_rows = [
        ["Report ID",     str(analysis.get("id", "N/A"))],
        ["Input Type",    analysis.get("input_type", "").upper()],
        ["AI Engine",     str(ai_engine)],
        ["Scam Type",     analysis.get("scam_type", "N/A")],
        ["Generated On",  analysis.get("created_at", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))],
    ]
    if analysis.get("input_content"):
        content_preview = str(analysis["input_content"])[:200]
        if len(str(analysis["input_content"])) > 200:
            content_preview += "…"
        meta_rows.append(["Input Preview", content_preview])

    meta_table = Table(meta_rows, colWidths=[4*cm, 12.6*cm])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (0,-1), colors.HexColor("#1E1E3A")),
        ("BACKGROUND",   (1,0), (1,-1), colors.HexColor("#0F1629")),
        ("TEXTCOLOR",    (0,0), (-1,-1), colors.white),
        ("FONTNAME",     (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTSIZE",     (0,0), (-1,-1), 9),
        ("GRID",         (0,0), (-1,-1), 0.5, colors.HexColor("#2A2A4A")),
        ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",   (0,0), (-1,-1), 6),
        ("BOTTOMPADDING",(0,0), (-1,-1), 6),
        ("LEFTPADDING",  (0,0), (-1,-1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 0.4*cm))

    # ── Explanation ────────────────────────────────────────────────────────────
    story.append(Paragraph("🔍 AI Analysis Explanation", h2))
    explanation = analysis.get("explanation", "No detailed explanation available.")
    story.append(Paragraph(explanation, body))
    story.append(Spacer(1, 0.4*cm))

    # ── Indicators ─────────────────────────────────────────────────────────────
    indicators = analysis.get("indicators", [])
    if indicators:
        story.append(Paragraph("⚠️  Detected Indicators", h2))
        for ind in indicators:
            if isinstance(ind, dict):
                label = ind.get("label", "Indicator")
                detail = ind.get("detail", "")
                sev = ind.get("severity", "medium").upper()
                sev_col = {"HIGH": "#EF4444", "MEDIUM": "#F97316", "LOW": "#EAB308"}.get(sev, "#EAB308")
                story.append(Paragraph(
                    f'<font color="{sev_col}">▶ [{sev}]</font>  <b>{label}</b> — {detail}', body))
            else:
                story.append(Paragraph(f"▶ {ind}", body))
        story.append(Spacer(1, 0.3*cm))

    # ── Evidence ───────────────────────────────────────────────────────────────
    evidence = analysis.get("evidence", {})
    if evidence:
        story.append(Paragraph("🧾 Evidence Details", h2))
        for k, v in evidence.items():
            label = k.replace("_", " ").title()
            story.append(Paragraph(f"<b>{label}:</b>", body))
            story.append(Paragraph(str(v)[:500], code if "url" in k.lower() or "code" in k.lower() else body))
        story.append(Spacer(1, 0.3*cm))

    # ── Recommendations ────────────────────────────────────────────────────────
    recommendations = analysis.get("recommendations", [])
    if recommendations:
        story.append(Paragraph("🔒 Security Recommendations", h2))
        for i, rec in enumerate(recommendations, 1):
            if isinstance(rec, dict):
                title = rec.get("title", f"Recommendation {i}")
                detail = rec.get("detail", "")
                story.append(Paragraph(f"<b>{i}. {title}</b>", body))
                if detail:
                    story.append(Paragraph(f"   {detail}", body))
            else:
                story.append(Paragraph(f"{i}. {rec}", body))
        story.append(Spacer(1, 0.3*cm))

    # ── Footer ─────────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=BRAND_ACCENT))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        "This report was generated by FraudShield AI. "
        "Results are AI-assisted analysis and should be reviewed by a security professional.",
        small))
    story.append(Paragraph(
        f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
        ParagraphStyle("footer_r", parent=styles["Normal"], fontSize=7,
                       textColor=colors.grey, alignment=TA_CENTER)))

    doc.build(story)
    return filepath
