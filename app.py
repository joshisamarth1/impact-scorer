import pandas as pd
import streamlit as st

from main import analyze
from scoring import MAX_POINTS

st.set_page_config(page_title="Corporate Action Impact Scorer", layout="wide")


@st.cache_data(show_spinner="Downloading and reading PDFs…")
def load():
    return analyze()


results, errors = load()

st.title("Corporate Action Impact Scorer")
st.caption("Exchange filings ranked by how strongly they can move a company's fundamentals.")

for url, error in errors.items():
    st.warning(f"{url.rsplit('/', 1)[-1]}: {error}. Download it into the pdfs/ folder, then re-run.")
if st.button("Re-run analysis"):
    st.cache_data.clear()
    st.rerun()
if not results:
    st.error("No filing could be analysed.")
    st.stop()

first, second, third = st.columns(3)
first.metric("Filings analysed", len(results))
second.metric("Top score", f"{results[0]['score']} / 100")
third.metric("Failed to load", len(errors))
st.markdown(f"**Highest impact:** {results[0]['company']}")

st.subheader("Ranking")
table = pd.DataFrame([
    {
        "Rank": rank, "Company": r["company"], "Event": r["type"], "Direction": r["direction"],
        "Value (₹ Cr)": r["value_cr"], "Months": r["months"], "Sector": r["sector"], "Score": r["score"],
    }
    for rank, r in enumerate(results, 1)
])
st.dataframe(
    table,
    hide_index=True,
    width="stretch",
    column_config={
        "Score": st.column_config.ProgressColumn("Score", min_value=0, max_value=100, format="%d"),
        "Value (₹ Cr)": st.column_config.NumberColumn(format="%.2f"),
    },
)

st.subheader("Where the points come from")
st.bar_chart(pd.DataFrame({r["company"]: r["parts"] for r in results}).T)
st.caption("Filings where the company says there is no material impact are halved after adding up.")

st.subheader("Details")
for rank, r in enumerate(results, 1):
    with st.expander(f"#{rank}  {r['company']}  —  {r['score']} / 100"):
        st.write(r["why"])
        st.table(pd.DataFrame({"Points": r["parts"], "Max": MAX_POINTS}))
        st.link_button("Open original PDF", r["url"])
