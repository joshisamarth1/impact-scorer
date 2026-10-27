import re
from pathlib import Path

import pdfplumber
import requests

PDF_DIR = Path("pdfs")
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

# ponytail: keyword rules keep this explainable. Swap for an LLM if filings vary more.
EVENTS = {
    "Order win": ["notification of award", "awarded", "work order", "letter of award", "letter of intent", "secures"],
    "Penalty / legal order": ["penalt", "appeal", "show cause", "demand notice", "tribunal"],
    "Acquisition / investment": ["acquisition", "acquire", "stake", "merger", "amalgamation"],
    "Fund raise": ["preferential", "rights issue", "qip", "debentures", "fund raising"],
    "Dividend / buyback": ["dividend", "buyback", "bonus shares"],
    "Results": ["financial results", "quarterly results"],
    "Management change": ["resignation", "appointment of"],
}
DIRECTION = {
    "Order win": "Positive",
    "Acquisition / investment": "Positive",
    "Dividend / buyback": "Positive",
    "Penalty / legal order": "Negative",
}
SECTORS = {
    "Power & Energy": ["power", "hydro", "mw", "thermal", "energy", "electricity", "solar", "renewable", "transmission"],
    "Infrastructure": ["highway", "railway", "metro", "bridge", "construction"],
    "Defence": ["defence", "navy", "army", "missile", "ordnance"],
    "Banking & Finance": ["bank", "nbfc", "loan", "lending"],
    "IT & Technology": ["software", "cloud", "digital", "it services"],
    "Healthcare & Pharma": ["pharma", "hospital", "drug", "clinical"],
        "Education": ["education", "coaching", "students"],
    "Real Estate": ["real estate", "residential", "housing"],
}
GOVT = ["government", "govt", "ministry", "ntpc", "railway", "public sector", "psu", "commissioner", "tribunal", "authority"]

UNIT_TO_CRORE = {"cr": 1, "crore": 1, "lakh": 0.01, "lac": 0.01, "million": 0.1, "mn": 0.1, "billion": 100, "bn": 100}
WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5}

COMPANY = re.compile(r"\bFor\s+([A-Z][A-Za-z&.' ]+?\s(?:Limited|Ltd))")
AMOUNT = re.compile(r"(?:\b(?:rs\.?|inr)|₹)\s*(\d[\d,]*(?:\.\d+)?)\s*(cr|crores?|lakhs?|lacs?|million|mn|billion|bn)?\b", re.I)
DURATION = re.compile(r"\b(\d+|one|two|three|four|five)\s+(?:additional\s+)?(month|year)s?\b", re.I)
NOT_MATERIAL = re.compile(r"\b(?:no|not|nor)\s+(?:\w+\s+){0,3}material impact", re.I)


def fetch_pdf(url):
    """Download once, then reuse the copy in pdfs/. Manual downloads there also work."""
    path = PDF_DIR / url.rsplit("/", 1)[-1]
    if path.exists():
        return path
    referer = "https://www.bseindia.com/" if "bseindia" in url else "https://www.nseindia.com/"
    try:
        response = requests.get(url, headers={"User-Agent": USER_AGENT, "Referer": referer}, timeout=30)
        response.raise_for_status()
    except requests.RequestException as error:
        raise ValueError(f"download failed ({type(error).__name__}), site unreachable or blocking bots") from error
    if not response.content.startswith(b"%PDF"):
        raise ValueError("server did not return a PDF (blocked?)")
    PDF_DIR.mkdir(exist_ok=True)
    path.write_bytes(response.content)
    return path


def read_text(path):
    with pdfplumber.open(path) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    if not text.strip():
        raise ValueError("no text layer (scanned PDF)")
    return text


def best(options, text):
    """Name of the option whose keywords appear most often, or None."""
    hits = {name: sum(len(re.findall(r"\b" + re.escape(k), text)) for k in words) for name, words in options.items()}
    top = max(hits, key=hits.get)
    return top if hits[top] else None


def to_crore(number, unit):
    value = float(number.replace(",", ""))
    return value * UNIT_TO_CRORE[unit.lower().rstrip("s")] if unit else value / 1e7  # no unit = rupees


def to_months(text):
    match = DURATION.search(text)
    if not match:
        return None
    count = WORDS.get(match.group(1).lower()) or int(match.group(1))
    return count * 12 if match.group(2).lower() == "year" else count


def extract_facts(text, source=""):
    lower = text.lower()
    company = COMPANY.search(text)
    event = best(EVENTS, lower) or "Other"
    amounts = [to_crore(number, unit) for number, unit in AMOUNT.findall(text)]
    return {
        "company": company.group(1) if company else source.split("_")[0],
        "type": event,
        "direction": DIRECTION.get(event, "Neutral"),
        "sector": best(SECTORS, lower) or "Unspecified",
        "value_cr": max(amounts, default=None),  # biggest amount = order size
        "months": to_months(text),
        "govt": any(re.search(r"\b" + word, lower) for word in GOVT),
        "not_material": bool(NOT_MATERIAL.search(text)),
    }