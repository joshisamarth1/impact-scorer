from extract import extract_facts, fetch_pdf, read_text
from scoring import justify, score

URLS = [
    "https://nsearchives.nseindia.com/corporate/BHELCC_05062026113257_Info_to_SE_05_06_2026.pdf",
    "https://nsearchives.nseindia.com/corporate/BLUSPRING_05062026130923_Reg_30_-_SESI-BALCO.pdf",
    "https://nsearchives.nseindia.com/corporate/ETHOS_05062026160606_Disclosure_GST_Order.pdf",
    "https://nsearchives.nseindia.com/corporate/EDUTECH_05062026174716_Disclosure_Reg_30_EDUTECH_05062026.pdf",
    "https://www.bseindia.com/xml-data/corpfiling/AttachLive/cc79e53e-be66-400d-82db-6e88c3a42188.pdf",
]


def analyze(urls=URLS):
    """Returns (results ranked by score, {url: error})."""
    results, errors = [], {}
    for url in urls:
        try:
            facts = extract_facts(read_text(fetch_pdf(url)), url.rsplit("/", 1)[-1])
        except Exception as error:
            errors[url] = str(error)
            continue
        points, parts = score(facts)
        results.append({**facts, "score": points, "parts": parts, "why": justify(facts, parts), "url": url})
    return sorted(results, key=lambda r: r["score"], reverse=True), errors


if __name__ == "__main__":
    results, errors = analyze()
    for rank, r in enumerate(results, 1):
        print(f"{rank}. {r['company']} | {r['type']} | score {r['score']}/100")
        print(f"   {r['why']}")
    for url, error in errors.items():
        print(f"FAILED {url.rsplit('/', 1)[-1]}: {error}")
