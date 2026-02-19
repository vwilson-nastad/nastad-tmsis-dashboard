import streamlit as st
import duckdb

st.set_page_config(page_title="NASTAD TMSIS Dashboard", page_icon="🏥", layout="wide")

st.title("🏥 NASTAD TMSIS Dashboard")
st.markdown("**Proof of Concept** — Live connection to MotherDuck (227M rows)")

# Connect to MotherDuck
@st.cache_resource
def get_connection():
    token = st.secrets["motherduck"]["token"]
    conn = duckdb.connect(f"md:my_db?motherduck_token={token}")
    return conn

try:
    conn = get_connection()

    # Test query - state summary
    st.header("State Overview")
    st.markdown("Aggregating from the full `tmsis_enriched` table in real time.")

    df_states = conn.execute("""
        SELECT
            "Provider Business Practice Location Address State Name" AS state,
            COUNT(DISTINCT BILLING_PROVIDER_NPI_NUM) AS total_providers,
            SUM(TOTAL_CLAIMS) AS total_claims,
            SUM(TOTAL_UNIQUE_BENEFICIARIES) AS total_beneficiaries,
            ROUND(SUM(TOTAL_PAID), 2) AS total_paid
        FROM tmsis_enriched
        WHERE "Provider Business Practice Location Address State Name" IS NOT NULL
        GROUP BY 1
        ORDER BY total_claims DESC
    """).df()

    # Multi-state filter
    all_states = df_states["state"].tolist()
    selected_states = st.multiselect("Filter by State(s)", all_states, default=None)

    if selected_states:
        df_display = df_states[df_states["state"].isin(selected_states)]
    else:
        df_display = df_states

    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("States", len(df_display))
    col2.metric("Providers", f"{df_display['total_providers'].sum():,.0f}")
    col3.metric("Total Claims", f"{df_display['total_claims'].sum():,.0f}")
    col4.metric("Total Paid", f"${df_display['total_paid'].sum():,.0f}")

    # Table
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "state": "State",
            "total_providers": st.column_config.NumberColumn("Providers", format="%d"),
            "total_claims": st.column_config.NumberColumn("Total Claims", format="%d"),
            "total_beneficiaries": st.column_config.NumberColumn("Beneficiaries", format="%d"),
            "total_paid": st.column_config.NumberColumn("Total Paid ($)", format="$%.2f"),
        }
    )

    # Bar chart
    st.bar_chart(df_display.set_index("state")["total_claims"])

    st.success("✅ Live connection to MotherDuck working! Querying 227M rows in real time.")

except Exception as e:
    st.error(f"Connection error: {e}")
    st.info("Make sure your MotherDuck token is configured in Streamlit secrets.")
