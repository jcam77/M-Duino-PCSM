from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = ROOT / "Diagrams" / "mduino_trigger_scope_connections_v000.png"

W = 1800
H = 1320
BG = (248, 250, 252)
PANEL_BG = (255, 255, 255)
BORDER = (198, 210, 224)
TEXT = (23, 35, 49)
MUTED = (92, 107, 122)
ACCENT = (27, 76, 120)
GREEN = (58, 136, 92)
ORANGE = (184, 96, 32)
PURPLE = (109, 76, 164)


def get_font(size, bold=False):
    candidates = []
    if bold:
        candidates.extend(
            [
                "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
                "/System/Library/Fonts/Supplemental/Helvetica Bold.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            ]
        )
    candidates.extend(
        [
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/System/Library/Fonts/Supplemental/Helvetica.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
    )
    for path in candidates:
        try:
            return ImageFont.truetype(path, size=size)
        except Exception:
            continue
    return ImageFont.load_default()


TITLE_FONT = get_font(40, bold=True)
SUB_FONT = get_font(22)
SECTION_FONT = get_font(26, bold=True)
LABEL_FONT = get_font(20, bold=True)
BODY_FONT = get_font(18)
SMALL_FONT = get_font(16)


def rounded_box(draw, xy, fill, outline=BORDER, width=3, radius=18):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def draw_box(draw, x, y, w, h, title, subtitle="", fill=PANEL_BG, accent=ACCENT):
    rounded_box(draw, (x, y, x + w, y + h), fill=fill)
    draw.rounded_rectangle((x, y, x + w, y + 44), radius=18, fill=accent)
    draw.text((x + 18, y + 9), title, font=LABEL_FONT, fill=(255, 255, 255))
    if subtitle:
        draw.multiline_text((x + 18, y + 60), subtitle, font=BODY_FONT, fill=TEXT, spacing=5)


def arrow(draw, start, end, fill=ACCENT, width=5, head=16):
    x1, y1 = start
    x2, y2 = end
    draw.line((x1, y1, x2, y2), fill=fill, width=width)
    if abs(x2 - x1) >= abs(y2 - y1):
        if x2 >= x1:
            pts = [(x2, y2), (x2 - head, y2 - head // 2), (x2 - head, y2 + head // 2)]
        else:
            pts = [(x2, y2), (x2 + head, y2 - head // 2), (x2 + head, y2 + head // 2)]
    else:
        if y2 >= y1:
            pts = [(x2, y2), (x2 - head // 2, y2 - head), (x2 + head // 2, y2 - head)]
        else:
            pts = [(x2, y2), (x2 - head // 2, y2 + head), (x2 + head // 2, y2 + head)]
    draw.polygon(pts, fill=fill)


def label(draw, x, y, text, fill=MUTED, font=SMALL_FONT):
    draw.text((x, y), text, font=font, fill=fill)


def panel_title(draw, x, y, text, subtext):
    draw.text((x, y), text, font=SECTION_FONT, fill=ACCENT)
    draw.text((x, y + 34), subtext, font=SMALL_FONT, fill=MUTED)


def main():
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    draw.text((70, 40), "M-Duino Trigger Timing Characterisation", font=TITLE_FONT, fill=TEXT)
    draw.text(
        (70, 92),
        "Oscilloscope connection guide for controller delay, DAQ splitter timing, and camera-vs-DAQ checks",
        font=SUB_FONT,
        fill=MUTED,
    )

    panel_h = 330
    margin_x = 70
    gap_y = 40
    panel_w = W - 2 * margin_x

    # Panel 1
    y1 = 160
    rounded_box(draw, (margin_x, y1, margin_x + panel_w, y1 + panel_h), fill=PANEL_BG)
    panel_title(
        draw,
        margin_x + 28,
        y1 + 20,
        "Run 1. Controller delay measurement",
        "Measures input -> DAQ trigger output and input -> camera trigger path",
    )
    draw_box(draw, 120, y1 + 110, 210, 105, "Pulse Source", "Clean test edge\nused as timing reference", accent=GREEN)
    draw_box(draw, 500, y1 + 100, 260, 125, "M-Duino", "Input under test\nDAQ trigger output\nCamera trigger path")
    draw_box(draw, 1030, y1 + 80, 560, 170, "Oscilloscope", "CH1 = input event\nCH2 = DAQ trigger output\nCH3 = camera trigger path", accent=PURPLE)
    arrow(draw, (330, y1 + 145), (500, y1 + 145), fill=GREEN)
    arrow(draw, (330, y1 + 190), (1030, y1 + 125), fill=GREEN)
    arrow(draw, (760, y1 + 145), (1030, y1 + 175), fill=ACCENT)
    arrow(draw, (760, y1 + 205), (1030, y1 + 225), fill=ORANGE)
    label(draw, 375, y1 + 128, "test pulse to input")
    label(draw, 560, y1 + 122, "CH2")
    label(draw, 560, y1 + 202, "CH3", fill=ORANGE)
    label(draw, 610, y1 + 270, "Trigger the scope on CH1. Measure all delays at the same edge crossing.", fill=TEXT, font=BODY_FONT)

    # Panel 2
    y2 = y1 + panel_h + gap_y
    rounded_box(draw, (margin_x, y2, margin_x + panel_w, y2 + panel_h), fill=PANEL_BG)
    panel_title(
        draw,
        margin_x + 28,
        y2 + 20,
        "Run 2. DAQ splitter timing",
        "Measures M-Duino DAQ output -> DAQ 1, M-Duino DAQ output -> DAQ 2, and DAQ 1 -> DAQ 2 skew",
    )
    draw_box(draw, 120, y2 + 130, 260, 110, "M-Duino DAQ Output", "Probe this point before\nthe BNC splitter", accent=ACCENT)
    draw_box(draw, 560, y2 + 145, 180, 80, "BNC Splitter", accent=GREEN)
    draw_box(draw, 930, y2 + 90, 220, 90, "DAQ 1 Trigger In", accent=ORANGE)
    draw_box(draw, 930, y2 + 205, 220, 90, "DAQ 2 Trigger In", accent=ORANGE)
    draw_box(draw, 1290, y2 + 80, 290, 190, "Oscilloscope", "CH1 = DAQ output\nCH2 = DAQ 1 input\nCH3 = DAQ 2 input", accent=PURPLE)
    arrow(draw, (380, y2 + 185), (560, y2 + 185), fill=ACCENT)
    arrow(draw, (740, y2 + 185), (930, y2 + 135), fill=GREEN)
    arrow(draw, (740, y2 + 185), (930, y2 + 250), fill=GREEN)
    arrow(draw, (380, y2 + 155), (1290, y2 + 120), fill=ACCENT)
    arrow(draw, (1150, y2 + 135), (1290, y2 + 170), fill=ORANGE)
    arrow(draw, (1150, y2 + 250), (1290, y2 + 220), fill=ORANGE)
    label(draw, 450, y2 + 148, "CH1 reference")
    label(draw, 1180, y2 + 144, "CH2", fill=ORANGE)
    label(draw, 1180, y2 + 244, "CH3", fill=ORANGE)
    label(draw, 580, y2 + 282, "Keep CH1 at the same physical node in every DAQ comparison run.", fill=TEXT, font=BODY_FONT)

    # Panel 3
    y3 = y2 + panel_h + gap_y
    rounded_box(draw, (margin_x, y3, margin_x + panel_w, y3 + panel_h), fill=PANEL_BG)
    panel_title(
        draw,
        margin_x + 28,
        y3 + 20,
        "Run 3. Camera versus DAQ timing",
        "Measures relative offset between the camera trigger branch and the DAQ trigger branch",
    )
    draw_box(draw, 120, y3 + 130, 260, 110, "M-Duino DAQ Output", "Use as common timing\nreference if possible", accent=ACCENT)
    draw_box(draw, 610, y3 + 85, 220, 90, "Camera Trigger Path", accent=ORANGE)
    draw_box(draw, 610, y3 + 210, 220, 90, "DAQ Trigger Input", accent=GREEN)
    draw_box(draw, 1100, y3 + 80, 480, 190, "Oscilloscope", "CH1 = M-Duino DAQ output\nCH2 = camera trigger path\nCH3 = DAQ trigger input\nRepeat with DAQ 2 if needed", accent=PURPLE)
    arrow(draw, (380, y3 + 165), (1100, y3 + 120), fill=ACCENT)
    arrow(draw, (830, y3 + 130), (1100, y3 + 175), fill=ORANGE)
    arrow(draw, (830, y3 + 255), (1100, y3 + 225), fill=GREEN)
    label(draw, 870, y3 + 120, "CH2", fill=ORANGE)
    label(draw, 870, y3 + 245, "CH3", fill=GREEN)
    label(draw, 470, y3 + 282, "The most important result here is the stability of the camera-to-DAQ offset.", fill=TEXT, font=BODY_FONT)

    footer = "Use the same trigger edge as the real experiment, measure at a consistent edge crossing, and probe the real experiment nodes rather than convenient intermediate points."
    draw.text((70, H - 52), footer, font=SMALL_FONT, fill=MUTED)

    img.save(OUTPUT_PATH, format="PNG")


if __name__ == "__main__":
    main()
