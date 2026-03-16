"""
Generates data/extracted/methodology_review.pdf using reportlab.
Re-run whenever content needs updating.
"""
from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    FrameBreak,
    Image,
    KeepTogether,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.frames import Frame

# ── Colours ──────────────────────────────────────────────────────────────────
NAVY       = colors.HexColor("#1a3a6b")
BLUE       = colors.HexColor("#2255a4")
BLUE_LIGHT = colors.HexColor("#dce8f7")
TEAL       = colors.HexColor("#1a5276")
GOLD       = colors.HexColor("#f0c040")
AMBER_BG   = colors.HexColor("#fff8e1")
AMBER_BORDER = colors.HexColor("#f5c518")
GREEN_BG   = colors.HexColor("#e8f5e9")
GREEN_BORDER = colors.HexColor("#2e7d32")
GREEN_HDR  = colors.HexColor("#2e7d32")
WHITE      = colors.white
GREY_LINE  = colors.HexColor("#cccccc")
ROW_ALT    = colors.HexColor("#f5f8fd")

W, H = A4
MARGIN = 20 * mm

# ── Styles ───────────────────────────────────────────────────────────────────
base = getSampleStyleSheet()

def _s(name, **kw):
    return ParagraphStyle(name, **kw)

title_style = _s("Title",
    fontSize=22, textColor=NAVY, alignment=TA_CENTER,
    fontName="Helvetica-Bold", spaceAfter=4)
subtitle_style = _s("Subtitle",
    fontSize=12, textColor=BLUE, alignment=TA_CENTER,
    fontName="Helvetica", spaceAfter=2)
date_style = _s("Date",
    fontSize=9, textColor=colors.HexColor("#888888"), alignment=TA_CENTER,
    fontName="Helvetica", spaceAfter=16)
h1_style = _s("H1",
    fontSize=16, textColor=NAVY, fontName="Helvetica-Bold",
    spaceBefore=14, spaceAfter=6)
h2_style = _s("H2",
    fontSize=12, textColor=BLUE, fontName="Helvetica-Bold",
    spaceBefore=10, spaceAfter=4)
body_style = _s("Body",
    fontSize=9, textColor=colors.black, fontName="Helvetica",
    leading=13, spaceAfter=4, alignment=TA_JUSTIFY)
small_style = _s("Small",
    fontSize=8, textColor=colors.HexColor("#555555"), fontName="Helvetica",
    leading=11, alignment=TA_CENTER)
caption_style = _s("Caption",
    fontSize=8, textColor=colors.HexColor("#555555"), fontName="Helvetica-Oblique",
    leading=11, alignment=TA_CENTER, spaceAfter=6)
cell_style = _s("Cell",
    fontSize=8.5, textColor=colors.black, fontName="Helvetica", leading=12)
cell_bold = _s("CellBold",
    fontSize=8.5, textColor=colors.black, fontName="Helvetica-Bold", leading=12)
hdr_style = _s("HdrCell",
    fontSize=8.5, textColor=WHITE, fontName="Helvetica-Bold", leading=12)
note_style = _s("Note",
    fontSize=8.5, textColor=colors.black, fontName="Helvetica",
    leading=12, spaceAfter=4, alignment=TA_LEFT)
note_bold = _s("NoteBold",
    fontSize=8.5, textColor=colors.black, fontName="Helvetica-Bold",
    leading=12, spaceAfter=4)
list_style = _s("List",
    fontSize=9, textColor=colors.black, fontName="Helvetica",
    leading=14, leftIndent=12, spaceAfter=2)
proposed_label = _s("PropLabel",
    fontSize=8, textColor=colors.HexColor("#1a6b2a"), fontName="Helvetica-Bold",
    leading=10)

# ── Helpers ──────────────────────────────────────────────────────────────────
def P(text, style=body_style):
    return Paragraph(text, style)

def hdr(text):
    return Paragraph(text, hdr_style)

def cell(text, bold=False):
    return Paragraph(text, cell_bold if bold else cell_style)

def divider():
    return Table([[""]], colWidths=[W - 2*MARGIN],
                 style=[("LINEABOVE", (0,0), (-1,0), 0.5, GREY_LINE),
                        ("TOPPADDING", (0,0), (-1,0), 0),
                        ("BOTTOMPADDING", (0,0), (-1,0), 0)])

def callout(content_rows, bg=AMBER_BG, border=AMBER_BORDER):
    """Styled callout/infobox table."""
    inner = Table(content_rows, colWidths=[W - 2*MARGIN - 12])
    inner.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), bg),
        ("BOX",           (0,0), (-1,-1), 1.5, border),
        ("TOPPADDING",    (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("LEFTPADDING",   (0,0), (-1,-1), 10),
        ("RIGHTPADDING",  (0,0), (-1,-1), 10),
    ]))
    return inner

def std_table(headers, rows, col_widths, alt=True):
    """Standard styled table with blue header row."""
    data = [[hdr(h) for h in headers]] + [[cell(r) for r in row] for row in rows]
    style = [
        ("BACKGROUND",    (0,0), (-1,0), BLUE),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, ROW_ALT] if alt else [WHITE]),
        ("BOX",           (0,0), (-1,-1), 0.5, GREY_LINE),
        ("INNERGRID",     (0,0), (-1,-1), 0.3, GREY_LINE),
        ("VALIGN",        (0,0), (-1,-1), "TOP"),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING",   (0,0), (-1,-1), 6),
        ("RIGHTPADDING",  (0,0), (-1,-1), 6),
    ]
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle(style))
    return t

def comparison_table(headers, col_colors, rows, col_widths):
    """Three-column comparison table with per-column header colours."""
    data = [[hdr(h) for h in headers]] + [[cell(r) for r in row] for row in rows]
    style = [
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, ROW_ALT]),
        ("BOX",           (0,0), (-1,-1), 0.5, GREY_LINE),
        ("INNERGRID",     (0,0), (-1,-1), 0.3, GREY_LINE),
        ("VALIGN",        (0,0), (-1,-1), "TOP"),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING",   (0,0), (-1,-1), 6),
        ("RIGHTPADDING",  (0,0), (-1,-1), 6),
    ]
    for col, c in enumerate(col_colors):
        style.append(("BACKGROUND", (col, 0), (col, 0), c))
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle(style))
    return t

# ── Image helper ─────────────────────────────────────────────────────────────
IMG_DIR = Path("data/extracted")

def img(name, width, height):
    p = IMG_DIR / name
    if p.exists():
        return Image(str(p), width=width, height=height)
    return Paragraph(f"[image: {name}]", small_style)

# ── Document setup ────────────────────────────────────────────────────────────
OUT = Path("data/extracted/methodology_review.pdf")
OUT.parent.mkdir(parents=True, exist_ok=True)

def build_pdf():
    doc = BaseDocTemplate(
        str(OUT),
        pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=MARGIN,
    )
    frame = Frame(MARGIN, MARGIN, W - 2*MARGIN, H - 2*MARGIN, id="main")
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame])])

    story = []

    # ─────────────────────────────────────────────────────────────────────────
    # PAGE 1 — Title
    # ─────────────────────────────────────────────────────────────────────────
    story += [
        Spacer(1, 30*mm),
        P("AI vs Physician Diagnostic Performance", title_style),
        P("Systematic Review &amp; Meta-Analysis", title_style),
        divider(),
        Spacer(1, 4*mm),
        P("Methodology Comparison, First-Run Findings &amp; Proposed Scope Expansion",
          subtitle_style),
        P("Prepared for group review — March 03, 2026", date_style),
        Spacer(1, 8*mm),
        callout([
            [P("<b>Purpose of this document</b>", note_bold)],
            [P("Compares our pipeline methodology against Takita 2025 (npj Digital Medicine) and Chen 2026 "
               "(Nature Medicine). Presents first-run results and key findings that motivate a proposed scope "
               "expansion (v3 criteria) for group discussion before re-running.", note_style)],
        ]),
        PageBreak(),
    ]

    # ─────────────────────────────────────────────────────────────────────────
    # PAGE 2 — Section 1: Methodology Comparison
    # ─────────────────────────────────────────────────────────────────────────
    story += [
        P("1. Methodology Comparison", h1_style),
        divider(),
        Spacer(1, 4*mm),
        P("1.1 Search Strategy", h2_style),
    ]

    CW4 = [38*mm, 46*mm, 46*mm, 46*mm]
    HDR_COLS = [NAVY, BLUE, BLUE, TEAL]
    search_rows = [
        ["Databases",
         "MEDLINE, Scopus, Web of Science, CENTRAL, medRxiv",
         "Embase, PubMed, Scopus",
         "PubMed, medRxiv, arXiv"],
        ["Date range",
         "Jun 2018 – Jun 2024",
         "Jan 2022 – Sep 2025",
         "Jan 2022 – Sep 2025 → Feb 2026 (proposed)"],
        ["Records after dedup", "8,014", "12,894", "3,475"],
        ["Final included", "83 studies", "4,609 studies", "98 studies"],
        ["Screener",
         "Manual (human)",
         "GPT-5 (κ=0.82 vs human)",
         "Claude Haiku (κ pending)"],
        ["Missing vs Chen", "—", "—",
         "Missing: Embase, Scopus (~est. 30–50% recall gap)"],
    ]
    story.append(comparison_table(
        ["Dimension", "Takita 2025 (npj Dig. Med.)", "Chen 2026 (Nature Med.)", "Our Study"],
        HDR_COLS, search_rows, CW4))
    story.append(Spacer(1, 6*mm))

    story.append(P("1.2 Inclusion / Exclusion Criteria", h2_style))
    inc_rows = [
        ["AI task scope",
         "Diagnostic tasks only",
         "All clinical tasks (diagnosis, comms, admin, education)",
         "Diagnostic &amp; triage only (→ proposed to expand)"],
        ["Physician comparison required", "No", "No", "Yes — mandatory"],
        ["Accuracy metric required",
         "Yes (129 studies excluded without it)",
         "No",
         "No (dropped from v1)"],
        ["Preprints", "Yes (medRxiv)", "Yes", "Yes"],
        ["Human screening validation",
         "Yes — manual",
         "500-label human validation",
         "100-record sample prepared (pending review)"],
    ]
    story.append(comparison_table(
        ["Criterion", "Takita 2025", "Chen 2026", "Our Study"],
        HDR_COLS, inc_rows, CW4))
    story.append(Spacer(1, 6*mm))

    story.append(P("1.3 Data Extraction", h2_style))
    ext_rows = [
        ["Method", "Manual",
         "LLM (GPT-5) from abstract",
         "LLM (Claude Sonnet) from abstract + Unpaywall PDF"],
        ["Arm types captured",
         "AI vs physician only",
         "Win/loss vs any human",
         "5 arm types (AI vs MD, AI+MD vs MD, etc.)"],
        ["Physician condition",
         "Expert vs non-expert level",
         "Training level",
         "unaided / conventional resources / ai_assisted"],
        ["Quality assessment",
         "PROBAST (76% high RoB)",
         "Not reported",
         "Confidence score per arm"],
    ]
    story.append(comparison_table(
        ["Dimension", "Takita 2025", "Chen 2026", "Our Study"],
        HDR_COLS, ext_rows, CW4))
    story.append(PageBreak())

    # ─────────────────────────────────────────────────────────────────────────
    # PAGE 3 — Section 2: First-Run Findings
    # ─────────────────────────────────────────────────────────────────────────
    story += [
        P("2. First-Run Findings", h1_style),
        divider(),
        Spacer(1, 4*mm),
        P("2.1 Corpus Overview", h2_style),
    ]

    CW3 = [55*mm, 35*mm, 86*mm]
    corpus_rows = [
        ["Records searched", "3,475", "PubMed + medRxiv + arXiv"],
        ["Studies included", "98",
         "After screening + manual addition of 13 missed studies"],
        ["Comparison arms extracted", "233", "From 98 studies"],
        ["Arms with paired accuracy data", "80 (34%)",
         "Rest have ai_better flag only or no data"],
        ["Studies from full PDF", "42 (43%)",
         "Via Unpaywall; 56 abstract-only (65% missing data)"],
        ["Studies never extracted", "13 → now resolved",
         "Were in included.csv but missed by extractor; now added"],
    ]
    story.append(std_table(["Metric", "Value", "Notes"], corpus_rows, CW3))
    story.append(Spacer(1, 6*mm))

    story.append(P("2.2 Win Rate by Arm Type (from paired numeric accuracy data only, n=80 arms)", h2_style))
    CW6 = [42*mm, 14*mm, 16*mm, 14*mm, 16*mm, 74*mm]
    win_rows = [
        ["AI vs MD unaided",      "66", "33%", "65%", "–6.8pp",
         "The main head-to-head comparison. MDs clearly ahead."],
        ["AI vs MD w/ resources", "6",  "50%", "50%", "–3.0pp",
         "Balanced; small n"],
        ["AI+MD vs MD alone",     "1",  "100%","0%",  "—",
         "Only 1 arm with numbers — insufficient"],
        ["AI+MD vs MD w/ resources","4","100%","0%",  "—",
         "4 arms — still underpowered"],
        ["AI vs AI+MD",           "3",  "100%","0%",  "—",
         "AI alone loses to AI+MD team"],
        ["OVERALL",               "80", "41%", "58%", "–6.1pp",
         "Physicians win majority head-to-head"],
    ]
    story.append(std_table(
        ["Arm Type","n arms","AI wins","MD wins","Mean diff","Interpretation"],
        win_rows, CW6))
    story.append(Spacer(1, 4*mm))
    story.append(callout([
        [P("<b>Key finding:</b> AI beats physicians when combined with a physician (augmentation), "
           "but loses head-to-head. However, the augmentation finding is <b>underpowered</b> — "
           "only 5 arms with paired numbers across 3 studies. This is the primary motivation "
           "for expanding scope.", note_style)],
    ]))
    story.append(Spacer(1, 6*mm))

    story.append(P("2.3 Win Rate by Study Tier (from paired numeric data)", h2_style))
    CW5 = [16*mm, 48*mm, 20*mm, 20*mm, 72*mm]
    tier_rows = [
        ["Tier I",   "Real-world patient data",   "23", "39%", "57%",
         "Small AI disadvantage on real patients"],
        ["Tier II",  "Case-based evaluation",      "37", "32%", "68%",
         "Physicians clearly better on structured cases"],
        ["Tier III", "Vignettes / exam-style",     "20", "60%", "40%",
         "AI does best on synthetic/exam tasks"],
    ]
    story.append(std_table(
        ["Tier","Description","n arms","AI wins","MD wins","Interpretation"],
        [r[:6] for r in tier_rows],
        [16*mm, 48*mm, 18*mm, 18*mm, 18*mm, 58*mm]))
    story.append(Spacer(1, 4*mm))
    story.append(P(
        "Consistent with both Takita and Chen: AI performance degrades with task realism. "
        "Tier III vignette win rate (60%) vs Tier I real-world (39%) is the clearest gradient.",
        body_style))

    story.append(P("2.4 Performance by LLM (top models, from paired numeric data)", h2_style))
    llm_rows = [
        ["GPT-4 (incl. variants)","51","37","54%","–4.5%",
         "Largest evidence base; modest AI deficit"],
        ["GPT-4o",   "14","17","29%","–3.0%",
         "Better gap than GPT-4 but still losing"],
        ["GPT-3.5",  "12","5", "40%","–22.3%",
         "Much worse performance; older model"],
        ["Gemini",   "11","4", "0%", "–27.0%",
         "Worst win rate; small n"],
        ["AMIE (Google)","2","3","100%","+16.1%",
         "Purpose-built medical AI; very small n"],
        ["Claude",   "5", "1", "100%","+28.6%",
         "n=1 — insufficient to conclude"],
    ]
    story.append(std_table(
        ["LLM","Studies","Arms w/ numbers","AI win rate","Mean diff","Notes"],
        llm_rows,
        [34*mm, 22*mm, 26*mm, 22*mm, 22*mm, 50*mm]))
    story.append(Spacer(1, 3*mm))
    story.append(P(
        "GPT-4 estimates most reliable given n=37 paired arms. "
        "AMIE and Claude numbers are indicative only.", small_style))
    story.append(PageBreak())

    # ─────────────────────────────────────────────────────────────────────────
    # PAGE 4 — Section 2 cont: Data Quality & Scope Coverage
    # ─────────────────────────────────────────────────────────────────────────
    story.append(P("2.5 Data Quality &amp; Missingness", h2_style))
    miss_rows = [
        ["Arms with no ai_better and no accuracy data",
         "119 / 233 (51%)", "Cannot contribute to win rate analysis"],
        ["Abstract-only studies (no full PDF)",
         "56 / 98 (57%)", "65% missing ai_better vs 33% for full-text studies"],
        ["Augmentation arms with paired numbers",
         "5 / 33 (15%)", "Cannot pool augmentation effect numerically"],
        ["Studies still paywalled (Tier I priority)",
         "4 studies", "Key Tier I papers inaccessible"],
        ["Screener validation (κ)",
         "Not yet computed", "100-record human sample prepared; awaiting review"],
    ]
    story.append(std_table(["Issue","Count","Impact"], miss_rows,
                            [72*mm, 36*mm, 68*mm]))
    story.append(Spacer(1, 6*mm))

    story.append(P("2.6 Scope Coverage vs Chen 2026", h2_style))
    sc = img("scope_comparison.png", W - 2*MARGIN, 80*mm)
    story.append(sc)
    story.append(P(
        "Figure: Left pie = Chen's task distribution across 4,609 studies. "
        "Middle = our specialty distribution. Right = specialty share comparison. "
        "Tasks absent from our corpus (yellow box) include clinical management, "
        "patient communication, and documentation — together ~44% of Chen's corpus.",
        caption_style))
    story.append(PageBreak())

    # ─────────────────────────────────────────────────────────────────────────
    # PAGE 5 — Section 3: Why Expand?
    # ─────────────────────────────────────────────────────────────────────────
    story += [
        P("3. Why Expand Scope? (Motivation)", h1_style),
        divider(),
        Spacer(1, 4*mm),
    ]

    why_rows = [
        ["Augmentation is underpowered",
         "The most clinically relevant question — does AI help physicians perform better? — "
         "currently rests on 5 arms with numbers from 3 studies. Clinical management and "
         "decision support studies are where AI+MD teaming is most commonly tested."],
        ["Missing ~44% of relevant literature",
         "Our diagnostic-only filter excludes clinical management (Chen: 16% of studies) "
         "and risk stratification tasks. Many Tier I real-world studies involve treatment "
         "decisions and prognostic scoring, not just diagnosis."],
        ["Physician comparison is the common thread",
         "Our unique contribution is the physician comparison arm analysis. This applies equally "
         "to treatment decisions and risk stratification — we don't need to limit it to diagnosis "
         "to maintain the paper's focus."],
        ["Better alignment with Chen &amp; Takita for comparability",
         "Takita: diagnostic tasks only (narrow). Chen: all tasks (too broad). A middle-ground "
         "(diagnostic + management + risk) would be the most clinically meaningful and "
         "distinctive contribution."],
        ["Low additional cost",
         "Re-screening 3,475 existing records costs ~$3–5 (Claude Haiku) and takes 2–4 hours. "
         "No new database search required for the initial expansion."],
    ]

    why_data = [[cell(r[0], bold=True), cell(r[1])] for r in why_rows]
    why_table = Table(why_data, colWidths=[50*mm, 126*mm])
    why_table.setStyle(TableStyle([
        ("BOX",           (0,0), (-1,-1), 0.5, GREY_LINE),
        ("INNERGRID",     (0,0), (-1,-1), 0.3, GREY_LINE),
        ("VALIGN",        (0,0), (-1,-1), "TOP"),
        ("TOPPADDING",    (0,0), (-1,-1), 7),
        ("BOTTOMPADDING", (0,0), (-1,-1), 7),
        ("LEFTPADDING",   (0,0), (-1,-1), 8),
        ("RIGHTPADDING",  (0,0), (-1,-1), 8),
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [WHITE, ROW_ALT]),
    ]))
    story.append(why_table)
    story.append(PageBreak())

    # ─────────────────────────────────────────────────────────────────────────
    # PAGE 6 — Section 4: Proposed v3 Criteria
    # ─────────────────────────────────────────────────────────────────────────
    story += [
        P("4. Proposed v3 Criteria", h1_style),
        divider(),
        Spacer(1, 4*mm),
        P("4.1 Criteria Changes", h2_style),
    ]

    crit_rows = [
        ["Inclusion #2 (AI task scope)",
         "Uses a generative AI model (LLM) for a diagnostic or triage task",
         "Uses a generative AI model (LLM) for a diagnostic, triage, clinical management, "
         "treatment decision, or risk stratification/prognostic task"],
        ["Exclusion #4 (admin/comms only)",
         "Uses AI only for administrative tasks (coding, documentation, scheduling)",
         "Uses AI only for administrative tasks (coding, documentation, scheduling) "
         "OR only for patient communication, education, or explanation with no clinical "
         "decision outcome"],
        ["All other criteria", "Unchanged", "Unchanged"],
    ]
    crit_hdrs = ["Item", "Current (v1/v2)", "Proposed (v3)"]
    crit_cols = [NAVY, BLUE, colors.HexColor("#1a6b2a")]
    CW3b = [42*mm, 66*mm, 68*mm]
    story.append(comparison_table(crit_hdrs, crit_cols, crit_rows, CW3b))
    story.append(Spacer(1, 6*mm))

    story.append(P("4.2 Expected Impact", h2_style))
    impact_rows = [
        ["New includes from re-screening",
         "~50–150 additional studies (clinical management + risk stratification papers "
         "currently excluded)",
         "Corpus grows from ~98 to ~150–250 studies"],
        ["Augmentation arms",
         "Clinical decision support studies typically test AI+MD teams; "
         "expect 2–4x more augmentation arms",
         "From 33 → ~70–100 augmentation arms"],
        ["Tier I coverage",
         "More real-world deployment studies: EHR treatment decisions, "
         "ICU risk scoring, prescribing",
         "From 44 → ~60–80 Tier I arms"],
        ["Pipeline cost",
         "Re-screen 3,475 records at Claude Haiku rates",
         "~$3–5 API cost, ~2–4 hours"],
        ["Additional proposed: physician expertise",
         "Add expert/non-expert/trainee field to extraction prompt",
         "Enables subgroup analysis matching Takita's key finding"],
    ]
    story.append(std_table(["Change","Detail","Est. impact"], impact_rows,
                            [46*mm, 78*mm, 52*mm]))
    story.append(Spacer(1, 6*mm))

    story.append(P("4.3 Questions for Group Discussion", h2_style))
    questions = [
        "1. Should we add Embase and/or Scopus to the search? Largest single gap vs Takita "
        "and Chen — potentially 500–1,000+ missed studies. Would require re-running the search step.",
        "2. Expand scope as proposed (diagnostic + management + risk), or keep strictly diagnostic?",
        "3. Add physician expertise level (expert / non-expert / trainee) to the extraction schema? "
        "This is Takita's central subgroup finding.",
        "4. Apply formal PROBAST risk-of-bias assessment to at least Tier I studies?",
        "5. Run inter-rater reliability (Cohen's κ) on the screener using the 100-record "
        "human validation sample?",
        "6. Should we target a journal before re-running — to align scope and framing with "
        "the target audience?",
    ]
    for q in questions:
        story.append(P(q, list_style))
    story.append(PageBreak())

    # ─────────────────────────────────────────────────────────────────────────
    # PAGE 7 — NEW Section 5: Proposed Changes (Code Implemented, Run Pending)
    # ─────────────────────────────────────────────────────────────────────────
    story += [
        P("5. Proposed Changes — Code Implemented, Run Pending Group Consensus", h1_style),
        divider(),
        Spacer(1, 4*mm),
        callout([
            [P("<b>Status:</b> Both changes below have been implemented in the pipeline codebase. "
               "No re-run has been executed. The pipeline will only be re-run once the group has "
               "reviewed and agreed on the full scope of changes (sections 4.3 and 5.3).", note_style)],
        ], bg=GREEN_BG, border=GREEN_BORDER),
        Spacer(1, 6*mm),
    ]

    story.append(P("5.1 Date Range Extension", h2_style))
    date_change_rows = [
        ["Parameter",  "Before",              "After (proposed)"],
        ["DATE_END",   "2025/09/30",           "2026/02/28"],
        ["Affected searches", "PubMed, medRxiv, arXiv",
         "All three (config/queries.py cascades automatically)"],
        ["New records (est.)", "—",
         "~200–500 new records from Oct 2025 – Feb 2026"],
        ["File modified", "—", "config/queries.py line 13"],
    ]
    date_data = [[hdr(date_change_rows[0][i]) for i in range(3)]] + \
                [[cell(r[i]) for i in range(3)] for r in date_change_rows[1:]]
    date_col_hdrs = [NAVY, BLUE, GREEN_HDR]
    date_t = Table(date_data, colWidths=[52*mm, 58*mm, 66*mm])
    date_t.setStyle(TableStyle([
        *[("BACKGROUND", (i, 0), (i, 0), date_col_hdrs[i]) for i in range(3)],
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, ROW_ALT]),
        ("BOX",           (0,0), (-1,-1), 0.5, GREY_LINE),
        ("INNERGRID",     (0,0), (-1,-1), 0.3, GREY_LINE),
        ("VALIGN",        (0,0), (-1,-1), "TOP"),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING",   (0,0), (-1,-1), 6),
        ("RIGHTPADDING",  (0,0), (-1,-1), 6),
    ]))
    story.append(date_t)
    story.append(Spacer(1, 6*mm))

    story.append(P("5.2 v3 Criteria — Code Changes", h2_style))
    code_rows = [
        ["File", "Change", "Detail"],
        ["config/queries.py",
         "Added INCLUSION_CRITERIA_V3\nand EXCLUSION_CRITERIA_V3",
         "New constants appended after v2 (v1/v2 unchanged for backwards compatibility)"],
        ["src/screen.py",
         "Added criteria_version parameter\nto screen() and _build_prompt()",
         "Dynamically selects inclusion/exclusion list based on version string; "
         "default remains 'v1'"],
        ["run.py",
         "Added --criteria-version CLI flag",
         "Choices: v1, v2, v3. Default: v1. Output files auto-named "
         "(screened_v3.csv, included_v3.csv, uncertain_v3.csv)"],
    ]
    code_data = [[hdr(code_rows[0][i]) for i in range(3)]] + \
                [[cell(r[i]) for i in range(3)] for r in code_rows[1:]]
    code_t = Table(code_data, colWidths=[46*mm, 60*mm, 70*mm])
    code_t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0), NAVY),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [WHITE, ROW_ALT]),
        ("BOX",           (0,0), (-1,-1), 0.5, GREY_LINE),
        ("INNERGRID",     (0,0), (-1,-1), 0.3, GREY_LINE),
        ("VALIGN",        (0,0), (-1,-1), "TOP"),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING",   (0,0), (-1,-1), 6),
        ("RIGHTPADDING",  (0,0), (-1,-1), 6),
    ]))
    story.append(code_t)
    story.append(Spacer(1, 6*mm))

    story.append(P("5.3 Run Commands (awaiting group consensus before executing)", h2_style))

    cmd_rows = [
        ["Step", "Command", "Purpose", "Output"],
        ["1 — Search",
         "python run.py search --force",
         "Re-fetch all records with new DATE_END; fetches Oct 2025 – Feb 2026",
         "pubmed_raw.csv, medrxiv_raw.csv, arxiv_raw.csv (updated)"],
        ["2 — Dedup",
         "python run.py deduplicate",
         "Merge new records with existing 3,475; remove duplicates",
         "data/raw/combined_deduped.csv"],
        ["3 — Screen",
         "python run.py screen --force\n  --criteria-version v3",
         "Re-screen full corpus with expanded v3 criteria",
         "screened_v3.csv\nincluded_v3.csv\nuncertain_v3.csv"],
        ["4 — Extract",
         "python run.py extract\n  (with included_v3.csv)",
         "Extract arms from new studies only; merge into extracted_arms.csv",
         "extracted_arms.csv (appended)"],
    ]
    cmd_data = [[hdr(cmd_rows[0][i]) for i in range(4)]] + \
               [[cell(r[i]) for i in range(4)] for r in cmd_rows[1:]]
    cmd_t = Table(cmd_data, colWidths=[28*mm, 50*mm, 62*mm, 36*mm])
    cmd_t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0), NAVY),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [WHITE, ROW_ALT]),
        ("BOX",           (0,0), (-1,-1), 0.5, GREY_LINE),
        ("INNERGRID",     (0,0), (-1,-1), 0.3, GREY_LINE),
        ("VALIGN",        (0,0), (-1,-1), "TOP"),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING",   (0,0), (-1,-1), 6),
        ("RIGHTPADDING",  (0,0), (-1,-1), 6),
    ]))
    story.append(cmd_t)
    story.append(Spacer(1, 6*mm))

    story.append(P("5.4 Expected Outcomes", h2_style))
    outcome_rows = [
        ["Metric", "Current", "Expected after re-run"],
        ["Total records in corpus", "3,475", "~3,675–3,975 (+200–500)"],
        ["Studies included", "~98", "~150–250 (v3 screen)"],
        ["Augmentation arms", "33 (5 paired)", "~70–100 (20–30 paired)"],
        ["Tier I arms", "~44", "~60–80"],
        ["Date coverage", "Jan 2022 – Sep 2025", "Jan 2022 – Feb 2026"],
    ]
    out_data = [[hdr(outcome_rows[0][i]) for i in range(3)]] + \
               [[cell(r[i]) for i in range(3)] for r in outcome_rows[1:]]
    out_col_hdrs = [NAVY, BLUE, GREEN_HDR]
    out_t = Table(out_data, colWidths=[60*mm, 52*mm, 64*mm])
    out_t.setStyle(TableStyle([
        *[("BACKGROUND", (i, 0), (i, 0), out_col_hdrs[i]) for i in range(3)],
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [WHITE, ROW_ALT]),
        ("BOX",           (0,0), (-1,-1), 0.5, GREY_LINE),
        ("INNERGRID",     (0,0), (-1,-1), 0.3, GREY_LINE),
        ("VALIGN",        (0,0), (-1,-1), "TOP"),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING",   (0,0), (-1,-1), 6),
        ("RIGHTPADDING",  (0,0), (-1,-1), 6),
    ]))
    story.append(out_t)
    story.append(Spacer(1, 8*mm))

    # Footer note
    story.append(callout([
        [P("<b>Next step:</b> Group review of sections 4.3 (open questions) and 5.3 (run commands). "
           "Once consensus is reached, the pipeline will be re-run. Existing extracted_arms.csv "
           "is preserved — only new studies will be extracted and merged.", note_style)],
    ], bg=GREEN_BG, border=GREEN_BORDER))

    # ─────────────────────────────────────────────────────────────────────────
    # Footer on all pages
    # ─────────────────────────────────────────────────────────────────────────
    footer_text = (
        "Generated by automated pipeline · ai-vs-physician-meta · "
        "Data as of March 2026 · Subject to human validation"
    )

    def add_footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#888888"))
        canvas.drawCentredString(W / 2, 12*mm, footer_text)
        canvas.restoreState()

    template = doc.pageTemplates[0]
    template.beforeDrawPage = add_footer
    doc.build(story)
    print(f"PDF written → {OUT}")


if __name__ == "__main__":
    build_pdf()
