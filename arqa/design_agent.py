"""
ARQA Phase 1 — Design Agent (Day 12)

Procedural floor-plan generator. Reads the blackboard's structured
requirements (rooms, plot) and produces a layout: each room placed as
a non-overlapping rectangle inside the plot, via simple row-packing.

Explainable by design (every placement has a stated reason) — the
baseline that the Phase-2 learned generator will improve on.

Author: Muhammad Irfan
"""

import math

# Default floor areas (square metres) per room type.
# Defaults only — refinable later from client input or building-code minimums.
# Majlis is generously sized: guest reception is culturally important (Gulf).
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
    """Read a {min,max} room value's min (the count). None/0 if absent."""
    if isinstance(req_value, dict):
        return req_value.get("min") or 0
    return 0


def expand_rooms(requirements):
    """
    Turn the requirements' room COUNTS into a flat list of room instances,
    each with a type, a label, and a default area.

    e.g. bedrooms {min:2} -> [Bedroom 1 (12 m2), Bedroom 2 (12 m2)]
    """
    rooms = requirements.get("rooms") or {}
    instances = []

    for room_type, area in DEFAULT_AREAS.items():
        count = _room_min(rooms.get(room_type))
        for i in range(count):
            singular = {"bedrooms": "Bedroom", "bathrooms": "Bathroom"}
            label = singular.get(room_type, room_type.capitalize())
            label = label.capitalize()
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
    # default: treat as square metres (sqm, m2, or bare number)
    return value


def compute_plot(rooms, plot_size=None):
    """
    Decide plot dimensions (width, height in metres).
      - If plot_size given: use that total area.
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

    # Make a sensible rectangle (slightly wider than tall: 1.25 aspect ratio).
    height = math.sqrt(total_area / 1.25)
    width = total_area / height
    return round(width, 1), round(height, 1), round(total_area, 1), source


def pack_rooms(rooms, plot_w, plot_h):
    """
    Row-packing placement. Place rooms left-to-right in rows of fixed
    height; wrap to a new row when the current row is full.

    Returns a list of placed rooms with x, y, w, h (metres) and a reason.
    """
    if not rooms:
        return []

    # Row height: divide plot height into enough rows for the rooms.
    # Start with a row height that gives roughly square-ish rooms.
    n = len(rooms)
    rows_estimate = max(1, round(math.sqrt(n)))
    row_h = plot_h / rows_estimate

    placed = []
    x, y = 0.0, 0.0
    row_index = 1

    for room in rooms:
        w = room["area"] / row_h            # width so that w * row_h = area

        # If this room would overflow the row, wrap to the next row.
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


def generate_layout(requirements):
    """
    Main entry point: requirements dict -> a layout dict.

    Returns:
      {
        "rooms": [ {type,label,area,x,y,w,h,reason}, ... ],
        "plot": {"width","height","area","source"},
        "summary": "..."
      }
    """
    rooms = expand_rooms(requirements)
    plot_w, plot_h, total_area, source = compute_plot(
        rooms, requirements.get("plot_size")
    )
    placed = pack_rooms(rooms, plot_w, plot_h)

    return {
        "rooms": placed,
        "plot": {"width": plot_w, "height": plot_h,
                 "area": total_area, "source": source},
        "summary": f"{len(placed)} rooms on a {plot_w} x {plot_h} m plot "
                   f"({total_area} m2, {source})",
    }


def ascii_floorplan(layout, cols=60, rows=24):
    """
    Render the layout as an ASCII floor plan grid, so we can SEE it
    in the terminal with zero dependencies.
    """
    plot_w = layout["plot"]["width"]
    plot_h = layout["plot"]["height"]

    # Empty grid
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

        # Draw border + a letter label inside
        letter = room["label"][0].upper()
        for r in range(r0, min(r1, rows)):
            for c in range(c0, min(c1, cols)):
                if r in (r0, r1 - 1) or c in (c0, c1 - 1):
                    grid[r][c] = "#"          # wall
                elif grid[r][c] == " ":
                    grid[r][c] = letter       # room interior label

    border = "+" + "-" * cols + "+"
    lines = [border]
    for row in grid:
        lines.append("|" + "".join(row) + "|")
    lines.append(border)
    return "\n".join(lines)


if __name__ == "__main__":
    import json

    # A sample requirements dict (as the Communication Agent would produce).
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
    print("ARQA Design Agent — Procedural Layout (Day 12)")
    print("=" * 64)
    print(layout["summary"])
    print()
    print(f"{'Room':<14}{'Area':>7}{'x':>7}{'y':>7}{'w':>7}{'h':>7}")
    for r in layout["rooms"]:
        print(f"{r['label']:<14}{r['area']:>6.0f}m{r['x']:>7}{r['y']:>7}"
              f"{r['w']:>7}{r['h']:>7}")
    print()
    print(ascii_floorplan(layout))