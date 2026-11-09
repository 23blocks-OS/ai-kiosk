"""Draw the three fictional "Ciao Shop" screens as PNG (needs rsvg-convert). Run: python3 make.py"""
import subprocess, pathlib

HERE = pathlib.Path(__file__).parent
FONT = "font-family='Segoe UI, Arial, sans-serif'"


def button(x, y, w, h, label, fill="#e6e6e6", text="#1a1a1a"):
    return (f"<rect x='{x}' y='{y}' width='{w}' height='{h}' rx='3' fill='{fill}' stroke='#8a8a8a'/>"
            f"<text x='{x + w / 2}' y='{y + h / 2 + 6}' text-anchor='middle' font-size='18' fill='{text}' {FONT}>{label}</text>")


def frame(title, tabs, active, body):
    tab_svg = ""
    x = 20
    for i, t in enumerate(tabs):
        w = 30 + 11 * len(t)
        fill = "#ffffff" if i == active else "#d9e3f0"
        tab_svg += f"<rect x='{x}' y='62' width='{w}' height='36' fill='{fill}' stroke='#8a8a8a'/><text x='{x + w / 2}' y='86' text-anchor='middle' font-size='17' {FONT}>{t}</text>"
        x += w + 4
    return f"""<svg xmlns='http://www.w3.org/2000/svg' width='1024' height='640' viewBox='0 0 1024 640'>
<rect width='1024' height='640' fill='#f0f0f0'/>
<rect width='1024' height='44' fill='#1f4e79'/>
<text x='16' y='29' font-size='20' fill='white' {FONT}>{title} - Ciao Shop (demo, fictional)</text>
<rect x='930' y='8' width='80' height='28' fill='#c0392b'/><text x='970' y='28' text-anchor='middle' fill='white' font-size='18' {FONT}>X</text>
<rect y='44' width='1024' height='56' fill='#d9e3f0'/>
{tab_svg}
<rect x='20' y='98' width='984' height='520' fill='white' stroke='#8a8a8a'/>
{body}
</svg>"""


screens = {
    "sales": frame("Sales", ["Sales", "Inventory", "Settings"], 0,
        "<text x='40' y='140' font-size='22' font-weight='bold' " + FONT + ">Today: 14 sales, $482.50</text>"
        + button(40, 170, 220, 56, "New Sale", "#2e7d32", "white")
        + button(280, 170, 260, 56, "Print Daily Report")
        + button(560, 170, 200, 56, "Refund")
        + button(780, 170, 200, 56, "Close Register", "#f5c86b")
        + "<rect x='40' y='260' width='940' height='330' fill='#fafafa' stroke='#bbb'/>"
          "<text x='60' y='292' font-size='17' font-weight='bold' " + FONT + ">Time     Item                    Qty    Total</text>"
          "<text x='60' y='326' font-size='17' " + FONT + ">09:12    Notebook A5            2      $7.00</text>"
          "<text x='60' y='356' font-size='17' " + FONT + ">09:40    Pen blue (box)         1      $4.25</text>"
          "<text x='60' y='386' font-size='17' " + FONT + ">10:05    Stapler                1      $9.90</text>"),
    "inventory": frame("Inventory", ["Sales", "Inventory", "Settings"], 1,
        button(40, 120, 200, 50, "Add Item", "#2e7d32", "white")
        + button(260, 120, 220, 50, "Low Stock List")
        + button(500, 120, 240, 50, "Export to Excel")
        + "<rect x='40' y='200' width='940' height='380' fill='#fafafa' stroke='#bbb'/>"
          "<text x='60' y='232' font-size='17' font-weight='bold' " + FONT + ">Item                     In stock    Reorder at</text>"
          "<text x='60' y='266' font-size='17' " + FONT + ">Notebook A5               38          10</text>"
          "<text x='60' y='296' font-size='17' fill='#c0392b' " + FONT + ">Pen blue (box)            3           5   LOW</text>"
          "<text x='60' y='326' font-size='17' " + FONT + ">Stapler                    12          4</text>"),
    "settings": frame("Settings", ["Sales", "Inventory", "Settings"], 2,
        "<text x='40' y='140' font-size='22' font-weight='bold' " + FONT + ">Settings</text>"
        + button(40, 170, 300, 56, "Receipt Printer...")
        + button(40, 245, 300, 56, "Tax Rate...")
        + button(40, 320, 300, 56, "Backup Now", "#2e7d32", "white")
        + button(40, 395, 300, 56, "Change Password...")
        + "<text x='380' y='205' font-size='17' fill='#555' " + FONT + ">Printer: USB Receipt 80mm (connected)</text>"
          "<text x='380' y='280' font-size='17' fill='#555' " + FONT + ">Tax rate: 8.8%</text>"
          "<text x='380' y='355' font-size='17' fill='#555' " + FONT + ">Last backup: yesterday 18:02</text>"),
}
for name, svg in screens.items():
    (HERE / f"{name}.svg").write_text(svg)
    subprocess.run(["rsvg-convert", "-o", str(HERE / f"{name}.png"), str(HERE / f"{name}.svg")], check=True)
    (HERE / f"{name}.svg").unlink()
