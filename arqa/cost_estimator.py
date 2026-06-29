"""
ARQA Phase 1 — Cost Estimator (Day 15)

Turns a Design Agent layout into a priced estimate using REAL, sourced
regional construction-cost benchmarks (mid-range, turnkey construction;
excludes land, permits, and furnishing — consistent with how each source
defines its figures).

Benchmarks (researched May 2026, cited; market ranges, not site quotes):
  Pakistan      : turnkey ~5,500-8,800 PKR/sq ft (grey ~2,650-3,300 PKR/sq ft)
                  -> converted to PKR/m^2 (1 m^2 = 10.764 sq ft)
                  Sources: avenirdevelopments.com, elegantdesignpk.com,
                  gloriousbuilders.com (Lahore/Islamabad, Apr-Jun 2026)
  Saudi Arabia  : turnkey construction ~1,200-2,500 SAR/m^2 (excl. land)
                  Sources: saudicostguide.com, businesooq.com (2026)
  UAE           : standard villas ~4,200 AED/m^2, up to ~11,000 AED/m^2 luxury
                  Source: Knight Frank UAE Construction Landscape Review,
                  Q2 2025, via capitalassociated.com
  Qatar         : average house cost ~9,000 QAR/m^2 (villas trend higher)
                  Source: arabmls.org / saakin.qa (2026)

These are MARKET BENCHMARKS, not site-specific quotes — presented as an
estimate range, exactly as a real preliminary architect's estimate would be.

Author: Muhammad Irfan
"""

SQFT_PER_M2 = 10.764

# Cost per m^2, as (low, high) mid-range turnkey construction bands.
# country key matches the Communication Agent's extracted `country` field.
COST_PER_M2 = {
    "pakistan": {
        "currency": "PKR",
        "low": 5500 * SQFT_PER_M2,    # ~59,200 PKR/m2
        "high": 8800 * SQFT_PER_M2,   # ~94,700 PKR/m2
        "source": "Lahore/Islamabad turnkey rates, Apr-Jun 2026 "
                  "(avenirdevelopments.com, elegantdesignpk.com, gloriousbuilders.com)",
    },
    "saudi_arabia": {
        "currency": "SAR",
        "low": 1200,
        "high": 2500,
        "source": "Saudi turnkey construction (excl. land), 2026 "
                  "(saudicostguide.com, businesooq.com)",
    },
    "uae": {
        "currency": "AED",
        "low": 4200,
        "high": 6000,    # standard-to-mid; luxury runs to ~11,000
        "source": "Knight Frank UAE Construction Landscape Review, Q2 2025 "
                  "(via capitalassociated.com)",
    },
    "qatar": {
        "currency": "QAR",
        "low": 7000,
        "high": 9000,
        "source": "Qatar average house cost, 2026 (arabmls.org, saakin.qa)",
    },
}


def takeoff(layout):
    """
    Material/area takeoff: read a Design Agent layout and produce the
    built-area quantities a cost estimate needs.

    Returns:
      {
        "total_built_area": float (m^2, sum of DRAWN room areas),
        "rooms": [ {label, type, area_m2}, ... ]   # one row per room
      }
    """
    rooms = []
    total = 0.0
    for r in layout["rooms"]:
        area = round(r["w"] * r["h"], 1)
        rooms.append({"label": r["label"], "type": r["type"], "area_m2": area})
        total += area

    return {"total_built_area": round(total, 1), "rooms": rooms}


def estimate_cost(layout, country):
    """
    Cost estimate for one layout: takeoff x cost/m^2 benchmark.

    Returns:
      {
        "country", "currency", "total_built_area",
        "low_estimate", "high_estimate", "source",
        "takeoff": {...}
      }
      or None if the country has no benchmark (honest "out of coverage").
    """
    bench = COST_PER_M2.get(country)
    if not bench:
        return None   # no benchmark for this country — be honest, don't guess

    tk = takeoff(layout)
    area = tk["total_built_area"]

    return {
        "country": country,
        "currency": bench["currency"],
        "total_built_area": area,
        "low_estimate": round(area * bench["low"], 0),
        "high_estimate": round(area * bench["high"], 0),
        "source": bench["source"],
        "takeoff": tk,
    }


def estimate_scenarios(requirements, generate_layout_fn):
    """
    Range -> priced scenarios (Day-8 decision, activated).

    If a room count is a RANGE (min != max), generate one layout per value
    in the range and price each — so the client compares options instead
    of ARQA silently picking one. If everything is exact, returns a single
    scenario.

    generate_layout_fn: design_agent.generate_layout (passed in to avoid
    a circular import between design_agent and cost_estimator).

    Returns a list of:
      { "label": "...", "rooms_changed": {...}, "estimate": {...} }
    """
    rooms = requirements.get("rooms") or {}
    country = requirements.get("country")

    # Find the first room type with a real range (min != max) to vary.
    # (Phase 1: vary one dimension at a time — the common, demoable case.)
    varying_field = None
    for field, val in rooms.items():
        if isinstance(val, dict):
            lo, hi = val.get("min"), val.get("max")
            if lo is not None and hi is not None and lo != hi:
                varying_field = field
                break

    if varying_field is None:
        # No range — a single, exact scenario.
        layout = generate_layout_fn(requirements)
        est = estimate_cost(layout, country)
        return [{"label": "As specified", "rooms_changed": {}, "estimate": est}]

    # Build one scenario per value in the range.
    lo, hi = rooms[varying_field]["min"], rooms[varying_field]["max"]
    scenarios = []
    for value in range(lo, hi + 1):
        scenario_rooms = dict(rooms)
        scenario_rooms[varying_field] = {"min": value, "max": value}
        scenario_reqs = {**requirements, "rooms": scenario_rooms}

        layout = generate_layout_fn(scenario_reqs)
        est = estimate_cost(layout, country)
        scenarios.append({
            "label": f"{value} {varying_field}",
            "rooms_changed": {varying_field: value},
            "estimate": est,
        })

    return scenarios


def format_estimate(est):
    """Human-readable one-line summary of a cost estimate."""
    if est is None:
        return "No cost benchmark available for this country (out of coverage)."
    return (
        f"{est['total_built_area']} m\u00b2 built area  ->  "
        f"{est['currency']} {est['low_estimate']:,.0f} - {est['currency']} {est['high_estimate']:,.0f} "
        f"(estimate; source: {est['source']})"
    )


if __name__ == "__main__":
    from arqa.design_agent import generate_layout

    print("=" * 64)
    print("ARQA Cost Estimator (Day 15) — single estimate")
    print("=" * 64)
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
    est = estimate_cost(layout, sample["country"])
    print(f"Country: {sample['country']}")
    print(format_estimate(est))
    print()
    print("Room-by-room takeoff:")
    for r in est["takeoff"]["rooms"]:
        print(f"   {r['label']:<14}{r['area_m2']:>6.1f} m\u00b2")

    print()
    print("=" * 64)
    print("ARQA Cost Estimator — RANGE -> PRICED SCENARIOS (Day 8 decision)")
    print("=" * 64)
    ranged = {
        "project_type": "villa",
        "country": "saudi_arabia",
        "plot_size": None,
        "rooms": {
            "bedrooms": {"min": 3, "max": 4},   # <- a real range
            "bathrooms": {"min": 2, "max": 2},
            "kitchen": {"min": 1, "max": 1},
            "living": {"min": 1, "max": 1},
            "majlis": {"min": 1, "max": 1},
        },
    }
    scenarios = estimate_scenarios(ranged, generate_layout)
    for sc in scenarios:
        print(f"\nScenario: {sc['label']}")
        print("   " + format_estimate(sc["estimate"]))