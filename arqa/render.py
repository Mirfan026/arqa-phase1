"""
ARQA Phase 1 — Renderers (Day 13)

Turns a Design Agent layout into visual output. Rendering is a SEPARATE
concern from layout generation: the same layout can be drawn as ASCII,
SVG, (later) PNG or DXF. This module holds the SVG renderer — zero
dependencies, vector output, opens in any browser.

Author: Muhammad Irfan
"""

# Scale + margin for metre -> pixel mapping.
SCALE = 20      # 1 metre = 20 pixels
MARGIN = 40     # px border around the plot
LABEL_PANEL = 150  # px reserved on the right for the title/legend

# Color per room type (light fills; majlis distinct to highlight the
# culturally-important guest space).
ROOM_COLORS = {
    "bedrooms":  "#bfdbfe",   # light blue
    "bathrooms": "#bbf7d0",   # light green
    "kitchen":   "#fed7aa",   # light orange
    "living":    "#fde68a",   # light gold
    "majlis":    "#ddd6fe",   # light purple (distinct — cultural space)
}
DEFAULT_COLOR = "#e5e7eb"     # grey for any other room type


def _m2px(metres):
    """Convert a metre length to pixels (size only, no margin)."""
    return metres * SCALE


def render_svg(layout, title=None):
    """
    Render a layout dict (from design_agent.generate_layout) to an SVG string.

    Each room -> a colored <rect> with a <text> label (name + area).
    Plus a plot border, a title, and a legend on the right.
    """
    plot = layout["plot"]
    plot_w_px = _m2px(plot["width"])
    plot_h_px = _m2px(plot["height"])

    # Total image size: plot + margins + right-side label panel.
    img_w = MARGIN * 2 + plot_w_px + LABEL_PANEL
    img_h = MARGIN * 2 + plot_h_px

    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{img_w:.0f}" height="{img_h:.0f}" '
        f'viewBox="0 0 {img_w:.0f} {img_h:.0f}" '
        f'font-family="Arial, sans-serif">'
    )
    # White background
    parts.append(f'<rect x="0" y="0" width="{img_w:.0f}" height="{img_h:.0f}" fill="white"/>')

    # Plot boundary
    parts.append(
        f'<rect x="{MARGIN}" y="{MARGIN}" '
        f'width="{plot_w_px:.0f}" height="{plot_h_px:.0f}" '
        f'fill="none" stroke="#1a1a24" stroke-width="3"/>'
    )

    # Rooms
    for room in layout["rooms"]:
        rx = MARGIN + _m2px(room["x"])
        ry = MARGIN + _m2px(room["y"])
        rw = _m2px(room["w"])
        rh = _m2px(room["h"])
        color = ROOM_COLORS.get(room["type"], DEFAULT_COLOR)

        # Room rectangle (wall = dark stroke)
        parts.append(
            f'<rect x="{rx:.1f}" y="{ry:.1f}" width="{rw:.1f}" height="{rh:.1f}" '
            f'fill="{color}" stroke="#1a1a24" stroke-width="1.5"/>'
        )
        # Label: name + area, centered — but sized to fit the room.
        cx = rx + rw / 2
        cy = ry + rh / 2

        # Decide what fits: tiny rooms get a short label only; very tiny
        # rooms get just an initial. Avoids text overflowing small boxes.
        if rw >= 70 and rh >= 40:
            # Roomy: full name + area on two lines
            parts.append(
                f'<text x="{cx:.1f}" y="{cy - 3:.1f}" text-anchor="middle" '
                f'font-size="11" font-weight="bold" fill="#1a1a24">{room["label"]}</text>'
            )
            parts.append(
                f'<text x="{cx:.1f}" y="{cy + 11:.1f}" text-anchor="middle" '
                f'font-size="9" fill="#555">{room["area"]:.0f} m\u00b2</text>'
            )
        elif rw >= 38:
            # Narrow: short name only, smaller font, no area line
            short = room["label"].split()[0]      # "Bathroom 1" -> "Bathroom"
            parts.append(
                f'<text x="{cx:.1f}" y="{cy + 3:.1f}" text-anchor="middle" '
                f'font-size="8" fill="#1a1a24">{short}</text>'
            )
        else:
            # Very tiny: just the initial (e.g. "B")
            parts.append(
                f'<text x="{cx:.1f}" y="{cy + 3:.1f}" text-anchor="middle" '
                f'font-size="9" font-weight="bold" fill="#1a1a24">{room["label"][0]}</text>'
            )
        
        parts.append(
            f'<text x="{cx:.1f}" y="{cy + 11:.1f}" text-anchor="middle" '
            f'font-size="9" fill="#555">{room["area"]:.0f} m²</text>'
        )

    # Title + summary (top of the right panel)
    panel_x = MARGIN + plot_w_px + 20
    title = title or "ARQA Floor Plan"
    parts.append(
        f'<text x="{panel_x}" y="{MARGIN + 5}" font-size="15" '
        f'font-weight="bold" fill="#7c3aed">{title}</text>'
    )
    parts.append(
        f'<text x="{panel_x}" y="{MARGIN + 24}" font-size="10" fill="#555">'
        f'Plot: {plot["width"]} x {plot["height"]} m ({plot["area"]:.0f} m²)</text>'
    )

    # Legend
    ly = MARGIN + 50
    parts.append(
        f'<text x="{panel_x}" y="{ly}" font-size="11" font-weight="bold" '
        f'fill="#1a1a24">Rooms</text>'
    )
    ly += 16
    seen = []
    for room in layout["rooms"]:
        if room["type"] in seen:
            continue
        seen.append(room["type"])
        color = ROOM_COLORS.get(room["type"], DEFAULT_COLOR)
        parts.append(
            f'<rect x="{panel_x}" y="{ly - 9:.0f}" width="12" height="12" '
            f'fill="{color}" stroke="#1a1a24" stroke-width="1"/>'
        )
        parts.append(
            f'<text x="{panel_x + 18}" y="{ly}" font-size="10" fill="#333">'
            f'{room["type"].capitalize()}</text>'
        )
        ly += 18

    parts.append('</svg>')
    return "\n".join(parts)


def save_svg(layout, path, title=None):
    """Render and write an SVG file."""
    svg = render_svg(layout, title=title)
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    return path


if __name__ == "__main__":
    from arqa.design_agent import generate_layout

    sample = {
        "project_type": "villa",
        "country": "saudi_arabia",
        "plot_size": None,
        "rooms": {
            "bedrooms":  {"min": 4, "max": 4},
            "bathrooms": {"min": 2, "max": 2},
            "kitchen":   {"min": 1, "max": 1},
            "living":    {"min": 1, "max": 1},
            "majlis":    {"min": 1, "max": 1},
        },
    }

    layout = generate_layout(sample)
    out = save_svg(layout, "floorplan.svg", title="ARQA Villa — Riyadh")
    print(f"SVG written to: {out}")
    print(f"Layout: {layout['summary']}")
    print("Open floorplan.svg in your browser to view it.")