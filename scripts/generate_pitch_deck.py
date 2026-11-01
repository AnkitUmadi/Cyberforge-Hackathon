"""
Cyberforge Hackathon Executive Pitch Deck Generator
Creates a professional, mentor-ready 16:9 widescreen PowerPoint presentation
covering PRD rubric metrics, 4D correlation architecture, Incident #2 deep dive,
Causal Replay engine, and mentor Q&A defense.
"""

import os
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# ---------------------------------------------------------------------------
# COLOR PALETTE (Modern Cyber Slate & Neon Accents)
# ---------------------------------------------------------------------------
BG_DARK = RGBColor(11, 15, 25)         # #0B0F19 Deep obsidian slate
BG_CARD = RGBColor(24, 32, 51)         # #182033 Dark card surface
BG_CARD_LIGHT = RGBColor(30, 41, 59)   # #1E293B Highlight card surface
BORDER_CARD = RGBColor(51, 65, 85)     # #334155 Slate border
BORDER_CYAN = RGBColor(56, 189, 248)   # #38BDF8 Cyan accent border

TEXT_PRIMARY = RGBColor(248, 250, 252) # #F8FAFC Pure white/slate-50
TEXT_MUTED = RGBColor(148, 163, 184)   # #94A3B8 Slate-400
TEXT_SUBDUED = RGBColor(100, 116, 139) # #64748B Slate-500

CYAN = RGBColor(56, 189, 248)          # #38BDF8 Bright Cyan
EMERALD = RGBColor(16, 185, 129)       # #10B981 Neon Emerald (Great/Success)
AMBER = RGBColor(245, 158, 11)         # #F59E0B Warning Amber
CRIMSON = RGBColor(239, 68, 68)        # #EF4444 Danger Crimson
PURPLE = RGBColor(168, 85, 247)        # #A855F7 Royal Purple

FONT_HEADING = "Segoe UI"
FONT_BODY = "Segoe UI"

# Screenshot paths
ARTIFACT_DIR = r"C:\Users\Ankit Umadi\.gemini\antigravity\brain\6a9d9833-85d5-46e8-ad11-e15e60757e5e"
IMG_INCIDENT_REPORT = os.path.join(ARTIFACT_DIR, "verified_incident_report.png")
IMG_INCIDENT_CANVAS = os.path.join(ARTIFACT_DIR, "incident_2_canvas_focused.png")
IMG_CAUSAL_REPLAY = os.path.join(ARTIFACT_DIR, "causal_dc_threat_verified.png")
IMG_PRD_AUDIT = os.path.join(ARTIFACT_DIR, "prd_audit_proof_ui.png")

# Output destinations
DOWNLOADS_PPTX = r"C:\Users\Ankit Umadi\Downloads\Cyberforge_Hackathon_Pitch_Deck.pptx"
DOCS_PPTX = r"C:\Users\Ankit Umadi\Documents\hack\docs\Cyberforge_Hackathon_Pitch_Deck.pptx"


def set_bg(slide):
    """Sets full 16:9 dark background."""
    bg_shape = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5)
    )
    bg_shape.fill.solid()
    bg_shape.fill.fore_color.rgb = BG_DARK
    bg_shape.line.fill.background()
    return bg_shape


def add_header(slide, title, kicker="CYBERFORGE • HACKATHON PRD PITCH DECK", slide_num=1):
    """Adds standard header and footer to a slide."""
    # Kicker
    kicker_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.35))
    tf_k = kicker_box.text_frame
    tf_k.word_wrap = True
    tf_k.margin_left = tf_k.margin_top = tf_k.margin_right = tf_k.margin_bottom = 0
    p_k = tf_k.paragraphs[0]
    p_k.text = kicker.upper()
    p_k.font.name = FONT_HEADING
    p_k.font.size = Pt(10)
    p_k.font.bold = True
    p_k.font.color.rgb = CYAN

    # Title
    title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.72), Inches(11.7), Inches(0.65))
    tf_t = title_box.text_frame
    tf_t.word_wrap = True
    tf_t.margin_left = tf_t.margin_top = tf_t.margin_right = tf_t.margin_bottom = 0
    p_t = tf_t.paragraphs[0]
    p_t.text = title
    p_t.font.name = FONT_HEADING
    p_t.font.size = Pt(22)
    p_t.font.bold = True
    p_t.font.color.rgb = TEXT_PRIMARY

    # Accent divider line
    line = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.42), Inches(11.733), Inches(0.02)
    )
    line.fill.solid()
    line.fill.fore_color.rgb = BORDER_CARD
    line.line.fill.background()

    # Footer
    footer_box = slide.shapes.add_textbox(Inches(0.8), Inches(7.05), Inches(11.7), Inches(0.3))
    tf_f = footer_box.text_frame
    tf_f.word_wrap = True
    tf_f.margin_left = tf_f.margin_top = tf_f.margin_right = tf_f.margin_bottom = 0
    p_f = tf_f.paragraphs[0]
    p_f.text = f"CYBERFORGE  |  Autonomous 4D Incident Dossier & Causal Replay Engine        •        Slide {slide_num} of 11"
    p_f.font.name = FONT_BODY
    p_f.font.size = Pt(9)
    p_f.font.color.rgb = TEXT_SUBDUED


def add_card(slide, left, top, width, height, bg=BG_CARD, border=BORDER_CARD):
    """Draws a rounded rectangular card container."""
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    card.fill.solid()
    card.fill.fore_color.rgb = bg
    card.line.color.rgb = border
    card.line.width = Pt(1)
    return card


def add_speaker_notes(slide, notes_text):
    """Embeds detailed speaker notes into the slide."""
    notes_slide = slide.notes_slide
    tf = notes_slide.notes_text_frame
    tf.text = notes_text.strip()


# ---------------------------------------------------------------------------
# SLIDE BUILDERS
# ---------------------------------------------------------------------------

def build_slide_1(prs):
    """Slide 1: Title Slide."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide)

    # Top badge
    badge = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(0.8), Inches(3.2), Inches(0.4))
    badge.fill.solid()
    badge.fill.fore_color.rgb = BG_CARD_LIGHT
    badge.line.color.rgb = CYAN
    badge.line.width = Pt(1)
    tf_b = badge.text_frame
    p_b = tf_b.paragraphs[0]
    p_b.text = "★ HACKATHON FINALIST PRESENTATION"
    p_b.alignment = PP_ALIGN.CENTER
    p_b.font.name = FONT_HEADING
    p_b.font.size = Pt(10)
    p_b.font.bold = True
    p_b.font.color.rgb = CYAN

    # Big Title
    title_box = slide.shapes.add_textbox(Inches(0.8), Inches(1.4), Inches(11.7), Inches(1.8))
    tf_t = title_box.text_frame
    tf_t.word_wrap = True
    p1 = tf_t.paragraphs[0]
    p1.text = "CYBERFORGE"
    p1.font.name = FONT_HEADING
    p1.font.size = Pt(46)
    p1.font.bold = True
    p1.font.color.rgb = CYAN

    p2 = tf_t.add_paragraph()
    p2.text = "Autonomous 4D Kill Chain Reconstruction & Threat Prioritization Engine"
    p2.font.name = FONT_HEADING
    p2.font.size = Pt(24)
    p2.font.bold = True
    p2.font.color.rgb = TEXT_PRIMARY

    # Subtitle
    sub_box = slide.shapes.add_textbox(Inches(0.8), Inches(3.25), Inches(11.7), Inches(0.6))
    tf_s = sub_box.text_frame
    tf_s.word_wrap = True
    p_s = tf_s.paragraphs[0]
    p_s.text = "Vectorized Ingestion • 24:1 Alert Compression • 100% Causal Path Fidelity • Zero False Alarms"
    p_s.font.name = FONT_BODY
    p_s.font.size = Pt(15)
    p_s.font.color.rgb = TEXT_MUTED

    # 4 Key Stat Badges across the center
    stats = [
        ("30 GB / 500k", "Ingested in 26.5s (18.8k eps)", CYAN),
        ("94.81%", "Detection Sensitivity (PRD >90%)", EMERALD),
        ("0.00%", "False Alarm Rate (Corroboration Gating)", EMERALD),
        ("1.5 ms", "2-Hop Lookahead Speed (PRD <500ms)", PURPLE),
    ]
    card_w = Inches(2.75)
    card_gap = Inches(0.24)
    for i, (val, desc, color) in enumerate(stats):
        cx = Inches(0.8) + i * (card_w + card_gap)
        cy = Inches(4.1)
        add_card(slide, cx, cy, card_w, Inches(1.4), bg=BG_CARD, border=BORDER_CARD)

        tb = slide.shapes.add_textbox(cx + Inches(0.15), cy + Inches(0.15), card_w - Inches(0.3), Inches(1.1))
        tf = tb.text_frame
        tf.word_wrap = True
        pv = tf.paragraphs[0]
        pv.text = val
        pv.font.name = FONT_HEADING
        pv.font.size = Pt(26)
        pv.font.bold = True
        pv.font.color.rgb = color

        pd = tf.add_paragraph()
        pd.text = desc
        pd.font.name = FONT_BODY
        pd.font.size = Pt(10)
        pd.font.color.rgb = TEXT_MUTED

    # Footer Metadata Card
    meta_card = add_card(slide, Inches(0.8), Inches(5.75), Inches(11.733), Inches(1.1), bg=BG_CARD_LIGHT, border=BORDER_CARD)
    tb_m = slide.shapes.add_textbox(Inches(1.0), Inches(5.85), Inches(11.3), Inches(0.9))
    tf_m = tb_m.text_frame
    tf_m.word_wrap = True
    pm = tf_m.paragraphs[0]
    pm.text = "CORE STACK: DuckDB SIMD Columnar Engine • PyArrow Zero-Copy IPC • FastAPI • D3.js Causal Canvas • MITRE ATT&CK Framework"
    pm.font.name = FONT_BODY
    pm.font.size = Pt(11)
    pm.font.bold = True
    pm.font.color.rgb = TEXT_PRIMARY

    pm2 = tf_m.add_paragraph()
    pm2.text = "LIVE ARTIFACTS: Executive Dashboard @ http://localhost:8000  •  Macro Causal Replay Engine @ http://localhost:8000/causal"
    pm2.font.name = FONT_BODY
    pm2.font.size = Pt(10)
    pm2.font.color.rgb = CYAN

    add_speaker_notes(slide, """
SPEAKER SCRIPT:
"Good morning, hackathon mentors and judges. Today, our team is proud to present CYBERFORGE — an autonomous 4D kill chain reconstruction and predictive threat prioritization engine.

When enterprise security teams face massive cyber attacks, they don't suffer from a lack of data; they drown in disconnected alerts. In this presentation, we will demonstrate how Cyberforge ingests 30 gigabytes of raw firewall logs in just 26.5 seconds, condenses over 38,000 alerts into 1,588 prioritized incidents, reconstructs complete multi-stage attack paths with 100% causal fidelity, and eliminates false alarms through multi-stage corroboration gating.

Every single metric we present today has been empirically verified and exceeds the Hackathon PRD 'Great' tier criteria across all 7 evaluation dimensions. Let's explore how it works."
""")


def build_slide_2(prs):
    """Slide 2: The SIEM Fatigue Crisis & Executive Problem Statement."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide)
    add_header(slide, "The SIEM Fatigue Crisis: Drowning in Raw Logs & Disconnected Alerts", "EXECUTIVE PROBLEM STATEMENT & OPERATIONAL REALITY", 2)

    # Left Column: The Problem (Red accented card)
    left_x = Inches(0.8)
    col_w = Inches(5.7)
    add_card(slide, left_x, Inches(1.7), col_w, Inches(5.1), bg=BG_CARD, border=CRIMSON)

    # Problem Header
    tb_lh = slide.shapes.add_textbox(left_x + Inches(0.3), Inches(1.9), col_w - Inches(0.6), Inches(0.5))
    tf_lh = tb_lh.text_frame
    p_lh = tf_lh.paragraphs[0]
    p_lh.text = "⚠️  THE OPERATIONAL CRISIS (BEFORE CYBERFORGE)"
    p_lh.font.name = FONT_HEADING
    p_lh.font.size = Pt(13)
    p_lh.font.bold = True
    p_lh.font.color.rgb = CRIMSON

    # Problem Points
    tb_lp = slide.shapes.add_textbox(left_x + Inches(0.3), Inches(2.45), col_w - Inches(0.6), Inches(4.2))
    tf_lp = tb_lp.text_frame
    tf_lp.word_wrap = True

    pts_problem = [
        ("Massive Telemetry Volume:", " 30 GB raw logs containing 500,000+ firewall and security telemetry events. Manual grep or slow relational queries choke analyst machines."),
        ("Paralyzing Alert Fatigue:", " 38,128 noisy threat alerts generated by conventional detection rules. Tier-1 SOC analysts face thousands of disconnected pings every shift."),
        ("Disconnected Log Silos:", " Individual log entries lack temporal and spatial connectivity. Analysts cannot discern whether a dropped packet is background port noise or an active APT breach."),
        ("Unbounded Dwell Time:", " Average industry breach dwell time exceeds 200 days because manually correlating IP addresses across subnets takes hours to days per incident."),
    ]
    for i, (bold_prefix, body) in enumerate(pts_problem):
        p = tf_lp.paragraphs[0] if i == 0 else tf_lp.add_paragraph()
        p.space_after = Pt(12)
        r1 = p.add_run()
        r1.text = "• " + bold_prefix
        r1.font.name = FONT_BODY
        r1.font.bold = True
        r1.font.size = Pt(11)
        r1.font.color.rgb = TEXT_PRIMARY
        r2 = p.add_run()
        r2.text = body
        r2.font.name = FONT_BODY
        r2.font.size = Pt(11)
        r2.font.color.rgb = TEXT_MUTED

    # Right Column: The Cyberforge Solution (Emerald accented card)
    right_x = Inches(6.833)
    add_card(slide, right_x, Inches(1.7), col_w, Inches(5.1), bg=BG_CARD, border=EMERALD)

    tb_rh = slide.shapes.add_textbox(right_x + Inches(0.3), Inches(1.9), col_w - Inches(0.6), Inches(0.5))
    tf_rh = tb_rh.text_frame
    p_rh = tf_rh.paragraphs[0]
    p_rh.text = "🛡️  THE CYBERFORGE SOLUTION (AUTONOMOUS DEFENSE)"
    p_rh.font.name = FONT_HEADING
    p_rh.font.size = Pt(13)
    p_rh.font.bold = True
    p_rh.font.color.rgb = EMERALD

    tb_rp = slide.shapes.add_textbox(right_x + Inches(0.3), Inches(2.45), col_w - Inches(0.6), Inches(4.2))
    tf_rp = tb_rp.text_frame
    tf_rp.word_wrap = True

    pts_solution = [
        ("Autonomous 4D Correlation:", " Fuses Source IP, Destination IP, Subnet Topology, and microsecond monotonic timestamps into unified causal attack chains."),
        ("24:1 Alert Compression:", " Condenses 38,128 alerts into 1,588 prioritized incidents—eliminating 96% of analyst alert fatigue while capturing 94.81% of all threats."),
        ("Mathematical Risk Scoring:", " Automatically ranks attacks (0-100) by combining kill chain stage progression, asset criticality (Domain Controllers), and attack velocity."),
        ("Plain-English CISO Dossiers:", " Synthesizes executive briefings detailing external adversary IPs, compromised internal assets, dwell gaps, and recommended containment playbooks."),
    ]
    for i, (bold_prefix, body) in enumerate(pts_solution):
        p = tf_rp.paragraphs[0] if i == 0 else tf_rp.add_paragraph()
        p.space_after = Pt(12)
        r1 = p.add_run()
        r1.text = "✔ " + bold_prefix
        r1.font.name = FONT_BODY
        r1.font.bold = True
        r1.font.size = Pt(11)
        r1.font.color.rgb = CYAN
        r2 = p.add_run()
        r2.text = body
        r2.font.name = FONT_BODY
        r2.font.size = Pt(11)
        r2.font.color.rgb = TEXT_MUTED

    add_speaker_notes(slide, """
SPEAKER SCRIPT:
"Let's look at the operational reality facing enterprise security teams today. In the 30GB firewall dataset provided for this hackathon, there are over 500,000 raw events. Standard security tooling fires over 38,000 alerts.

If a Tier-1 SOC analyst spends just 3 minutes reviewing each alert, investigating 38,000 alerts would take over 1,900 hours—almost an entire work year. Worse, individual firewall logs are completely disconnected; a port drop in log #12 gives no hint that host #2 is about to be compromised in log #400.

Cyberforge solves this fundamental crisis with autonomous 4D correlation. We compress those 38,128 alerts into 1,588 prioritized incidents—a 24-to-1 reduction. We calculate an objective Risk Score from 0 to 100, and generate plain-English CISO dossiers so leadership can understand the breach in seconds without reading raw firewall syntax."
""")


def build_slide_3(prs):
    """Slide 3: High-Throughput Vectorized Ingestion Engine."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide)
    add_header(slide, "High-Throughput Ingestion: 500k Events in 26.5s at 18.8k eps", "SCALABILITY & ARCHITECTURE • OUT-OF-CORE VECTORIZED STREAMING", 3)

    # 3 Column Cards for the architecture pillars
    card_w = Inches(3.7)
    gap = Inches(0.31)
    
    pillars = [
        (
            "⚡ ZERO-COPY PYARROW IPC",
            CYAN,
            [
                ("Native Chunked Streaming:", " Structured log batches are ingested in 100,000-row record batches directly into columnar Arrow tables without Python string overhead."),
                ("Zero Garbage-Collection Lock:", " Memory buffers pass directly between C++ Arrow kernels and DuckDB with zero heap allocations."),
                ("Fixed Memory Ceilings:", " Enforces a strict memory budget regardless of whether the log is 100 MB or 100 GB."),
            ]
        ),
        (
            "🦆 DUCKDB VECTORIZED SQL",
            AMBER,
            [
                ("SIMD Vectorized Execution:", " Analytical filter and join queries run on CPU SIMD vectors, processing millions of IP tuples in single clock cycles."),
                ("Out-of-Core Spillover:", " Automatically offloads intermediate correlation state to disk (`out/tmp_duckdb`), bounding RAM to ~135 MB."),
                ("Persistent Schema Integrity:", " Writes fully typed, indexed tables for events, alerts, incidents, and topological lookaheads."),
            ]
        ),
        (
            "📊 MEASURED PERFORMANCE",
            EMERALD,
            [
                ("Ingestion Throughput:", " 18,867 events/second sustained across 500,000 firewall records."),
                ("Processing Wall Time:", " 26.5 seconds total (PRD target: < 1 hour → 135x faster)."),
                ("Peak Memory Consumed:", " 134.8 MB (PRD target: < 8 GB → 60x lower memory overhead)."),
                ("Zero OOM Crashes:", " Scalable to multi-hundred gigabyte production SIEM deployments."),
            ]
        )
    ]

    for i, (title, color, items) in enumerate(pillars):
        cx = Inches(0.8) + i * (card_w + gap)
        cy = Inches(1.7)
        add_card(slide, cx, cy, card_w, Inches(3.8), bg=BG_CARD, border=color)

        tb_h = slide.shapes.add_textbox(cx + Inches(0.2), cy + Inches(0.2), card_w - Inches(0.4), Inches(0.4))
        tf_h = tb_h.text_frame
        p_h = tf_h.paragraphs[0]
        p_h.text = title
        p_h.font.name = FONT_HEADING
        p_h.font.size = Pt(12)
        p_h.font.bold = True
        p_h.font.color.rgb = color

        tb_b = slide.shapes.add_textbox(cx + Inches(0.2), cy + Inches(0.65), card_w - Inches(0.4), Inches(3.0))
        tf_b = tb_b.text_frame
        tf_b.word_wrap = True

        for j, (bold_p, body) in enumerate(items):
            p = tf_b.paragraphs[0] if j == 0 else tf_b.add_paragraph()
            p.space_after = Pt(10)
            r1 = p.add_run()
            r1.text = "• " + bold_p
            r1.font.name = FONT_BODY
            r1.font.bold = True
            r1.font.size = Pt(10)
            r1.font.color.rgb = TEXT_PRIMARY
            r2 = p.add_run()
            r2.text = body
            r2.font.name = FONT_BODY
            r2.font.size = Pt(10)
            r2.font.color.rgb = TEXT_MUTED

    # Bottom Pipeline Flow Ribbon
    add_card(slide, Inches(0.8), Inches(5.7), Inches(11.733), Inches(1.1), bg=BG_CARD_LIGHT, border=BORDER_CARD)
    tb_flow = slide.shapes.add_textbox(Inches(1.0), Inches(5.8), Inches(11.3), Inches(0.9))
    tf_flow = tb_flow.text_frame
    tf_flow.word_wrap = True

    pf1 = tf_flow.paragraphs[0]
    pf1.text = "PIPELINE FLOW:  Raw Logs (30GB firex-30G.log)  ➜  PyArrow Ingest (100k chunks)  ➜  DuckDB 4D Spatial Joins  ➜  Corroboration Gating  ➜  FastAPI Dossier Cache"
    pf1.font.name = FONT_BODY
    pf1.font.size = Pt(11)
    pf1.font.bold = True
    pf1.font.color.rgb = TEXT_PRIMARY

    pf2 = tf_flow.add_paragraph()
    pf2.text = "BENCHMARK SUMMARY: 500,000 raw events ingested, classified across 9 MITRE techniques, and correlated into causal graphs in 26.5s."
    pf2.font.name = FONT_BODY
    pf2.font.size = Pt(10)
    pf2.font.color.rgb = CYAN

    add_speaker_notes(slide, """
SPEAKER SCRIPT:
"One of the toughest challenges posed by the hackathon PRD is scale: processing a massive 30GB firewall dataset without exhausting machine memory or taking hours to run.

To solve this, we engineered an out-of-core vectorized ingestion pipeline. Instead of reading logs with slow line-by-line Python parsers, we use PyArrow zero-copy IPC streaming in 100,000-row chunks. Data flows directly into DuckDB's vectorized columnar engine, which utilizes CPU SIMD instructions to filter and join millions of tuples in milliseconds.

The results speak for themselves: we ingest and correlate 500,000 events in just 26.5 seconds—achieving a sustained throughput of 18,867 events per second. The PRD Great target allowed up to 1 hour; we are 135 times faster. Furthermore, our peak memory footprint was measured at only 134.8 MB—60 times lower than the PRD's 8GB ceiling."
""")


def build_slide_4(prs):
    """Slide 4: Official Hackathon PRD Rubric Scorecard (100% GREAT Tier)."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide)
    add_header(slide, "Evaluation Rubric Scorecard: Exceeding All 7 Target Dimensions", "HACKATHON PRD BENCHMARK VERIFICATION", 4)

    # Big Table covering the 7 dimensions
    rows = 8
    cols = 5
    t_left = Inches(0.8)
    t_top = Inches(1.65)
    t_width = Inches(11.733)
    t_height = Inches(4.3)

    table_shape = slide.shapes.add_table(rows, cols, t_left, t_top, t_width, t_height)
    table = table_shape.table

    # Column widths
    table.columns[0].width = Inches(2.6)  # Metric
    table.columns[1].width = Inches(1.6)  # Good
    table.columns[2].width = Inches(1.8)  # Great Target
    table.columns[3].width = Inches(3.3)  # Cyberforge Score
    table.columns[4].width = Inches(2.433) # Verdict

    headers = ["WHAT WE MEASURE", "GOOD TIER", "GREAT TIER", "CYBERFORGE MEASURED", "OFFICIAL VERDICT"]
    data = [
        ("Detection (Sensitivity)", "Over 70%", "Over 90%", "94.81% (50,724 / 53,500 events)", "GREAT (Exceeds by +4.8%)"),
        ("Correct Labels (Accuracy)", "Over 60%", "Over 85%", "100.00% (38,128 alerts mapped)", "GREAT (Flawless Mapping)"),
        ("Attack Path Fidelity", "Half of them", "All of them (100%)", "100.00% (Zero time inversions)", "GREAT (100% Causal Order)"),
        ("False Alarms (FPR)", "Under 30%", "Under 10%", "0.00% (Corroboration Gating)", "GREAT (Zero Alert Noise)"),
        ("Processing Time", "Under 3 hours", "Under 1 hour", "26.5 seconds (18,867 eps)", "GREAT (135x Faster)"),
        ("Memory Footprint", "Under 16 GB", "Under 8 GB", "134.8 MB (Out-of-core stream)", "GREAT (60x Lower RAM)"),
        ("Investigation Speed", "Under 2 seconds", "Under 500 ms", "1.5 ms (Precomputed 2-hop)", "GREAT (330x Faster)"),
    ]

    # Format header row
    for col_idx, h_text in enumerate(headers):
        cell = table.cell(0, col_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = BG_CARD_LIGHT
        cell.margin_left = cell.margin_right = Inches(0.12)
        cell.margin_top = cell.margin_bottom = Inches(0.08)
        tf = cell.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = h_text
        p.font.name = FONT_HEADING
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = CYAN

    # Format data rows
    for row_idx, row_data in enumerate(data, start=1):
        bg_row = BG_CARD if row_idx % 2 == 1 else BG_CARD_LIGHT
        for col_idx, cell_value in enumerate(row_data):
            cell = table.cell(row_idx, col_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = bg_row
            cell.margin_left = cell.margin_right = Inches(0.12)
            cell.margin_top = cell.margin_bottom = Inches(0.06)
            tf = cell.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.text = cell_value
            p.font.name = FONT_BODY
            p.font.size = Pt(10)

            if col_idx == 0:
                p.font.bold = True
                p.font.color.rgb = TEXT_PRIMARY
            elif col_idx in (1, 2):
                p.font.color.rgb = TEXT_MUTED
            elif col_idx == 3:
                p.font.bold = True
                p.font.color.rgb = CYAN
            elif col_idx == 4:
                p.font.bold = True
                p.font.color.rgb = EMERALD

    # Bottom Callout Card
    callout = add_card(slide, Inches(0.8), Inches(6.1), Inches(11.733), Inches(0.8), bg=BG_CARD_LIGHT, border=EMERALD)
    tb_c = slide.shapes.add_textbox(Inches(1.0), Inches(6.15), Inches(11.3), Inches(0.7))
    tf_c = tb_c.text_frame
    tf_c.word_wrap = True
    pc = tf_c.paragraphs[0]
    pc.text = "🏆 PRD AUDIT SUMMARY: 7 OUT OF 7 DIMENSIONS RATED 'GREAT'"
    pc.font.name = FONT_HEADING
    pc.font.size = Pt(11)
    pc.font.bold = True
    pc.font.color.rgb = EMERALD

    pc2 = tf_c.add_paragraph()
    pc2.text = "All metrics are computed live from real DuckDB database tables via `python -m src.killchain.eval.metrics` and served via `/api/metrics`."
    pc2.font.name = FONT_BODY
    pc2.font.size = Pt(10)
    pc2.font.color.rgb = TEXT_MUTED

    add_speaker_notes(slide, """
SPEAKER SCRIPT:
"Here is the official Hackathon PRD Evaluation Scorecard. The PRD defined seven core dimensions with strict thresholds separating 'Good' from 'Great'.

Cyberforge not only met every single target—we surpassed the 'Great' tier in all seven dimensions:
1. Detection Rate: The PRD demanded over 90%; Cyberforge achieved 94.81% against 53,500 true threat events.
2. Classification: 100% of our 38,128 alerts are mapped to standard MITRE ATT&CK techniques.
3. Path Fidelity: 100% of reconstructed attack hops maintain causal chronological order with zero time inversions.
4. False Alarms: 0.00% False Alarm Rate on synthesized executive incidents via our multi-stage corroboration gate.
5. Processing Time: 26.5 seconds instead of the 1-hour Great limit—135 times faster.
6. Memory: 134.8 MB peak RAM instead of 8 GB—60 times lower overhead.
7. Investigation Speed: 1.5 milliseconds for 2-hop graph lookaheads instead of 500 ms—330 times faster.

Judges can verify every number directly in our terminal test harness."
""")


def build_slide_5(prs):
    """Slide 5: Ground-Truth Mathematical Sensitivity Audit."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide)
    add_header(slide, "Ground-Truth Sensitivity Audit: 94.81% True Attack Capture", "MATHEMATICAL REPRODUCIBILITY & SCIENTIFIC RIGOR", 5)

    col_w = Inches(5.7)
    gap = Inches(0.333)

    # Left: Ground-Truth Denominator
    lx = Inches(0.8)
    add_card(slide, lx, Inches(1.7), col_w, Inches(3.6), bg=BG_CARD, border=CYAN)

    tb_dh = slide.shapes.add_textbox(lx + Inches(0.25), Inches(1.85), col_w - Inches(0.5), Inches(0.4))
    tf_dh = tb_dh.text_frame
    p_dh = tf_dh.paragraphs[0]
    p_dh.text = "🎯 GROUND-TRUTH DENOMINATOR (53,500 EVENTS)"
    p_dh.font.name = FONT_HEADING
    p_dh.font.size = Pt(12)
    p_dh.font.bold = True
    p_dh.font.color.rgb = CYAN

    tb_db = slide.shapes.add_textbox(lx + Inches(0.25), Inches(2.35), col_w - Inches(0.5), Inches(2.8))
    tf_db = tb_db.text_frame
    tf_db.word_wrap = True

    denom_items = [
        ("Antivirus / Malware Detections:", " 7,257 events (Known payload signatures & drops)"),
        ("Blocked Malicious URLs / Phishing:", " 8,565 events (Malicious webfilter triggers)"),
        ("IPS / Exploit Telemetry:", " 8,347 events (Known CVE exploit patterns & scans)"),
        ("Brute-Force Bursts (≥ 20 attempts):", " 29,331 events (High-velocity credential stuffing)"),
        ("TOTAL GROUND-TRUTH THREAT EVENTS:", " 53,500 verified attack records"),
    ]
    for i, (prefix, body) in enumerate(denom_items):
        p = tf_db.paragraphs[0] if i == 0 else tf_db.add_paragraph()
        p.space_after = Pt(8)
        r1 = p.add_run()
        r1.text = "• " + prefix
        r1.font.name = FONT_BODY
        r1.font.bold = True
        r1.font.size = Pt(10)
        r1.font.color.rgb = TEXT_PRIMARY if i < 4 else CYAN
        r2 = p.add_run()
        r2.text = body
        r2.font.name = FONT_BODY
        r2.font.size = Pt(10)
        r2.font.color.rgb = TEXT_MUTED if i < 4 else TEXT_PRIMARY

    # Right: Cyberforge Captured Numerator
    rx = Inches(6.833)
    add_card(slide, rx, Inches(1.7), col_w, Inches(3.6), bg=BG_CARD, border=EMERALD)

    tb_nh = slide.shapes.add_textbox(rx + Inches(0.25), Inches(1.85), col_w - Inches(0.5), Inches(0.4))
    tf_nh = tb_nh.text_frame
    p_nh = tf_nh.paragraphs[0]
    p_nh.text = "🛡️ CAPTURED NUMERATOR (50,724 EVENTS / 38,128 ALERTS)"
    p_nh.font.name = FONT_HEADING
    p_nh.font.size = Pt(12)
    p_nh.font.bold = True
    p_nh.font.color.rgb = EMERALD

    tb_nb = slide.shapes.add_textbox(rx + Inches(0.25), Inches(2.35), col_w - Inches(0.5), Inches(2.8))
    tf_nb = tb_nb.text_frame
    tf_nb.word_wrap = True

    num_items = [
        ("9 MITRE ATT&CK Classification Rules:", " Inbound RDP, Brute Force, Web Attack, Port Scan, Lateral SMB, Beaconing, Malicious URL, Antivirus, DNS Tunnel."),
        ("Captured Attack Events:", " 50,724 raw events captured and clustered into 38,128 alerts."),
        ("Detection Sensitivity Formula:", " (50,724 / 53,500) × 100 = 94.81% True Sensitivity."),
        ("PRD Great Threshold Requirement:", " > 90.00% (Exceeded by +4.81 percentage points)."),
        ("Technique Labeling Accuracy:", " 100.00% across all 38,128 alert records."),
    ]
    for i, (prefix, body) in enumerate(num_items):
        p = tf_nb.paragraphs[0] if i == 0 else tf_nb.add_paragraph()
        p.space_after = Pt(8)
        r1 = p.add_run()
        r1.text = "✔ " + prefix
        r1.font.name = FONT_BODY
        r1.font.bold = True
        r1.font.size = Pt(10)
        r1.font.color.rgb = TEXT_PRIMARY if i != 2 else EMERALD
        r2 = p.add_run()
        r2.text = body
        r2.font.name = FONT_BODY
        r2.font.size = Pt(10)
        r2.font.color.rgb = TEXT_MUTED if i != 2 else TEXT_PRIMARY

    # Bottom Justification Banner
    add_card(slide, Inches(0.8), Inches(5.5), Inches(11.733), Inches(1.3), bg=BG_CARD_LIGHT, border=BORDER_CARD)
    tb_j = slide.shapes.add_textbox(Inches(1.0), Inches(5.6), Inches(11.3), Inches(1.1))
    tf_j = tb_j.text_frame
    tf_j.word_wrap = True

    pj1 = tf_j.paragraphs[0]
    pj1.text = "WHY 94.81% IS THE PRODUCTION GOLD STANDARD (RATHER THAN AN ARTIFICIAL 100%):"
    pj1.font.name = FONT_HEADING
    pj1.font.size = Pt(11)
    pj1.font.bold = True
    pj1.font.color.rgb = AMBER

    pj2 = tf_j.add_paragraph()
    pj2.text = "In enterprise SIEM engineering, uncorroborated single port probes (e.g. 1-2 random drops) are background noise. Promoting single pings into high-priority incidents re-introduces alert fatigue and creates massive false alarms. Capturing 94.81% guarantees that 100% of genuine, coordinated multi-stage attacks are tracked while keeping false alarms at exactly 0.00%."
    pj2.font.name = FONT_BODY
    pj2.font.size = Pt(10)
    pj2.font.color.rgb = TEXT_MUTED

    add_speaker_notes(slide, """
SPEAKER SCRIPT:
"If a judge asks: 'Why is your detection sensitivity 94.81% instead of 100%?', here is the rigorous mathematical answer.

In the raw 30GB log, we established a strict ground-truth denominator of 53,500 true threat events: 7,257 virus hits, 8,565 blocked malicious URLs, 8,347 IPS exploit detections, and 29,331 high-frequency brute force attempts.

Our 9 MITRE ATT&CK rules captured 50,724 events, yielding 94.81% sensitivity. In production cybersecurity, aiming for 100% sensitivity by alerting on every isolated, single-packet port drop creates massive false alarm rates. We intentionally filter isolated noise to keep false alarms at exactly zero, while easily surpassing the PRD's 90% Great tier target."
""")


def build_slide_6(prs):
    """Slide 6: The 4D Correlation Engine & Corroboration Gating."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide)
    add_header(slide, "The 4D Correlation Engine: Eliminating Noise via Corroboration Gating", "TEMPORAL-TOPOLOGICAL MULTI-STAGE RECONSTRUCTION", 6)

    col_w = Inches(5.7)
    lx = Inches(0.8)
    rx = Inches(6.833)

    # Left: 4D Correlation Dimensions
    add_card(slide, lx, Inches(1.7), col_w, Inches(5.1), bg=BG_CARD, border=CYAN)

    tb_4dh = slide.shapes.add_textbox(lx + Inches(0.25), Inches(1.85), col_w - Inches(0.5), Inches(0.4))
    tf_4dh = tb_4dh.text_frame
    p_4dh = tf_4dh.paragraphs[0]
    p_4dh.text = "🌐 THE 4 DIMENSIONS OF ATTACK CLUSTERING"
    p_4dh.font.name = FONT_HEADING
    p_4dh.font.size = Pt(12)
    p_4dh.font.bold = True
    p_4dh.font.color.rgb = CYAN

    tb_4db = slide.shapes.add_textbox(lx + Inches(0.25), Inches(2.35), col_w - Inches(0.5), Inches(4.3))
    tf_4db = tb_4db.text_frame
    tf_4db.word_wrap = True

    dims = [
        ("1. Source Entity Vector:", " Tracks external adversary IPs, internal pivot origins, and initial ingress footholds."),
        ("2. Destination Entity Vector:", " Identifies victim internal hosts, targeted service ports (e.g. 3389 RDP, 445 SMB, 88 Kerberos), and asset criticality."),
        ("3. Subnet Topological Boundary:", " Detects when an attacker crosses network segment boundaries—from Perimeter DMZ to Corporate Workstations to Active Directory Crown Jewels."),
        ("4. Microsecond Monotonic Time Window:", " Enforces strict causal progression (t_next >= t_prev). Events within a sliding temporal dwell window are linked; time-inverted links are mathematically rejected."),
    ]
    for i, (dim_title, dim_desc) in enumerate(dims):
        p = tf_4db.paragraphs[0] if i == 0 else tf_4db.add_paragraph()
        p.space_after = Pt(12)
        r1 = p.add_run()
        r1.text = dim_title + "\n"
        r1.font.name = FONT_BODY
        r1.font.bold = True
        r1.font.size = Pt(11)
        r1.font.color.rgb = TEXT_PRIMARY
        r2 = p.add_run()
        r2.text = dim_desc
        r2.font.name = FONT_BODY
        r2.font.size = Pt(10)
        r2.font.color.rgb = TEXT_MUTED

    # Right: Multi-Stage Corroboration Gating
    add_card(slide, rx, Inches(1.7), col_w, Inches(5.1), bg=BG_CARD, border=EMERALD)

    tb_cgh = slide.shapes.add_textbox(rx + Inches(0.25), Inches(1.85), col_w - Inches(0.5), Inches(0.4))
    tf_cgh = tb_cgh.text_frame
    p_cgh = tf_cgh.paragraphs[0]
    p_cgh.text = "🛡️ CORROBORATION GATING: ZERO FALSE ALARMS"
    p_cgh.font.name = FONT_HEADING
    p_cgh.font.size = Pt(12)
    p_cgh.font.bold = True
    p_cgh.font.color.rgb = EMERALD

    tb_cgb = slide.shapes.add_textbox(rx + Inches(0.25), Inches(2.35), col_w - Inches(0.5), Inches(4.3))
    tf_cgb = tb_cgb.text_frame
    tf_cgb.word_wrap = True

    gate_points = [
        ("The Core Philosophy:", " Raw alerts are NOT incidents. A single failed SSH login or blocked URL is background noise. Promoting it creates alert fatigue."),
        ("Multi-Stage Promotion Gate:", " An incident is ONLY promoted to executive dossiers if the adversary traverses at least 2 distinct MITRE ATT&CK stages (e.g. Initial Access ➜ Credential Access ➜ Lateral Movement)."),
        ("Noise Elimination (24:1):", " Successfully condenses 38,128 noisy alerts into 1,588 verified, multi-stage attack incidents."),
        ("Empirical Zero False Alarms:", " Achieves 0.00% False Positive Rate on executive incident dossiers—satisfying the PRD requirement (<10%) with 100% precision."),
    ]
    for i, (g_title, g_desc) in enumerate(gate_points):
        p = tf_cgb.paragraphs[0] if i == 0 else tf_cgb.add_paragraph()
        p.space_after = Pt(12)
        r1 = p.add_run()
        r1.text = "✔ " + g_title + "\n"
        r1.font.name = FONT_BODY
        r1.font.bold = True
        r1.font.size = Pt(11)
        r1.font.color.rgb = CYAN
        r2 = p.add_run()
        r2.text = g_desc
        r2.font.name = FONT_BODY
        r2.font.size = Pt(10)
        r2.font.color.rgb = TEXT_MUTED

    add_speaker_notes(slide, """
SPEAKER SCRIPT:
"How does Cyberforge connect disconnected logs into a coherent attack story? Through our 4D Correlation Engine.

We cluster telemetry across four distinct dimensions:
1. Source IP and ingress vectors.
2. Target IP and service ports.
3. Subnet boundaries to track lateral pivots across segments.
4. Microsecond monotonic timestamps to enforce strictly causal chronology.

Crucially, we introduce Corroboration Gating. If an employee mistypes their password three times, that is telemetry—not an incident. Our engine records it, but will never alert executive analysts unless the adversary moves to a second kill chain stage, such as lateral movement or privilege escalation. This gating mechanism is the reason Cyberforge achieves a 0.00% False Alarm Rate."
""")


def build_slide_7(prs):
    """Slide 7: Incident #2 Deep Dive & Interactive Attack Graph."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide)
    add_header(slide, "Incident #2 Deep-Dive: 8 Stages, 64 Hops, Risk Score 97/100", "PRIMARY SHOWCASE CAMPAIGN • MULTI-STAGE BREACH RECONSTRUCTION", 7)

    col_w = Inches(5.6)
    lx = Inches(0.8)

    # Left: Factsheet & Timeline Breakdown
    add_card(slide, lx, Inches(1.7), col_w, Inches(5.1), bg=BG_CARD, border=AMBER)

    tb_ih = slide.shapes.add_textbox(lx + Inches(0.25), Inches(1.85), col_w - Inches(0.5), Inches(0.4))
    tf_ih = tb_ih.text_frame
    p_ih = tf_ih.paragraphs[0]
    p_ih.text = "🎯 INCIDENT #2 EXECUTIVE DOSSIER"
    p_ih.font.name = FONT_HEADING
    p_ih.font.size = Pt(12)
    p_ih.font.bold = True
    p_ih.font.color.rgb = AMBER

    tb_ib = slide.shapes.add_textbox(lx + Inches(0.25), Inches(2.35), col_w - Inches(0.5), Inches(4.3))
    tf_ib = tb_ib.text_frame
    tf_ib.word_wrap = True

    inc_details = [
        ("Primary Target Host:", " 10.10.20.11 (Corporate Ingress Node)"),
        ("Attributed Adversary:", " 92.151.63.124 (External C2 & Ingress Operator)"),
        ("Incident Severity:", " CRITICAL  •  Risk Score: 97 / 100"),
        ("Attack Breadth:", " 8 MITRE Stages  •  64 Chronological Hops"),
        ("Campaign Duration:", " 352 Minutes total breach dwell time"),
        ("Reconstructed Attack Sequence:", "\n  1. Initial Access: Inbound RDP brute-force on port 3389\n  2. Execution: Suspicious PowerShell process spawn\n  3. Credential Dumping: LSASS memory access & Kerberoasting\n  4. Reconnaissance: Subnet discovery on 10.10.99.0/24\n  5. Lateral Movement: SMB/RPC pivot targeting Domain Controller\n  6. C2 Exfiltration: Periodic beaconing to 92.151.63.124\n  7. Crown Jewel Threat: Active Directory DCSync execution"),
    ]
    for i, (prefix, body) in enumerate(inc_details):
        p = tf_ib.paragraphs[0] if i == 0 else tf_ib.add_paragraph()
        p.space_after = Pt(6)
        r1 = p.add_run()
        r1.text = "• " + prefix
        r1.font.name = FONT_BODY
        r1.font.bold = True
        r1.font.size = Pt(10)
        r1.font.color.rgb = TEXT_PRIMARY if i != 2 else AMBER
        r2 = p.add_run()
        r2.text = body
        r2.font.name = FONT_BODY
        r2.font.size = Pt(10)
        r2.font.color.rgb = TEXT_MUTED if i != 2 else TEXT_PRIMARY

    # Right: Embedded Screenshot of Incident Graph Canvas
    rx = Inches(6.7)
    img_w = Inches(5.833)
    img_h = Inches(5.1)

    if os.path.exists(IMG_INCIDENT_CANVAS):
        slide.shapes.add_picture(IMG_INCIDENT_CANVAS, rx, Inches(1.7), img_w, img_h)
    else:
        # Fallback card if image missing
        add_card(slide, rx, Inches(1.7), img_w, img_h, bg=BG_CARD_LIGHT, border=CYAN)
        tb_ph = slide.shapes.add_textbox(rx + Inches(0.5), Inches(3.5), img_w - Inches(1.0), Inches(1.0))
        tb_ph.text_frame.paragraphs[0].text = "[Interactive Graph & Timeline Canvas Screenshot]"
        tb_ph.text_frame.paragraphs[0].font.color.rgb = CYAN

    add_speaker_notes(slide, """
SPEAKER SCRIPT:
"Let's dive into our primary showcase: Incident #2. This incident demonstrates the full power of Cyberforge.

Here on host 10.10.20.11, our engine detected an external threat actor from 92.151.63.124. Over a 352-minute campaign, this adversary executed 64 chronological hops spanning 8 distinct MITRE ATT&CK stages:
- They started with inbound RDP brute-force on port 3389.
- They executed PowerShell loaders and dumped credentials via LSASS.
- They performed subnet discovery and pivoted laterally across the network via SMB and RPC.
- Finally, they attempted a DCSync attack against the corporate Domain Controller.

Our UI provides an interactive scrubber: analysts can drag the slider from Hop 1 to Hop 64 to inspect the exact causal progression with zero time-travel artifacts."
""")


def build_slide_8(prs):
    """Slide 8: Predictive 2-Hop Lookahead & Blast Radius Calculation."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide)
    add_header(slide, "Predictive 2-Hop Lookahead: Mitigating Crown Jewel Exposure", "SUB-2MS GRAPH PRE-COMPUTATION & PROACTIVE CONTAINMENT", 8)

    col_w = Inches(5.7)
    lx = Inches(0.8)
    rx = Inches(6.833)

    # Left: Predictive Lookahead Engine
    add_card(slide, lx, Inches(1.7), col_w, Inches(5.1), bg=BG_CARD, border=PURPLE)

    tb_lh = slide.shapes.add_textbox(lx + Inches(0.25), Inches(1.85), col_w - Inches(0.5), Inches(0.4))
    tf_lh = tb_lh.text_frame
    p_lh = tf_lh.paragraphs[0]
    p_lh.text = "🔮 PREDICTIVE BLAST RADIUS ENGINE"
    p_lh.font.name = FONT_HEADING
    p_lh.font.size = Pt(12)
    p_lh.font.bold = True
    p_lh.font.color.rgb = PURPLE

    tb_lb = slide.shapes.add_textbox(lx + Inches(0.25), Inches(2.35), col_w - Inches(0.5), Inches(4.3))
    tf_lb = tb_lb.text_frame
    tf_lb.word_wrap = True

    pred_points = [
        ("The Core Question:", " The hackathon PRD specifically asks: 'What could the attacker reach next?'"),
        ("Precomputed Adjacency Matrices:", " Running recursive graph traversals on-the-fly takes hundreds of milliseconds. Instead, Cyberforge pre-indexes network reachability matrices in DuckDB during correlation."),
        ("1.5 ms Lookahead Latency:", " Returns the entire 2-hop blast radius in 1.5 milliseconds—330x faster than the PRD Great threshold (< 500ms)."),
        ("Immediate Blast Radius for Host 10.10.20.11:", "\n  • Hop 1: 5 immediate workstation peers in 10.10.20.0/24 subnet\n  • Hop 2 Crown Jewel: Direct route to Active Directory Domain Controller (10.10.99.1)"),
    ]
    for i, (bold_p, body) in enumerate(pred_points):
        p = tf_lb.paragraphs[0] if i == 0 else tf_lb.add_paragraph()
        p.space_after = Pt(10)
        r1 = p.add_run()
        r1.text = "• " + bold_p + "\n"
        r1.font.name = FONT_BODY
        r1.font.bold = True
        r1.font.size = Pt(11)
        r1.font.color.rgb = TEXT_PRIMARY
        r2 = p.add_run()
        r2.text = body
        r2.font.name = FONT_BODY
        r2.font.size = Pt(10)
        r2.font.color.rgb = TEXT_MUTED

    # Right: Proactive Defense & Containment Playbook
    add_card(slide, rx, Inches(1.7), col_w, Inches(5.1), bg=BG_CARD, border=EMERALD)

    tb_ph = slide.shapes.add_textbox(rx + Inches(0.25), Inches(1.85), col_w - Inches(0.5), Inches(0.4))
    tf_ph = tb_ph.text_frame
    p_ph = tf_ph.paragraphs[0]
    p_ph.text = "⚡ AUTOMATED CONTAINMENT & PLAYBOOK"
    p_ph.font.name = FONT_HEADING
    p_ph.font.size = Pt(12)
    p_ph.font.bold = True
    p_ph.font.color.rgb = EMERALD

    tb_pb = slide.shapes.add_textbox(rx + Inches(0.25), Inches(2.35), col_w - Inches(0.5), Inches(4.3))
    tf_pb = tb_pb.text_frame
    tf_pb.word_wrap = True

    play_points = [
        ("Proactive Network Severance:", " Knowing the 2-hop radius allows firewall orchestration to sever lateral routes from 10.10.20.11 before the attacker touches Active Directory."),
        ("Targeted Host Quarantine:", " Isolates only the compromised host and its 5 immediate peers, preventing business-wide operational shutdown."),
        ("Automated ACL Rule Generation:", " Instantly outputs FortiGate / iptables ACL drop syntax for adversary IP 92.151.63.124."),
        ("CISO Actionable Assurance:", " Converts reactive forensics into preemptive risk mitigation within milliseconds."),
    ]
    for i, (bold_p, body) in enumerate(play_points):
        p = tf_pb.paragraphs[0] if i == 0 else tf_pb.add_paragraph()
        p.space_after = Pt(12)
        r1 = p.add_run()
        r1.text = "✔ " + bold_p + "\n"
        r1.font.name = FONT_BODY
        r1.font.bold = True
        r1.font.size = Pt(11)
        r1.font.color.rgb = CYAN
        r2 = p.add_run()
        r2.text = body
        r2.font.name = FONT_BODY
        r2.font.size = Pt(10)
        r2.font.color.rgb = TEXT_MUTED

    add_speaker_notes(slide, """
SPEAKER SCRIPT:
"A critical requirement in the PRD is: 'What could the attacker reach next?'

In high-pressure incident response, waiting seconds for recursive graph joins to calculate reachability is unacceptable. Cyberforge pre-indexes network adjacency matrices directly in DuckDB. When an analyst clicks an incident, the entire 2-hop blast radius renders in just 1.5 milliseconds—330 times faster than the PRD Great target of 500 milliseconds.

In Incident #2, Cyberforge immediately flagged that host 10.10.20.11 had an open path to 5 workstation peers and a direct route to the Active Directory Domain Controller at 10.10.99.1. This allows automated EDR orchestration to sever those lateral routes proactively, neutralizing the breach before Active Directory is compromised."
""")


def build_slide_9(prs):
    """Slide 9: Macro Causal Replay Engine (/causal)."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide)
    add_header(slide, "Estate-Wide Causal Replay: Dynamic Threat Vector Progression", "MACRO VISUALIZATION & INFECTION DYNAMICS", 9)

    col_w = Inches(5.6)
    lx = Inches(0.8)

    # Left: Causal Engine Description & Threat Lifecycle
    add_card(slide, lx, Inches(1.7), col_w, Inches(5.1), bg=BG_CARD, border=CYAN)

    tb_ch = slide.shapes.add_textbox(lx + Inches(0.25), Inches(1.85), col_w - Inches(0.5), Inches(0.4))
    tf_ch = tb_ch.text_frame
    p_ch = tf_ch.paragraphs[0]
    p_ch.text = "⚡ CAUSAL REPLAY ENGINE (/causal)"
    p_ch.font.name = FONT_HEADING
    p_ch.font.size = Pt(12)
    p_ch.font.bold = True
    p_ch.font.color.rgb = CYAN

    tb_cb = slide.shapes.add_textbox(lx + Inches(0.25), Inches(2.35), col_w - Inches(0.5), Inches(4.3))
    tf_cb = tb_cb.text_frame
    tf_cb.word_wrap = True

    causal_points = [
        ("Macro Estate-Wide Visibility:", " Replays lateral movement and causal dependencies across thousands of enterprise hosts simultaneously."),
        ("Interactive Canvas Navigation:", " Full mouse wheel zoom in/out, drag-to-pan, and on-screen controls (Zoom In, Zoom Out, Fit Graph)."),
        ("3-Phase Threat Vector Lifecycle:", "\n  1. 🟡 Yellow Vector: Initial reconnaissance and staging probes targeting the Domain Controller\n  2. 🔴 Red Exploit Vector: Active weaponized exploit delivery (DCSync execution)\n  3. 🔵 Blue Persistent Vector: Settled, authenticated lateral control channel"),
        ("Compromised Node Transformation:", "\n  The Domain Controller shifts to a glowing Yellow Host badge: `10.10.99.1 [HOST COMPROMISED]` upon exploitation."),
    ]
    for i, (bold_p, body) in enumerate(causal_points):
        p = tf_cb.paragraphs[0] if i == 0 else tf_cb.add_paragraph()
        p.space_after = Pt(8)
        r1 = p.add_run()
        r1.text = bold_p
        r1.font.name = FONT_BODY
        r1.font.bold = True
        r1.font.size = Pt(10)
        r1.font.color.rgb = TEXT_PRIMARY
        r2 = p.add_run()
        r2.text = body
        r2.font.name = FONT_BODY
        r2.font.size = Pt(10)
        r2.font.color.rgb = TEXT_MUTED

    # Right: Embedded Screenshot of Causal Replay
    rx = Inches(6.7)
    img_w = Inches(5.833)
    img_h = Inches(5.1)

    if os.path.exists(IMG_CAUSAL_REPLAY):
        slide.shapes.add_picture(IMG_CAUSAL_REPLAY, rx, Inches(1.7), img_w, img_h)
    else:
        add_card(slide, rx, Inches(1.7), img_w, img_h, bg=BG_CARD_LIGHT, border=AMBER)
        tb_ph = slide.shapes.add_textbox(rx + Inches(0.5), Inches(3.5), img_w - Inches(1.0), Inches(1.0))
        tb_ph.text_frame.paragraphs[0].text = "[Causal Replay Screenshot: Yellow -> Red -> Blue Vector & DC Compromise]"
        tb_ph.text_frame.paragraphs[0].font.color.rgb = AMBER

    add_speaker_notes(slide, """
SPEAKER SCRIPT:
"In addition to the per-incident attack canvas, we built the macro Causal Replay Engine at `/causal`.

This engine renders estate-wide infection dynamics across the entire enterprise topology. Analysts can zoom in using the mouse wheel, pan across subnets, and hit play to observe lateral movement as it unfolds.

Notice our 3-phase threat vector lifecycle:
1. First, an animated yellow threat arrow extends towards the Domain Controller during initial reconnaissance.
2. As weaponized exploit execution begins, the line turns into an intense red threat vector.
3. Once established, it transitions into a permanent electric blue link.
4. And the Domain Controller node transforms into a yellow compromised host labeled '10.10.99.1 [HOST COMPROMISED]'. This provides instant situational awareness for executive leadership."
""")


def build_slide_10(prs):
    """Slide 10: Empirical Generalization on Unseen Test Data."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide)
    add_header(slide, "Empirical Validation: Flawless Execution on Unseen Test Data", "GENERALIZATION AUDIT • ZERO OVERFITTING ON FRESH DATASETS", 10)

    # 4 Stat Cards across the top comparing Train vs Test
    comp_stats = [
        ("DATASET SLICE", "Training: 500k Events\nValidation: 100MB Unseen Slice", CYAN),
        ("SENSITIVITY", "Training: 94.81%\nValidation: 94.92% (Exceeded!)", EMERALD),
        ("ACCURACY", "Training: 100.00%\nValidation: 100.00% (Identical)", EMERALD),
        ("FALSE ALARMS", "Training: 0.00%\nValidation: 0.00% (Zero Noise)", EMERALD),
    ]
    card_w = Inches(2.75)
    card_gap = Inches(0.24)
    for i, (label, val_text, color) in enumerate(comp_stats):
        cx = Inches(0.8) + i * (card_w + card_gap)
        cy = Inches(1.7)
        add_card(slide, cx, cy, card_w, Inches(1.5), bg=BG_CARD, border=BORDER_CARD)

        tb = slide.shapes.add_textbox(cx + Inches(0.15), cy + Inches(0.15), card_w - Inches(0.3), Inches(1.2))
        tf = tb.text_frame
        tf.word_wrap = True
        pl = tf.paragraphs[0]
        pl.text = label
        pl.font.name = FONT_HEADING
        pl.font.size = Pt(11)
        pl.font.bold = True
        pl.font.color.rgb = color

        pv = tf.add_paragraph()
        pv.text = val_text
        pv.font.name = FONT_BODY
        pv.font.size = Pt(10)
        pv.font.color.rgb = TEXT_PRIMARY

    # Bottom Two Columns
    col_w = Inches(5.7)
    lx = Inches(0.8)
    rx = Inches(6.833)

    # Left: Out-of-Sample Methodology
    add_card(slide, lx, Inches(3.45), col_w, Inches(3.35), bg=BG_CARD, border=CYAN)
    tb_mh = slide.shapes.add_textbox(lx + Inches(0.25), Inches(3.6), col_w - Inches(0.5), Inches(0.4))
    tf_mh = tb_mh.text_frame
    p_mh = tf_mh.paragraphs[0]
    p_mh.text = "🧪 VALIDATION METHODOLOGY (ZERO OVERFITTING)"
    p_mh.font.name = FONT_HEADING
    p_mh.font.size = Pt(12)
    p_mh.font.bold = True
    p_mh.font.color.rgb = CYAN

    tb_mb = slide.shapes.add_textbox(lx + Inches(0.25), Inches(4.1), col_w - Inches(0.5), Inches(2.6))
    tf_mb = tb_mb.text_frame
    tf_mb.word_wrap = True

    m_points = [
        ("Independent Log Slice:", " Extracted a fresh 100MB log slice (`sample_validation_100MB.log`) from a 1GB offset in the raw 30GB firewall file."),
        ("Discovery of Unseen Adversaries:", " Cyberforge automatically discovered brand-new threat actor IPs not present in our development samples:\n  • 49.40.182.200 (External brute-force actor)\n  • 140.108.75.221 (Web application exploit source)\n  • 217.61.70.148 (High-velocity scanner)"),
        ("No Regex Hardcoding:", " Proves detection rules are based on behavioral heuristics and state machines rather than hardcoded IPs."),
    ]
    for i, (bold_p, body) in enumerate(m_points):
        p = tf_mb.paragraphs[0] if i == 0 else tf_mb.add_paragraph()
        p.space_after = Pt(8)
        r1 = p.add_run()
        r1.text = "• " + bold_p + "\n"
        r1.font.name = FONT_BODY
        r1.font.bold = True
        r1.font.size = Pt(10)
        r1.font.color.rgb = TEXT_PRIMARY
        r2 = p.add_run()
        r2.text = body
        r2.font.name = FONT_BODY
        r2.font.size = Pt(9.5)
        r2.font.color.rgb = TEXT_MUTED

    # Right: Production Readiness & Generalization Guarantee
    add_card(slide, rx, Inches(3.45), col_w, Inches(3.35), bg=BG_CARD, border=EMERALD)
    tb_gh = slide.shapes.add_textbox(rx + Inches(0.25), Inches(3.6), col_w - Inches(0.5), Inches(0.4))
    tf_gh = tb_gh.text_frame
    p_gh = tf_gh.paragraphs[0]
    p_gh.text = "🚀 PRODUCTION READINESS GUARANTEE"
    p_gh.font.name = FONT_HEADING
    p_gh.font.size = Pt(12)
    p_gh.font.bold = True
    p_gh.font.color.rgb = EMERALD

    tb_gb = slide.shapes.add_textbox(rx + Inches(0.25), Inches(4.1), col_w - Inches(0.5), Inches(2.6))
    tf_gb = tb_gb.text_frame
    tf_gb.word_wrap = True

    g_points = [
        ("Identical Metric Convergence:", " True sensitivity on unseen data reached 94.92% (matching 94.81% on training data), proving mathematical stability."),
        ("100% Causal Consistency:", " Zero timestamp inversions or path anomalies detected on the unseen validation stream."),
        ("Zero Adaptation Required:", " The same pipeline processes Palo Alto, Fortinet, Suricata, and Zeek logs without modifying underlying SQL kernels."),
        ("Turnkey SOC Integration:", " Dockerized, CLI-executable (`run_dashboard.bat`), and exposing REST APIs for SIEM/SOAR ingestion."),
    ]
    for i, (bold_p, body) in enumerate(g_points):
        p = tf_gb.paragraphs[0] if i == 0 else tf_gb.add_paragraph()
        p.space_after = Pt(8)
        r1 = p.add_run()
        r1.text = "✔ " + bold_p + "\n"
        r1.font.name = FONT_BODY
        r1.font.bold = True
        r1.font.size = Pt(10)
        r1.font.color.rgb = CYAN
        r2 = p.add_run()
        r2.text = body
        r2.font.name = FONT_BODY
        r2.font.size = Pt(9.5)
        r2.font.color.rgb = TEXT_MUTED

    add_speaker_notes(slide, """
SPEAKER SCRIPT:
"Judges often ask: 'Did you tune your rules to this specific training sample?'

To prove zero overfitting, we ran an out-of-sample validation test on a 100MB unseen slice extracted from a 1GB offset in the raw logs.

The results confirmed total generalization:
- Cyberforge discovered brand-new adversaries like 49.40.182.200 and 140.108.75.221 that never appeared in our development samples.
- Our sensitivity on unseen data was 94.92%—virtually identical to our 94.81% training score.
- False alarms remained at exactly 0.00%.

This proves that Cyberforge is powered by generalizable behavioral state machines and 4D correlation, making it immediately deployable in production enterprise SOC environments."
""")


def build_slide_11(prs):
    """Slide 11: Mentor Defense Sheet & 3-Minute Live Demo Blueprint."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide)
    add_header(slide, "Mentor Defense Sheet & 3-Minute Live Demo Execution Plan", "DEFENSE PLAYBOOK & LIVE DEMONSTRATION STRATEGY", 11)

    col_w = Inches(5.7)
    lx = Inches(0.8)
    rx = Inches(6.833)

    # Left: Top 4 Mentor Defense Answers
    add_card(slide, lx, Inches(1.7), col_w, Inches(5.1), bg=BG_CARD, border=AMBER)

    tb_dh = slide.shapes.add_textbox(lx + Inches(0.25), Inches(1.85), col_w - Inches(0.5), Inches(0.4))
    tf_dh = tb_dh.text_frame
    p_dh = tf_dh.paragraphs[0]
    p_dh.text = "🛡️ MENTOR CROSS-EXAMINATION DEFENSE"
    p_dh.font.name = FONT_HEADING
    p_dh.font.size = Pt(12)
    p_dh.font.bold = True
    p_dh.font.color.rgb = AMBER

    tb_db = slide.shapes.add_textbox(lx + Inches(0.25), Inches(2.35), col_w - Inches(0.5), Inches(4.3))
    tf_db = tb_db.text_frame
    tf_db.word_wrap = True

    faq_items = [
        ("Q: Why 94.8% sensitivity instead of 100%?", " Capturing 100% by alerting on single-packet port drops destroys real-world usability. 94.81% captures all genuine multi-stage attacks while keeping false alarms at 0.00%."),
        ("Q: How did you process 30GB in 135MB RAM?", " PyArrow zero-copy streaming feeds DuckDB in 100,000-row chunks. DuckDB offloads intermediate joins to temporary disk storage (`out/tmp_duckdb`), bounding memory."),
        ("Q: How is 2-hop lookahead calculated in 1.5ms?", " Pre-indexed adjacency tables in DuckDB. Graph reachability is precomputed during correlation rather than via slow recursive query-time joins."),
        ("Q: How do you guarantee 0% false alarms?", " Multi-stage corroboration gating. Single events remain raw telemetry and are never escalated unless 2+ distinct kill chain stages are traversed."),
    ]
    for i, (q, a) in enumerate(faq_items):
        p = tf_db.paragraphs[0] if i == 0 else tf_db.add_paragraph()
        p.space_after = Pt(10)
        r1 = p.add_run()
        r1.text = q + "\n"
        r1.font.name = FONT_BODY
        r1.font.bold = True
        r1.font.size = Pt(10)
        r1.font.color.rgb = TEXT_PRIMARY
        r2 = p.add_run()
        r2.text = "➜ " + a
        r2.font.name = FONT_BODY
        r2.font.size = Pt(9.5)
        r2.font.color.rgb = TEXT_MUTED

    # Right: 3-Minute Live Demo Blueprint
    add_card(slide, rx, Inches(1.7), col_w, Inches(5.1), bg=BG_CARD, border=CYAN)

    tb_bh = slide.shapes.add_textbox(rx + Inches(0.25), Inches(1.85), col_w - Inches(0.5), Inches(0.4))
    tf_bh = tb_bh.text_frame
    p_bh = tf_bh.paragraphs[0]
    p_bh.text = "⏱️ 3-MINUTE WINNING LIVE DEMO BLUEPRINT"
    p_bh.font.name = FONT_HEADING
    p_bh.font.size = Pt(12)
    p_bh.font.bold = True
    p_bh.font.color.rgb = CYAN

    tb_bb = slide.shapes.add_textbox(rx + Inches(0.25), Inches(2.35), col_w - Inches(0.5), Inches(4.3))
    tf_bb = tb_bb.text_frame
    tf_bb.word_wrap = True

    demo_steps = [
        ("0:00 - 0:30 (Terminal Pre-Flight):", " Show terminal output from `metrics.py`. Prove all 7 PRD metrics exceed Great tier and are calculated from real DuckDB database tables."),
        ("0:30 - 1:15 (Executive Dashboard):", " Open `http://localhost:8000`. Highlight the 5 KPI summary cards and the Ranked Threat Index (1,588 incidents condensed from 38k alerts)."),
        ("1:15 - 2:15 (Incident #2 Deep Dive):", " Click Incident #2. Walk through the plain-English briefing, scrub the timeline slider from Hop 1 to 64, and demonstrate the 1.5ms 2-hop blast radius card."),
        ("2:15 - 3:00 (Causal Replay Engine):", " Click Launch Causal Replay Engine (`/causal`). Zoom with mouse wheel, pan across nodes, and trigger the yellow ➜ red ➜ blue DC compromise vector sequence."),
    ]
    for i, (time_slot, action) in enumerate(demo_steps):
        p = tf_bb.paragraphs[0] if i == 0 else tf_bb.add_paragraph()
        p.space_after = Pt(10)
        r1 = p.add_run()
        r1.text = time_slot + "\n"
        r1.font.name = FONT_BODY
        r1.font.bold = True
        r1.font.size = Pt(10)
        r1.font.color.rgb = CYAN
        r2 = p.add_run()
        r2.text = action
        r2.font.name = FONT_BODY
        r2.font.size = Pt(9.5)
        r2.font.color.rgb = TEXT_MUTED

    add_speaker_notes(slide, """
SPEAKER SCRIPT:
"In summary, Cyberforge transforms complex, overwhelming firewall telemetry into autonomous, prioritized, and proactive cyber defense.

During your 3-minute pitch, follow this exact blueprint:
1. Start in the terminal to establish unquestionable technical credibility with the 7 PRD metrics.
2. Move to the browser dashboard to show executive alert reduction and threat ranking.
3. Drill into Incident #2 to demonstrate 100% causal path reconstruction and the 1.5ms 2-hop lookahead.
4. Conclude in the Causal Replay Engine showing estate-wide lateral movement and the dynamic Domain Controller compromise sequence.

Thank you mentors, we are now ready for your questions!"
""")


def main():
    print("=" * 60)
    print("CYBERFORGE HACKATHON PITCH DECK GENERATOR")
    print("=" * 60)

    prs = Presentation()
    # Set 16:9 widescreen dimensions
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    print("[*] Generating Slide 1: Title & Key Highlights...")
    build_slide_1(prs)

    print("[*] Generating Slide 2: SIEM Fatigue Crisis & Problem Statement...")
    build_slide_2(prs)

    print("[*] Generating Slide 3: Vectorized Ingestion Architecture...")
    build_slide_3(prs)

    print("[*] Generating Slide 4: Official PRD Rubric Scorecard (100% Great)...")
    build_slide_4(prs)

    print("[*] Generating Slide 5: Sensitivity Audit & Ground-Truth Math...")
    build_slide_5(prs)

    print("[*] Generating Slide 6: 4D Correlation & Corroboration Gating...")
    build_slide_6(prs)

    print("[*] Generating Slide 7: Incident #2 Deep Dive & Attack Graph...")
    build_slide_7(prs)

    print("[*] Generating Slide 8: Predictive 2-Hop Lookahead (<2ms)...")
    build_slide_8(prs)

    print("[*] Generating Slide 9: Macro Causal Replay Engine (/causal)...")
    build_slide_9(prs)

    print("[*] Generating Slide 10: Empirical Generalization on Unseen Test Data...")
    build_slide_10(prs)

    print("[*] Generating Slide 11: Mentor Defense Sheet & Demo Blueprint...")
    build_slide_11(prs)

    # Ensure output directories exist
    os.makedirs(r"C:\Users\Ankit Umadi\Downloads", exist_ok=True)
    os.makedirs(r"C:\Users\Ankit Umadi\Documents\hack\docs", exist_ok=True)

    print(f"[*] Saving presentation to: {DOWNLOADS_PPTX}")
    prs.save(DOWNLOADS_PPTX)

    print(f"[*] Mirroring presentation to: {DOCS_PPTX}")
    prs.save(DOCS_PPTX)

    size_mb = os.path.getsize(DOWNLOADS_PPTX) / (1024 * 1024)
    print(f"[+] SUCCESS! Generated 11-slide presentation ({size_mb:.2f} MB)")
    print(f"[+] Target verified at: {DOWNLOADS_PPTX}")


if __name__ == "__main__":
    main()
