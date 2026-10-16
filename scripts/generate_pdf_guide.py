"""
PDF Generator for Final-Year Project Viva & Presentation Guide
Builds docs/SIMPLE_PROJECT_VIVA_GUIDE.pdf from docs/SIMPLE_PROJECT_VIVA_GUIDE.md
Preserves 100% of content with professional study-notes formatting, TrueType fonts, and vector diagrams.
"""

import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon, Group
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

# Register TrueType Fonts for native Unicode & math symbol support
FONT_REGULAR = "Helvetica"
FONT_BOLD = "Helvetica-Bold"
FONT_ITALIC = "Helvetica-Oblique"
FONT_MONO = "Courier"

if os.path.exists("C:\\Windows\\Fonts\\arial.ttf"):
    pdfmetrics.registerFont(TTFont("Arial-Unicode", "C:\\Windows\\Fonts\\arial.ttf"))
    pdfmetrics.registerFont(TTFont("Arial-Unicode-Bold", "C:\\Windows\\Fonts\\arialbd.ttf"))
    pdfmetrics.registerFont(TTFont("Arial-Unicode-Italic", "C:\\Windows\\Fonts\\ariali.ttf"))
    FONT_REGULAR = "Arial-Unicode"
    FONT_BOLD = "Arial-Unicode-Bold"
    FONT_ITALIC = "Arial-Unicode-Italic"

if os.path.exists("C:\\Windows\\Fonts\\cour.ttf"):
    pdfmetrics.registerFont(TTFont("Courier-TT", "C:\\Windows\\Fonts\\cour.ttf"))
    pdfmetrics.registerFont(TTFont("Courier-TT-Bold", "C:\\Windows\\Fonts\\courbd.ttf"))
    FONT_MONO = "Courier-TT"

PAGE_WIDTH, PAGE_HEIGHT = letter
MARGIN = 40.0
USABLE_WIDTH = PAGE_WIDTH - 2 * MARGIN # 532 pt

class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and display 'Page X of Y' with running headers."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_decorations(self, page_count):
        if self._pageNumber == 1:
            # Suppress running header and footer on cover page
            return

        self.saveState()
        self.setFont(FONT_BOLD, 7.5)
        self.setFillColor(HexColor("#1E3A8A"))
        self.drawString(MARGIN, PAGE_HEIGHT - 30, "AI-BASED WI-FI COVERAGE OPTIMIZATION & DEAD-ZONE PREDICTION SYSTEM")

        self.setFont(FONT_REGULAR, 7.5)
        self.setFillColor(HexColor("#64748B"))
        self.drawRightString(PAGE_WIDTH - MARGIN, PAGE_HEIGHT - 30, "B.Tech Final-Year CSE Major Project • Viva Study Guide")

        # Top rule
        self.setStrokeColor(HexColor("#CBD5E1"))
        self.setLineWidth(0.6)
        self.line(MARGIN, PAGE_HEIGHT - 34, PAGE_WIDTH - MARGIN, PAGE_HEIGHT - 34)

        # Bottom rule
        self.line(MARGIN, 38, PAGE_WIDTH - MARGIN, 38)
        self.setFont(FONT_REGULAR, 7.5)
        self.setFillColor(HexColor("#64748B"))
        self.drawString(MARGIN, 26, "Final-Year Major Project Implementation • Verified Working System")
        self.drawRightString(PAGE_WIDTH - MARGIN, 26, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()


def create_system_architecture_diagram():
    """Generates a high-resolution vector system architecture diagram."""
    w, h = USABLE_WIDTH, 175
    d = Drawing(w, h)

    # Background card
    d.add(Rect(0, 0, w, h, rx=6, ry=6, fillColor=HexColor("#F8FAFC"), strokeColor=HexColor("#CBD5E1"), strokeWidth=1))
    d.add(String(w/2, h - 16, "SYSTEM ARCHITECTURE & MULTI-TIER DATA PIPELINE", fontName=FONT_BOLD, fontSize=9, fillColor=HexColor("#1E3A8A"), textAnchor="middle"))

    # 1. Frontend Tier
    d.add(Rect(12, h - 56, w - 24, 32, rx=4, ry=4, fillColor=HexColor("#1E40AF"), strokeColor=HexColor("#1E3A8A"), strokeWidth=1))
    d.add(String(w/2, h - 40, "PRESENTATION TIER: React 19 + TypeScript + Tailwind CSS", fontName=FONT_BOLD, fontSize=8.5, fillColor=colors.white, textAnchor="middle"))
    d.add(String(w/2, h - 51, "Interactive SVG Floorplan • Simulation Controller • Real Survey Pinning • ML Risk Grid • AP Optimizer Dashboard", fontName=FONT_REGULAR, fontSize=7, fillColor=HexColor("#E2E8F0"), textAnchor="middle"))

    # Arrow Down
    d.add(Line(w/2, h - 57, w/2, h - 67, strokeColor=HexColor("#3B82F6"), strokeWidth=2))

    # 2. API Tier
    d.add(Rect(80, h - 86, w - 160, 20, rx=4, ry=4, fillColor=HexColor("#6366F1"), strokeColor=HexColor("#4F46E5"), strokeWidth=1))
    d.add(String(w/2, h - 77, "REST API GATEWAY: FastAPI + Pydantic v2 + Asynchronous Request Routers", fontName=FONT_BOLD, fontSize=7.5, fillColor=colors.white, textAnchor="middle"))

    # Arrow Down
    d.add(Line(w/2, h - 87, w/2, h - 97, strokeColor=HexColor("#6366F1"), strokeWidth=2))

    # 3. Core Engine Tier (5 cards)
    engine_w = (w - 24 - 32) / 5
    y_eng = 46
    h_eng = 44

    engines = [
        ("RF Physics Engine", "COST-231 Multi-Wall\nRay Intersection\nShadowing Fading", HexColor("#0284C7")),
        ("Survey Collector", "Windows netsh wlan\nGateway ICMP Ping\nHardware Telemetry", HexColor("#0D9488")),
        ("Dead-Zone Engine", "DBSCAN Clustering\nConvex Hull 2D\nSeverity Diagnosis", HexColor("#DC2626")),
        ("ML Predictive Engine", "Random Forest (100 Trees)\nRisk Probability Grid\nFeature Importance", HexColor("#7C3AED")),
        ("AP Optimizer", "Centroid Candidates\nCoverage Re-Simulation\nBefore vs After Eval", HexColor("#D97706")),
    ]

    for idx, (title, details, fill_c) in enumerate(engines):
        x = 12 + idx * (engine_w + 8)
        d.add(Rect(x, y_eng, engine_w, h_eng, rx=4, ry=4, fillColor=fill_c, strokeColor=HexColor("#0F172A"), strokeWidth=0.5))
        d.add(String(x + engine_w/2, y_eng + 31, title, fontName=FONT_BOLD, fontSize=7, fillColor=colors.white, textAnchor="middle"))

        lines = details.split("\n")
        d.add(String(x + engine_w/2, y_eng + 19, lines[0], fontName=FONT_REGULAR, fontSize=6, fillColor=HexColor("#F1F5F9"), textAnchor="middle"))
        d.add(String(x + engine_w/2, y_eng + 10, lines[1], fontName=FONT_REGULAR, fontSize=6, fillColor=HexColor("#F1F5F9"), textAnchor="middle"))
        d.add(String(x + engine_w/2, y_eng + 2, lines[2], fontName=FONT_REGULAR, fontSize=6, fillColor=HexColor("#F1F5F9"), textAnchor="middle"))

    # Arrow Down
    d.add(Line(w/2, y_eng - 1, w/2, 33, strokeColor=HexColor("#475569"), strokeWidth=2))

    # 4. Database Tier
    d.add(Rect(60, 8, w - 120, 24, rx=4, ry=4, fillColor=HexColor("#0F766E"), strokeColor=HexColor("#115E59"), strokeWidth=1))
    d.add(String(w/2, 17, "PERSISTENCE TIER: SQLite Relational DB + SQLAlchemy ORM (Floors, Walls, APs, Measurements, Dead Zones)", fontName=FONT_BOLD, fontSize=7.5, fillColor=colors.white, textAnchor="middle"))

    return d


def create_horizontal_pipeline_diagram(title, steps, colors_list):
    """Generates a clean horizontal 5-stage pipeline diagram."""
    w, h = USABLE_WIDTH, 68
    d = Drawing(w, h)

    # Outer box
    d.add(Rect(0, 0, w, h, rx=5, ry=5, fillColor=HexColor("#F8FAFC"), strokeColor=HexColor("#E2E8F0"), strokeWidth=1))
    d.add(String(w/2, h - 14, title, fontName=FONT_BOLD, fontSize=8, fillColor=HexColor("#1E3A8A"), textAnchor="middle"))

    n = len(steps)
    step_w = (w - 24 - (n - 1) * 16) / n
    box_h = 36
    box_y = 10

    for idx, (step_num, title_txt, sub_txt) in enumerate(steps):
        x = 12 + idx * (step_w + 16)
        c = colors_list[idx % len(colors_list)]
        d.add(Rect(x, box_y, step_w, box_h, rx=3, ry=3, fillColor=c, strokeColor=HexColor("#334155"), strokeWidth=0.5))
        d.add(String(x + step_w/2, box_y + 24, f"{step_num}. {title_txt}", fontName=FONT_BOLD, fontSize=6.5, fillColor=colors.white, textAnchor="middle"))

        subs = sub_txt.split("\n")
        if len(subs) == 1:
            d.add(String(x + step_w/2, box_y + 11, subs[0], fontName=FONT_REGULAR, fontSize=5.5, fillColor=HexColor("#F8FAFC"), textAnchor="middle"))
        else:
            d.add(String(x + step_w/2, box_y + 13, subs[0], fontName=FONT_REGULAR, fontSize=5.5, fillColor=HexColor("#F8FAFC"), textAnchor="middle"))
            d.add(String(x + step_w/2, box_y + 5, subs[1], fontName=FONT_REGULAR, fontSize=5.5, fillColor=HexColor("#F8FAFC"), textAnchor="middle"))

        # Arrow to next
        if idx < n - 1:
            arr_x = x + step_w + 2
            d.add(Line(arr_x, box_y + box_h/2, arr_x + 12, box_y + box_h/2, strokeColor=HexColor("#64748B"), strokeWidth=1.5))
            d.add(Polygon(points=[arr_x + 12, box_y + box_h/2, arr_x + 8, box_y + box_h/2 + 3, arr_x + 8, box_y + box_h/2 - 3], fillColor=HexColor("#64748B"), strokeColor=None))

    return d


def create_before_after_diagram():
    """Generates a Before vs After verification diagram."""
    w, h = USABLE_WIDTH, 82
    d = Drawing(w, h)

    d.add(Rect(0, 0, w, h, rx=5, ry=5, fillColor=HexColor("#F8FAFC"), strokeColor=HexColor("#CBD5E1"), strokeWidth=1))
    d.add(String(w/2, h - 14, "AP OPTIMIZATION BEFORE VS AFTER VERIFICATION BENCHMARK", fontName=FONT_BOLD, fontSize=8, fillColor=HexColor("#1E3A8A"), textAnchor="middle"))

    box_w = (w - 24 - 40) / 2
    box_h = 50
    box_y = 10

    # Before Box (Red theme)
    d.add(Rect(12, box_y, box_w, box_h, rx=4, ry=4, fillColor=HexColor("#FEE2E2"), strokeColor=HexColor("#EF4444"), strokeWidth=1))
    d.add(String(12 + box_w/2, box_y + 37, "BEFORE OPTIMIZATION (3 Base APs)", fontName=FONT_BOLD, fontSize=7.5, fillColor=HexColor("#991B1B"), textAnchor="middle"))
    d.add(String(12 + box_w/2, box_y + 25, "• Detected Dead Zones: 4 distinct clusters", fontName=FONT_REGULAR, fontSize=6.5, fillColor=HexColor("#7F1D1D"), textAnchor="middle"))
    d.add(String(12 + box_w/2, box_y + 15, "• Total Dead-Zone Area: 292.0 m² (4.8% of floor)", fontName=FONT_REGULAR, fontSize=6.5, fillColor=HexColor("#7F1D1D"), textAnchor="middle"))
    d.add(String(12 + box_w/2, box_y + 5, "• Severe wall loss & distance deficits in corner wings", fontName=FONT_REGULAR, fontSize=6.5, fillColor=HexColor("#7F1D1D"), textAnchor="middle"))

    # Central Arrow
    mid_x = 12 + box_w + 4
    d.add(Line(mid_x, box_y + box_h/2, mid_x + 32, box_y + box_h/2, strokeColor=HexColor("#0D9488"), strokeWidth=2))
    d.add(Polygon(points=[mid_x + 32, box_y + box_h/2, mid_x + 24, box_y + box_h/2 + 4, mid_x + 24, box_y + box_h/2 - 4], fillColor=HexColor("#0D9488"), strokeColor=None))
    d.add(String(mid_x + 16, box_y + box_h/2 + 7, "RECOMMEND", fontName=FONT_BOLD, fontSize=5.5, fillColor=HexColor("#0D9488"), textAnchor="middle"))
    d.add(String(mid_x + 16, box_y + box_h/2 - 11, "+2 APs", fontName=FONT_BOLD, fontSize=6, fillColor=HexColor("#0D9488"), textAnchor="middle"))

    # After Box (Green theme)
    right_x = 12 + box_w + 40
    d.add(Rect(right_x, box_y, box_w, box_h, rx=4, ry=4, fillColor=HexColor("#DCFCE7"), strokeColor=HexColor("#22C55E"), strokeWidth=1))
    d.add(String(right_x + box_w/2, box_y + 37, "AFTER OPTIMIZATION (+2 Recommended APs)", fontName=FONT_BOLD, fontSize=7.5, fillColor=HexColor("#166534"), textAnchor="middle"))
    d.add(String(right_x + box_w/2, box_y + 25, "• Remaining Dead Zones: 1 small pocket", fontName=FONT_REGULAR, fontSize=6.5, fillColor=HexColor("#14532D"), textAnchor="middle"))
    d.add(String(right_x + box_w/2, box_y + 15, "• Total Dead-Zone Area: 68.0 m² (only 1.1%)", fontName=FONT_BOLD, fontSize=6.5, fillColor=HexColor("#14532D"), textAnchor="middle"))
    d.add(String(right_x + box_w/2, box_y + 5, "• NET DEAD-ZONE REDUCTION: 76.7% (-224.0 m²)", fontName=FONT_BOLD, fontSize=6.5, fillColor=HexColor("#15803D"), textAnchor="middle"))

    return d


def build_pdf():
    pdf_path = os.path.join("docs", "SIMPLE_PROJECT_VIVA_GUIDE.pdf")
    os.makedirs("docs", exist_ok=True)

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN + 10,
        bottomMargin=MARGIN + 10
    )

    styles = getSampleStyleSheet()

    # Custom typography styles
    title_style = ParagraphStyle(
        "CoverTitle",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=20,
        leading=25,
        textColor=HexColor("#1E3A8A"),
        alignment=1
    )

    subtitle_style = ParagraphStyle(
        "CoverSubtitle",
        parent=styles["Normal"],
        fontName=FONT_REGULAR,
        fontSize=11,
        leading=16,
        textColor=HexColor("#475569"),
        alignment=1
    )

    h1_style = ParagraphStyle(
        "SectionH1",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=12.5,
        leading=16,
        textColor=HexColor("#1E3A8A"),
        spaceBefore=16,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        "SectionH2",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=10,
        leading=13,
        textColor=HexColor("#0F172A"),
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        "DocBody",
        parent=styles["Normal"],
        fontName=FONT_REGULAR,
        fontSize=8.5,
        leading=12,
        textColor=HexColor("#1E293B"),
        spaceAfter=4
    )

    body_bold = ParagraphStyle(
        "DocBodyBold",
        parent=body_style,
        fontName=FONT_BOLD,
        textColor=HexColor("#0F172A")
    )

    bullet_style = ParagraphStyle(
        "DocBullet",
        parent=body_style,
        leftIndent=14,
        firstLineIndent=-10,
        spaceAfter=3
    )

    callout_style = ParagraphStyle(
        "DocCallout",
        parent=styles["Normal"],
        fontName=FONT_ITALIC,
        fontSize=8,
        leading=11.5,
        textColor=HexColor("#1E3A8A")
    )

    code_style = ParagraphStyle(
        "DocCode",
        parent=styles["Normal"],
        fontName=FONT_MONO,
        fontSize=7,
        leading=9.5,
        textColor=HexColor("#0F172A")
    )

    tbl_head_style = ParagraphStyle(
        "TblHead",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=8,
        leading=10.5,
        textColor=colors.white,
        alignment=1
    )

    tbl_cell_style = ParagraphStyle(
        "TblCell",
        parent=styles["Normal"],
        fontName=FONT_REGULAR,
        fontSize=7.5,
        leading=10,
        textColor=HexColor("#1E293B")
    )

    tbl_cell_bold = ParagraphStyle(
        "TblCellBold",
        parent=tbl_cell_style,
        fontName=FONT_BOLD,
        textColor=HexColor("#0F172A")
    )

    viva_q_style = ParagraphStyle(
        "VivaQ",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=8.5,
        leading=12,
        textColor=HexColor("#1E40AF"),
        spaceBefore=6,
        spaceAfter=2,
        keepWithNext=True
    )

    viva_a_style = ParagraphStyle(
        "VivaA",
        parent=styles["Normal"],
        fontName=FONT_REGULAR,
        fontSize=8,
        leading=11.5,
        textColor=HexColor("#1E293B"),
        leftIndent=10,
        spaceAfter=4
    )

    story = []

    # =========================================================================
    # COVER PAGE
    # =========================================================================
    story.append(Spacer(1, 30))
    story.append(Paragraph("B.TECH COMPUTER SCIENCE & ENGINEERING", subtitle_style))
    story.append(Paragraph("FINAL-YEAR MAJOR PROJECT PRESENTATION & VIVA DEFENSE GUIDE", ParagraphStyle("CoverSub", parent=subtitle_style, fontName=FONT_BOLD, fontSize=11, textColor=HexColor("#0284C7"))))
    story.append(Spacer(1, 20))

    story.append(Paragraph("AI-Based Wi-Fi Coverage Optimization and Dead-Zone Prediction System", title_style))
    story.append(Spacer(1, 15))

    story.append(Paragraph("Complete Technical Architecture • COST-231 Physics Engine • DBSCAN Spatial Clustering<br/>Random Forest ML Predictor • Real College Laptop Telemetry • Verified Optimization", subtitle_style))
    story.append(Spacer(1, 28))

    # Meta card table
    meta_data = [
        [Paragraph("<b>Academic Degree:</b>", tbl_cell_style), Paragraph("Bachelor of Technology in Computer Science & Engineering (B.Tech CSE)", tbl_cell_style)],
        [Paragraph("<b>Project Phase:</b>", tbl_cell_style), Paragraph("Major Project Final Implementation & Comprehensive Viva Voce", tbl_cell_style)],
        [Paragraph("<b>Core Workflow:</b>", tbl_cell_style), Paragraph("<b>DETECT ──► UNDERSTAND ──► PREDICT ──► OPTIMIZE ──► VERIFY</b>", tbl_cell_style)],
        [Paragraph("<b>Operating Modes:</b>", tbl_cell_style), Paragraph("1. Virtual RF Simulation Mode (COST-231 Indoor Multi-Wall Model)<br/>2. Real College Survey Mode (Native Windows netsh + Gateway ICMP Ping)", tbl_cell_style)],
        [Paragraph("<b>Verification Status:</b>", tbl_cell_style), Paragraph("<b>21 / 21 Automated Backend Tests Passed (Pytest)</b> • 0 Frontend Build Errors", tbl_cell_style)],
        [Paragraph("<b>Target Audience:</b>", tbl_cell_style), Paragraph("Final-Year Student, External Examiners, Project Evaluators, Faculty Guide", tbl_cell_style)],
        [Paragraph("<b>Guiding Principle:</b>", tbl_cell_style), Paragraph("100% Honest Engineering • Rigorous Mathematics • Zero Fabricated Claims", tbl_cell_style)],
    ]
    meta_table = Table(meta_data, colWidths=[130, USABLE_WIDTH - 130])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), HexColor("#F8FAFC")),
        ('BOX', (0,0), (-1,-1), 1, HexColor("#CBD5E1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, HexColor("#E2E8F0")),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(meta_table)

    story.append(Spacer(1, 35))
    story.append(HRFlowable(width="100%", thickness=1, color=HexColor("#3B82F6"), spaceAfter=14))
    story.append(Paragraph("<b>CONFIDENTIAL STUDY NOTES</b> • Designed for thorough examination preparation, oral defense, and code walkthrough.", ParagraphStyle("Foot", parent=subtitle_style, fontSize=8, textColor=HexColor("#64748B"))))

    story.append(PageBreak())

    # =========================================================================
    # TABLE OF CONTENTS
    # =========================================================================
    story.append(Paragraph("TABLE OF CONTENTS", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=HexColor("#1E3A8A"), spaceAfter=10))

    toc_items = [
        ("1. What is Our Project?", "Project Title, Problem Solved, Solution Overview, Software Role, Main Novelty"),
        ("2. Technologies Used & Why We Chose Them", "Full technology justification table: FastAPI, React 19, SQLite, Scikit-learn, DBSCAN, netsh"),
        ("3. How the Project Works (High-Level Architecture)", "Client-Server architecture, System Architecture Diagram, 7 operational execution steps"),
        ("4. Simulation Mode (Virtual RF Physics Engine)", "Virtual metrics, Multi-Wall COST-231 math formulas, Wall Attenuation Factors, Network correlation"),
        ("5. Real College Survey Mode (Laptop Telemetry)", "Windows netsh wlan, Gateway ICMP ping rationale, Pin coordinate selection, Real vs Estimated table"),
        ("6. Dead-Zone Detection (DBSCAN Clustering & Severity)", "Dead zone multi-metric criteria, DBSCAN epsilon/min_samples, Convex Hull area, Severity scoring"),
        ("7. Dead-Zone Prediction (Random Forest Machine Learning)", "Classifier architecture, 7 input features, Evaluation metrics (Acc/Prec/Rec/F1), Feature importance"),
        ("8. AP Placement Optimization & Before-vs-After", "Candidate generation at centroids, physics re-simulation, ranking, verified reduction formula"),
        ("9. Complete Step-by-Step Workflows", "Execution guide for Workflow A (Simulation Demo) and Workflow B (Real Campus Survey Walk)"),
        ("10. Button-by-Button UI Guide", "Comprehensive table of every button: label, internal backend API action, and visual result"),
        ("11. Testing & Verification Suite", "21 automated unit/integration tests breakdown, frontend Vite production build status"),
        ("12. Actual Results & Verification Numbers", "Explicitly separated [SIMULATED] benchmark numbers vs [REAL LAPTOP] live hardware test"),
        ("13. Honest Academic Limitations", "Indoor positioning realities, 2D planar model vs 3D multipath, non-flooding throughput"),
        ("14. 3-to-5 Minute Presentation Script", "Word-for-word spoken script for the project demo and oral viva introduction"),
        ("15. 30 Viva Questions & Simple Answers", "Categorized defense questions: Concepts, ML/Algorithms, RF Physics, Architecture, Defense"),
        ("16. Quick Cheat Sheet (5-Minute Revision)", "Last-minute memory sheet with formulas, numbers, thresholds, and examiner trap questions"),
    ]

    toc_data = []
    for num_title, desc in toc_items:
        toc_data.append([
            Paragraph(f"<b>{num_title}</b>", tbl_cell_bold),
            Paragraph(desc, tbl_cell_style)
        ])

    toc_table = Table(toc_data, colWidths=[180, USABLE_WIDTH - 180])
    toc_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), HexColor("#FFFFFF")),
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [HexColor("#F8FAFC"), HexColor("#FFFFFF")]),
        ('INNERGRID', (0,0), (-1,-1), 0.5, HexColor("#E2E8F0")),
        ('BOX', (0,0), (-1,-1), 1, HexColor("#CBD5E1")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(toc_table)

    story.append(PageBreak())

    # =========================================================================
    # SECTION 1: WHAT IS OUR PROJECT?
    # =========================================================================
    story.append(Paragraph("1. WHAT IS OUR PROJECT?", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.8, color=HexColor("#1E3A8A"), spaceAfter=8))

    story.append(Paragraph("Project Title", h2_style))
    story.append(Paragraph("<b>AI-Based Wi-Fi Coverage Optimization and Dead-Zone Prediction System</b>", body_style))

    story.append(Paragraph("What Problem Are We Solving?", h2_style))
    story.append(Paragraph(
        "In large indoor environments like college engineering blocks, hostels, libraries, and hospitals, Wi-Fi connectivity is often unpredictable. Students or staff experience sudden disconnections, slow buffering, or dropped calls in specific corners, behind thick concrete pillars, or at the edges of hallways.<br/><br/>"
        "Normally, network administrators troubleshoot this by either:<br/>"
        "1. Waiting for people to file complaints.<br/>"
        "2. Walking around blindly with a phone speed test.<br/>"
        "3. Guessing where to install an extra Access Point (AP), which frequently causes signal interference or leaves the actual dead zone unaddressed.",
        body_style
    ))

    story.append(Paragraph("What is Our Solution?", h2_style))
    story.append(Paragraph(
        "We built an intelligent, full-stack software system that:<br/>"
        "• Models or maps indoor building floorplans.<br/>"
        "• Analyzes multi-parameter network quality (Signal RSSI, Ping Latency, Packet Loss, and Throughput).<br/>"
        "• Automatically groups clustered poor spots into distinct, bounded <b>Dead Zones</b> using spatial machine learning.<br/>"
        "• Diagnoses the physical root causes (e.g., wall attenuation vs distance vs interference).<br/>"
        "• Uses a trained <b>Machine Learning classifier</b> to predict potential dead zones in areas that haven't even been measured yet.<br/>"
        "• Intelligently recommends the best placement coordinates for new Access Points to eliminate dead zones.<br/>"
        "• Mathematically verifies the improvement by providing a side-by-side <b>Before vs After</b> evaluation.",
        body_style
    ))

    story.append(Paragraph("What Does the Software Actually Do?", h2_style))
    story.append(Paragraph(
        "The software operates in two distinct operational modes:<br/>"
        "1. <b>Simulation Mode</b>: Uses indoor radio-frequency (RF) wave propagation physics (the COST-231 multi-wall model) to simulate how radio waves pass through concrete walls, drywall, and glass partitions across a 100m × 60m campus building floor.<br/>"
        "2. <b>Real College Survey Mode</b>: Turns any standard Windows laptop into an active survey device. A student walks around their real college campus, points to where they are on the digital floorplan, and the system extracts real hardware Wi-Fi telemetry and gateway round-trip latency.",
        body_style
    ))

    story.append(Paragraph("What is the Main Novelty?", h2_style))
    story.append(Paragraph(
        "Most commercial tools (like NetSpot or Ekahau) only draw passive, colorful heatmaps of signal strength.<br/>"
        "Our project is novel because:<br/>"
        "1. <b>Multi-Parameter Detection</b>: It defines a dead zone not just by weak signal (dBm), but by the combination of high latency (> 120 ms), packet loss (> 15%), and dropped throughput (< 5 Mbps).<br/>"
        "2. <b>DBSCAN Spatial Clustering</b>: It separates isolated temporary glitches from genuine physical dead zones with polygon boundaries and m² area measurements.<br/>"
        "3. <b>Predictive Machine Learning</b>: It uses Random Forest to extrapolate and predict dead-zone risk in unmeasured grid coordinates.<br/>"
        "4. <b>Closed-Loop Optimization</b>: It doesn't just show problems; it provides recommended AP coordinates and verifies the dead-zone reduction percentage.",
        body_style
    ))

    # Core workflow diagram
    cw_steps = [
        ("1", "DETECT", "Multi-parameter\nDBSCAN clusters"),
        ("2", "UNDERSTAND", "Diagnose wall loss\n& physical distance"),
        ("3", "PREDICT", "Random Forest ML\nRisk probability"),
        ("4", "OPTIMIZE", "Centroid candidate\nAP placement"),
        ("5", "VERIFY", "Before vs After\nArea reduction %")
    ]
    story.append(Spacer(1, 4))
    story.append(create_horizontal_pipeline_diagram("THE CORE OPERATIONAL WORKFLOW PIPELINE", cw_steps, [
        HexColor("#DC2626"), HexColor("#D97706"), HexColor("#7C3AED"), HexColor("#0284C7"), HexColor("#16A34A")
    ]))
    story.append(Spacer(1, 8))

    # =========================================================================
    # SECTION 2: TECHNOLOGIES USED
    # =========================================================================
    story.append(Paragraph("2. TECHNOLOGIES USED & WHY WE CHOSE THEM", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.8, color=HexColor("#1E3A8A"), spaceAfter=8))

    tech_rows = [
        [Paragraph("<b>Technology</b>", tbl_head_style), Paragraph("<b>Layer</b>", tbl_head_style), Paragraph("<b>Why We Used It (Student Justification)</b>", tbl_head_style)],
        [Paragraph("<b>Python 3.11</b>", tbl_cell_bold), Paragraph("Backend Language", tbl_cell_style), Paragraph("Standard language for data science, networking scripts, and ML modeling. Clean syntax and extensive library support.", tbl_cell_style)],
        [Paragraph("<b>FastAPI</b>", tbl_cell_bold), Paragraph("Backend Web Framework", tbl_cell_style), Paragraph("Extremely fast, modern Python asynchronous API framework. Auto-generates interactive Swagger documentation (/docs) and uses Pydantic for strict request validation.", tbl_cell_style)],
        [Paragraph("<b>SQLite + SQLAlchemy</b>", tbl_cell_bold), Paragraph("Database & ORM", tbl_cell_style), Paragraph("Lightweight, zero-configuration relational database. Perfect for local deployment on a laptop without needing complex PostgreSQL/MySQL background daemons. SQLAlchemy handles object-relational mapping cleanly.", tbl_cell_style)],
        [Paragraph("<b>Scikit-learn</b>", tbl_cell_bold), Paragraph("Machine Learning Engine", tbl_cell_style), Paragraph("Industry-standard ML library. We use its RandomForestClassifier for dead-zone prediction and DBSCAN for unsupervised spatial clustering.", tbl_cell_style)],
        [Paragraph("<b>NumPy & Pandas</b>", tbl_cell_bold), Paragraph("Data Processing", tbl_cell_style), Paragraph("Vectorized array operations for distance calculation, grid coordinates, and data frame manipulation.", tbl_cell_style)],
        [Paragraph("<b>SciPy (Spatial)</b>", tbl_cell_bold), Paragraph("Computational Geometry", tbl_cell_style), Paragraph("Computes the 2D Convex Hull polygon boundaries around dead zones and calculates exact affected floor areas (m²).", tbl_cell_style)],
        [Paragraph("<b>React 19 & TypeScript</b>", tbl_cell_bold), Paragraph("Frontend UI Framework", tbl_cell_style), Paragraph("Component-based, reactive user interface with strict compile-time type safety. Ensures no null reference crashes when switching between survey points and simulated data.", tbl_cell_style)],
        [Paragraph("<b>Vite</b>", tbl_cell_bold), Paragraph("Frontend Build Tool", tbl_cell_style), Paragraph("Ultra-fast development server with instant Hot Module Replacement (HMR) and optimized static asset bundling.", tbl_cell_style)],
        [Paragraph("<b>Tailwind CSS</b>", tbl_cell_bold), Paragraph("Styling", tbl_cell_style), Paragraph("Utility-first CSS framework providing a clean, responsive, dark-mode modern dashboard UI.", tbl_cell_style)],
        [Paragraph("<b>Lucide React</b>", tbl_cell_bold), Paragraph("Icons", tbl_cell_style), Paragraph("Crisp, lightweight icons for APs, signals, alerts, metrics, and navigation.", tbl_cell_style)],
        [Paragraph("<b>Interactive SVG / Canvas</b>", tbl_cell_bold), Paragraph("Floorplan Rendering", tbl_cell_style), Paragraph("Vector rendering allows smooth zooming, real-time AP dragging, clickable pin drops, and color-coded measurement overlays without blurry pixels.", tbl_cell_style)],
        [Paragraph("<b>Windows Native netsh & ping</b>", tbl_cell_bold), Paragraph("Hardware Survey Collector", tbl_cell_style), Paragraph("Reads real Wi-Fi adapter hardware info (SSID, BSSID, RSSI, channel, link speed) and gateway round-trip latency without requiring third-party drivers or paid APIs.", tbl_cell_style)],
        [Paragraph("<b>Pytest</b>", tbl_cell_bold), Paragraph("Testing Suite", tbl_cell_style), Paragraph("Automated backend test framework with 21 unit and integration tests verifying API routes, physics math, DBSCAN clustering, and survey parsing.", tbl_cell_style)],
    ]

    t_tech = Table(tech_rows, colWidths=[110, 110, USABLE_WIDTH - 220])
    t_tech.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), HexColor("#1E3A8A")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [HexColor("#F8FAFC"), HexColor("#FFFFFF")]),
        ('GRID', (0,0), (-1,-1), 0.5, HexColor("#CBD5E1")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_tech)
    story.append(Spacer(1, 10))

    # =========================================================================
    # SECTION 3: HOW THE PROJECT WORKS
    # =========================================================================
    story.append(Paragraph("3. HOW THE PROJECT WORKS (HIGH-LEVEL ARCHITECTURE)", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.8, color=HexColor("#1E3A8A"), spaceAfter=8))

    story.append(Paragraph("The system follows a clean client-server architecture:", body_style))
    story.append(Spacer(1, 4))
    story.append(create_system_architecture_diagram())
    story.append(Spacer(1, 8))

    story.append(Paragraph("The 7 Operational Execution Steps:", h2_style))
    steps_list = [
        "<b>1. Floorplan Initialization:</b> A 2D representation of a campus floor is loaded with walls (concrete, drywall, glass) and Access Point locations.",
        "<b>2. Data Acquisition:</b> In Simulation Mode, the physics engine computes signal drop and network metrics at every grid coordinate. In Real Survey Mode, the user clicks a room on the floorplan, and the laptop samples live Wi-Fi signal and gateway latency.",
        "<b>3. Quality Evaluation:</b> Every measurement is evaluated against performance thresholds for RSSI, latency, packet loss, and throughput.",
        "<b>4. Dead-Zone Clustering (DBSCAN):</b> Poor points are clustered spatially. Isolated glitches are discarded as noise. Concentrated clusters become labeled <b>Dead Zones</b> with computed boundary polygons and area in m².",
        "<b>5. Root-Cause Diagnosis:</b> The system analyzes why each dead zone exists (e.g., 'Wall attenuation: 28 dB loss' or 'Excessive distance: 32 meters').",
        "<b>6. ML Extrapolation:</b> A Random Forest classifier predicts whether unmeasured areas are at risk of becoming dead zones.",
        "<b>7. AP Optimization & Verification:</b> The optimizer simulates candidate AP locations at dead-zone centroids, selects the best placement, and generates a Before vs After verification report."
    ]
    for s in steps_list:
        story.append(Paragraph(s, bullet_style))
    story.append(Spacer(1, 10))

    # =========================================================================
    # SECTION 4: SIMULATION MODE
    # =========================================================================
    story.append(Paragraph("4. SIMULATION MODE (VIRTUAL RF PHYSICS ENGINE)", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.8, color=HexColor("#1E3A8A"), spaceAfter=8))

    sim_steps = [
        ("1", "Floor & Walls", "Multi-partition layout\n100m x 60m campus"),
        ("2", "Grid Generation", "Virtual measurement points\nspaced 2m-3m apart"),
        ("3", "COST-231 Physics", "Ray-trace wall loss\nDistance path loss"),
        ("4", "Correlate Metrics", "Loss, Latency & Tput\nShadowing noise"),
        ("5", "Save to DB", "Simulation run records\nwith quality tags")
    ]
    story.append(create_horizontal_pipeline_diagram("SIMULATION ENGINE WORKFLOW", sim_steps, [
        HexColor("#0284C7"), HexColor("#0369A1"), HexColor("#075985"), HexColor("#0C4A6E"), HexColor("#082F49")
    ]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("What Data is Generated?", h2_style))
    story.append(Paragraph(
        "In Simulation Mode, the system generates a grid of virtual measurement points across the floor (e.g., spaced every 2 to 3 meters). For each point (x, y), it records:<br/>"
        "• <b>RSSI</b> (Received Signal Strength Indicator in dBm)<br/>"
        "• <b>Ping Latency</b> (round-trip time in milliseconds)<br/>"
        "• <b>Packet Loss</b> (percentage of dropped packets, 0–100%)<br/>"
        "• <b>Throughput</b> (estimated bandwidth in Mbps)<br/>"
        "• <b>Quality Category</b> (GOOD, MODERATE, or POOR)<br/>"
        "• <b>Distance to Nearest AP</b> (in meters)<br/>"
        "• <b>Wall Attenuation Factor</b> (cumulative dB loss through intersected walls)",
        body_style
    ))

    story.append(Paragraph("How is the Physics Modeled? (The Math)", h2_style))
    story.append(Paragraph(
        "We implemented the <b>Multi-Wall COST-231 Indoor Propagation Model</b> (also aligned with ITU-R P.1238):<br/><br/>"
        "<b>PL(d) = PL(d₀) + 10 · n · log₁₀(d / d₀) + ∑ WAFᵢ + X_σ</b><br/><br/>"
        "Where:<br/>"
        "• <b>PL(d)</b> is the total path loss at distance d.<br/>"
        "• <b>PL(d₀)</b> is the reference path loss at 1 meter (set to 40 dB for 2.4 GHz).<br/>"
        "• <b>n</b> is the indoor path loss exponent (set to 3.0 for multi-partition office/academic environments).<br/>"
        "• <b>d</b> is Euclidean distance: √((x - x_AP)² + (y - y_AP)²).<br/>"
        "• <b>∑ WAFᵢ</b> is the Wall Attenuation Factor: the cumulative loss of all walls directly intersecting the straight-line ray from the AP to the receiver:<br/>"
        "  - <b>Concrete Wall</b>: 12 dB to 15 dB loss<br/>"
        "  - <b>Drywall / Brick</b>: 6 dB to 8 dB loss<br/>"
        "  - <b>Glass Partition</b>: 2 dB to 3 dB loss<br/>"
        "• <b>X_σ</b> is log-normal shadowing noise: a Gaussian random variable N(0, σ²) representing unpredictable multi-path fading (σ = 1.8 dB).<br/><br/>"
        "Finally, received signal is:<br/>"
        "<b>RSSI = P_tx - PL(d)</b> (where P_tx is AP transmit power, typically +20 dBm / 100 mW).",
        body_style
    ))

    story.append(Paragraph("Correlated Network Performance Metrics", h2_style))
    story.append(Paragraph(
        "Signal strength directly dictates network performance. We model this physical relationship realistically:<br/>"
        "• <b>Good Signal (RSSI ≥ -65 dBm)</b>: Low latency (10–25 ms), negligible packet loss (0–1%), high throughput (100–250 Mbps).<br/>"
        "• <b>Moderate Signal (-65 dBm > RSSI ≥ -78 dBm)</b>: Moderate latency (35–80 ms), minor packet loss (2–6%), usable throughput (30–75 Mbps).<br/>"
        "• <b>Poor Signal (RSSI < -78 dBm)</b>: Wi-Fi adapter drops to basic modulation schemes (BPSK), retransmissions spike. Latency jumps to 120–400 ms, packet loss climbs to 15–50%, throughput collapses below 5 Mbps.",
        body_style
    ))

    story.append(Paragraph("Why is this Called 'Simulated Data'?", h2_style))
    story.append(Paragraph(
        "Because no physical radio antennas are being measured during this mode. The data is generated purely mathematically inside Python using established RF physics equations and 2D ray-intersection geometry. This allows testing building layouts before physical construction or deployment.",
        body_style
    ))
    story.append(Spacer(1, 10))

    # =========================================================================
    # SECTION 5: REAL COLLEGE SURVEY MODE
    # =========================================================================
    story.append(Paragraph("5. REAL COLLEGE SURVEY MODE (LAPTOP TELEMETRY)", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.8, color=HexColor("#1E3A8A"), spaceAfter=8))

    surv_steps = [
        ("1", "Walk Spot", "Carry laptop to campus\nphysical location"),
        ("2", "Click Pin", "User marks exact spot\non digital floorplan"),
        ("3", "Run Telemetry", "Execute netsh wlan &\nping local gateway"),
        ("4", "Score Quality", "GOOD, MODERATE, POOR\ncomposite evaluation"),
        ("5", "Save / CSV", "Persistent SQLite record\nExportable to CSV")
    ]
    story.append(create_horizontal_pipeline_diagram("REAL SURVEY TELEMETRY WORKFLOW", surv_steps, [
        HexColor("#0D9488"), HexColor("#0F766E"), HexColor("#115E59"), HexColor("#134E4A"), HexColor("#042F2E")
    ]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("How Does the Laptop Collect Real Wi-Fi Info?", h2_style))
    story.append(Paragraph(
        "In Real College Survey Mode, the Python backend executes native Windows operating system commands directly on the user's laptop:<br/><br/>"
        "1. <b>Wi-Fi Telemetry via netsh</b>:<br/>"
        "The backend executes: <code>netsh wlan show interfaces</code> and parses the output using regular expressions (re).<br/><br/>"
        "2. <b>Network Latency & Packet Loss via ping</b>:<br/>"
        "The backend automatically identifies the laptop's local default IPv4 gateway (the Wi-Fi router IP, e.g., 192.168.1.1 or 172.20.10.1) using PowerShell (<code>Get-NetRoute</code>) or <code>ipconfig</code>. It then sends 3 ICMP echo requests: <code>ping -n 3 -w 1000 &lt;GATEWAY_IP&gt;</code>.",
        body_style
    ))

    # Gateway callout box
    gw_callout = [
        [Paragraph(
            "<b>Key Viva Defense Point: Why Ping the Local Gateway Instead of Google (8.8.8.8)?</b><br/>"
            "If you ping <code>google.com</code> or <code>8.8.8.8</code>, your latency includes the college ISP fiber line, external internet congestion, and DNS resolution. Pinging the <b>local default gateway</b> isolates the <b>first-hop wireless link</b>, measuring purely the laptop-to-AP radio performance!",
            callout_style
        )]
    ]
    t_gw = Table(gw_callout, colWidths=[USABLE_WIDTH])
    t_gw.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), HexColor("#EFF6FF")),
        ('BOX', (0,0), (-1,-1), 1, HexColor("#3B82F6")),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(t_gw)
    story.append(Spacer(1, 6))

    story.append(Paragraph("What Information is Collected?", h2_style))
    story.append(Paragraph(
        "• <b>SSID</b>: Service Set Identifier (network name, e.g., Campus_WiFi_5G).<br/>"
        "• <b>BSSID</b>: Physical MAC address of the specific Access Point radio the laptop is connected to (e.g., a2:a4:e4:13:06:a7).<br/>"
        "• <b>Radio Standard</b>: E.g., 802.11ac (Wi-Fi 5) or 802.11ax (Wi-Fi 6).<br/>"
        "• <b>Band & Channel</b>: E.g., 5 GHz, Channel 149.<br/>"
        "• <b>Signal Percentage</b>: 0% to 100% reported by the Windows WLAN API.<br/>"
        "• <b>RSSI (dBm)</b>: Hardware RSSI if exposed by the driver, or calculated via standard Microsoft formula.<br/>"
        "• <b>Link Speed</b>: Current physical modulation rate (e.g., 866 Mbps or 1201 Mbps).<br/>"
        "• <b>Gateway Round-Trip Latency</b>: Average ping time in milliseconds.<br/>"
        "• <b>Packet Loss</b>: Percentage of dropped packets (0%, 33%, 66%, or 100%).<br/>"
        "• <b>Timestamp</b>: Exact UTC capture time.<br/>"
        "• <b>Floorplan Coordinates</b>: User-selected (x, y) position in meters.",
        body_style
    ))

    story.append(Paragraph("How Does the User Select Location on the Floorplan?", h2_style))
    story.append(Paragraph(
        "1. The student walks to a physical spot on their campus (e.g., 'Library Room 102, back desk').<br/>"
        "2. On the Real Survey page, the student looks at the digital floorplan and clicks that exact spot.<br/>"
        "3. The UI places a visual <b>Target Pin</b> (crosshair indicator) and shows the exact coordinates: X = 14.5 m, Y = 8.2 m.<br/>"
        "4. (Optional) The student can also click quick-pick room chips like [Room 101] or [Auditorium] to auto-position the pin.<br/>"
        "5. The student clicks <b>'Capture Measurement at Pin'</b>.",
        body_style
    ))

    story.append(Paragraph("Real vs Estimated Values (Honest Technical Transparency)", h2_style))
    real_est_rows = [
        [Paragraph("<b>Metric</b>", tbl_head_style), Paragraph("<b>Source</b>", tbl_head_style), Paragraph("<b>Real Hardware or Derived?</b>", tbl_head_style)],
        [Paragraph("<b>SSID & BSSID</b>", tbl_cell_bold), Paragraph("Windows netsh wlan show interfaces", tbl_cell_style), Paragraph("<b>100% Real Hardware Telemetry</b>", tbl_cell_style)],
        [Paragraph("<b>Radio Type, Band, Channel</b>", tbl_cell_bold), Paragraph("Windows netsh wlan show interfaces", tbl_cell_style), Paragraph("<b>100% Real Hardware Telemetry</b>", tbl_cell_style)],
        [Paragraph("<b>Signal %</b>", tbl_cell_bold), Paragraph("Windows netsh wlan show interfaces", tbl_cell_style), Paragraph("<b>100% Real Hardware Telemetry</b>", tbl_cell_style)],
        [Paragraph("<b>Link Speed (Tx/Rx rate)</b>", tbl_cell_bold), Paragraph("Windows netsh wlan show interfaces", tbl_cell_style), Paragraph("<b>100% Real Hardware Telemetry</b>", tbl_cell_style)],
        [Paragraph("<b>Ping Latency & Packet Loss</b>", tbl_cell_bold), Paragraph("Native ICMP ping to default gateway", tbl_cell_style), Paragraph("<b>100% Real Network Telemetry</b>", tbl_cell_style)],
        [Paragraph("<b>RSSI (dBm)</b>", tbl_cell_bold), Paragraph("Hardware driver (if supported) OR formula (Signal% / 2) - 100", tbl_cell_style), Paragraph("Real if driver supports; clearly tagged with is_rssi_estimated: True/False", tbl_cell_style)],
        [Paragraph("<b>Throughput</b>", tbl_cell_bold), Paragraph("Derived from physical link speed (Rx/Tx)", tbl_cell_style), Paragraph("Estimated operational bandwidth (we do not run a full iperf saturating bandwidth)", tbl_cell_style)],
    ]
    t_re = Table(real_est_rows, colWidths=[130, 180, USABLE_WIDTH - 310])
    t_re.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), HexColor("#0D9488")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [HexColor("#F8FAFC"), HexColor("#FFFFFF")]),
        ('GRID', (0,0), (-1,-1), 0.5, HexColor("#CBD5E1")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_re)
    story.append(Spacer(1, 10))

    # =========================================================================
    # SECTION 6: DEAD-ZONE DETECTION
    # =========================================================================
    story.append(Paragraph("6. DEAD-ZONE DETECTION (DBSCAN CLUSTERING & SEVERITY)", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.8, color=HexColor("#1E3A8A"), spaceAfter=8))

    dz_steps = [
        ("1", "Filter Poor", "RSSI < -78dBm, Lat>120ms\nLoss>15%, Tput<5Mbps"),
        ("2", "DBSCAN Cluster", "Density-based grouping\neps=6-12m, min_samples=3"),
        ("3", "Discard Noise", "Isolated glitches (label -1)\nprevent false alarms"),
        ("4", "Convex Hull", "Graham scan 2D polygon\nShoelace area in m²"),
        ("5", "Severity Diagnosis", "Composite penalty score\nWall vs Distance causes")
    ]
    story.append(create_horizontal_pipeline_diagram("DEAD-ZONE DETECTION ENGINE PIPELINE", dz_steps, [
        HexColor("#DC2626"), HexColor("#B91C1C"), HexColor("#991B1B"), HexColor("#7F1D1D"), HexColor("#450A0A")
    ]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("What is a Wi-Fi Dead Zone?", h2_style))
    story.append(Paragraph(
        "A dead zone is not just a spot with low bars. In our system, a dead zone is defined as:<br/>"
        "<b>A continuous spatial region where network degradation prevents reliable communication, characterized by severe signal attenuation, excessive round-trip latency, high packet loss, or collapsed throughput.</b>",
        body_style
    ))

    story.append(Paragraph("Multi-Metric Poor Point Thresholds", h2_style))
    story.append(Paragraph(
        "A measurement point is flagged as <b>POOR</b> if it meets ANY of these conditions:<br/>"
        "1. <b>RSSI &lt; -78.0 dBm</b> (Signal too weak for stable QAM modulation)<br/>"
        "2. <b>Ping Latency &gt; 120.0 ms</b> (Excessive buffer delay / retries)<br/>"
        "3. <b>Packet Loss &gt; 15.0%</b> (Frequent TCP retransmissions & dropped connections)<br/>"
        "4. <b>Throughput &lt; 5.0 Mbps</b> (Insufficient bandwidth for video/voice)",
        body_style
    ))

    story.append(Paragraph("Spatial Clustering: Why DBSCAN?", h2_style))
    story.append(Paragraph(
        "We use <b>DBSCAN</b> (<i>Density-Based Spatial Clustering of Applications with Noise</i>):<br/>"
        "• <b>eps (epsilon)</b> = 6.0 to 12.0 meters (maximum distance between neighbor points)<br/>"
        "• <b>min_samples</b> = 3 points (minimum points to constitute a real dead zone)<br/><br/>"
        "<b>Why DBSCAN instead of K-Means?</b><br/>"
        "1. <b>We don't know the number of clusters in advance</b>: K-Means requires specifying K (e.g., K = 3). In a building, we have no idea whether there are 0, 2, or 5 dead zones. DBSCAN discovers the number of clusters automatically.<br/>"
        "2. <b>Arbitrary shapes</b>: Dead zones follow corridors or odd room corners. K-Means assumes spherical clusters; DBSCAN can find any arbitrary shape.<br/>"
        "3. <b>Noise Handling</b>: If a single measurement drops due to someone walking by, DBSCAN labels it as <b>noise</b> (label -1) and discards it! <b>A single bad measurement never creates a false dead zone.</b>",
        body_style
    ))

    story.append(Paragraph("How Does a Cluster Become a Dead-Zone Area?", h2_style))
    story.append(Paragraph(
        "When DBSCAN identifies a cluster of ≥ 3 poor points:<br/>"
        "1. <b>Centroid</b>: Computes (x̄, ȳ) average center coordinate.<br/>"
        "2. <b>Convex Hull Boundary</b>: Runs the Graham scan 2D convex hull algorithm to form a closed polygon around the perimeter points.<br/>"
        "3. <b>Area Calculation (m²)</b>: Applies the Shoelace formula on the polygon vertices: Area = ½ |∑ (xᵢ yᵢ₊₁ - xᵢ₊₁ yᵢ) + (xₙ y₁ - x₁ yₙ)|, bounded by grid cell coverage (N_points × 4 m²).<br/>"
        "4. <b>Severity Scoring</b>: Computes a multi-metric composite penalty score (0–100):<br/>"
        "   - ≥ 75 → <b>CRITICAL</b><br/>"
        "   - 52 - 74 → <b>HIGH</b><br/>"
        "   - 32 - 51 → <b>MEDIUM</b><br/>"
        "   - &lt; 32 → <b>LOW</b><br/>"
        "5. <b>Contributing Factor Diagnosis</b>: The system inspects average wall loss, distance, and packet loss to output human-readable causes (e.g., <i>'Severe wall attenuation: 24.0 dB loss through multiple concrete partitions'</i>).",
        body_style
    ))
    story.append(Spacer(1, 10))

    # =========================================================================
    # SECTION 7: DEAD-ZONE PREDICTION (ML)
    # =========================================================================
    story.append(Paragraph("7. DEAD-ZONE PREDICTION (RANDOM FOREST MACHINE LEARNING)", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.8, color=HexColor("#1E3A8A"), spaceAfter=8))

    ml_steps = [
        ("1", "Training Corpus", "Physics COST-231 corpus\n+ historical DB records"),
        ("2", "Feature Vector", "7 spatial & RF features\nBalanced class weights"),
        ("3", "Random Forest", "100 Decision Trees\nMax Depth = 12"),
        ("4", "Evaluation", "Accuracy (~89%), Precision,\nRecall, F1 & Confusion Matrix"),
        ("5", "Risk Inference", "Predicts unmeasured points\nSpatial risk probability map")
    ]
    story.append(create_horizontal_pipeline_diagram("MACHINE LEARNING PREDICTION PIPELINE", ml_steps, [
        HexColor("#7C3AED"), HexColor("#6D28D9"), HexColor("#5B21B6"), HexColor("#4C1D95"), HexColor("#2E1065")
    ]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("What Model is Used & Why?", h2_style))
    story.append(Paragraph(
        "We use a <b>Random Forest Classifier</b> (<code>RandomForestClassifier</code> from Scikit-learn):<br/>"
        "• <b>Ensemble Size</b>: 100 decision trees (<code>n_estimators = 100</code>)<br/>"
        "• <b>Max Depth</b>: 12 levels (<code>max_depth = 12</code>)<br/>"
        "• <b>Class Weighting</b>: Balanced (<code>class_weight = 'balanced'</code>) to handle class imbalance between normal areas and dead zones.<br/><br/>"
        "<b>Why Random Forest?</b><br/>"
        "1. <b>Non-linear Relationships</b>: Wi-Fi propagation and obstacle penetration are non-linear; decision trees model threshold cutoffs naturally.<br/>"
        "2. <b>Robust Against Overfitting</b>: Combining 100 randomized trees via bagging prevents the model from overfitting to isolated noise.<br/>"
        "3. <b>Feature Importance</b>: Random Forest automatically tells us <i>which</i> network features had the biggest influence on predicting dead zones.<br/>"
        "4. <b>Fast Inference</b>: Can predict hundreds of unmeasured spatial grid points in under 50 milliseconds.",
        body_style
    ))

    story.append(Paragraph("Input Features & Target Label", h2_style))
    feat_rows = [
        [Paragraph("<b>Feature Name</b>", tbl_head_style), Paragraph("<b>Description</b>", tbl_head_style)],
        [Paragraph("<b>rssi</b>", tbl_cell_bold), Paragraph("Signal strength in dBm", tbl_cell_style)],
        [Paragraph("<b>latency</b>", tbl_cell_bold), Paragraph("Ping latency in milliseconds", tbl_cell_style)],
        [Paragraph("<b>packet_loss</b>", tbl_cell_bold), Paragraph("Packet loss percentage (0-100%)", tbl_cell_style)],
        [Paragraph("<b>throughput</b>", tbl_cell_bold), Paragraph("Estimated or measured data rate in Mbps", tbl_cell_style)],
        [Paragraph("<b>distance_to_ap</b>", tbl_cell_bold), Paragraph("Distance to closest operational AP in meters", tbl_cell_style)],
        [Paragraph("<b>wall_factor</b>", tbl_cell_bold), Paragraph("Cumulative wall attenuation along line-of-sight (dB)", tbl_cell_style)],
        [Paragraph("<b>ap_density</b>", tbl_cell_bold), Paragraph("Count of operational APs within a 25-meter radius", tbl_cell_style)],
    ]
    t_feat = Table(feat_rows, colWidths=[150, USABLE_WIDTH - 150])
    t_feat.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), HexColor("#7C3AED")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [HexColor("#F8FAFC"), HexColor("#FFFFFF")]),
        ('GRID', (0,0), (-1,-1), 0.5, HexColor("#CBD5E1")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_feat)
    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>Target Label (dead_zone_risk):</b> <code>0</code>: NOT_DEAD_ZONE (Healthy area), <code>1</code>: POTENTIAL_DEAD_ZONE (High-risk weak area).", body_style))

    story.append(Paragraph("Evaluation Metrics Explained in Plain English", h2_style))
    story.append(Paragraph(
        "• <b>Accuracy ((TP + TN) / Total)</b>: Overall percentage of correct predictions across all test points (typically <b>~88%–92%</b>).<br/>"
        "• <b>Precision (TP / (TP + FP))</b>: <i>'When the model predicts an area is a dead zone, how often is it actually right?'</i> (Prevents wasting money installing APs where signal is actually fine).<br/>"
        "• <b>Recall (TP / (TP + FN))</b>: <i>'Out of all real dead zones in the building, how many did the model catch?'</i> (High recall ensures no dead zones are missed).<br/>"
        "• <b>F1-Score (2 · Precision · Recall / (Precision + Recall))</b>: Harmonic mean of precision and recall. Best single metric for balanced performance.<br/>"
        "• <b>Confusion Matrix</b>: A 2 × 2 grid showing exact counts of TP, FP, FN, and TN.<br/>"
        "• <b>Feature Importance</b>: Ranked percentages showing what mattered most (e.g., <code>rssi</code> ~38%, <code>distance_to_ap</code> ~24%, <code>wall_factor</code> ~18%).",
        body_style
    ))
    story.append(Spacer(1, 10))

    # =========================================================================
    # SECTION 8: AP PLACEMENT OPTIMIZATION
    # =========================================================================
    story.append(Paragraph("8. AP PLACEMENT OPTIMIZATION & BEFORE-VS-AFTER VERIFICATION", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.8, color=HexColor("#1E3A8A"), spaceAfter=8))

    story.append(Paragraph("How Does the System Suggest New AP Locations?", h2_style))
    story.append(Paragraph(
        "When dead zones are detected, the optimizer doesn't just guess a random spot:<br/>"
        "1. <b>Candidate Generation</b>:<br/>"
        "   - Primary candidate: The exact centroid (x̄, ȳ) of each detected dead-zone polygon.<br/>"
        "   - Secondary candidate: Centroids of affected rooms containing dead zones.<br/>"
        "   - Minimum separation constraint: Ensures candidates are at least 12 meters away from existing APs to prevent co-channel interference.<br/>"
        "2. <b>Physics Re-Simulation</b>:<br/>"
        "   The engine virtually adds each candidate AP (at +20 dBm transmit power) to the floor's AP list and re-runs the RF path loss calculation across the entire floor.<br/>"
        "3. <b>Ranking by Impact</b>:<br/>"
        "   Candidates are ranked by:<br/>"
        "   - <b>Dead-Zone Area Reduction (m²)</b>: How much dead-zone space is wiped out.<br/>"
        "   - <b>Coverage Improvement (%)</b>: Floor area brought above -75 dBm.<br/>"
        "4. <b>Before vs After Verification</b>:<br/>"
        "   The system calculates the exact delta: <b>Dead Zone Reduction % = ((Area_before - Area_after) / Area_before) × 100</b>",
        body_style
    ))

    story.append(Spacer(1, 4))
    story.append(create_before_after_diagram())
    story.append(Spacer(1, 10))

    # =========================================================================
    # SECTION 9: COMPLETE STEP-BY-STEP WORKFLOWS
    # =========================================================================
    story.append(Paragraph("9. COMPLETE STEP-BY-STEP WORKFLOWS", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.8, color=HexColor("#1E3A8A"), spaceAfter=8))

    story.append(Paragraph("Workflow A: Simulation Mode (Demo Walkthrough)", h2_style))
    wf_a = [
        "1. Navigate to <b>Simulation</b> page.",
        "2. Click <b>'Load Default Virtual Environment'</b> (creates 100m × 60m campus floor with 8 rooms, 3 active APs, and multiple walls).",
        "3. Click <b>'Run Full Wi-Fi Simulation'</b> (calculates signal & network metrics across 100+ grid points).",
        "4. Navigate to <b>Dead-Zone Analysis</b> page.",
        "5. Click <b>'Run Dead-Zone Detection'</b> (DBSCAN clusters weak points, draws red convex hulls, displays severity & factors).",
        "6. Navigate to <b>Dead-Zone Prediction</b> page.",
        "7. Click <b>'Train Random Forest Model'</b> (trains on dataset, displays Accuracy, Precision, Recall, Confusion Matrix).",
        "8. Click <b>'Run Spatial Grid Prediction'</b> (evaluates all unmeasured floor coordinates and overlays orange risk markers).",
        "9. Navigate to <b>AP Optimization</b> page.",
        "10. Click <b>'Generate AP Recommendations'</b> (suggests optimal placement coords).",
        "11. Navigate to <b>Before vs After</b> page to inspect the comparative reduction metrics and side-by-side floorplans."
    ]
    for s in wf_a:
        story.append(Paragraph(s, bullet_style))

    story.append(Spacer(1, 4))
    story.append(Paragraph("Workflow B: Real College Survey Mode (Walk-Through with Laptop)", h2_style))
    wf_b = [
        "1. Open the application on your laptop (connected to your college Wi-Fi).",
        "2. Navigate to <b>Real College Survey</b> page.",
        "3. Select the building floor (e.g., Engineering Block - Floor 1).",
        "4. Walk to a physical location inside the building (e.g., Room 104).",
        "5. Click that spot on the digital floorplan (Target Pin appears with coordinates).",
        "6. Click <b>'Capture Measurement at Pin'</b>.",
        "7. The system queries netsh and pings the default gateway. A green notification confirms capture: <i>Captured at (35.0, 18.0) | SSID: Campus_WiFi | Signal: 68% | Latency: 22ms</i>",
        "8. Walk to 10–15 different spots across the floor (including rooms, hallways, and corners) and repeat.",
        "9. Click <b>'Export Survey Data as CSV'</b> to save your physical survey dataset.",
        "10. Click <b>'Analyze Survey Dead Zones'</b> to run DBSCAN and ML on your real-world measurements!"
    ]
    for s in wf_b:
        story.append(Paragraph(s, bullet_style))
    story.append(Spacer(1, 10))

    # =========================================================================
    # SECTION 10: BUTTON-BY-BUTTON UI GUIDE
    # =========================================================================
    story.append(Paragraph("10. BUTTON-BY-BUTTON UI GUIDE ('WHAT HAPPENS WHEN I CLICK?')", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.8, color=HexColor("#1E3A8A"), spaceAfter=8))

    btn_rows = [
        [Paragraph("<b>Page</b>", tbl_head_style), Paragraph("<b>Button Label</b>", tbl_head_style), Paragraph("<b>Internal Backend Action</b>", tbl_head_style), Paragraph("<b>Visual Result on Screen</b>", tbl_head_style)],
        [Paragraph("<b>Simulation</b>", tbl_cell_bold), Paragraph("Load Default Virtual Environment", tbl_cell_style), Paragraph("POST /api/simulation/reset-demo", tbl_cell_style), Paragraph("Wipes previous data and loads standard campus building with rooms, walls, and 3 APs.", tbl_cell_style)],
        [Paragraph("<b>Simulation</b>", tbl_cell_bold), Paragraph("Run Full Wi-Fi Simulation", tbl_cell_style), Paragraph("POST /api/simulation/run", tbl_cell_style), Paragraph("Floorplan fills with color-coded circles (Green = Good, Yellow = Moderate, Red = Poor).", tbl_cell_style)],
        [Paragraph("<b>Dead-Zone Analysis</b>", tbl_cell_bold), Paragraph("Detect Dead Zones", tbl_cell_style), Paragraph("POST /api/dead-zones/detect", tbl_cell_style), Paragraph("Outlines red dead-zone polygons on floorplan with labels (DZ-1, DZ-2) and severity badges.", tbl_cell_style)],
        [Paragraph("<b>Dead-Zone Prediction</b>", tbl_cell_bold), Paragraph("Train Prediction Model", tbl_cell_style), Paragraph("POST /api/ml/train", tbl_cell_style), Paragraph("Displays Accuracy, Precision, Recall, F1 cards, Confusion Matrix table, and Feature Importance bar chart.", tbl_cell_style)],
        [Paragraph("<b>Dead-Zone Prediction</b>", tbl_cell_bold), Paragraph("Predict Unmeasured Grid", tbl_cell_style), Paragraph("POST /api/ml/predict-floor", tbl_cell_style), Paragraph("Overlays orange warning dots on high-risk unmeasured zones.", tbl_cell_style)],
        [Paragraph("<b>AP Optimization</b>", tbl_cell_bold), Paragraph("Generate Recommendations", tbl_cell_style), Paragraph("POST /api/optimizer/recommend", tbl_cell_style), Paragraph("Shows suggested AP coordinates (e.g., X=72.5m, Y=38.0m) with expected area reduction in m².", tbl_cell_style)],
        [Paragraph("<b>Before vs After</b>", tbl_cell_bold), Paragraph("Run Verification", tbl_cell_style), Paragraph("GET /api/optimizer/before-after", tbl_cell_style), Paragraph("Side-by-side floorplans; metric comparison cards showing dead zones reduced (e.g., 4 → 1) and % reduction.", tbl_cell_style)],
        [Paragraph("<b>Real Survey</b>", tbl_cell_bold), Paragraph("Click on Floorplan", tbl_cell_style), Paragraph("Client-side state update", tbl_cell_style), Paragraph("Crosshair pin appears on map; coordinate badge updates (e.g., X: 24.0m, Y: 12.5m).", tbl_cell_style)],
        [Paragraph("<b>Real Survey</b>", tbl_cell_bold), Paragraph("Capture Measurement", tbl_cell_style), Paragraph("POST /api/survey/measurements", tbl_cell_style), Paragraph("Measurement pin added to map; real metrics table updates; audio/visual confirmation banner appears.", tbl_cell_style)],
        [Paragraph("<b>Real Survey</b>", tbl_cell_bold), Paragraph("Export CSV", tbl_cell_style), Paragraph("Client-side CSV generation", tbl_cell_style), Paragraph("Downloads survey_measurements_floor_X.csv to user's computer.", tbl_cell_style)],
    ]
    t_btn = Table(btn_rows, colWidths=[85, 115, 140, USABLE_WIDTH - 340])
    t_btn.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), HexColor("#1E3A8A")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [HexColor("#F8FAFC"), HexColor("#FFFFFF")]),
        ('GRID', (0,0), (-1,-1), 0.5, HexColor("#CBD5E1")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_btn)
    story.append(Spacer(1, 10))

    # =========================================================================
    # SECTION 11: TESTING & VERIFICATION SUITE
    # =========================================================================
    story.append(Paragraph("11. TESTING & VERIFICATION SUITE", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.8, color=HexColor("#1E3A8A"), spaceAfter=8))

    story.append(Paragraph("The project includes an automated test suite executed via Pytest: <code>cd backend &amp;&amp; pytest tests -v</code>", body_style))
    story.append(Paragraph("<b>Test Suite Summary: 21 Passed / 0 Failed (100% Pass Rate in 15.7s)</b>", body_bold))

    test_rows = [
        [Paragraph("<b>Test File</b>", tbl_head_style), Paragraph("<b>Count</b>", tbl_head_style), Paragraph("<b>What It Verifies (Ground Truth Assurance)</b>", tbl_head_style)],
        [Paragraph("<b>test_api.py</b>", tbl_cell_bold), Paragraph("6 tests", tbl_cell_style), Paragraph("Health check, API demo reset, dashboard summary, dead-zone analytics, ML metrics, alerts endpoint.", tbl_cell_style)],
        [Paragraph("<b>test_dead_zone_detection.py</b>", tbl_cell_bold), Paragraph("3 tests", tbl_cell_style), Paragraph("Multi-metric severity logic (LOW to CRITICAL), contributing factor diagnosis, DBSCAN spatial clustering.", tbl_cell_style)],
        [Paragraph("<b>test_ml_pipeline.py</b>", tbl_cell_bold), Paragraph("2 tests", tbl_cell_style), Paragraph("Synthetic corpus generation, Random Forest training, evaluation metrics generation, joblib persistence.", tbl_cell_style)],
        [Paragraph("<b>test_optimizer.py</b>", tbl_cell_bold), Paragraph("1 test", tbl_cell_style), Paragraph("AP recommendation candidate generation, dead-zone area reduction calculation, before-vs-after schema.", tbl_cell_style)],
        [Paragraph("<b>test_simulation.py</b>", tbl_cell_bold), Paragraph("4 tests", tbl_cell_style), Paragraph("RF physics path loss vs distance, wall attenuation loss, network metric correlation, geometry ray intersection.", tbl_cell_style)],
        [Paragraph("<b>test_survey.py</b>", tbl_cell_bold), Paragraph("5 tests", tbl_cell_style), Paragraph("Hardware RSSI parsing, signal percentage fallback formula, ping latency parsing, quality scoring, survey REST endpoints.", tbl_cell_style)],
    ]
    t_test = Table(test_rows, colWidths=[140, 60, USABLE_WIDTH - 200])
    t_test.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), HexColor("#1E3A8A")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [HexColor("#F8FAFC"), HexColor("#FFFFFF")]),
        ('GRID', (0,0), (-1,-1), 0.5, HexColor("#CBD5E1")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_test)
    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>Frontend Build Verification:</b> React/TypeScript compiles cleanly: <code>npm run build</code> → <b>built in 628ms (0 TypeScript errors)</b>.", body_style))
    story.append(Spacer(1, 10))

    # =========================================================================
    # SECTION 12: ACTUAL RESULTS & NUMBERS
    # =========================================================================
    story.append(Paragraph("12. ACTUAL RESULTS & VERIFICATION NUMBERS", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.8, color=HexColor("#1E3A8A"), spaceAfter=8))

    story.append(Paragraph(
        "<b>Critical Presentation Rule:</b> Never mix up simulated results and real laptop numbers. Always present them with their clear, honest source labels.",
        ParagraphStyle("Alert", parent=body_style, fontName=FONT_BOLD, textColor=HexColor("#DC2626"))
    ))

    story.append(Paragraph("A. Simulated Environment Benchmark Results [SIMULATED]", h2_style))
    story.append(Paragraph(
        "• <b>Floor Dimensions</b>: 100 m × 60 m (6000 m² total floor space)<br/>"
        "• <b>Active Access Points</b>: 3 APs (Transmit Power +20 dBm)<br/>"
        "• <b>Total Simulated Measurement Points</b>: 100+ points on regular grid<br/>"
        "• <b>Dead Zones Detected (DBSCAN)</b>: <b>4 distinct dead zones</b><br/>"
        "  - <i>DZ-1 (Far Corner Office)</i>: Area 96 m², Avg RSSI -86.2 dBm, Severity: <b>CRITICAL</b> (Factor: Distance 34 m + Wall loss 24 dB)<br/>"
        "  - <i>DZ-2 (Storage Wing)</i>: Area 84 m², Avg RSSI -82.1 dBm, Severity: <b>HIGH</b> (Factor: Concrete partition loss 20 dB)<br/>"
        "  - <i>DZ-3 (East Corridor Nook)</i>: Area 64 m², Avg RSSI -79.5 dBm, Severity: <b>MEDIUM</b><br/>"
        "  - <i>DZ-4 (Conference Annex)</i>: Area 48 m², Avg RSSI -78.8 dBm, Severity: <b>LOW</b><br/>"
        "• <b>Total Dead-Zone Area Before Optimization</b>: <b>292.0 m²</b><br/>"
        "• <b>Recommended Candidate Placements</b>: 2 APs added<br/>"
        "• <b>Total Dead-Zone Area After Optimization</b>: <b>68.0 m²</b><br/>"
        "• <b>Dead-Zone Area Reduction</b>: <b>76.7% reduction</b> (224 m² restored to healthy coverage)<br/>"
        "• <b>ML Model Metrics (Random Forest)</b>: Accuracy: <b>~89.3%</b>, Precision: <b>~88.5%</b>, Recall: <b>~86.2%</b>, F1-Score: <b>~87.3%</b>",
        body_style
    ))

    story.append(Paragraph("B. Live Hardware Laptop Verification [REAL LAPTOP]", h2_style))
    story.append(Paragraph(
        "<i>(Verified on student's actual physical machine during hardware testing)</i><br/>"
        "• <b>Connected SSID</b>: Alifa’s iPhone (Hotspot Wi-Fi test)<br/>"
        "• <b>BSSID</b>: a2:a4:e4:13:06:a7<br/>"
        "• <b>Radio Standard</b>: 802.11ax (Wi-Fi 6)<br/>"
        "• <b>Band & Channel</b>: 5 GHz, Channel 149<br/>"
        "• <b>Signal Percentage</b>: 100%<br/>"
        "• <b>Hardware RSSI</b>: -29.0 dBm (is_rssi_estimated: False, reported directly by driver)<br/>"
        "• <b>Physical Link Speed</b>: 1201.0 Mbps (Rx Rate)<br/>"
        "• <b>Default Gateway IP</b>: 172.20.10.1 (automatically discovered via PowerShell Get-NetRoute)<br/>"
        "• <b>Gateway Round-Trip Ping Latency</b>: 9.0 ms (Average of 3 ICMP echo requests)<br/>"
        "• <b>Packet Loss</b>: 0.0%<br/>"
        "• <b>Quality Score</b>: 98.5 (<b>GOOD</b>)",
        body_style
    ))
    story.append(Spacer(1, 10))

    # =========================================================================
    # SECTION 13: HONEST ACADEMIC LIMITATIONS
    # =========================================================================
    story.append(Paragraph("13. HONEST ACADEMIC LIMITATIONS", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.8, color=HexColor("#1E3A8A"), spaceAfter=8))

    story.append(Paragraph("When examiners ask <i>'What are the limitations of your project?'</i>, give this honest, mature answer. It shows deep academic maturity:", body_style))

    lims = [
        "<b>1. User-Assisted Indoor Positioning:</b> GPS does not work reliably indoors due to satellite signal attenuation through roofs and concrete floors. True autonomous indoor positioning requires expensive Ultra-Wideband (UWB) anchors or Bluetooth Low Energy (BLE) beacon arrays. Our software uses <b>user-assisted positioning</b>: the user clicks their physical position on the digital map.",
        "<b>2. 2D Approximation vs 3D Multipath:</b> Our RF engine calculates wave propagation in a 2D floor plane. In real multi-story buildings, RF signals leak through ceilings/floors (inter-floor penetration) and bounce off metallic furniture (complex 3D multipath reflections).",
        "<b>3. No Heavy Bandwidth Flooding:</b> To measure real throughput, tools like iperf3 flood the network with maximum traffic, which would disrupt college classes or administrative work. Our system derives throughput from the physical modulation rate (link speed) or lightweight sampling rather than aggressive network saturation.",
        "<b>4. Platform-Specific Wi-Fi Parsing:</b> The Real Survey telemetry collector uses native Windows tools (netsh and powershell). To run on macOS or Linux, equivalent shell adapters (airport or iwconfig/nmcli) would be needed."
    ]
    for l in lims:
        story.append(Paragraph(l, bullet_style))
    story.append(Spacer(1, 10))

    story.append(PageBreak())

    # =========================================================================
    # SECTION 14: PRESENTATION SCRIPT
    # =========================================================================
    story.append(Paragraph("14. 3-TO-5 MINUTE PRESENTATION SCRIPT", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.8, color=HexColor("#1E3A8A"), spaceAfter=8))

    story.append(Paragraph("<i>(You can memorize this script or use it as a guideline during your project presentation)</i>", body_style))

    script_text = (
        "\"Respected examiners, good morning.<br/><br/>"
        "My major project is titled: <b>'AI-Based Wi-Fi Coverage Optimization and Dead-Zone Prediction System'</b>.<br/><br/>"
        "<b>The Problem:</b> In large institutional buildings like our college engineering blocks, hostels, and libraries, Wi-Fi dead zones cause severe disruption. Currently, network administrators have no proactive way to find them. They wait for complaints, walk around blindly with mobile speed tests, or guess where to add an Access Point—which often creates signal interference rather than fixing the dead zone.<br/><br/>"
        "<b>Our Solution:</b> We have built a complete, intelligent software platform that detects existing dead zones, analyzes their physical causes, predicts potential dead zones in unmeasured locations using machine learning, and recommends optimal AP placements with verified before-and-after proof.<br/><br/>"
        "<b>How It Works:</b> The system operates in two modes:<br/>"
        "1. <b>Simulation Mode</b>: Uses the physics-based COST-231 multi-wall propagation model to simulate how 2.4 GHz and 5 GHz radio waves travel through concrete, brick, and glass partitions.<br/>"
        "2. <b>Real College Survey Mode</b>: Turns any standard laptop into an active site survey tool without needing Raspberry Pis, Arduinos, or paid cloud APIs. As you walk across campus, you mark your spot on the digital floorplan, and our backend extracts live Wi-Fi telemetry using Windows netsh and measures wireless link latency by pinging the local router gateway.<br/><br/>"
        "<b>The Core Pipeline:</b> Our workflow follows five steps: <b>DETECT, UNDERSTAND, PREDICT, OPTIMIZE, and VERIFY.</b><br/>"
        "• <b>Detect</b>: We don't just look at signal bars. A dead zone is defined multi-dimensionally: RSSI &lt; -78 dBm, latency &gt; 120 ms, packet loss &gt; 15%, or throughput &lt; 5 Mbps. We use <b>DBSCAN spatial clustering</b> to group weak points into clusters and calculate their physical area in square meters using convex hulls. A single bad reading is treated as noise—it never creates a false dead zone.<br/>"
        "• <b>Understand</b>: Our system diagnoses <i>why</i> the dead zone exists—whether it's excessive distance or attenuation from concrete walls.<br/>"
        "• <b>Predict</b>: We trained a <b>Random Forest classifier</b> with 100 decision trees. It looks at spatial coordinates, distance, wall factors, and existing AP density to predict whether unmeasured areas are at risk of becoming dead zones, achieving approximately <b>89% accuracy</b>.<br/>"
        "• <b>Optimize &amp; Verify</b>: Our AP optimizer tests candidate locations at dead-zone centroids, simulates coverage gain, and calculates exact before-and-after metrics—demonstrating over <b>75% reduction</b> in dead-zone area.<br/><br/>"
        "All 21 backend unit and integration tests pass, and the React frontend compiles cleanly. I am now ready to demonstrate the live application. Thank you.\""
    )
    script_box = [[Paragraph(script_text, body_style)]]
    t_script = Table(script_box, colWidths=[USABLE_WIDTH])
    t_script.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), HexColor("#F8FAFC")),
        ('BOX', (0,0), (-1,-1), 1, HexColor("#0284C7")),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(t_script)

    story.append(PageBreak())

    # =========================================================================
    # SECTION 15: 30 VIVA QUESTIONS & SIMPLE ANSWERS
    # =========================================================================
    story.append(Paragraph("15. 30 VIVA QUESTIONS & SIMPLE ANSWERS", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.8, color=HexColor("#1E3A8A"), spaceAfter=8))

    viva_qas = [
        # Conceptual & Networking
        ("Q1: What is RSSI, and what unit is it measured in?",
         "RSSI stands for Received Signal Strength Indicator. It is measured in decibel-milliwatts (dBm). Because signal power drops dramatically over distance, it is represented on a logarithmic scale with negative numbers. For example, -30 dBm is excellent, -65 dBm is good, and -85 dBm is very weak."),
        ("Q2: What is a Wi-Fi dead zone according to your project?",
         "In our project, a dead zone is a continuous physical area where network performance degrades to an unusable level. It is defined multi-dimensionally: RSSI < -78.0 dBm, latency > 120.0 ms, packet loss > 15.0%, or throughput < 5.0 Mbps."),
        ("Q3: Why not just buy more Access Points and install them everywhere?",
         "Adding too many APs creates severe Co-Channel Interference (CCI). When multiple APs transmit on the same frequency band, their radio waves collide, forcing devices to back off and wait, which actually decreases overall network speed. Intelligent placement eliminates dead zones with the minimum number of APs."),
        ("Q4: What is the difference between 2.4 GHz and 5 GHz Wi-Fi?",
         "2.4 GHz has a longer wavelength, so it penetrates walls better and covers larger distances, but offers lower maximum speed and suffers from channel congestion. 5 GHz provides much higher throughput and lower latency, but attenuates quickly through concrete walls and covers shorter distances."),
        ("Q5: Why did you ping the local gateway instead of 8.8.8.8 during the survey?",
         "Pinging an external IP like 8.8.8.8 (Google DNS) measures internet traffic, ISP fiber delays, and cloud routing. Pinging the local gateway (the Wi-Fi router) isolates the first-hop wireless radio link, measuring purely the laptop's connection to the local AP."),

        # ML & Algorithms
        ("Q6: What ML algorithm did you use for dead-zone prediction?",
         "We used a Random Forest Classifier with 100 decision trees (n_estimators = 100) and a maximum depth of 12."),
        ("Q7: Why did you choose Random Forest instead of a Deep Learning Neural Network?",
         "Random Forest is ideal for tabular spatial-network features. Deep Neural Networks require tens of thousands of data samples, heavy GPU compute, and act as black boxes. Random Forest trains in seconds on a CPU, resists overfitting through ensemble bagging, and gives explicit Feature Importance rankings."),
        ("Q8: What features does the ML model take as input?",
         "It takes 7 features: rssi, latency, packet_loss, throughput, distance_to_ap, wall_factor, and ap_density within a 25m radius."),
        ("Q9: Explain Precision vs Recall in the context of Wi-Fi dead zones.",
         "Precision is: 'When the model predicts an area is a dead zone, is it really a dead zone?' High precision prevents spending money installing APs where they aren't needed. Recall is: 'Out of all actual dead zones in the building, how many did the model find?' High recall ensures no dead zone is overlooked."),
        ("Q10: What is DBSCAN and why did you use it for dead-zone detection?",
         "DBSCAN is an unsupervised density-based spatial clustering algorithm. We used it because: 1. It does not require pre-specifying the number of clusters K. 2. It can find clusters of arbitrary geometric shapes (like hallways or L-shaped rooms). 3. It filters out isolated outliers as noise, ensuring a single bad measurement doesn't falsely trigger a dead zone."),
        ("Q11: What do the DBSCAN parameters ε (epsilon) and min_samples represent?",
         "ε (6 to 12 meters) is the maximum physical distance between two weak points for them to be considered neighbors. min_samples (3 points) is the minimum number of clustered poor points required to form a recognized dead zone."),
        ("Q12: How do you calculate the area of a dead zone in square meters?",
         "We compute the 2D Convex Hull polygon encompassing the clustered points, and then calculate its surface area using the Shoelace formula on the polygon's Cartesian (x, y) coordinates."),

        # RF Simulation
        ("Q13: Which propagation model did you implement in the simulation?",
         "The Multi-Wall COST-231 Indoor Propagation Model (also aligned with ITU-R P.1238)."),
        ("Q14: How does your code calculate wall attenuation between an AP and a point?",
         "Using 2D computational geometry ray-intersection. The code draws a straight line segment from the AP coordinate to the receiver coordinate. It checks if this line intersects any wall line segment using cross products (segments_intersect). If an intersection occurs, the wall's attenuation in dB (e.g., 12 dB for concrete) is added to the total path loss."),
        ("Q15: What is log-normal shadowing?",
         "In real environments, obstacles like desks, doors, and moving people cause random signal variations. Shadowing models this by adding a zero-mean Gaussian random variable X_σ ~ N(0, σ²) (with σ = 1.8 dB) to the path loss equation."),

        # Architecture & Real Survey
        ("Q16: How does the laptop know where it is inside the building?",
         "It does not use automatic indoor GPS because GPS signals cannot penetrate building roofs. Instead, the user marks their current physical position on the digital interactive floorplan by clicking the screen, which sets the (x, y) coordinates."),
        ("Q17: How did you extract Wi-Fi details from Windows without extra software?",
         "By running the native Windows Command Prompt command: netsh wlan show interfaces using Python's subprocess.run(), and parsing fields like SSID, BSSID, Signal %, and Channel with regular expressions (re)."),
        ("Q18: What is BSSID and why is it important?",
         "BSSID is the Basic Service Set Identifier, which is the hardware MAC address of the specific Access Point radio your laptop is connected to. In a campus with 50 APs all sharing the same SSID (e.g., Campus_WiFi), the BSSID tells us exactly which physical AP the device is communicating with."),
        ("Q19: If Windows only reports Signal percentage (e.g., 75%), how do you get RSSI in dBm?",
         "If the Wi-Fi driver does not expose raw RSSI, we apply the standard Microsoft WLAN approximation formula: RSSI (dBm) ≈ (Signal % / 2) - 100. For example, 80% → (40) - 100 = -60 dBm. Our database clearly tags whether RSSI was hardware-reported or estimated."),
        ("Q20: Why did you use FastAPI instead of Flask or Django?",
         "FastAPI provides native asynchronous request handling, automatic OpenAPI/Swagger interactive documentation (/docs), and strict data validation using Pydantic models. It is significantly faster and more modern than Flask."),
        ("Q21: Why SQLite instead of MongoDB or PostgreSQL?",
         "SQLite is embedded, serverless, and stores data in a single local file. Since our project is designed to run locally on a student's survey laptop while walking around campus, SQLite eliminates the need to run heavy background database services."),

        # AP Optimization & Defense
        ("Q22: How does the optimizer pick candidate locations for new APs?",
         "It generates candidates primarily at the centroids of detected dead-zone polygons and affected room centers, enforcing a minimum separation constraint (12 meters) from existing APs to prevent co-channel overlap."),
        ("Q23: How do you verify that the AP recommendation actually worked?",
         "The system runs a Before vs After evaluation. It re-computes the spatial coverage with the new AP in place, measures the new dead-zone area in m², and calculates the percentage area reduction (typically achieving > 75% reduction)."),
        ("Q24: What are the severity levels of dead zones in your system?",
         "LOW, MEDIUM, HIGH, and CRITICAL, calculated via a multi-parameter composite penalty score based on RSSI, latency, packet loss, and throughput."),
        ("Q25: Can this system be deployed in our college right now?",
         "Yes. A network administrator or student can open the Real College Survey mode on their laptop, upload our floorplan, walk the corridors, click their spots, and capture real measurements to detect dead zones immediately."),
        ("Q26: What happens if the laptop disconnects from Wi-Fi during the survey?",
         "The backend detects State: disconnected in the netsh output. It records connected: False, sets packet loss to 100%, and marks the quality as POOR with zero latency, accurately representing a total dead zone."),
        ("Q27: How many tests did you write, and what do they test?",
         "We wrote 21 automated tests using Pytest, covering API endpoints, RF path loss physics, DBSCAN clustering, Random Forest training/inference, AP optimization logic, and Windows network telemetry parsing."),
        ("Q28: Is this a software-only project or does it need hardware sensors?",
         "It is strictly software-only. It uses the built-in Wi-Fi radio and networking stack already present inside a standard Windows laptop. No Arduinos, Raspberry Pis, or external antennas are required."),
        ("Q29: What is the main difference between your project and commercial tools like NetSpot or Ekahau?",
         "NetSpot and Ekahau primarily create passive heatmaps of signal strength. Our project is an end-to-end AI system: it clusters multi-parameter weak spots with DBSCAN, diagnoses root causes, uses Machine Learning to predict dead zones in unmeasured locations, and automatically suggests AP coordinates with verified before/after reduction metrics."),
        ("Q30: What future enhancements would you suggest?",
         "Extending the RF model to 3D for multi-floor buildings (inter-floor RF penetration), adding automated Wi-Fi channel allocation algorithms (to prevent channel overlap), and developing a cross-platform mobile client for Android/iOS.")
    ]

    for q, a in viva_qas:
        story.append(KeepTogether([
            Paragraph(q, viva_q_style),
            Paragraph(f"<b>Answer:</b> {a}", viva_a_style)
        ]))

    story.append(PageBreak())

    # =========================================================================
    # SECTION 16: QUICK CHEAT SHEET
    # =========================================================================
    story.append(Paragraph("16. QUICK CHEAT SHEET (5-MINUTE LAST-MINUTE REVISION)", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.8, color=HexColor("#1E3A8A"), spaceAfter=8))

    cheat_sheet_text = (
        "<b>================================================================================</b><br/>"
        "<b>                    ⚡ 5-MINUTE LAST-MINUTE VIVA CHEAT SHEET ⚡</b><br/>"
        "<b>================================================================================</b><br/><br/>"
        "<b>1. PROJECT IN ONE SENTENCE:</b><br/>"
        "An AI-driven software platform that detects Wi-Fi dead zones, diagnoses why they happen, predicts weak spots in unmeasured areas using Random Forest, and recommends optimal AP placements with verified Before-vs-After reduction.<br/><br/>"
        "<b>2. THE CORE WORKFLOW:</b><br/>"
        "<b>DETECT ──► UNDERSTAND ──► PREDICT ──► OPTIMIZE ──► VERIFY</b><br/><br/>"
        "<b>3. THRESHOLDS TO REMEMBER:</b><br/>"
        "• Poor Signal (RSSI):   &lt; -78 dBm<br/>"
        "• High Latency:         &gt; 120 ms<br/>"
        "• High Packet Loss:     &gt; 15%<br/>"
        "• Low Throughput:       &lt; 5 Mbps<br/>"
        "• Dead-Zone Severity:   LOW (&lt;32), MEDIUM (32-51), HIGH (52-74), CRITICAL (≥75)<br/><br/>"
        "<b>4. ALGORITHMS &amp; MODELS:</b><br/>"
        "• Dead-Zone Clustering: DBSCAN (eps = 6-12m, min_samples = 3)<br/>"
        "• Boundary &amp; Area:      Convex Hull (Graham Scan) + Shoelace Area Formula<br/>"
        "• ML Prediction:        Random Forest Classifier (100 trees, max depth = 12)<br/>"
        "• RF Propagation:       Multi-Wall COST-231 Model (PL = PL_1m + 10*n*log10(d) + ∑ WAF)<br/><br/>"
        "<b>5. WINDOWS TELEMETRY COMMANDS:</b><br/>"
        "• Wi-Fi Adapter:        netsh wlan show interfaces (SSID, BSSID, Signal%, Channel)<br/>"
        "• Gateway Latency:      ping -n 3 -w 1000 &lt;Default_Gateway_IP&gt;<br/>"
        "• RSSI Formula:         RSSI ≈ (Signal% / 2) - 100 dBm (if driver omits dBm)<br/><br/>"
        "<b>6. BENCHMARK NUMBERS:</b><br/>"
        "• Tests:                21 / 21 Passed (Pytest)<br/>"
        "• ML Accuracy:          ~89% (Precision ~88%, Recall ~86%, F1 ~87%)<br/>"
        "• Optimization:         ~76% dead-zone area reduction (e.g., 292 m² -&gt; 68 m²)<br/>"
        "• Live Hardware Test:   Alifa’s iPhone, BSSID a2:a4:e4:13:06:a7, 100%, 9ms latency<br/><br/>"
        "<b>7. THREE COMMON TRAP QUESTIONS:</b><br/>"
        "• <i>'Why DBSCAN?'</i>         -&gt; Discovers cluster count automatically; ignores single-point noise.<br/>"
        "• <i>'Why Ping Gateway?'</i>   -&gt; Isolates the wireless Wi-Fi link from external ISP internet lag.<br/>"
        "• <i>'Does it have GPS?'</i>   -&gt; No, GPS fails indoors; user clicks position on floorplan (user-assisted).<br/>"
        "<b>================================================================================</b>"
    )

    t_cheat = Table([[Paragraph(cheat_sheet_text, code_style)]], colWidths=[USABLE_WIDTH])
    t_cheat.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), HexColor("#F1F5F9")),
        ('BOX', (0,0), (-1,-1), 1.2, HexColor("#475569")),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(t_cheat)

    # Build document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"SUCCESS: Generated PDF at {pdf_path}")

if __name__ == "__main__":
    build_pdf()
