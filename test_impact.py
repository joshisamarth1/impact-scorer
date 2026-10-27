"""Run: python test_impact.py"""
from extract import extract_facts, to_crore
from scoring import score

BHEL = """Bharat Heavy Electricals Limited (BHEL) has received a Notification of Award (NOA) from Meja Urja Nigam
Private Ltd. for 3x800 MW Meja STPP Stage-II (EPC package). A joint venture between NTPC Ltd. and UPRVUNL.
Completion within 70 months from the date of Notification of award. Reply: Over Rs. 21,000 Cr. excl. GST.
3x800 MW Meja supercritical thermal power project. For Bharat Heavy Electricals Limited"""

BLUSPRING = """STEAG Energy Services has been awarded an order from Bharat Aluminium Company Limited for 1740 MW Power Plant
Operations and Maintenance Contract. Estimated aggregate contract value is Rs. 2,049.8 Crores.
Contract shall remain in force for a period of 60 months w.e.f. 1st July 2026. For Bluspring Enterprises Limited"""

EDUTECH = """The Company secures ₹1.5 Crore Work Order from VANARTI, an autonomous institute of the Government of
Maharashtra, to provide coaching for JEE/NEET. The work order is valid for two years and may be extended
annually for up to two additional years. Work order value for 300 students is Rs.
1,50,90,000/-. For Career Point Edutech Limited"""

ETHOS = """Appeals filed by the Company were dismissed and penalties aggregating to ₹2,15,78,391 imposed under the CGST Act
were upheld by the Commissioner (Appeals-III). The order does not have any material impact on the operations.
The Company may file a further appeal. For Ethos Limited"""


DMR = """The Manager, BSE SME Platform, 25th Floor, Phiroze Jeejeebhoy Towers,
Dalal Street, Mumbai. The Company has received a work order for Owner's Engineer Services for 1125MW
Dorjilung Hydropower Project. The contract period of the work is 9 months for an aggregate amount of
Rs. 2,58,91,500/- (Rupees Two Crore only). Awarded by Dorjilung Hydro Power Limited, Bhutan.
For DMR Engineering Limited (Formerly DMR Hydroengineering & Infrastructures Limited)"""


def test_dmr_and_false_amounts():
    facts = extract_facts(DMR)
    assert facts["company"] == "DMR Engineering Limited"
    assert round(facts["value_cr"], 2) == 2.59  # "Towers, Dalal" must not count as an amount
    assert (facts["type"], facts["months"], facts["sector"]) == ("Order win", 9, "Power & Energy")


def test_amounts():
    assert round(to_crore("2,15,78,391", None), 2) == 2.16
    assert to_crore("21,000", "Cr") == 21000
    assert to_crore("2,049.8", "Crores") == 2049.8
    assert to_crore("5", "lakhs") == 0.05


def test_extraction():
    facts = extract_facts(BHEL)
    assert facts["company"] == "Bharat Heavy Electricals Limited"
    assert (facts["type"], facts["value_cr"], facts["months"], facts["sector"], facts["govt"]) == (
        "Order win", 21000, 70, "Power & Energy", True)
    facts = extract_facts(BLUSPRING)
    assert (facts["value_cr"], facts["months"], facts["govt"]) == (2049.8, 60, False)
    facts = extract_facts(EDUTECH)
    assert (facts["type"], facts["months"], facts["sector"]) == ("Order win", 24, "Education")
    facts = extract_facts(ETHOS)
    assert (facts["type"], facts["direction"], facts["months"], facts["not_material"]) == (
        "Penalty / legal order", "Negative", None, True)


def test_ranking():
    scores = [score(extract_facts(text))[0] for text in (BHEL, BLUSPRING, EDUTECH, ETHOS)]
    assert scores == sorted(scores, reverse=True), scores


if __name__ == "__main__":
    test_amounts()
    test_dmr_and_false_amounts()
    test_extraction()
    test_ranking()
    print("all checks passed")