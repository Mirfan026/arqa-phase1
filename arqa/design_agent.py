"""
ARQA Phase 1 — Design Agent

Procedural floor-plan generator. Reads the blackboard's structured
requirements (rooms, plot) and produces a layout: each room placed as a
non-overlapping rectangle inside the plot.

Placement uses CULTURAL ZONING (the privacy gradient): rooms are grouped
into guest / shared / private zones and stacked front-to-back, so the
majlis (guest reception) sits at the entrance and the bedrooms (private
family) sit at the rear — a documented principle of Gulf/Islamic
residential architecture, encoded as an explainable procedural prior.
The first bathroom becomes a guest WC in the shared zone (accessible to
guests without entering the private zone); the rest stay with the family.

Explainable by design (every placement records a reason) — the baseline
that the Phase-2 learned generator will improve on.

Author: Muhammad Irfan
"""

import math

# Default floor areas (m^2) per room type. Targets/minimums — refinable later
# from client input or building-code minimums. Majlis is generously sized:
# guest reception is culturally important (Gulf).
DEFAULT_AREAS = {
    "bedrooms": 12.0,
    "bathrooms": 4.0,
    "kitchen": 12.0,
    "living": 24.0,
    "majlis": 20.0,
}

# Reserve ~30% of plot for circulation (hallways, walls, stairs, entries).
CIRCULATION_FACTOR = 1.3

# Land-unit conversions to square metres.
MARLA_TO_M2 = 25.29   # Pakistan
KANAL_TO_M2 = 505.86  # 1 kanal = 20 marla


def _room_min(req_value):
    """Read a {min,max} room value's min (the count). 0 if absent."""
    if isinstance(req_value, dict):
        return req_value.get("min") or 0
    return 0


def expand_rooms(requirements):
    """
    Turn the requirements' room COUNTS into a flat list of room instances,
    each with a type, a label, and a default (target) area.
    """
    rooms = requirements.get("rooms") or {}
    instances = []

    for room_type, area in DEFAULT_AREAS.items():
        count = _room_min(rooms.get(room_type))
        for i in range(count):
            singular = {"bedrooms": "Bedroom", "bathrooms": "Bathroom"}
            label = singular.get(room_type, room_type.capitalize())
            if count > 1:
                label = f"{label} {i + 1}"
            instances.append({"type": room_type, "label": label, "area": area})

    return instances


def parse_plot_area(plot_size):
    """
    Parse a plot_size string into square metres, or return None.
    Handles 'N marla', 'N kanal', 'N sqm'/'N m2', 'N sq ft'.
    """
    if not plot_size or not isinstance(plot_size, str):
        return None

    s = plot_size.lower()
    num = ""
    for ch in s:
        if ch.isdigit() or ch == ".":
            num += ch
        elif num and ch == " ":
            break
    if not num:
        return None
    value = float(num)

    if "marla" in s:
        return value * MARLA_TO_M2
    if "kanal" in s:
        return value * KANAL_TO_M2
    if "sqft" in s or "sq ft" in s or "square feet" in s:
        return value * 0.0929
    return value     # default: square metres


def compute_plot(rooms, plot_size=None):
    """
    Decide plot dimensions (width, height in metres).
      - If plot_size given and larger than rooms: use it.
      - Else: total room area * circulation factor.
    Returns (width, height, total_area, source).
    """
    rooms_area = sum(r["area"] for r in rooms)

    given = parse_plot_area(plot_size)
    if given and given > rooms_area:
        total_area = given
        source = f"client plot_size ('{plot_size}')"
    else:
        total_area = rooms_area * CIRCULATION_FACTOR
        source = f"computed (rooms {rooms_area:.0f} m2 x {CIRCULATION_FACTOR})"

    # Sensible rectangle (slightly wider than tall: 1.25 aspect ratio).
    height = math.sqrt(total_area / 1.25)
    width = total_area / height
    return round(width, 1), round(height, 1), round(total_area, 1), source


def pack_rooms(rooms, plot_w, plot_h):
    """
    Row-packing placement (Day-12 baseline; kept for reference).
    Superseded as the default by zone_place() — see generate_layout().
    """
    if not rooms:
        return []

    n = len(rooms)
    rows_estimate = max(1, round(math.sqrt(n)))
    row_h = plot_h / rows_estimate

    placed = []
    x, y = 0.0, 0.0
    row_index = 1

    for room in rooms:
        w = room["area"] / row_h
        if x + w > plot_w + 0.01 and x > 0:
            x = 0.0
            y += row_h
            row_index += 1
        placed.append({
            **room,
            "x": round(x, 1), "y": round(y, 1),
            "w": round(w, 1), "h": round(row_h, 1),
            "reason": f"placed in row {row_index} (row-packing order)",
        })
        x += w

    return placed


# ── Cultural zoning: the privacy gradient ───────────────────────────────
# Room type -> functional zone. Zones placed front-to-back as a PUBLIC ->
# PRIVATE gradient — a documented principle of Gulf/Islamic residential
# architecture. [cite architectural literature in Dossier]
ZONE_OF = {
    "majlis":    "guest",     # front — public, by the entrance
    "living":    "shared",    # middle — semi-private family living
    "kitchen":   "shared",
    "bedrooms":  "private",   # rear — most private (family)
    "bathrooms": "private",
}
ZONE_ORDER = ["guest", "shared", "private"]   # front -> back = public -> private
ZONE_TITLE = {
    "guest":   "Guest zone (front, by entrance)",
    "shared":  "Shared family living (middle)",
    "private": "Private family zone (rear)",
}


def zone_place(rooms, plot_w, plot_h):
    """
    Privacy-gradient placement. Group rooms into zones (guest/shared/private),
    stack the zones front-to-back as horizontal bands sized by each zone's
    room area, and fill each band's width proportionally (no dead space).

    Cultural rules encoded:
      - majlis (guest) at the front near the entrance;
      - bedrooms (private) at the rear, farthest from guests;
      - first bathroom -> guest WC ("WC 1") in the SHARED zone (accessible
        to guests without entering the private zone); the rest ("WC 2", ...)
        stay private with the bedrooms.
    """
    if not rooms:
        return []

    total_area = sum(r["area"] for r in rooms)

    # Group rooms by zone, preserving zone order.
    by_zone = {z: [] for z in ZONE_ORDER}
    guest_wc_assigned = False
    for r in rooms:
        zone = ZONE_OF.get(r["type"], "shared")
        if r["type"] == "bathrooms":
            if not guest_wc_assigned:
                zone = "shared"                 # first bathroom -> guest WC
                r = {**r, "label": "WC 1"}      # guest WC, in shared zone
                guest_wc_assigned = True
            else:
                r = {**r, "label": "WC 2"}      # family WC, in private zone
        by_zone[zone].append(r)

    placed = []
    y = 0.0

    for zone in ZONE_ORDER:
        zrooms = by_zone[zone]
        if not zrooms:
            continue

        zone_area = sum(r["area"] for r in zrooms)
        band_h = plot_h * (zone_area / total_area)

        x = 0.0
        for i, r in enumerate(zrooms):
            rx = round(x, 1)
            if i == len(zrooms) - 1:
                rw = round(plot_w - rx, 1)      # last room snaps to right edge
            else:
                rw = round(plot_w * (r["area"] / zone_area), 1)

            placed.append({
                **r,
                "x": rx, "y": round(y, 1),
                "w": rw, "h": round(band_h, 1),
                "zone": zone,
                "reason": f"{ZONE_TITLE[zone]} — privacy gradient",
            })
            x = rx + rw                          # advance by rounded values

        y += band_h

    return placed


def generate_layout(requirements):
    """requirements dict -> layout dict (rooms placed, plot, summary)."""
    rooms = expand_rooms(requirements)
    plot_w, plot_h, total_area, source = compute_plot(
        rooms, requirements.get("plot_size")
    )
    placed = zone_place(rooms, plot_w, plot_h)   # privacy-gradient zoning

    return {
        "rooms": placed,
        "plot": {"width": plot_w, "height": plot_h,
                 "area": total_area, "source": source},
        "summary": f"{len(placed)} rooms on a {plot_w} x {plot_h} m plot "
                   f"({total_area} m2, {source})",
    }


def ascii_floorplan(layout, cols=60, rows=24):
    """ASCII floor-plan grid for zero-dependency terminal preview."""
    plot_w = layout["plot"]["width"]
    plot_h = layout["plot"]["height"]
    grid = [[" " for _ in range(cols)] for _ in range(rows)]

    def to_col(x):
        return min(cols - 1, max(0, int(x / plot_w * cols)))

    def to_row(y):
        return min(rows - 1, max(0, int(y / plot_h * rows)))

    for room in layout["rooms"]:
        c0, c1 = to_col(room["x"]), to_col(room["x"] + room["w"])
        r0, r1 = to_row(room["y"]), to_row(room["y"] + room["h"])
        c1 = max(c1, c0 + 1)
        r1 = max(r1, r0 + 1)
        letter = room["label"][0].upper()
        for r in range(r0, min(r1, rows)):
            for c in range(c0, min(c1, cols)):
                if r in (r0, r1 - 1) or c in (c0, c1 - 1):
                    grid[r][c] = "#"
                elif grid[r][c] == " ":
                    grid[r][c] = letter

    border = "+" + "-" * cols + "+"
    lines = [border]
    for row in grid:
        lines.append("|" + "".join(row) + "|")
    lines.append(border)
    return "\n".join(lines)


if __name__ == "__main__":
    sample = {
        "project_type": "villa",
        "country": "saudi_arabia",
        "plot_size": None,
        "rooms": {
            "bedrooms": {"min": 4, "max": 4},
            "bathrooms": {"min": 2, "max": 2},
            "kitchen": {"min": 1, "max": 1},
            "living": {"min": 1, "max": 1},
            "majlis": {"min": 1, "max": 1},
        },
    }

    layout = generate_layout(sample)

    print("=" * 64)
    print("ARQA Design Agent — Procedural Layout (cultural zoning)")
    print("=" * 64)
    print(layout["summary"])
    print()
    print(f"{'Room':<12}{'Zone':<10}{'Target':>7}{'x':>7}{'y':>7}{'w':>7}{'h':>7}{'drawn':>8}")
    for r in layout["rooms"]:
        drawn = round(r["w"] * r["h"], 1)
        print(f"{r['label']:<12}{r.get('zone',''):<10}{r['area']:>6.0f}m"
              f"{r['x']:>7}{r['y']:>7}{r['w']:>7}{r['h']:>7}{drawn:>7.1f}m")
    print()
    print(ascii_floorplan(layout))