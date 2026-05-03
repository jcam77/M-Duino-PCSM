from pathlib import Path
from datetime import date

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent.parent
DOCX_PATH = ROOT / "M-Duino-Trigger_Box_Code_Explanation" / "Trigger_Box_Controller_Explanation_v000.docx"
FLOWCHART_PATH = ROOT / "Diagrams" / "trigger_box_sequence_diagram_v004.png"
FALLBACK_FLOWCHART_PATH = ROOT / "Diagrams" / "trigger_box_sequence_diagram.png"


ACCENT = RGBColor(27, 76, 120)
MUTED = RGBColor(90, 90, 90)
LIGHT_FILL = "EEF4F8"
LIGHT_BORDER = "D9E2EA"


def set_page_number(paragraph):
    run = paragraph.add_run()
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = "PAGE"
    fld_sep = OxmlElement("w:fldChar")
    fld_sep.set(qn("w:fldCharType"), "separate")
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run._r.append(fld_begin)
    run._r.append(instr)
    run._r.append(fld_sep)
    run._r.append(fld_end)


def set_cell_shading(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def set_cell_text(cell, text, bold=False):
    cell.text = ""
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    run = p.add_run(text)
    run.bold = bold
    run.font.name = "Arial"
    run.font.size = Pt(10.5)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def style_table(table):
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.LEFT
    for row_index, row in enumerate(table.rows):
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                paragraph.paragraph_format.space_after = Pt(0)
                paragraph.paragraph_format.space_before = Pt(0)
            if row_index == 0:
                set_cell_shading(cell, LIGHT_FILL)


def add_bullet(document, text):
    p = document.add_paragraph(style="List Bullet")
    p.paragraph_format.space_after = Pt(6)
    p.add_run(text)


def add_number(document, text):
    p = document.add_paragraph(style="List Number")
    p.paragraph_format.space_after = Pt(6)
    p.add_run(text)


def create_styles(document):
    styles = document.styles

    normal = styles["Normal"]
    normal.font.name = "Arial"
    normal.font.size = Pt(11)
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.08

    title = styles["Title"]
    title.font.name = "Arial"
    title.font.size = Pt(22)
    title.font.bold = True
    title.font.color.rgb = ACCENT

    subtitle = styles["Subtitle"]
    subtitle.font.name = "Arial"
    subtitle.font.size = Pt(11.5)
    subtitle.font.color.rgb = MUTED

    for name, size in [("Heading 1", 16), ("Heading 2", 13), ("Heading 3", 11.5)]:
        style = styles[name]
        style.font.name = "Arial"
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = ACCENT

    if "Callout" not in styles:
        style = styles.add_style("Callout", WD_STYLE_TYPE.PARAGRAPH)
        style.base_style = styles["Normal"]
        style.font.name = "Arial"
        style.font.size = Pt(10.5)


def configure_page(document):
    section = document.sections[0]
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(0.8)
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)

    header_p = section.header.paragraphs[0]
    header_p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    header_run = header_p.add_run("Trigger Box Controller Guide")
    header_run.font.name = "Arial"
    header_run.font.size = Pt(9)
    header_run.font.color.rgb = MUTED

    p_pr = header_p._p.get_or_add_pPr()
    p_bdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "6")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), "BFCAD4")
    p_bdr.append(bottom)
    p_pr.append(p_bdr)

    footer_p = section.footer.paragraphs[0]
    footer_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    footer_run = footer_p.add_run("Page ")
    footer_run.font.name = "Arial"
    footer_run.font.size = Pt(9)
    footer_run.font.color.rgb = MUTED
    set_page_number(footer_p)


def add_paragraph(document, text, bold_prefix=None):
    p = document.add_paragraph()
    if bold_prefix:
        run = p.add_run(bold_prefix)
        run.bold = True
        p.add_run(text)
    else:
        p.add_run(text)
    return p


def enforce_run_font(run, font_name="Arial"):
    run.font.name = font_name
    r_pr = run._element.get_or_add_rPr()
    r_fonts = r_pr.rFonts
    if r_fonts is None:
        r_fonts = OxmlElement("w:rFonts")
        r_pr.append(r_fonts)
    r_fonts.set(qn("w:ascii"), font_name)
    r_fonts.set(qn("w:hAnsi"), font_name)
    r_fonts.set(qn("w:cs"), font_name)


def enforce_arial_everywhere(document):
    def process_paragraphs(paragraphs):
        for paragraph in paragraphs:
            for run in paragraph.runs:
                enforce_run_font(run)

    process_paragraphs(document.paragraphs)

    for table in document.tables:
        for row in table.rows:
            for cell in row.cells:
                process_paragraphs(cell.paragraphs)

    for section in document.sections:
        process_paragraphs(section.header.paragraphs)
        process_paragraphs(section.footer.paragraphs)


def build_flowchart_image(path: Path):
    width, height = 1800, 1200
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)

    try:
        title_font = ImageFont.truetype("Arial.ttf", 40)
        section_font = ImageFont.truetype("Arial Bold.ttf", 24)
        box_font = ImageFont.truetype("Arial.ttf", 24)
        small_font = ImageFont.truetype("Arial.ttf", 20)
    except OSError:
        title_font = ImageFont.load_default()
        section_font = ImageFont.load_default()
        box_font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    def box(x1, y1, x2, y2, text, fill="#EEF4F8", outline="#1B4C78", font=box_font, radius=22):
        draw.rounded_rectangle((x1, y1, x2, y2), radius=radius, fill=fill, outline=outline, width=3)
        draw.multiline_text(
            ((x1 + x2) / 2, (y1 + y2) / 2),
            text,
            fill="#111111",
            font=font,
            anchor="mm",
            align="center",
            spacing=4,
        )

    def arrow(x1, y1, x2, y2, text=None, color="#48515A", width_px=4):
        draw.line((x1, y1, x2, y2), fill=color, width=width_px)
        if abs(y2 - y1) >= abs(x2 - x1):
            direction = 1 if y2 > y1 else -1
            tip = [(x2, y2), (x2 - 10, y2 - 18 * direction), (x2 + 10, y2 - 18 * direction)]
        else:
            direction = 1 if x2 > x1 else -1
            tip = [(x2, y2), (x2 - 18 * direction, y2 - 10), (x2 - 18 * direction, y2 + 10)]
        draw.polygon(tip, fill=color)
        if text:
            draw.rounded_rectangle(
                (((x1 + x2) / 2) - 90, ((y1 + y2) / 2) - 22, ((x1 + x2) / 2) + 90, ((y1 + y2) / 2) + 10),
                radius=10,
                fill="white",
            )
            draw.text(((x1 + x2) / 2, (y1 + y2) / 2 - 6), text, fill=color, font=small_font, anchor="mm")

    def connector(points, text=None, color="#48515A"):
        for start, end in zip(points, points[1:]):
            arrow(start[0], start[1], end[0], end[1], None, color=color)
        if text:
            mid = points[len(points) // 2]
            draw.rounded_rectangle((mid[0] - 95, mid[1] - 24, mid[0] + 95, mid[1] + 8), radius=10, fill="white")
            draw.text((mid[0], mid[1] - 8), text, fill=color, font=small_font, anchor="mm")

    def bullet_list(x, y, lines, color="#2A2A2A"):
        cursor_y = y
        for line in lines:
            draw.ellipse((x, cursor_y + 8, x + 8, cursor_y + 16), fill=color)
            draw.text((x + 24, cursor_y), line, fill=color, font=small_font)
            cursor_y += 36

    draw.rounded_rectangle((40, 40, width - 40, height - 40), radius=30, outline="#D8E0E8", width=2)
    draw.rounded_rectangle((65, 95, width - 65, 150), radius=20, fill="#F5F8FB", outline="#D8E0E8", width=2)
    draw.text((width / 2, 122), "Trigger Box Sequence Overview", fill="#1B4C78", font=title_font, anchor="mm")

    draw.text((330, 200), "Spark-test branch", fill="#1B4C78", font=section_font, anchor="mm")
    draw.text((1110, 200), "Hydrogen-test branch", fill="#1B4C78", font=section_font, anchor="mm")
    draw.text((1560, 200), "Lockout / reset", fill="#9A5B00", font=section_font, anchor="mm")

    box(720, 230, 1080, 310, "Power on\nSafe startup", fill="#F7FAFC")
    box(720, 360, 1080, 440, "Mode selection", fill="#F7FAFC")
    arrow(900, 310, 900, 360)

    box(90, 500, 560, 670, "Spark-test mode\n\nArm active -> periodic ignition command cycles\nHot wires OFF\nDAQ OFF")
    connector([(720, 400), (560, 400), (325, 500)], "Mode HIGH", color="#1B4C78")

    box(720, 500, 1080, 580, "Idle\nAll outputs OFF")
    box(720, 640, 1080, 720, "Armed\nArm light ON\nWaiting for Trigger")
    box(720, 780, 1080, 880, "Melting\n3 hot-wire relays ON\nfor hotWireBurn_us")
    box(720, 940, 1080, 1020, "SparkOut ON\ncoil dwell / charge\nDAQ still OFF")
    box(1180, 940, 1540, 1020, "DAQ ON during final\ndaqPulse_us of dwell", fill="#EEF7F2", outline="#2E7D4F")
    box(1180, 1080, 1540, 1160, "Fired lockout\nAll outputs OFF", fill="#F3F6FA")

    connector([(1080, 400), (1260, 400), (1260, 470), (900, 470), (900, 500)], "Mode LOW", color="#1B4C78")
    arrow(900, 580, 900, 640, "Arm active")
    arrow(900, 720, 900, 780, "Trigger")
    arrow(900, 880, 900, 940)
    arrow(1080, 980, 1180, 980, "start DAQ", color="#2E7D4F")
    arrow(1360, 1020, 1360, 1080, "end spark", color="#2E7D4F")

    box(1380, 500, 1720, 690, "Lockout states\n\nFAIL\nABORTED\nFIRED", fill="#FFF4E8", outline="#9A5B00")
    box(1380, 760, 1720, 920, "Reset condition\n\nArm = OFF\nTrigger = OFF", fill="#FFF9F0", outline="#9A5B00")

    img.save(path)


def build_document():
    document = Document()
    create_styles(document)
    configure_page(document)

    if not FLOWCHART_PATH.exists():
        build_flowchart_image(FALLBACK_FLOWCHART_PATH)

    title = document.add_paragraph(style="Title")
    title.add_run("Trigger Box Controller")

    subtitle = document.add_paragraph(style="Subtitle")
    subtitle.add_run(
        "Code review summary of the reviewed M-Duino control logic for operator understanding, peer review, and lab handover."
    )

    meta = document.add_table(rows=3, cols=2)
    meta.alignment = WD_TABLE_ALIGNMENT.LEFT
    meta.autofit = True
    entries = [
        ("Target platform", "Industrial Shields M-Duino 19R+"),
        ("Document date", str(date.today())),
        ("Purpose", "Explain the reviewed M-Duino trigger-box logic for operator understanding, peer review, and lab handover."),
    ]
    for r, (label, value) in enumerate(entries):
        set_cell_text(meta.cell(r, 0), label, bold=True)
        set_cell_text(meta.cell(r, 1), value)
    style_table(meta)

    document.add_heading("1. Purpose", level=1)
    add_paragraph(
        document,
        "This controller manages a trigger box with two operating modes:",
    )
    add_bullet(document, "`Spark-test mode`")
    add_bullet(document, "`Hydrogen-test mode`")
    add_paragraph(document, "In hydrogen-test mode, the controller enforces a defined sequence:")
    for item in [
        "The operator arms the system.",
        "The operator presses `Trigger`.",
        "The three hot-wire relay outputs turn on for a fixed time.",
        "The ignition command output turns on and the coil dwell interval begins.",
        "The DAQ trigger turns on near the end of the dwell interval.",
        "All outputs turn off.",
        "If the ignition system fires on coil collapse, the physical spark is released when the dwell signal goes low.",
        "The system remains locked out until both `Arm` and `Trigger` are released.",
    ]:
        add_number(document, item)
    add_paragraph(
        document,
        "The revised code is longer than the original because it makes the sequence explicit and easier to audit. Instead of relying on several interacting flags, it uses a named state machine.",
    )

    document.add_heading("2. Hardware Signals", level=1)
    io_table = document.add_table(rows=1, cols=4)
    headers = ["Signal", "Type", "Purpose", "Meaning in the logic"]
    for i, header in enumerate(headers):
        set_cell_text(io_table.cell(0, i), header, bold=True)
    rows = [
        ("`Arm`", "Digital input", "Both modes", "Allows the system to arm. Must remain active during hazardous phases."),
        ("`Trigger`", "Digital input", "Hydrogen-test mode", "Starts the firing sequence after arming. Treated as a momentary start command."),
        ("`Mode`", "Digital input", "Both modes", "Selects `Spark-test` or `Hydrogen-test` behavior."),
        ("`ArmLight`", "Digital output", "Both modes", "Indicates that the system is armed or in an active sequence."),
        ("`HotWire1`, `HotWire2`, `HotWire3`", "Digital outputs", "Hydrogen-test mode", "Drive the three relay channels that control the external hot-wire power system."),
        ("`SparkOut`", "Digital output", "Both modes", "Commands the ignition stage. In a coil-based setup, this typically defines the dwell / coil-charge interval rather than the exact physical spark duration."),
        ("`DAQTrig`", "Digital output", "Hydrogen-test mode", "Sends a timing pulse to the data-acquisition system."),
    ]
    for row in rows:
        cells = io_table.add_row().cells
        for idx, value in enumerate(row):
            set_cell_text(cells[idx], value, bold=False)
    style_table(io_table)

    document.add_heading("3. Unit Convention", level=1)
    add_paragraph(
        document,
        "The code uses explicit units where they matter.",
    )
    add_bullet(document, "Any variable ending in `_us` is in `microseconds`.")
    add_bullet(document, "Pins, booleans, and states do not have physical units, so they do not get a unit suffix.")
    add_paragraph(document, "Examples:")
    add_bullet(document, "`hotWireBurn_us`")
    add_bullet(document, "`sparkDwell_us`")
    add_bullet(document, "`daqPulse_us`")
    add_bullet(document, "`sparkTestInterval_us`")
    add_bullet(document, "`debounce_us`")
    add_bullet(document, "`lastSerialPrint_us`")
    add_bullet(document, "`meltStart_us`")
    add_bullet(document, "`sparkStart_us`")
    add_paragraph(
        document,
        "This naming style makes the timing easier to understand and reduces mistakes when adjusting values.",
    )

    document.add_heading("4. Main Timing Variables", level=1)
    timing = document.add_table(rows=1, cols=4)
    for idx, header in enumerate(["Variable", "Current value", "Unit", "Meaning"]):
        set_cell_text(timing.cell(0, idx), header, bold=True)
    timing_rows = [
        ("`hotWireBurn_us`", "`10,000,000`", "microseconds", "Keeps the three hot-wire relay outputs on for 10 seconds."),
        ("`sparkDwell_us`", "`5,000`", "microseconds", "Coil dwell / ignition-command duration before release. In a coil-based system, the physical spark is typically produced when this command goes low."),
        ("`daqPulse_us`", "`600`", "microseconds", "Width of the DAQ trigger pulse during the final part of the dwell interval."),
        ("`sparkTestInterval_us`", "`500,000`", "microseconds", "Time between ignition-command cycles in spark-test mode."),
        ("`debounce_us`", "`30,000`", "microseconds", "Stable input time required before accepting a switch change."),
        ("`serialPrintInterval_us`", "`250,000`", "microseconds", "Limits how often the serial monitor is updated."),
    ]
    for row in timing_rows:
        cells = timing.add_row().cells
        for idx, value in enumerate(row):
            set_cell_text(cells[idx], value, bold=False)
    style_table(timing)

    document.add_heading("5. Sequence Overview", level=1)
    add_paragraph(
        document,
        "",
    )
    picture_path = FLOWCHART_PATH if FLOWCHART_PATH.exists() else FALLBACK_FLOWCHART_PATH
    document.add_picture(str(picture_path), width=Inches(6.6))
    cap = document.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap_run = cap.add_run("Figure 1. Trigger box sequence overview.")
    cap_run.italic = True
    cap_run.font.size = Pt(9.5)
    cap_run.font.color.rgb = MUTED
    add_paragraph(document, "Important interpretation note:")
    add_bullet(document, "The controller diagram is correct at the `SparkOut` command level.")
    add_bullet(document, "In a coil-based ignition system, the physical spark event is typically associated with the falling edge of `SparkOut`, not the moment `SparkOut` first goes high.")
    add_bullet(document, "This means the diagram should be read as a controller-sequence diagram, not as a literal plasma-duration diagram.")

    add_paragraph(document, "Hydrogen-test mode")
    for item in [
        "The controller starts in `stateIdle` with all outputs off.",
        "If `Trigger` is already active before proper arming, the controller enters `stateFail`.",
        "When `Arm` becomes active, the controller enters `stateArmed`.",
        "When `Trigger` is pressed, the controller starts the hot-wire stage if `useHotWireStep = true`.",
        "In `stateMelting`, all three hot-wire relay outputs stay on for `hotWireBurn_us`.",
        "After that delay, the hot-wire outputs turn off and the ignition command stage begins.",
        "In `stateSparkWaitDaq`, `SparkOut` is on and `DAQTrig` is still off.",
        "In a coil-based system, this interval is the coil dwell / coil-charge interval.",
        "After `sparkDwell_us - daqPulse_us`, the controller turns `DAQTrig` on.",
        "At the end of `sparkDwell_us`, the controller turns both `SparkOut` and `DAQTrig` off.",
        "If the ignition system fires on coil collapse, the physical spark is released at or immediately after this falling edge.",
        "The controller enters `stateFired`.",
        "The system remains locked out until both `Arm` and `Trigger` are released.",
    ]:
        add_number(document, item)
    add_paragraph(document, "Spark-test mode")
    for item in [
        "The hot-wire outputs stay off.",
        "The DAQ output stays off.",
        "If `Arm` is active, the controller generates periodic ignition-command cycles.",
        "If `Arm` is released, the controller turns the spark output off immediately.",
    ]:
        add_bullet(document, item)

    document.add_heading("6. State Machine", level=1)
    add_paragraph(
        document,
        "The reviewed version uses a state machine instead of several loosely connected flags.",
    )
    state_table = document.add_table(rows=1, cols=2)
    for idx, header in enumerate(["State", "Meaning"]):
        set_cell_text(state_table.cell(0, idx), header, bold=True)
    state_rows = [
        ("`stateIdle`", "Safe waiting state with all outputs off."),
        ("`stateArmed`", "Arm is active and the controller is waiting for Trigger."),
        ("`stateMelting`", "The three hot-wire relay outputs are energized."),
        ("`stateSparkWaitDaq`", "`SparkOut` is active and the controller is waiting for the DAQ start point. In a coil-based system, this corresponds to the dwell / charge interval."),
        ("`stateSparkWaitEnd`", "`SparkOut` and `DAQTrig` are active and the controller is waiting for the end of the dwell interval."),
        ("`stateFired`", "The sequence completed successfully. Reset is required before a new cycle."),
        ("`stateFail`", "An invalid start condition occurred, such as Trigger being active before proper arming."),
        ("`stateAborted`", "The sequence was interrupted because Arm was released during a hazardous phase."),
    ]
    for row in state_rows:
        cells = state_table.add_row().cells
        for idx, value in enumerate(row):
            set_cell_text(cells[idx], value)
    style_table(state_table)

    document.add_heading("7. Why This Version Is Safer and Easier to Read", level=1)
    add_paragraph(document, "Compared with the original short sketch, the reviewed version improves several important points:")
    for item in [
        "The hot-wire relay outputs are clearly separated from boolean flags.",
        "Timing variables include units in their names.",
        "The main sequence is explicit and easier to follow.",
        "Lockout behavior is deliberate rather than accidental.",
        "Unsafe transitions such as releasing `Arm` during the hot-wire or spark phase are handled immediately.",
        "Mode changes force the controller back to a safe state.",
    ]:
        add_bullet(document, item)

    document.add_heading("8. Code Structure", level=1)
    structure = document.add_table(rows=1, cols=2)
    for idx, header in enumerate(["Function or block", "Role"]):
        set_cell_text(structure.cell(0, idx), header, bold=True)
    structure_rows = [
        ("`setup()`", "Configures inputs and outputs, starts serial communication, and forces a safe startup state."),
        ("`loop()`", "Updates inputs, checks for mode changes, runs the appropriate mode handler, and prints status."),
        ("`DebouncedInput`", "Filters switch bounce so mechanical inputs behave more reliably."),
        ("`handleSparkTestMode()`", "Runs ignition-command behavior with a defined interval."),
        ("`handleHydrogenTestMode()`", "Runs the main sequence and lockout logic."),
        ("`startMeltingOrSpark()`", "Chooses whether to start the hot-wire stage or jump directly to the ignition-command stage."),
        ("`startSparkSequence()`", "Forces hot wires off, starts the ignition-command stage, and begins dwell timing."),
        ("`allOutputsOff()`", "Provides a reusable safe-off command for all outputs."),
    ]
    for row in structure_rows:
        cells = structure.add_row().cells
        for idx, value in enumerate(row):
            set_cell_text(cells[idx], value)
    style_table(structure)

    document.add_heading("9. Safety Behaviors Built Into the Logic", level=1)
    for item in [
        "All outputs are forced off at startup.",
        "All outputs are forced off after firing, failure, abort, or mode change.",
        "The controller requires `Arm` to remain active during the melting and spark phases.",
        "The controller requires both `Arm` and `Trigger` to be released before re-arming after a lockout state.",
        "The hot-wire outputs are turned off before the ignition-command stage begins.",
    ]:
        add_bullet(document, item)
    add_paragraph(document, "Important note:")
    add_bullet(document, "This software is not a substitute for a hardwired emergency stop.")
    add_bullet(document, "The emergency stop should physically remove power from the hot-wire supply and the spark system.")

    document.add_heading("10. Hardware Points to Confirm", level=1)
    add_paragraph(document, "Before using the controller on the real setup, two hardware questions should be confirmed:")
    add_number(document, "`Relay polarity`\nSome relay modules are active `LOW` rather than active `HIGH`. If the relays energize when the controller output goes low, the output logic in the code must be inverted.")
    add_number(document, "`Input wiring`\nThe `Arm`, `Trigger`, and `Mode` inputs must be electrically well-defined. If the wiring allows the input to float, the controller can behave unpredictably.")

    document.add_heading("11. Practical Test Strategy", level=1)
    add_paragraph(document, "Recommended step-by-step validation:")
    add_number(document, "Power the M-Duino correctly from its intended external supply.")
    add_number(document, "Connect the Mac by USB only for upload and serial monitoring.")
    add_number(document, "Test the logic first with the hazardous power stages disconnected.")
    add_number(document, "Use the serial monitor to check `Mode`, `Arm`, `Trigger`, and the current state name.")
    add_number(document, "Verify relay polarity on each hot-wire channel before connecting the real hot-wire power circuit.")
    add_number(document, "Introduce the real hot-wire and spark hardware only after the low-risk logic checks pass.")

    document.add_heading("12. Short Summary", level=1)
    add_paragraph(
        document,
        "This reviewed version keeps the same overall purpose as the original sketch, but it is easier to understand, easier to explain, and easier to review with colleagues. The main improvements are:",
    )
    for item in [
        "clearer naming",
        "explicit timing units",
        "a proper state machine",
        "deliberate safety and lockout behavior",
        "a clearer explanation of how hot wires, coil dwell, ignition release, and DAQ interact",
    ]:
        add_bullet(document, item)

    enforce_arial_everywhere(document)
    document.save(DOCX_PATH)


if __name__ == "__main__":
    build_document()
