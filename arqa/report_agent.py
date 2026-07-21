"""
ARQA Phase 1 — Report Agent: data assembly (Day 17)

Pulls together a Design Agent layout, a cost estimate, and a compliance
summary into one structured report-ready object. Rendering (PDF, any
language) is a SEPARATE concern — this module only assembles the data,
consistent with the layout/render separation established on Day 13.

Author: Muhammad Irfan
"""

from arqa.design_agent import generate_layout
from arqa.cost_estimator import estimate_cost
from arqa.compliance_checker import check_compliance


def assemble_report(requirements):
    """
    requirements (dict, as produced by the Communication Agent/Supervisor)
    -> a single report-ready dict:
      {
        "requirements": ...,
        "layout": ...,
        "cost": ...,
        "compliance": [...],
      }
    """
    layout = generate_layout(requirements)
    country = requirements.get("country")
    cost = estimate_cost(layout, country)
    compliance = check_compliance(layout, country)

    return {
        "requirements": requirements,
        "layout": layout,
        "cost": cost,
        "compliance": compliance,
    }


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

    report = assemble_report(sample)
    print("Report assembled. Keys:", list(report.keys()))
    print("Plot:", report["layout"]["summary"])
    print("Cost:", report["cost"]["currency"],
          f"{report['cost']['low_estimate']:,.0f} - {report['cost']['high_estimate']:,.0f}")
    print("Compliance checks:", len(report["compliance"]))