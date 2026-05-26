"""
ARQA Phase 1 — Renderers

SVG renderer for Design Agent layouts. Zero dependencies, vector output,
opens in any browser. Annotates the cultural zoning (ENTRANCE marker +
GUEST/SHARED/PRIVATE zone labels). In-room labels stay short (name +
drawn area); a ROOM SCHEDULE lists every room's drawn vs. target area
with a TOTAL row. All areas use one consistent precision, so a room shows
the identical value in its box and in the schedule.

Author: Muhammad Irfan
"""

SCALE = 20          # 1 metre = 20 pixels
MARGIN = 40         # px border around the plot
LABEL_PANEL = 200   # px reserved on the right for title/legend/schedule

ROOM_COLORS = {
    "bedrooms":  "#bfdbfe",   # light blue
    "bathrooms": "#bbf7d0",   # light green
    "kitchen":   "#fed7aa",   # light orange
    "living":    "#fde68a",   # light gold
    "majlis":    "#ddd6fe",   # light purple (distinct — cultural space)
}
DEFAULT_COLOR = "#e5e7eb"

TYPE_NAMES = {
    "bedrooms": "Bedroom",
    "bathrooms": "Bathroom / WC",
    "kitchen": "Kitchen",
    "living": "Living",
    "majlis": "Majlis (guest)",
}


def _m2px(metres):
    return metres * SCALE


def _short_tag(label, rtype):
    """Short in-room tag for narrow/tiny rooms."""
    if "WC" in label:
        return label                      # "WC 1" / "WC 2" stay as-is
    if rtype == "bathrooms":
        return "WC"
    return label.split()[0]


def render_svg(layout, title=None):
    plot = layout["plot"]
    plot_w_px = _m2px(plot["width"])
    plot_h_px = _m2px(plot["height"])

    # Canvas: width = plot + panel; height = taller of plot OR right panel.
    img_w = MARGIN * 2 + plot_w_px + LABEL_PANEL
    n_rooms = len(layout["rooms"])
    n_types = len({r["type"] for r in layout["rooms"]})
    panel_h = 30 + (n_types * 18 + 26) + (n_rooms * 12 + 60)
    img_h = MARGIN * 2 + max(plot_h_px, panel_h)

    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{img_w:.0f}" height="{img_h:.0f}" '
        f'viewBox="0 0 {img_w:.0f} {img_h:.0f}" '
        f'font-family="Arial, sans-serif">'
    )
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
        drawn = round(room["w"] * room["h"], 1)   # ONE precision, used everywhere

        parts.append(
            f'<rect x="{rx:.1f}" y="{ry:.1f}" width="{rw:.1f}" height="{rh:.1f}" '
            f'fill="{color}" stroke="#1a1a24" stroke-width="1.5"/>'
        )

        cx = rx + rw / 2
        cy = ry + rh / 2

        if rw >= 50 and rh >= 30:
            parts.append(
                f'<text x="{cx:.1f}" y="{cy - 2:.1f}" text-anchor="middle" '
                f'font-size="10" font-weight="bold" fill="#1a1a24">{room["label"]}</text>'
            )
            parts.append(
                f'<text x="{cx:.1f}" y="{cy + 9:.1f}" text-anchor="middle" '
                f'font-size="8" fill="#555">{drawn:.1f} m\u00b2</text>'
            )
        else:
            tag = _short_tag(room["label"], room["type"])
            parts.append(
                f'<text x="{cx:.1f}" y="{cy - 1:.1f}" text-anchor="middle" '
                f'font-size="7.5" font-weight="bold" fill="#1a1a24">{tag}</text>'
            )
            parts.append(
                f'<text x="{cx:.1f}" y="{cy + 8:.1f}" text-anchor="middle" '
                f'font-size="6.5" fill="#555">{drawn:.1f} m\u00b2</text>'
            )

    # ── Right panel ──
    panel_x = MARGIN + plot_w_px + 20

    title = title or "ARQA Floor Plan"
    parts.append(
        f'<text x="{panel_x}" y="{MARGIN + 5}" font-size="15" '
        f'font-weight="bold" fill="#7c3aed">{title}</text>'
    )
    parts.append(
        f'<text x="{panel_x}" y="{MARGIN + 24}" font-size="10" fill="#555">'
        f'Plot: {plot["width"]} x {plot["height"]} m ({plot["area"]:.0f} m\u00b2)</text>'
    )

    # Legend
    ly = MARGIN + 50
    parts.append(
        f'<text x="{panel_x}" y="{ly}" font-size="11" font-weight="bold" '
        f'fill="#1a1a24">Room types (colour key)</text>'
    )
    ly += 16
    seen = []
    for room in layout["rooms"]:
        if room["type"] in seen:
            continue
        seen.append(room["type"])
        color = ROOM_COLORS.get(room["type"], DEFAULT_COLOR)
        name = TYPE_NAMES.get(room["type"], room["type"].capitalize())
        parts.append(
            f'<rect x="{panel_x}" y="{ly - 9:.0f}" width="12" height="12" '
            f'fill="{color}" stroke="#1a1a24" stroke-width="1"/>'
        )
        parts.append(
            f'<text x="{panel_x + 18}" y="{ly}" font-size="10" fill="#333">{name}</text>'
        )
        ly += 18

    # Room schedule
    ly += 12
    parts.append(
        f'<text x="{panel_x}" y="{ly}" font-size="11" font-weight="bold" '
        f'fill="#1a1a24">Room schedule (m\u00b2)</text>'
    )
    ly += 15
    parts.append(f'<text x="{panel_x}" y="{ly}" font-size="8" font-weight="bold" fill="#555">Room</text>')
    parts.append(f'<text x="{panel_x + 105}" y="{ly}" font-size="8" font-weight="bold" fill="#555">Drawn</text>')
    parts.append(f'<text x="{panel_x + 150}" y="{ly}" font-size="8" font-weight="bold" fill="#555">Target</text>')
    ly += 4
    parts.append(f'<line x1="{panel_x}" y1="{ly}" x2="{panel_x + 185}" y2="{ly}" stroke="#ccc" stroke-width="0.5"/>')
    ly += 11
    for room in layout["rooms"]:
        drawn = round(room["w"] * room["h"], 1)    # SAME value as in-room label
        parts.append(f'<text x="{panel_x}" y="{ly}" font-size="8" fill="#333">{room["label"]}</text>')
        parts.append(f'<text x="{panel_x + 105}" y="{ly}" font-size="8" fill="#333">{drawn:.1f}</text>')
        parts.append(f'<text x="{panel_x + 150}" y="{ly}" font-size="8" fill="#333">{room["area"]:.0f}</text>')
        ly += 12

    # Total row
    total_drawn = round(sum(r["w"] * r["h"] for r in layout["rooms"]), 1)
    total_target = sum(r["area"] for r in layout["rooms"])
    ly += 2
    parts.append(f'<line x1="{panel_x}" y1="{ly - 8}" x2="{panel_x + 185}" y2="{ly - 8}" stroke="#ccc" stroke-width="0.5"/>')
    parts.append(f'<text x="{panel_x}" y="{ly}" font-size="8" font-weight="bold" fill="#333">TOTAL</text>')
    parts.append(f'<text x="{panel_x + 105}" y="{ly}" font-size="8" font-weight="bold" fill="#333">{total_drawn:.1f}</text>')
    parts.append(f'<text x="{panel_x + 150}" y="{ly}" font-size="8" font-weight="bold" fill="#333">{total_target:.0f}</text>')

    # ── Entrance marker ──
    entry_cx = MARGIN + plot_w_px / 2
    parts.append(f'<rect x="{entry_cx - 18:.0f}" y="{MARGIN - 5:.0f}" width="36" height="6" fill="#10b981"/>')
    parts.append(
        f'<text x="{entry_cx:.0f}" y="{MARGIN - 10:.0f}" text-anchor="middle" '
        f'font-size="10" font-weight="bold" fill="#10b981">ENTRANCE</text>'
    )

    # ── Zone labels (left edge) ──
    zone_bounds = {}
    for room in layout["rooms"]:
        z = room.get("zone")
        if not z:
            continue
        top = MARGIN + _m2px(room["y"])
        bot = top + _m2px(room["h"])
        if z not in zone_bounds:
            zone_bounds[z] = [top, bot]
        else:
            zone_bounds[z][0] = min(zone_bounds[z][0], top)
            zone_bounds[z][1] = max(zone_bounds[z][1], bot)
    for z, (top, bot) in zone_bounds.items():
        mid = (top + bot) / 2
        parts.append(
            f'<text x="14" y="{mid:.0f}" font-size="8" fill="#9ca3af" '
            f'transform="rotate(-90 14 {mid:.0f})" text-anchor="middle" '
            f'letter-spacing="1">{z.upper()}</text>'
        )

    parts.append('</svg>')
    return "\n".join(parts)


def save_svg(layout, path, title=None):
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