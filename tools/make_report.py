"""Builds Report/Lab_Assignment_Report.docx (and .pdf) from the real source
code, screenshots and console output. Run after tools/build_and_capture.sh:
    python3 tools/make_report.py
"""
import re, subprocess, pathlib
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

ROOT = pathlib.Path(__file__).resolve().parent.parent
REP = ROOT / "Report"
P1 = ROOT / "Problem1_Bangladesh_Tribute_Scene/bangladesh_tribute_scene.cpp"
P2 = ROOT / "Problem2_Village_Scenery/village_scenery.cpp"


def parse_log(path):
    """Return {title: [point lines]} from the program's console output."""
    runs, title = {}, None
    for line in path.read_text().splitlines():
        if line.startswith("  k=") and title:
            runs[title].append(line.strip())
        elif line.strip() and not line.startswith("First"):
            title = line.strip()
            runs[title] = []
    return runs


def table(doc, header, rows):
    t = doc.add_table(rows=1, cols=len(header))
    t.style = "Light Grid Accent 1"
    for i, h in enumerate(header):
        t.rows[0].cells[i].text = h
    for r in rows:
        cells = t.add_row().cells
        for i, v in enumerate(r):
            cells[i].text = v
    for row in t.rows:
        for c in row.cells:
            for p in c.paragraphs:
                for run in p.runs:
                    run.font.size = Pt(9)


def code(doc, path):
    p = doc.add_paragraph()
    run = p.add_run(path.read_text())
    run.font.name = "Courier New"
    run.font.size = Pt(7.5)


def heading(doc, text, level):
    doc.add_heading(text, level=level)


doc = Document()
for s in doc.sections:
    s.left_margin = s.right_margin = Inches(0.8)
    s.top_margin = s.bottom_margin = Inches(0.7)

# ---------------- cover ----------------
for text, bold, size in [
    ("American International University-Bangladesh (AIUB)", True, 15),
    ("Faculty of Science and Technology - Department of Computer Science", False, 11),
    ("Course: Computer Graphics", False, 11),
    ("MID TERM LAB ASSIGNMENT REPORT", True, 14),
]:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(text)
    r.bold, r.font.size = bold, Pt(size)
p = doc.add_paragraph("Name: SIAM HOSSAIN        ID: ____________        Section: ______")
p.alignment = WD_ALIGN_PARAGRAPH.CENTER

# ================= Problem 1 =================
heading(doc, "Problem 1: Bangladesh Tribute Scene (DDA, Bresenham, Midpoint Circle)", 1)

heading(doc, "1. Screenshot of Output", 2)
doc.add_picture(str(REP / "screenshots/problem1.png"), width=Inches(6.5))

heading(doc, "2. Short Report", 2)
doc.add_paragraph(
    "The scene is drawn on a 1000 x 600 pixel grid (gluOrtho2D, 1 unit = 1 pixel). "
    "The only OpenGL drawing call is putPixel(x, y), which plots one GL_POINT. All lines "
    "and circles come from our own DDA, Bresenham and Midpoint Circle functions. Part A "
    "(flag), Part B (Shaheed Minar) and Part C (footpath, clouds, flowers) are drawn "
    "together in one window. The flag follows the real 10:6 ratio. The sun radius is "
    "length/5 and its centre is at 9/20 of the length, so it sits slightly left of centre.")

doc.add_paragraph().add_run("a. Which part uses which algorithm").bold = True
table(doc, ["Algorithm", "Parts of the scene"], [
    ["DDA", "Flagpole; grille bars inside the five pillars; decorative line on the "
            "platform; flower stems and leaves"],
    ["Bresenham", "Flag frame (border); base platform border; pillar edges; footpath "
                  "edges and tile lines; every filled area (horizontal scan-lines)"],
    ["Midpoint Circle", "Red sun of the flag; big red sun behind the Minar; arch on top "
                        "of the middle pillar; pole knob; clouds (overlapping circles); "
                        "flower petals"],
])

doc.add_paragraph().add_run(
    "b. Sample point outputs (first 5 plotted points, printed by the program)").bold = True
runs = parse_log(REP / "problem1_console_output.txt")
for algo in ["DDA", "Bresenham", "Midpoint Circle"]:
    for title, points in runs.items():
        if title.startswith(algo):
            p = doc.add_paragraph()
            p.add_run(title).bold = True
            rows = []
            for pt in points:
                k = re.search(r"k=(\d+)", pt).group(1)
                pix = re.search(r"pixel (\(.*\))", pt).group(1)
                detail = pt.split("->")[0].split(None, 1)[1].strip()
                rows.append([k, detail, pix])
            table(doc, ["k", "Values in the algorithm", "Plotted pixel"], rows)

heading(doc, "3. Source Code", 2)
code(doc, P1)

# ================= Problem 2 =================
doc.add_page_break()
heading(doc, "Problem 2: Simple Village Scenery (OpenGL Built-in Functions)", 1)

heading(doc, "1. Screenshot of Output", 2)
doc.add_picture(str(REP / "screenshots/problem2.png"), width=Inches(6.5))

heading(doc, "2. Short Report", 2)
doc.add_paragraph("a. Primitives used for each object").runs[0].bold = True
table(doc, ["Object", "OpenGL primitive"], [
    ["Sky, ground, river", "GL_QUADS (sky has a colour gradient)"],
    ["Sun, clouds, tree leaves", "GL_POLYGON (60-sided circle)"],
    ["House body, door, windows, tree trunk", "GL_QUADS"],
    ["House roofs, mountains, snow caps, boat sail", "GL_TRIANGLES"],
    ["Boat hull", "GL_POLYGON"],
    ["Window bars, river waves, boat mast, birds (V shape)", "GL_LINES"],
])
doc.add_paragraph("b. Scene arrangement").runs[0].bold = True
for line in [
    "The window is 1000 x 600 and gluOrtho2D(0, 1000, 0, 600) makes 1 unit = 1 pixel.",
    "The horizon is at y = 330: the sky is above it and the ground is below it.",
    "Objects are drawn back to front: sky, sun, mountains, clouds, ground, river, "
    "houses, tree, boat, birds.",
    "Each object is drawn around its own origin, placed with glTranslatef(x, y, 0) and "
    "resized with glScalef(s, s, 1) inside glPushMatrix()/glPopMatrix().",
    "The same drawHouse() is used twice: scale 1.6 at x = 90 and scale 1.3 at x = 380, "
    "with different colours. Clouds use scales 0.8 to 1.1.",
    "The river is a long slanted quad from (0, 40-130) to (1000, 70-160), and the boat "
    "sits on it. Part C extras: mountains, boat and birds.",
]:
    doc.add_paragraph(line, style="List Bullet")

heading(doc, "3. Source Code", 2)
code(doc, P2)

out = REP / "Lab_Assignment_Report.docx"
doc.save(out)
print("saved", out)
subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(REP), str(out)],
               check=False, capture_output=True)
print("pdf:", (REP / "Lab_Assignment_Report.pdf").exists())
