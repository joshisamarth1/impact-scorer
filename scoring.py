# All weights live here. Change a number, the ranking changes.
MAX_POINTS = {
    "Order size": 30,
    "Revenue contribution": 20,
    "Sector": 15,
    "Credibility": 15,
    "Timeline": 10,
    "Event type": 10,
}

# (minimum, points), biggest first.
SIZE = [(10000, 30), (1000, 24), (500, 20), (100, 15), (10, 9), (1, 4)]   # order value, ₹ Cr
REVENUE = [(1000, 20), (250, 16), (100, 12), (25, 8), (5, 4), (0.5, 1)]   # value per year, ₹ Cr
TIMELINE = [(60, 10), (36, 8), (12, 5), (1, 3)]                           # contract length, months

SECTOR_POINTS = {
    "Defence": 15, "Power & Energy": 14, "Infrastructure": 13, "Banking & Finance": 12,
    "Healthcare & Pharma": 10, "IT & Technology": 10, "Real Estate": 8, "Education": 7,
}
UNSPECIFIED_SECTOR = 6

EVENT_POINTS = {
    "Order win": 10, "Acquisition / investment": 10, "Fund raise": 7, "Dividend / buyback": 6,
    "Results": 6, "Penalty / legal order": 5, "Management change": 3, "Other": 2,
}
NOT_MATERIAL_FACTOR = 0.5  # company itself says "no material impact"


def tier(value, steps):
    return next((points for minimum, points in steps if value >= minimum), 0)


def annual_value(facts):
    """₹ Cr per year. No stated duration = treated as a one-year / one-off amount."""
    value = facts["value_cr"] or 0
    return value / (facts["months"] / 12) if facts["months"] else value


def score(facts):
    parts = {
        "Order size": tier(facts["value_cr"] or 0, SIZE),
        "Revenue contribution": tier(annual_value(facts), REVENUE),
        "Sector": SECTOR_POINTS.get(facts["sector"], UNSPECIFIED_SECTOR),
        "Credibility": (10 if facts["govt"] else 6) + (5 if facts["value_cr"] else 0),
        "Timeline": tier(facts["months"] or 0, TIMELINE),
        "Event type": EVENT_POINTS.get(facts["type"], EVENT_POINTS["Other"]),
    }
    total = sum(parts.values())
    if facts["not_material"]:
        total *= NOT_MATERIAL_FACTOR
    return round(total), parts


def justify(facts, parts):
    value, months = facts["value_cr"], facts["months"]
    text = f"{facts['type']} worth ₹{value:,.2f} Cr" if value else f"{facts['type']} with no stated value"
    if months:
        text += f" over {months} months (about ₹{annual_value(facts):,.2f} Cr a year)"
    text += f". Sector: {facts['sector']}. Counterparty: {'government / public body' if facts['govt'] else 'private or unspecified'}."
    if facts["not_material"]:
        text += " The company says there is no material impact, so the score is halved."
    return text
