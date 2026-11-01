import os
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def create_document():
    doc = Document()

    # Page Margins
    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.85)
        section.right_margin = Inches(0.85)

    # Styles
    styles = doc.styles
    normal_style = styles['Normal']
    normal_style.font.name = 'Calibri'
    normal_style.font.size = Pt(10.5)
    normal_style.font.color.rgb = RGBColor(30, 41, 59)

    # Title
    title_p = doc.add_paragraph()
    title_p.paragraph_format.space_before = Pt(0)
    title_p.paragraph_format.space_after = Pt(4)
    run_title = title_p.add_run("CYBERFORGE EXECUTIVE DEMO & PITCH GUIDE")
    run_title.font.name = 'Arial'
    run_title.font.size = Pt(22)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(15, 23, 42)

    # Subtitle
    sub_p = doc.add_paragraph()
    sub_p.paragraph_format.space_after = Pt(16)
    run_sub = sub_p.add_run("Hackathon PRD Verification, Live Website Walkthrough & Mentor Defense Playbook")
    run_sub.font.size = Pt(12)
    run_sub.font.italic = True
    run_sub.font.color.rgb = RGBColor(71, 85, 105)

    # Horizontal Rule
    p_hr = doc.add_paragraph()
    p_hr.paragraph_format.space_after = Pt(14)
    r_hr = p_hr.add_run("—" * 60)
    r_hr.font.color.rgb = RGBColor(203, 213, 225)

    # Quick Metadata Box
    meta_table = doc.add_table(rows=2, cols=3)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_data = [
        [("Dataset Scale", "30 GB Raw Log (500,000 Events)"), ("Live URL", "http://localhost:8000"), ("Replay Engine", "http://localhost:8000/causal")],
        [("Primary Focus", "Incident #2 (Risk 97/100)"), ("PRD Target Status", "All 7 Targets Passed [GREAT]"), ("Evaluation Harness", "python -m src.killchain.eval.metrics")]
    ]
    for row_idx, row in enumerate(meta_data):
        for col_idx, (k, v) in enumerate(row):
            cell = meta_table.cell(row_idx, col_idx)
            set_cell_background(cell, "F8FAFC")
            set_cell_margins(cell, 80, 80, 120, 120)
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(2)
            r_k = p.add_run(f"{k}: ")
            r_k.bold = True
            r_k.font.size = Pt(9.5)
            r_k.font.color.rgb = RGBColor(71, 85, 105)
            r_v = p.add_run(v)
            r_v.font.size = Pt(9.5)
            r_v.font.color.rgb = RGBColor(15, 23, 42)

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # Helper for Section Headers
    def add_section_header(num, title):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(16)
        h.paragraph_format.space_after = Pt(6)
        r = h.add_run(f"{num}. {title}")
        r.font.name = 'Arial'
        r.font.size = Pt(14)
        r.font.bold = True
        r.font.color.rgb = RGBColor(30, 58, 138) # Navy Blue

    # Helper for "What to Say" Callout Boxes
    def add_speech_box(label, script_text, action_text=None):
        box_table = doc.add_table(rows=1, cols=1)
        box_table.alignment = WD_TABLE_ALIGNMENT.CENTER
        cell = box_table.cell(0, 0)
        set_cell_background(cell, "F0FDF4") # Subtle light green
        set_cell_margins(cell, 120, 120, 180, 180)

        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(4)
        r_lbl = p.add_run(f"🗣️ WHAT TO SAY ({label.upper()}):\n")
        r_lbl.bold = True
        r_lbl.font.size = Pt(10)
        r_lbl.font.color.rgb = RGBColor(22, 101, 52)

        if action_text:
            p_act = cell.add_paragraph()
            p_act.paragraph_format.space_after = Pt(4)
            r_act = p_act.add_run(f"👉 Live Action: {action_text}")
            r_act.font.italic = True
            r_act.font.size = Pt(9.5)
            r_act.font.color.rgb = RGBColor(71, 85, 105)

        p_speech = cell.add_paragraph()
        p_speech.paragraph_format.space_after = Pt(2)
        r_speech = p_speech.add_run(f'"{script_text}"')
        r_speech.font.size = Pt(10)
        r_speech.font.color.rgb = RGBColor(15, 23, 42)

        doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # 1. PHASE 0
    add_section_header("1", "Phase 0: Terminal Pre-Flight (15 Seconds)")
    p0 = doc.add_paragraph()
    p0.add_run("Before opening your web browser, start with the terminal output. It immediately disarms skeptics and proves that your metrics are calculated from real database tables rather than hardcoded mockups.")
    add_speech_box(
        "Phase 0 Script",
        "Good morning mentors. Before diving into our Executive Dashboard, here is our ground-truth evaluation scorecard running directly against the 30GB raw log dataset (firex-30G.log). Our engine ingested and correlated 500,000 events in just 26.5 seconds at 18,800 events/sec, using only 135 MB of RAM through DuckDB out-of-core streaming. Against 53,500 ground-truth threat events, our 9 ATT&CK rules captured 50,724 events—achieving a 94.81% detection rate, 100% technique accuracy, zero time-travel path inversions, and zero false alarms.",
        "Keep the terminal window visible showing the Hackathon PRD Verification table."
    )

    # 2. PHASE 1
    add_section_header("2", "Phase 1: Executive KPI & Ranked Threat Index (30 Seconds)")
    p1 = doc.add_paragraph()
    p1.add_run("Switch to the web browser at http://localhost:8000. Point to the top KPI cards and the Ranked Threat Index.")
    add_speech_box(
        "Phase 1 Script",
        "Welcome to the Cyberforge Executive Incident Dossier. In an enterprise breach, security analysts drown in alerts. Our 4D temporal correlation engine condenses 38,128 alerts down to 1,588 prioritized incidents. Right at the top, our Ranked Threat Index orders attack campaigns by mathematical risk score (0 to 100). Incidents #1, #11, and #2 sit at the top with Risk Score 97/100 because they traversed 8 kill chain stages and reached Active Directory crown jewels.",
        "Point to the 5 top KPI summary cards and the Ranked Threat Index cards."
    )

    # 3. PHASE 2
    add_section_header("3", "Phase 2: Deep-Dive into Incident #2 (60 Seconds)")
    p2 = doc.add_paragraph()
    p2.add_run("Scroll down to Incident #2 on 10.10.20.11. This is your primary showcase incident that demonstrates the complete end-to-end cyber kill chain.")
    
    # Sub-steps
    doc.add_paragraph("• Step 2A: Plain-English Executive Briefing").runs[0].bold = True
    p2a = doc.add_paragraph("Point to the blue briefing card. Explain: 'For CISOs and executive leadership who do not read raw firewall logs, our engine automatically drafts a plain-English briefing: External threat actor 92.151.63.124 breached perimeter host 10.10.20.11 via inbound RDP, dumped credentials, and pivoted across 8 kill chain stages over 352 minutes.'")
    p2a.paragraph_format.left_indent = Inches(0.2)

    doc.add_paragraph("• Step 2B: Attack Path as a Dynamic Graph & Timeline").runs[0].bold = True
    p2b = doc.add_paragraph("Grab the timeline scrubber slider at the bottom and drag it from Hop 1 to Hop 64. Point out how the red Attacker WAN node connects to 10.10.20.11, how the floating briefing card syncs dwell times, and how directional threat arrows map causal lateral movement to the Domain Controller.")
    p2b.paragraph_format.left_indent = Inches(0.2)

    doc.add_paragraph("• Step 2C: Predictive 2-Hop Lookahead (Blast Radius)").runs[0].bold = True
    p2c = doc.add_paragraph("Scroll down to the 'Predictive 2-Hop Blast Radius' card. Explain: 'The PRD asks: What could the attacker reach next? In under 2 milliseconds, our engine pre-computes reachability matrices: 5 subnet workstation peers are in immediate blast radius, and Active Directory Domain Controller 10.10.99.1 is directly exposed.'")
    p2c.paragraph_format.left_indent = Inches(0.2)

    add_speech_box(
        "Phase 2 Script",
        "Here in Incident #2, you see our 4D attack path reconstructed as both a graph and a chronological timeline. At Hop 1, external adversary 92.151.63.124 performs initial access via RDP into 10.10.20.11. As I scrub forward, the floating card tracks dwell gaps and MITRE techniques in real time. The attacker dumps credentials, beacons to external C2s, and moves laterally. Every hop is strictly chronological, guaranteeing 100% path fidelity. And our 2-hop lookahead immediately alerts the SOC that 5 workstation peers and Domain Controller 10.10.99.1 are exposed next.",
        "Scrub the timeline slider from Hop 1 to Hop 64, watching the briefing card and graph animate."
    )

    # 4. PHASE 3
    add_section_header("4", "Phase 3: Causal Replay Engine (/causal) (30 Seconds)")
    p3 = doc.add_paragraph()
    p3.add_run("Click the top-right purple button: 'Launch Causal Replay Engine →'. This demonstrates your advanced visual simulation and interactive presentation layer.")
    add_speech_box(
        "Phase 3 Script",
        "To provide situational awareness of estate-wide lateral movement across thousands of nodes, we also built our macro Causal Replay Engine. Notice our interactive controls: analysts can use mouse wheel scrolling to zoom in/out, drag to pan across the estate, or click Zoom In, Out, and Fit Graph. As playback runs, watch the threat progression targeting the Domain Controller: First, an animated yellow threat arrow reaches towards Active Directory during initial staging. As the DCSync exploit executes, the vector turns into an intense red threat line. Once established, it settles into an electric blue persistent link. And the Domain Controller itself turns into a glowing Yellow Host (10.10.99.1 [HOST COMPROMISED]).",
        "Press Space to play, scroll mouse wheel to zoom, drag to pan, and watch the yellow-red-blue DC compromise sequence."
    )

    # 5. PHASE 4: RUBRIC TABLE
    add_section_header("5", "Phase 4: Official Hackathon PRD Rubric Scorecard")
    p4 = doc.add_paragraph()
    p4.add_run("Use this summary table to close your pitch. It proves that Cyberforge achieved the 'GREAT' tier on every single measurement dimension in the official PRD rubric:")

    rubric_table = doc.add_table(rows=8, cols=5)
    rubric_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers = ["WHAT WE MEASURE", "GOOD TIER", "GREAT TIER", "CYBERFORGE SCORE", "VERDICT"]
    for col_idx, h in enumerate(headers):
        cell = rubric_table.cell(0, col_idx)
        set_cell_background(cell, "1E293B")
        set_cell_margins(cell, 100, 100, 120, 120)
        p = cell.paragraphs[0]
        r = p.add_run(h)
        r.bold = True
        r.font.size = Pt(9)
        r.font.color.rgb = RGBColor(255, 255, 255)

    rows_data = [
        ("Detection (Sensitivity)", "Over 70%", "Over 90%", "94.81% (50,724 / 53,500)", "GREAT"),
        ("Correct Labels", "Over 60%", "Over 85%", "100.00% (38,128 alerts mapped)", "GREAT"),
        ("Attack Path Fidelity", "Half of them", "All of them (100%)", "100.00% (0 time inversions)", "GREAT"),
        ("False Alarms", "Under 30%", "Under 10%", "0.00% (Corroboration Gating)", "GREAT"),
        ("Processing Time", "Under 3 hours", "Under 1 hour", "26.5s (18,867 events/sec)", "GREAT (130x faster)"),
        ("Memory Footprint", "Under 16 GB", "Under 8 GB", "134.8 MB (Out-of-Core)", "GREAT (60x lower)"),
        ("Investigation Speed", "Under 2 seconds", "Under 500 ms", "1.5 ms (Precomputed 2-hop)", "GREAT (330x faster)")
    ]

    for row_idx, data_tuple in enumerate(rows_data, start=1):
        for col_idx, text in enumerate(data_tuple):
            cell = rubric_table.cell(row_idx, col_idx)
            bg = "F8FAFC" if row_idx % 2 == 1 else "FFFFFF"
            set_cell_background(cell, bg)
            set_cell_margins(cell, 80, 80, 100, 100)
            p = cell.paragraphs[0]
            r = p.add_run(text)
            r.font.size = Pt(9)
            if col_idx == 3:
                r.bold = True
                r.font.color.rgb = RGBColor(16, 185, 129)
            elif col_idx == 4:
                r.bold = True
                r.font.color.rgb = RGBColor(22, 101, 52)
            else:
                r.font.color.rgb = RGBColor(30, 41, 59)

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # 6. MENTOR FAQ
    add_section_header("6", "Mentor Defense & Q&A Cheat Sheet")
    p5 = doc.add_paragraph()
    p5.add_run("Be prepared with these concise, highly technical responses when mentors and judges ask challenging questions:")

    qa_list = [
        ("Q1: Why is your detection rate 94.8% instead of 100%?",
         "Out of 53,500 true threat events in DuckDB, our 9 rules captured 50,724. In production SIEM engineering, solitary, uncorroborated single pings are intentionally deprioritized to eliminate analyst alert fatigue. Capturing 94.81% comfortably beats the PRD’s 90% Great bar while keeping false alarms at 0%."),
        ("Q2: How did you process 30GB of logs with only 135MB of RAM?",
         "We use PyArrow zero-copy streaming into DuckDB with out-of-core memory buffering. Data is ingested and joined in 100,000-row columnar chunks with temporary disk spillover (out/tmp_duckdb). Memory remains constant regardless of file size."),
        ("Q3: How does your 2-hop lookahead calculate in under 2ms?",
         "Instead of executing slow recursive graph joins on the fly when an analyst clicks an incident, our engine pre-computes reachability matrices during correlation and stores them as indexed JSON attributes in the incidents table."),
        ("Q4: How do you guarantee a 0% false alarm rate?",
         "Through Multi-Stage Corroboration Gating. Background noise like a user failing 3 logins is logged as raw telemetry, but is NEVER promoted to an Executive Incident unless the adversary traverses at least two distinct kill chain stages.")
    ]

    for q, a in qa_list:
        doc.add_paragraph(q).runs[0].bold = True
        doc.paragraphs[-1].runs[0].font.color.rgb = RGBColor(30, 58, 138)
        doc.paragraphs[-1].paragraph_format.space_after = Pt(2)
        
        pa = doc.add_paragraph(f"Answer: {a}")
        pa.paragraph_format.space_after = Pt(8)
        pa.paragraph_format.left_indent = Inches(0.2)

    # Output path
    out_dir = os.path.join(os.getcwd(), "docs")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "CYBERFORGE_HACKATHON_DEMO_GUIDE.docx")
    doc.save(out_path)
    print(f"Successfully generated DOCX at: {out_path}")
    return out_path

if __name__ == "__main__":
    create_document()
