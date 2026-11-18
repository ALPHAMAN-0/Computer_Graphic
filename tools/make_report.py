"""Builds Report/Lab_Assignment_Report.docx and a PDF copy of it.

The source listings, the two screenshots and the sample points are read
from the project files, so after changing one of the programs run:
    bash tools/build_and_capture.sh
    python3 tools/make_report.py
"""
import datetime
import pathlib
import re
import subprocess

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Mm, Pt, RGBColor

ROOT = pathlib.Path(__file__).resolve().parent.parent
REP = ROOT / "Report"
SRC1 = ROOT / "Problem1_Bangladesh_Tribute_Scene" / "bangladesh_tribute_scene.cpp"
SRC2 = ROOT / "Problem2_Village_Scenery" / "village_scenery.cpp"
LOG1 = REP / "problem1_console_output.txt"
SHOT1 = REP / "screenshots" / "problem1.png"
SHOT2 = REP / "screenshots" / "problem2.png"
OUT = REP / "Lab_Assignment_Report.docx"

AUTHOR = "SIAM HOSSAIN"
BODY_FONT = "Times New Roman"
CODE_FONT = "Courier New"
LEFT = WD_ALIGN_PARAGRAPH.LEFT
CENTER = WD_ALIGN_PARAGRAPH.CENTER
BLANK = "_" * 26
NBSP = " "

# Line runs printed by Problem 1: console title -> (name, start, end).
# The start point is checked against the first plotted pixel.
LINE_RUNS = {
    "DDA - Flagpole": ("Flagpole", (110, 140), (110, 500)),
    "DDA - Flower stem": ("First flower stem", (450, 55), (456, 95)),
    "Bresenham - Flag frame (bottom edge)": ("Flag frame, bottom edge", (114, 372), (314, 372)),
    "Bresenham - Footpath left edge": ("Footpath, left edge", (470, 0), (570, 170)),
}
CIRCLE_RUNS = {
    "Midpoint Circle - Red sun of the flag": "Red sun of the flag",
    "Midpoint Circle - Arch on the middle pillar": "Arch on the middle pillar",
}
PIXEL = r"-> pixel \((-?\d+), (-?\d+)\)"
DDA_RE = re.compile(r"k=(\d+)\s+x=(\S+)\s+y=(\S+)\s+" + PIXEL)
BRES_RE = re.compile(r"k=(\d+)\s+p=(-?\d+)\s+" + PIXEL)
CIRCLE_RE = re.compile(r"k=(\d+)\s+\(x=(-?\d+), y=(-?\d+)\)\s+p=(-?\d+)\s+" + PIXEL)


# ----------------------------------------------------------------- xml bits
def insert_before(parent, child, successors):
    """Insert child in front of the first successor found (schema order)."""
    for tag in successors:
        found = parent.find(qn(tag))
        if found is not None:
            found.addprevious(child)
            return child
    parent.append(child)
    return child


def set_rfonts(rpr, name):
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.insert(0, rfonts)
    for attr in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
        rfonts.attrib.pop(qn(attr), None)
    for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rfonts.set(qn(attr), name)


def shade(cell, fill="D9D9D9"):
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    insert_before(cell._tc.get_or_add_tcPr(), shd,
                  ("w:noWrap", "w:tcMar", "w:textDirection", "w:tcFitText",
                   "w:vAlign", "w:hideMark"))


def bottom_border(paragraph):
    bdr = OxmlElement("w:pBdr")
    line = OxmlElement("w:bottom")
    for key, value in (("w:val", "single"), ("w:sz", "8"), ("w:space", "6"),
                       ("w:color", "000000")):
        line.set(qn(key), value)
    bdr.append(line)
    insert_before(paragraph._p.get_or_add_pPr(), bdr,
                  ("w:shd", "w:tabs", "w:suppressAutoHyphens", "w:spacing",
                   "w:ind", "w:contextualSpacing", "w:jc", "w:rPr"))


def page_number(paragraph):
    paragraph.alignment = CENTER
    for kind in ("begin", "instr", "separate", "text", "end"):
        run = paragraph.add_run()
        if kind == "text":
            run.text = "1"
            continue
        if kind == "instr":
            el = OxmlElement("w:instrText")
            el.set(qn("xml:space"), "preserve")
            el.text = " PAGE "
        else:
            el = OxmlElement("w:fldChar")
            el.set(qn("w:fldCharType"), kind)
        run._r.append(el)


# ------------------------------------------------------------------- styles
def setup_styles(doc):
    styles = doc.styles
    defaults = styles.element.find(qn("w:docDefaults"))
    set_rfonts(defaults.find(qn("w:rPrDefault")).find(qn("w:rPr")), BODY_FONT)

    normal = styles["Normal"]
    set_rfonts(normal.element.get_or_add_rPr(), BODY_FONT)
    normal.font.size = Pt(12)
    fmt = normal.paragraph_format
    fmt.space_before = Pt(0)
    fmt.space_after = Pt(6)
    fmt.line_spacing = 1.15
    fmt.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    for name, size, before, after in (("Heading 1", 16, 0, 12),
                                      ("Heading 2", 13, 16, 6),
                                      ("Heading 3", 12, 10, 4)):
        style = styles[name]
        set_rfonts(style.element.get_or_add_rPr(), BODY_FONT)
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.italic = False
        style.font.color.rgb = RGBColor(0, 0, 0)
        hf = style.paragraph_format
        hf.space_before = Pt(before)
        hf.space_after = Pt(after)
        hf.line_spacing = 1.0
        hf.keep_with_next = True
        hf.alignment = LEFT

    styles["List Bullet"].paragraph_format.space_after = Pt(4)
    styles["Footer"].font.size = Pt(10)

    code = styles.add_style("Code Listing", WD_STYLE_TYPE.PARAGRAPH)
    code.base_style = normal
    set_rfonts(code.element.get_or_add_rPr(), CODE_FONT)
    code.font.size = Pt(7.5)
    cf = code.paragraph_format
    cf.space_before = Pt(0)
    cf.space_after = Pt(0)
    cf.line_spacing = 1.0
    cf.alignment = LEFT
    cf.widow_control = False


def page_setup(section, code=False):
    section.page_width, section.page_height = Mm(210), Mm(297)
    side = Inches(0.6) if code else Inches(1.0)
    section.left_margin = section.right_margin = side
    section.top_margin = section.bottom_margin = Inches(0.75 if code else 1.0)
    section.header_distance = section.footer_distance = Inches(0.4)


def new_section(doc, code=False):
    section = doc.add_section(WD_SECTION.NEW_PAGE)
    section.different_first_page_header_footer = False
    page_setup(section, code)
    return section


# ------------------------------------------------------------ text helpers
def add_text(paragraph, text, size=None, bold=False, italic=False):
    """Add text to a paragraph. **x** is bold and `x` is set in Courier New.

    Spaces around = - + < > / become non-breaking, so a short formula such
    as p = 2dy - dx is never split over two lines.
    """
    text = re.sub(r" (=|-|\+|>=|<=|<|>|/) ", lambda m: NBSP + m.group(1) + NBSP, text)
    for part in re.split(r"(\*\*.+?\*\*|`.+?`)", text):
        if not part:
            continue
        is_bold = part.startswith("**")
        is_code = part.startswith("`")
        if is_bold:
            part = part[2:-2]
        elif is_code:
            part = part[1:-1]
        run = paragraph.add_run(part)
        if bold or is_bold:
            run.bold = True
        if italic:
            run.italic = True
        if is_code:
            run.font.name = CODE_FONT
        if size:
            run.font.size = Pt(size)
    return paragraph


def para(doc, text="", size=None, bold=False, italic=False, align=None,
         before=None, after=None, keep=False):
    p = doc.add_paragraph()
    if text:
        add_text(p, text, size, bold, italic)
    if align is not None:
        p.alignment = align
    pf = p.paragraph_format
    if before is not None:
        pf.space_before = Pt(before)
    if after is not None:
        pf.space_after = Pt(after)
    if keep:
        pf.keep_with_next = True
    return p


def spacer(doc, after=4):
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = Pt(2)
    p.paragraph_format.space_after = Pt(after)
    return p


def bullets(doc, items):
    for item in items:
        add_text(doc.add_paragraph(style="List Bullet"), item)


def numbered(doc, items):
    for n, item in enumerate(items, 1):
        p = doc.add_paragraph()
        pf = p.paragraph_format
        pf.left_indent = Inches(0.3)
        pf.first_line_indent = Inches(-0.3)
        pf.tab_stops.add_tab_stop(Inches(0.3))
        pf.space_after = Pt(4)
        add_text(p, f"{n}.\t{item}")


def command(doc, text):
    p = doc.add_paragraph(style="Code Listing")
    p.add_run(text).font.size = Pt(9.5)
    pf = p.paragraph_format
    pf.left_indent = Inches(0.35)
    pf.space_after = Pt(6)


def heading(doc, text, level, new_page=False, before=None):
    h = doc.add_heading(text, level)
    if new_page:
        h.paragraph_format.page_break_before = True
    if before is not None:
        h.paragraph_format.space_before = Pt(before)
    return h


def figure(doc, path, caption, width=6.0):
    p = doc.add_paragraph()
    p.alignment = CENTER
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(str(path), width=Inches(width))
    para(doc, caption, size=10, italic=True, align=CENTER, after=12)


def code_listing(doc, path):
    para(doc, f"File: {path.relative_to(ROOT).as_posix()}", size=11, bold=True,
         align=LEFT, after=6)
    for line in path.read_text().expandtabs(4).splitlines():
        p = doc.add_paragraph(style="Code Listing")
        if line:
            p.add_run(line)


# ------------------------------------------------------------ table helpers
def make_table(doc, widths, rows):
    table = doc.add_table(rows=rows, cols=len(widths))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    for i, w in enumerate(widths):
        table.columns[i].width = Inches(w)
        for cell in table.columns[i].cells:
            cell.width = Inches(w)
    return table


def fill(cell, text, size=10, bold=False, align=LEFT, header=False):
    cell.text = ""
    p = cell.paragraphs[0]
    add_text(p, text, size=size, bold=bold or header)
    pf = p.paragraph_format
    pf.space_before = Pt(0.5)
    pf.space_after = Pt(0.5)
    pf.line_spacing = 1.0
    p.alignment = align
    if header:
        shade(cell)


def keep_together(table):
    for row in table.rows:
        cant_split = OxmlElement("w:cantSplit")
        insert_before(row._tr.get_or_add_trPr(), cant_split,
                      ("w:trHeight", "w:tblHeader", "w:tblCellSpacing", "w:jc", "w:hidden"))
    for row in table.rows[:-1]:
        for cell in row.cells:
            for p in cell.paragraphs:
                p.paragraph_format.keep_with_next = True


def simple_table(doc, header, rows, widths):
    table = make_table(doc, widths, 1 + len(rows))
    for i, text in enumerate(header):
        fill(table.cell(0, i), text, header=True)
    for r, row in enumerate(rows, 1):
        for i, text in enumerate(row):
            fill(table.cell(r, i), text, bold=(i == 0))
    keep_together(table)
    spacer(doc)


def sample_table(doc, algo, runs, columns, widths):
    """Two runs of one algorithm side by side: k | run A columns | run B columns."""
    n = len(columns)
    table = make_table(doc, [0.95] + widths + widths, 2 + len(runs[0][1]))
    fill(table.cell(0, 0), algo, header=True)
    for j, (label, _) in enumerate(runs):
        merged = table.cell(0, 1 + j * n).merge(table.cell(0, n + j * n))
        fill(merged, label, align=CENTER)      # run name in bold, end points plain
        shade(merged)
    fill(table.cell(1, 0), "k", align=CENTER, header=True)
    for j in range(len(runs)):
        for i, name in enumerate(columns):
            fill(table.cell(1, 1 + j * n + i), name, align=CENTER, header=True)
    for r in range(len(runs[0][1])):
        fill(table.cell(2 + r, 0), str(r), align=CENTER)
        for j, (_, rows) in enumerate(runs):
            for i, value in enumerate(rows[r]):
                fill(table.cell(2 + r, 1 + j * n + i), value, align=CENTER)
    keep_together(table)
    spacer(doc)


def console_box(doc, blocks):
    """Console output in two columns of monospaced text."""
    half = (len(blocks) + 1) // 2
    table = make_table(doc, [3.12, 3.12], 1)
    keep_together(table)
    for i, part in enumerate((blocks[:half], blocks[half:])):
        cell = table.cell(0, i)
        shade(cell, "F2F2F2")
        lines = "\n\n".join(part).splitlines()
        for n, line in enumerate(lines):
            p = cell.paragraphs[0] if n == 0 else cell.add_paragraph()
            p.style = doc.styles["Code Listing"]
            if line:
                p.add_run(line)
    spacer(doc)


# ------------------------------------------------------- console output
def read_runs(path):
    """Return [(title, [point lines])] in the order the program printed them."""
    runs = []
    for line in path.read_text().splitlines():
        if line.startswith("  k=") and runs:
            runs[-1][1].append(line)
        elif line.strip() and not line.startswith("First"):
            runs.append((line.strip(), []))
    return runs


def line_run(title, points, regex, columns):
    name, start, end = LINE_RUNS[title]
    rows = []
    for text in points:
        groups = regex.search(text).groups()
        px, py = int(groups[-2]), int(groups[-1])
        if not rows and (px, py) != start:
            raise SystemExit(f"{title}: first pixel {(px, py)} does not match {start}")
        rows.append(list(columns(groups)) + [f"({px}, {py})"])
    label = f"**{name}**\n({start[0]}, {start[1]}) to ({end[0]}, {end[1]})"
    return label, rows


def circle_run(title, points):
    rows = []
    for text in points:
        _, x, y, p, px, py = CIRCLE_RE.search(text).groups()
        rows.append([f"({x}, {y})", p, f"({px}, {py})"])
    _, x0, y0, _, px0, py0 = CIRCLE_RE.search(points[0]).groups()
    xc, yc, r = int(px0) - int(x0), int(py0) - int(y0), int(y0)
    label = f"**{CIRCLE_RUNS[title]}**\ncentre ({xc}, {yc}), r = {r}"
    return label, rows


# ================================================================ content
def cover(doc):
    para(doc, "American International University-Bangladesh (AIUB)", size=17, bold=True,
         align=CENTER, before=30, after=4)
    para(doc, "Faculty of Science and Technology", size=13, align=CENTER, after=2)
    bottom_border(para(doc, "Department of Computer Science", size=13, align=CENTER, after=0))
    para(doc, "Course Title: Computer Graphics", size=14, align=CENTER, before=60, after=12)
    para(doc, "MID TERM LAB ASSIGNMENT REPORT", size=20, bold=True, align=CENTER, after=36)
    para(doc, "Problem 1: Bangladesh Tribute Scene (Using DDA, Bresenham, Midpoint Circle)",
         size=12, align=CENTER, after=4)
    para(doc, "Problem 2: Simple Village Scenery (OpenGL - Using Built-in Functions)",
         size=12, align=CENTER, after=70)

    rows = [("Submitted by", None), ("Name", AUTHOR), ("Student ID", BLANK),
            ("Section", BLANK), ("Submitted to", None), ("Course Teacher", BLANK),
            (None, None), ("Date of Submission", BLANK)]
    for label, value in rows:
        if label is None:
            para(doc, "", after=6)
            continue
        p = doc.add_paragraph()
        pf = p.paragraph_format
        pf.left_indent = Inches(1.2)
        pf.space_after = Pt(6)
        pf.tab_stops.add_tab_stop(Inches(3.0))
        p.alignment = LEFT
        if value is None:
            pf.space_before = Pt(10)
            add_text(p, label, size=13, bold=True)
        else:
            add_text(p, f"{label}\t:  {value}", size=12)


def problem1(doc):
    runs = read_runs(LOG1)
    by_title = dict(runs)

    heading(doc, "Problem 1: Bangladesh Tribute Scene (Using DDA, Bresenham, Midpoint Circle)",
            1, new_page=True)

    heading(doc, "1.1 Objective", 2, before=4)
    para(doc, "The first problem asks for a complete 2D scene on a pixel grid that pays tribute to "
              "Bangladesh. Only three algorithms may be used for drawing: the DDA line algorithm, the "
              "Bresenham line algorithm and the Midpoint circle algorithm. Built-in line and circle "
              "functions are not allowed, only putpixel(x, y) or something equivalent. The flag (Part A), "
              "the Shaheed Minar (Part B) and the extra elements (Part C) all have to be drawn together in "
              "one window as a single scene.")
    para(doc, "In my program the only OpenGL drawing call is the one inside putPixel(), which plots a "
              "single GL_POINT. The sky is just the background colour set with glClearColor(). Every line, "
              "circle, arc and filled area in the picture comes from my own code for the three algorithms.")

    heading(doc, "1.2 Screenshot of Output", 2)
    figure(doc, SHOT1, "Figure 1: Output window of Problem 1 (Bangladesh Tribute Scene)")

    heading(doc, "1.3 How I Built the Scene", 2)
    heading(doc, "Pixel grid", 3)
    para(doc, "The window is 1000 x 600 pixels. In init() I call gluOrtho2D(0, 1000, 0, 600), so one unit "
              "in my coordinates is exactly one pixel and (0, 0) is the bottom-left corner of the window. "
              "The point size is 1, which means every putPixel() call lights up one pixel only. The sky is "
              "the light blue clear colour, and the grass field below the horizon at y = 230 is filled with "
              "horizontal Bresenham lines, one for each row.")

    heading(doc, "The three algorithms", 3)
    para(doc, "**DDA line (ddaLine).** The number of steps is the larger of the absolute values of dx "
              "and dy, and the function works out xInc = dx / steps and yInc = dy / steps. One of the two "
              "increments is "
              "always 1 or -1 and the other one is a fraction. Starting from (x1, y1), it adds both "
              "increments at every step and rounds x and y to the nearest integer before plotting the "
              "pixel. Since it works with floating-point numbers, the DDA sample output has decimal values "
              "in it.")
    para(doc, "**Bresenham line (bresenhamLine).** This one uses integers only. For a gentle line, with a "
              "slope between -1 and 1, it moves one pixel along x at every step and keeps a decision parameter that "
              "starts at p = 2dy - dx. If p < 0, the next pixel stays on the same row and p becomes "
              "p + 2dy. Otherwise y also moves by one and p becomes p + 2dy - 2dx. For a steep line the "
              "roles of x and y are swapped and p starts at 2dx - dy. The step directions sx and sy can be "
              "+1 or -1, so the same function can draw a line of any slope in any direction. I needed this "
              "for the slanted edges of the footpath.")
    para(doc, "**Midpoint circle (midpointCircle).** It starts at (0, r) with p = 1 - r and works through "
              "one octant while x <= y. At every step x goes up by one. If p < 0, the midpoint is inside "
              "the circle, so y stays the same and p becomes p + 2x + 1. If not, y goes down by one and p "
              "becomes p + 2(x - y) + 1. Each point is copied to the other seven octants by symmetry in "
              "circlePoints(). I gave the function two options. With upperHalf, only the four points above "
              "the centre are plotted, which gives an arch. With filled, each pair of mirrored points on "
              "the same row is joined by a horizontal Bresenham line, which gives a solid disc. So the "
              "shape of every circle, filled or not, comes from the Midpoint algorithm.")
    para(doc, "There is no built-in rectangle either, so I wrote two small helpers. drawRect() draws the "
              "four sides with Bresenham, and fillRect() draws one horizontal Bresenham line for every row "
              "of the rectangle. All the flat coloured areas (grass, flag body, pole stand, platform, "
              "pillar frames and the footpath surface) are filled with horizontal Bresenham lines in this "
              "way.")

    heading(doc, "Part A: Bangladesh flag", 3)
    para(doc, "I kept the proportions of the real flag. The length and the height are in the ratio 10:6, "
              "the radius of the red circle is one fifth of the length, and the centre of the circle is "
              "9/20 of the length away from the pole side, which places it slightly left of the middle. "
              "With a flag length of 200 px, the flag runs from (114, 372) to (314, 492), the sun has a "
              "radius of 40 px and its centre is at (204, 432). That is 10 px to the left of the flag’s "
              "centre line at x = 214. For the colours I used the official bottle green (0, 106, 78) and "
              "red (244, 42, 65).")
    bullets(doc, [
        "The flag frame (border) is drawn with drawRect(), so it is made of four Bresenham lines. The "
        "green body inside it is filled with Bresenham scan-lines.",
        "The red sun is a filled Midpoint circle with a Midpoint outline drawn over it.",
        "The flagpole is drawn with DDA. It goes from y = 140 up to y = 500 and is 4 px thick, so it is "
        "made of four vertical DDA lines placed side by side.",
        "To finish the pole I added a small golden knob on top (Midpoint circle, r = 5) and a grey stand "
        "at the bottom (Bresenham fill).",
    ])

    heading(doc, "Part B: Shaheed Minar", 3)
    para(doc, "The Minar is centred at x = 640, to the right of the flag, and it has the minimum structure "
              "given in the assignment.")
    bullets(doc, [
        "**Base platform:** one wide rectangle of 460 x 25 px (x = 410 to 870, y = 170 to 195). It is "
        "filled light grey, its border is drawn with Bresenham, and a thin decorative line across its "
        "front at y = 182 is drawn with DDA.",
        "**Five pillars:** the pillars stand 80 px apart, and each step away from the centre makes a "
        "pillar 55 px shorter. So the middle pillar is 250 px tall, the two beside it are 195 px and the "
        "two outer ones are 140 px. The middle pillar is also wider (50 px instead of 36 px). Each pillar has a "
        "6 px white frame, black grille bars and a grey outline. The pillar edges are Bresenham lines and "
        "the grille bars are vertical DDA lines placed 5 px apart. I left the inside of the pillars open, "
        "so the red sun, the sky and the grass show through the bars, which is close to how the real "
        "monument looks.",
        "**Top arch:** a half circle of radius 25 with its centre at (640, 445), right on top of the "
        "middle pillar. It is filled with the upper-half option and then outlined with drawArc(). Both "
        "use the Midpoint circle algorithm.",
        "**Red sun:** the big red circle (r = 110) behind the pillars is a filled Midpoint circle. It is "
        "drawn first, so the pillars stand in front of it.",
    ])

    heading(doc, "Part C: Extra elements", 3)
    para(doc, "Any two of the six extras were enough, but I drew three of them:")
    numbered(doc, [
        "**Road / footpath (Bresenham).** A path runs from the bottom of the window up to the platform. "
        "It is 340 px wide at the bottom and 140 px at the top, which gives a simple perspective look. "
        "The surface is filled row by row, tile joints are drawn every 25 px, and the two slanted side "
        "edges go from (470, 0) to (570, 170) and from (810, 0) to (710, 170). Every one of these lines "
        "is Bresenham.",
        "**Clouds (Midpoint circle).** There are three clouds, and each one is made of four overlapping "
        "filled circles of different sizes.",
        "**Flowers (Midpoint circle + DDA).** Five red and five white flowers grow on the two sides of "
        "the path, a bit like the flowers people leave at the Shaheed Minar on 21 February. The stem and "
        "the two leaves of each flower are DDA lines, and the four petals and the yellow centre are small "
        "filled Midpoint circles.",
    ])

    heading(doc, "Drawing order", 3)
    para(doc, "A pixel drawn later covers whatever was there before, so the order of the calls in "
              "display() matters. The scene is drawn in this order: ground, clouds, footpath, Shaheed "
              "Minar (red sun, platform, pillars, arch), flowers and finally the flag. The footpath comes "
              "before the Minar so that the platform hides its top end.")

    heading(doc, "Following the strict algorithm rules", 3)
    bullets(doc, [
        "Each kind of straight line has one fixed algorithm, never a random mix. Edges, borders, "
        "footpath lines and all fills use Bresenham. The flagpole, the grille bars, the platform "
        "decoration and the flower stems and leaves use DDA. This is labelled in the comment block at "
        "the top of the source file and again in comments next to the drawing code.",
        "Every circle and arc (both suns, the arch, the pole knob, the clouds and the petals) is drawn "
        "with the Midpoint circle algorithm.",
        "All three algorithms are implemented, and each one is used many times in the scene.",
    ])

    heading(doc, "Printing the sample points", 3)
    para(doc, "To get the sample points for the report I added a small logging step. startLog() is called "
              "just before an algorithm run that I want to record, and shouldLog() then lets the next five "
              "plotted points of that algorithm print their values. It only happens while the first frame "
              "is drawn, so the console is not flooded when the window is redrawn. This is what the program "
              "printed:", keep=True)
    console_box(doc, [title + "\n" + "\n".join(points) for title, points in runs])

    heading(doc, "1.4 Short Report", 2, new_page=True, before=0)
    para(doc, "My scene shows the Bangladesh flag on its pole at the left and a simplified Shaheed Minar "
              "with a red sun behind it at the right, with a footpath, red and white flowers and three "
              "clouds as the extra elements. Nothing is drawn with an OpenGL line or circle function. The "
              "only drawing call is putPixel(), which plots one GL_POINT, and every line and circle comes "
              "from my own DDA, Bresenham and Midpoint circle code.", size=11)
    para(doc, "a. Which parts use DDA, Bresenham and Midpoint Circle", bold=True, keep=True, after=4)
    simple_table(doc, ["Algorithm", "Parts of the scene"], [
        ["DDA", "Flagpole (four parallel lines), grille bars inside the five pillars, decorative line "
                "on the platform, flower stems and leaves"],
        ["Bresenham", "Flag frame, platform border, pillar edges, footpath side edges and tile lines, "
                      "and every filled area as horizontal scan-lines (grass, flag body, pole stand, "
                      "platform, pillar frames, footpath surface and the inside of filled circles)"],
        ["Midpoint Circle", "Red sun of the flag, big red sun behind the Minar, arch on the middle "
                            "pillar, knob on the flagpole, clouds, flower petals and flower centres"],
    ], [1.45, 4.8])

    para(doc, "b. Sample point outputs (first 5 plotted points of each run)", bold=True, keep=True,
         before=4, after=2)
    para(doc, "Copied from the console output in Section 1.3, with two runs of each algorithm.",
         size=11, keep=True, after=6)
    sample_table(doc, "DDA", [
        line_run("DDA - Flagpole", by_title["DDA - Flagpole"], DDA_RE, lambda g: g[1:3]),
        line_run("DDA - Flower stem", by_title["DDA - Flower stem"], DDA_RE, lambda g: g[1:3]),
    ], ["x", "y", "Pixel"], [0.75, 0.75, 1.05])
    sample_table(doc, "Bresenham", [
        line_run("Bresenham - Flag frame (bottom edge)",
                 by_title["Bresenham - Flag frame (bottom edge)"], BRES_RE, lambda g: g[1:2]),
        line_run("Bresenham - Footpath left edge",
                 by_title["Bresenham - Footpath left edge"], BRES_RE, lambda g: g[1:2]),
    ], ["p", "Pixel"], [1.2, 1.35])
    sample_table(doc, "Midpoint", [
        circle_run(title, by_title[title]) for title in CIRCLE_RUNS
    ], ["(x, y)", "p", "Pixel"], [0.85, 0.65, 1.05])
    para(doc, "These values match a hand calculation. The flower stem leans 6 px over 40 rows, so x grows "
              "by only 0.15 per step and first rounds up to 451 at k = 4. The flag’s bottom edge is "
              "horizontal (dy = 0), so p stays at -200 and y never changes. The footpath edge is steep "
              "(dx = 100, dy = 170), so p starts at 2(100) - 170 = 30 and x moves right only when p >= 0. "
              "In both circles p starts at 1 - r and grows by 2x + 1 while it is negative. For the arch it "
              "reaches 0 at k = 4, so the next point drops to y = 24. The pixel listed for a circle is the "
              "(xc + x, yc + y) point, and the other seven come from symmetry.", size=11)

    new_section(doc, code=True)
    heading(doc, "1.5 Source Code", 2, before=0)
    code_listing(doc, SRC1)


def problem2(doc):
    new_section(doc)
    heading(doc, "Problem 2: Simple Village Scenery (OpenGL - Using Built-in Functions)", 1)

    heading(doc, "2.1 Objective", 2, before=4)
    para(doc, "The second problem is a simple 2D village scene. This time the drawing is done with "
              "OpenGL’s built-in functions such as glBegin(), glEnd(), glVertex2f() and glColor3f(), "
              "together with primitives like GL_LINES, GL_TRIANGLES, GL_QUADS and GL_POLYGON, so there is "
              "no need to write DDA, Bresenham or Midpoint code. The scene needs a background (sky, ground, "
              "sun and two or three clouds), the village elements (two houses, one tree and a river or "
              "road) and any two extra elements. It has to be one complete scene on one screen, use at "
              "least four different primitives and give the major objects different colours, while "
              "staying simple and clean with no textures.")

    heading(doc, "2.2 Screenshot of Output", 2)
    figure(doc, SHOT2, "Figure 2: Output window of Problem 2 (Simple Village Scenery)")

    heading(doc, "2.3 How I Built the Scene", 2)
    heading(doc, "Setup", 3)
    para(doc, "The window is again 1000 x 600, and gluOrtho2D(0, 1000, 0, 600) maps one unit to one "
              "pixel. The horizon is at y = 330, with the sky above it and the field below it. I set the "
              "line width to 2 so that thin details such as the window bars, waves and birds are easy to "
              "see. To keep display() short I wrote four helper functions:")
    bullets(doc, [
        "quad(x, y, w, h) draws a rectangle with GL_QUADS",
        "triangle(x1, y1, x2, y2, x3, y3) draws a triangle with GL_TRIANGLES",
        "circle(cx, cy, r) draws a circle as a 60-sided GL_POLYGON, with the vertices worked out using "
        "cos and sin",
        "line(x1, y1, x2, y2) draws a line segment with GL_LINES",
    ])

    heading(doc, "Part A: Background", 3)
    para(doc, "The sky is one large GL_QUADS rectangle from the horizon to the top of the window. I gave "
              "its two bottom corners a pale blue and its two top corners a deeper blue, and OpenGL’s "
              "smooth shading blends them into a soft gradient. The ground is another large GL_QUADS "
              "rectangle in green, from y = 0 up to the horizon. The sun is a yellow circle of radius 42 at "
              "(840, 515), drawn as a GL_POLYGON.")
    para(doc, "There are three white clouds. Each one is built from four overlapping polygon circles, "
              "moved into place with glTranslatef() and drawn at a different size with glScalef() (1.0, "
              "0.8 and 1.1), so the three clouds do not look identical.")

    heading(doc, "Part B: Village elements", 3)
    bullets(doc, [
        "**Two houses:** both come from the same drawHouse() function. The body is a 100 x 70 GL_QUADS "
        "rectangle and the roof is a GL_TRIANGLES triangle that overhangs each wall by 12 units. The door "
        "is a dark brown quad, and there are two light blue window quads, each with a cross made of "
        "GL_LINES. The first house is at (90, 195) with scale 1.6, cream walls and a red roof. The second "
        "is at (380, 200) with scale 1.3, light brown walls and a brown roof, so it looks a little "
        "farther away.",
        "**One tree:** the trunk is a brown GL_QUADS rectangle and the leaves are a cluster of four green "
        "polygon circles. The tree stands at (720, 195) with scale 1.2.",
        "**River:** one long GL_QUADS shape across the whole width of the window. Its left end covers "
        "y = 40 to 130 and its right end covers y = 70 to 160, so the river runs at a slight angle. Short "
        "light blue GL_LINES on the water act as waves, and they follow the same slope.",
    ])

    heading(doc, "Part C: Extra elements", 3)
    para(doc, "Two extras were required and I added three:")
    bullets(doc, [
        "**Mountains:** four GL_TRIANGLES mountains stand on the horizon in two shades of blue-grey, "
        "which gives the range some depth. A small white triangle over the top 20% of each one works as "
        "a snow cap.",
        "**Boat on the river:** the hull is a trapezoid drawn with GL_POLYGON, the mast is a GL_LINES "
        "segment and the sail is a GL_TRIANGLES triangle. The boat sits on the water at (600, 85).",
        "**Birds:** five birds in the sky, each made of two GL_LINES segments that meet at one point to "
        "form a V.",
    ])

    heading(doc, "Rules and constraints", 3)
    para(doc, "Everything is drawn in one window as a single 2D scene. The program uses four different "
              "primitives: GL_QUADS, GL_TRIANGLES, GL_POLYGON and GL_LINES. Each major object has its own "
              "colour: a blue sky, a green field, a yellow sun, a cream house with a red roof, a light "
              "brown house with a brown roof, a green tree with a brown trunk and a blue river. No textures "
              "are used. Apart from the soft gradient in the sky, every shape is filled with one flat "
              "colour.")

    heading(doc, "2.4 Short Report", 2, new_page=True, before=0)
    para(doc, "The village scene is built from four OpenGL primitives: GL_QUADS, GL_TRIANGLES, GL_POLYGON "
              "and GL_LINES.")
    para(doc, "a. OpenGL primitives used for each object", bold=True, keep=True, after=4)
    simple_table(doc, ["Object", "Primitive(s) used"], [
        ["Sky", "GL_QUADS (one large rectangle with a colour gradient)"],
        ["Ground / field", "GL_QUADS"],
        ["Sun", "GL_POLYGON (60-sided circle)"],
        ["Clouds", "GL_POLYGON (four overlapping circles per cloud)"],
        ["Houses", "GL_QUADS for the body, door and windows, GL_TRIANGLES for the roof, GL_LINES for "
                   "the window bars"],
        ["Tree", "GL_QUADS for the trunk, GL_POLYGON circles for the leaves"],
        ["River", "GL_QUADS (one long slanted quad), GL_LINES for the waves"],
        ["Mountains", "GL_TRIANGLES (mountain and snow cap)"],
        ["Boat", "GL_POLYGON for the hull, GL_LINES for the mast, GL_TRIANGLES for the sail"],
        ["Birds", "GL_LINES (two segments in a V shape)"],
    ], [1.6, 4.65])
    para(doc, "b. How the scene is arranged (positions and scaling)", bold=True, keep=True,
         before=6, after=4)
    numbered(doc, [
        "gluOrtho2D(0, 1000, 0, 600) makes one unit equal to one pixel, and the horizon at y = 330 "
        "separates the sky from the field.",
        "Objects are drawn from back to front (sky, sun, mountains, clouds, ground, river, houses, tree, "
        "boat, birds), so the nearer objects cover the ones behind them.",
        "The sky, ground, river and mountains are drawn directly in window coordinates.",
        "Houses, the tree, clouds, the boat and the birds are built around their own origin (0, 0), then "
        "moved with glTranslatef(x, y, 0) and resized with glScalef(s, s, 1) between glPushMatrix() and "
        "glPopMatrix(), so one object’s transformation does not affect the next.",
        "The same drawHouse() is used twice, at (90, 195) with scale 1.6 and at (380, 200) with scale "
        "1.3. The tree uses scale 1.2 and the clouds use 0.8 to 1.1.",
    ])

    new_section(doc, code=True)
    heading(doc, "2.5 Source Code", 2, before=0)
    code_listing(doc, SRC2)


def closing(doc):
    new_section(doc)
    heading(doc, "How to Compile and Run", 1)
    para(doc, "Both programs are single C++ files that only need OpenGL and GLUT (freeglut on Windows "
              "and Linux).")
    para(doc, "**Windows (Code::Blocks / MinGW):** make a console project, add the .cpp file and put "
              "these libraries in the linker options:", align=LEFT, after=2)
    command(doc, "-lfreeglut -lopengl32 -lglu32")
    para(doc, "**Linux:**", align=LEFT, after=2)
    command(doc, "g++ bangladesh_tribute_scene.cpp -lGL -lGLU -lglut")
    para(doc, "**macOS:**", align=LEFT, after=2)
    command(doc, "clang++ bangladesh_tribute_scene.cpp -framework OpenGL -framework GLUT")
    para(doc, "The same commands work for village_scenery.cpp. Problem 1 prints its sample points to the "
              "console as soon as the window opens.")

    heading(doc, "Conclusion", 1, before=18)
    para(doc, "Doing the two problems one after the other showed me clearly how much work a graphics "
              "library does for us. In Problem 1 even a filled rectangle had to be built one scan-line at "
              "a time, and printing the decision parameters made it easy to see how Bresenham and the "
              "Midpoint circle method pick the next pixel using integer arithmetic only, while DDA depends "
              "on floating-point steps and rounding. In Problem 2 OpenGL took care of all of that, so the "
              "work was mostly about choosing a suitable primitive for each shape and placing the objects "
              "with translation and scaling. Reusing one house function at two different sizes was a good "
              "example of how transformations save both time and code.")


def main():
    doc = Document()
    setup_styles(doc)
    zoom = doc.settings.element.find(qn("w:zoom"))
    if zoom is not None and zoom.get(qn("w:percent")) is None:
        zoom.set(qn("w:percent"), "100")         # required by the schema

    first = doc.sections[0]
    page_setup(first)
    first.different_first_page_header_footer = True
    first.first_page_footer.paragraphs[0].text = ""     # no number on the cover
    page_number(first.footer.paragraphs[0])

    props = doc.core_properties
    now = datetime.datetime.now().replace(microsecond=0)
    props.author = props.last_modified_by = AUTHOR
    props.title = "Computer Graphics Mid Term Lab Assignment Report"
    props.subject = "Computer Graphics"
    props.comments = props.keywords = props.category = ""
    props.created = props.modified = now
    props.revision = 1

    cover(doc)
    problem1(doc)
    problem2(doc)
    closing(doc)

    doc.save(OUT)
    print("saved", OUT.relative_to(ROOT))
    result = subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(REP),
                             str(OUT)], capture_output=True, text=True)
    pdf = OUT.with_suffix(".pdf")
    print("pdf:", pdf.relative_to(ROOT) if pdf.exists() and result.returncode == 0 else result.stderr)


if __name__ == "__main__":
    main()
