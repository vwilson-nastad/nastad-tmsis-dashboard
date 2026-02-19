import streamlit as st
import duckdb
import pandas as pd

st.set_page_config(page_title="NASTAD TMSIS Dashboard", page_icon="🏥", layout="wide")

# ============================================================
# DATABASE CONNECTION
# ============================================================
@st.cache_resource
def get_connection():
    token = st.secrets["motherduck"]["token"]
    conn = duckdb.connect(f"md:my_db?motherduck_token={token}")
    return conn

conn = get_connection()

@st.cache_data(ttl=3600)
def run_query(query):
    return conn.execute(query).df()

# ============================================================
# SIDEBAR - Navigation and State Filter
# ============================================================
st.sidebar.title("🏥 NASTAD TMSIS Dashboard")
st.sidebar.markdown("Medicaid Provider Analysis for **Ending the HIV Epidemic**")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigate",
    ["🏠 State Overview", "🔬 HIV Services", "👩‍⚕️ Provider Directory", "📈 Trends"],
)

st.sidebar.markdown("---")

# Load states for filter
states_df = run_query("""
    SELECT DISTINCT "Provider Business Practice Location Address State Name" AS state
    FROM tmsis_enriched
    WHERE "Provider Business Practice Location Address State Name" IS NOT NULL
    ORDER BY state
""")

selected_states = st.sidebar.multiselect(
    "Filter by State(s)",
    states_df["state"].tolist(),
    default=None,
    help="Leave empty to show all states"
)

# Build WHERE clause helper
def state_filter(alias=""):
    col = f'{alias}"Provider Business Practice Location Address State Name"' if alias else '"Provider Business Practice Location Address State Name"'
    if selected_states:
        state_list = ", ".join([f"'{s}'" for s in selected_states])
        return f"AND {col} IN ({state_list})"
    return ""

st.sidebar.markdown("---")
st.sidebar.caption("**Data:** CMS TMSIS 2018–2024")
st.sidebar.caption("**Records:** 227M enriched claims")
st.sidebar.caption("**Updated:** February 2026")
st.sidebar.caption("Built by NASTAD")


# ============================================================
# PAGE 1: STATE OVERVIEW
# ============================================================
if page == "🏠 State Overview":
    st.title("🏠 State Overview")
    st.markdown("All Medicaid claims aggregated by state from the full TMSIS dataset (2018–2024).")

    df = run_query(f"""
        SELECT
            "Provider Business Practice Location Address State Name" AS state,
            COUNT(DISTINCT BILLING_PROVIDER_NPI_NUM) AS total_providers,
            SUM(TOTAL_CLAIMS) AS total_claims,
            SUM(TOTAL_UNIQUE_BENEFICIARIES) AS total_beneficiaries,
            ROUND(SUM(TOTAL_PAID), 2) AS total_paid
        FROM tmsis_enriched
        WHERE "Provider Business Practice Location Address State Name" IS NOT NULL
        {state_filter()}
        GROUP BY 1
        ORDER BY total_claims DESC
    """)

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("States", len(df))
    col2.metric("Providers", f"{df['total_providers'].sum():,.0f}")
    col3.metric("Total Claims", f"{df['total_claims'].sum():,.0f}")
    col4.metric("Total Paid", f"${df['total_paid'].sum():,.2f}")

    st.markdown("---")

    # Table and chart in tabs
    tab1, tab2 = st.tabs(["📊 Chart", "📋 Table"])

    with tab1:
        st.bar_chart(df.set_index("state")["total_claims"], use_container_width=True)

    with tab2:
        st.dataframe(
            df,
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

    csv = df.to_csv(index=False)
    st.download_button("📥 Download State Summary (CSV)", csv, "state_summary.csv", "text/csv")


# ============================================================
# PAGE 2: HIV SERVICES
# ============================================================
elif page == "🔬 HIV Services":
    st.title("🔬 HIV Services Analysis")
    st.markdown("Medicaid claims filtered to HIV-related HCPCS codes, organized by service category.")

    # Category summary
    df_cat = run_query(f"""
        SELECT
            h.category,
            COUNT(DISTINCT t.BILLING_PROVIDER_NPI_NUM) AS providers,
            SUM(t.TOTAL_CLAIMS) AS total_claims,
            SUM(t.TOTAL_UNIQUE_BENEFICIARIES) AS total_beneficiaries,
            ROUND(SUM(t.TOTAL_PAID), 2) AS total_paid
        FROM tmsis_enriched t
        INNER JOIN hiv_hcpcs_reference h ON t.HCPCS_CODE = h.hcpcs_code
        WHERE "Provider Business Practice Location Address State Name" IS NOT NULL
        {state_filter("t.")}
        GROUP BY 1
        ORDER BY total_claims DESC
    """)

    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Service Categories", len(df_cat))
    col2.metric("HIV Providers", f"{df_cat['providers'].sum():,.0f}")
    col3.metric("HIV Claims", f"{df_cat['total_claims'].sum():,.0f}")
    col4.metric("HIV Paid", f"${df_cat['total_paid'].sum():,.2f}")

    st.markdown("---")

    st.subheader("Claims by HIV Service Category")
    tab1, tab2 = st.tabs(["📊 Chart", "📋 Table"])

    with tab1:
        st.bar_chart(df_cat.set_index("category")["total_claims"], use_container_width=True)

    with tab2:
        st.dataframe(
            df_cat,
            use_container_width=True,
            hide_index=True,
            column_config={
                "category": "Service Category",
                "providers": st.column_config.NumberColumn("Providers", format="%d"),
                "total_claims": st.column_config.NumberColumn("Claims", format="%d"),
                "total_beneficiaries": st.column_config.NumberColumn("Beneficiaries", format="%d"),
                "total_paid": st.column_config.NumberColumn("Total Paid ($)", format="$%.2f"),
            }
        )

    st.markdown("---")

    # Category + State breakdown
    st.subheader("HIV Claims by Category and State")
    df_cat_state = run_query(f"""
        SELECT
            h.category,
            "Provider Business Practice Location Address State Name" AS state,
            COUNT(DISTINCT t.BILLING_PROVIDER_NPI_NUM) AS providers,
            SUM(t.TOTAL_CLAIMS) AS total_claims,
            SUM(t.TOTAL_UNIQUE_BENEFICIARIES) AS total_beneficiaries,
            ROUND(SUM(t.TOTAL_PAID), 2) AS total_paid
        FROM tmsis_enriched t
        INNER JOIN hiv_hcpcs_reference h ON t.HCPCS_CODE = h.hcpcs_code
        WHERE "Provider Business Practice Location Address State Name" IS NOT NULL
        {state_filter("t.")}
        GROUP BY 1, 2
        ORDER BY total_claims DESC
    """)

    st.dataframe(
        df_cat_state,
        use_container_width=True,
        hide_index=True,
        column_config={
            "category": "Category",
            "state": "State",
            "providers": st.column_config.NumberColumn("Providers", format="%d"),
            "total_claims": st.column_config.NumberColumn("Claims", format="%d"),
            "total_beneficiaries": st.column_config.NumberColumn("Beneficiaries", format="%d"),
            "total_paid": st.column_config.NumberColumn("Total Paid ($)", format="$%.2f"),
        }
    )

    st.markdown("---")

    # HCPCS Code detail
    st.subheader("Detail by HCPCS Code")
    df_code = run_query(f"""
        SELECT
            h.hcpcs_code,
            h.category,
            h.description,
            COUNT(DISTINCT t.BILLING_PROVIDER_NPI_NUM) AS providers,
            SUM(t.TOTAL_CLAIMS) AS total_claims,
            SUM(t.TOTAL_UNIQUE_BENEFICIARIES) AS total_beneficiaries,
            ROUND(SUM(t.TOTAL_PAID), 2) AS total_paid
        FROM tmsis_enriched t
        INNER JOIN hiv_hcpcs_reference h ON t.HCPCS_CODE = h.hcpcs_code
        WHERE "Provider Business Practice Location Address State Name" IS NOT NULL
        {state_filter("t.")}
        GROUP BY 1, 2, 3
        ORDER BY total_claims DESC
    """)

    st.dataframe(
        df_code,
        use_container_width=True,
        hide_index=True,
        column_config={
            "hcpcs_code": "HCPCS Code",
            "category": "Category",
            "description": "Description",
            "providers": st.column_config.NumberColumn("Providers", format="%d"),
            "total_claims": st.column_config.NumberColumn("Claims", format="%d"),
            "total_beneficiaries": st.column_config.NumberColumn("Beneficiaries", format="%d"),
            "total_paid": st.column_config.NumberColumn("Total Paid ($)", format="$%.2f"),
        }
    )

    csv = df_cat_state.to_csv(index=False)
    st.download_button("📥 Download HIV Services Data (CSV)", csv, "hiv_services.csv", "text/csv")


# ============================================================
# PAGE 3: PROVIDER DIRECTORY
# ============================================================
elif page == "👩‍⚕️ Provider Directory":
    st.title("👩‍⚕️ HIV Service Provider Directory")
    st.markdown("Searchable directory of Medicaid providers billing for HIV-related services. Use this for **Ryan White coordination** and **provider gap analysis**.")

    if not selected_states:
        st.warning("⚠️ Please select at least one state in the sidebar to load the provider directory. Loading all states at once would return too many results.")
    else:
        with st.spinner("Loading provider directory..."):
            df_providers = run_query(f"""
                SELECT
                    t.BILLING_PROVIDER_NPI_NUM AS npi,
                    COALESCE(
                        t."Provider Organization Name (Legal Business Name)",
                        t."Provider First Name" || ' ' || t."Provider Last Name (Legal Name)"
                    ) AS provider_name,
                    t."Provider Credential Text" AS credentials,
                    t."Healthcare Provider Taxonomy Code_1" AS taxonomy,
                    t."Provider First Line Business Practice Location Address" AS address,
                    t."Provider Business Practice Location Address City Name" AS city,
                    t."Provider Business Practice Location Address State Name" AS state,
                    t."Provider Business Practice Location Address Postal Code" AS zip,
                    COUNT(DISTINCT h.category) AS hiv_service_categories,
                    STRING_AGG(DISTINCT h.category, ', ' ORDER BY h.category) AS categories_served,
                    SUM(t.TOTAL_CLAIMS) AS total_hiv_claims,
                    SUM(t.TOTAL_UNIQUE_BENEFICIARIES) AS total_beneficiaries,
                    ROUND(SUM(t.TOTAL_PAID), 2) AS total_paid
                FROM tmsis_enriched t
                INNER JOIN hiv_hcpcs_reference h ON t.HCPCS_CODE = h.hcpcs_code
                WHERE "Provider Business Practice Location Address State Name" IS NOT NULL
                {state_filter("t.")}
                GROUP BY 1, 2, 3, 4, 5, 6, 7, 8
                ORDER BY total_hiv_claims DESC
            """)

        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("HIV Providers", f"{len(df_providers):,.0f}")
        col2.metric("Total HIV Claims", f"{df_providers['total_hiv_claims'].sum():,.0f}")
        col3.metric("Beneficiaries Served", f"{df_providers['total_beneficiaries'].sum():,.0f}")
        col4.metric("Total Paid", f"${df_providers['total_paid'].sum():,.2f}")

        st.markdown("---")

        # Category filter
        all_categories = sorted(df_providers["categories_served"].str.split(", ").explode().unique())
        selected_category = st.selectbox("Filter by HIV Service Category", ["All"] + list(all_categories))

        # Search box
        search = st.text_input("🔍 Search providers (name, city, NPI)")

        df_display = df_providers.copy()

        if selected_category != "All":
            df_display = df_display[df_display["categories_served"].str.contains(selected_category, na=False)]

        if search:
            mask = df_display.apply(lambda row: search.lower() in str(row.values).lower(), axis=1)
            df_display = df_display[mask]

        st.markdown(f"**{len(df_display):,} providers found**")

        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            height=600,
            column_config={
                "npi": "NPI",
                "provider_name": "Provider Name",
                "credentials": "Credentials",
                "taxonomy": "Taxonomy",
                "address": "Address",
                "city": "City",
                "state": "State",
                "zip": "ZIP",
                "hiv_service_categories": st.column_config.NumberColumn("# Categories", format="%d"),
                "categories_served": "HIV Categories Served",
                "total_hiv_claims": st.column_config.NumberColumn("HIV Claims", format="%d"),
                "total_beneficiaries": st.column_config.NumberColumn("Beneficiaries", format="%d"),
                "total_paid": st.column_config.NumberColumn("Total Paid ($)", format="$%.2f"),
            }
        )

        csv = df_display.to_csv(index=False)
        st.download_button("📥 Download Provider Directory (CSV)", csv, "provider_directory.csv", "text/csv")


# ============================================================
# PAGE 4: TRENDS
# ============================================================
elif page == "📈 Trends":
    st.title("📈 HIV Services Trends (2018–2024)")
    st.markdown("Track Medicaid HIV service utilization over time to identify trends in provider participation, claims volume, and beneficiary access.")

    # Monthly trends
    df_monthly = run_query(f"""
        SELECT
            t.CLAIM_FROM_MONTH AS month,
            COUNT(DISTINCT t.BILLING_PROVIDER_NPI_NUM) AS providers,
            SUM(t.TOTAL_CLAIMS) AS total_claims,
            SUM(t.TOTAL_UNIQUE_BENEFICIARIES) AS total_beneficiaries,
            ROUND(SUM(t.TOTAL_PAID), 2) AS total_paid
        FROM tmsis_enriched t
        INNER JOIN hiv_hcpcs_reference h ON t.HCPCS_CODE = h.hcpcs_code
        WHERE "Provider Business Practice Location Address State Name" IS NOT NULL
        {state_filter("t.")}
        GROUP BY 1
        ORDER BY 1
    """)

    # Yearly summary
    df_yearly = run_query(f"""
        SELECT
            LEFT(t.CLAIM_FROM_MONTH, 4) AS year,
            COUNT(DISTINCT t.BILLING_PROVIDER_NPI_NUM) AS providers,
            SUM(t.TOTAL_CLAIMS) AS total_claims,
            SUM(t.TOTAL_UNIQUE_BENEFICIARIES) AS total_beneficiaries,
            ROUND(SUM(t.TOTAL_PAID), 2) AS total_paid
        FROM tmsis_enriched t
        INNER JOIN hiv_hcpcs_reference h ON t.HCPCS_CODE = h.hcpcs_code
        WHERE "Provider Business Practice Location Address State Name" IS NOT NULL
        {state_filter("t.")}
        GROUP BY 1
        ORDER BY 1
    """)

    # Category trends
    df_cat_trend = run_query(f"""
        SELECT
            t.CLAIM_FROM_MONTH AS month,
            h.category,
            SUM(t.TOTAL_CLAIMS) AS total_claims
        FROM tmsis_enriched t
        INNER JOIN hiv_hcpcs_reference h ON t.HCPCS_CODE = h.hcpcs_code
        WHERE "Provider Business Practice Location Address State Name" IS NOT NULL
        {state_filter("t.")}
        GROUP BY 1, 2
        ORDER BY 1
    """)

    # Yearly table
    st.subheader("Yearly Summary")
    st.dataframe(
        df_yearly,
        use_container_width=True,
        hide_index=True,
        column_config={
            "year": "Year",
            "providers": st.column_config.NumberColumn("Providers", format="%d"),
            "total_claims": st.column_config.NumberColumn("Claims", format="%d"),
            "total_beneficiaries": st.column_config.NumberColumn("Beneficiaries", format="%d"),
            "total_paid": st.column_config.NumberColumn("Total Paid ($)", format="$%.2f"),
        }
    )

    st.markdown("---")

    st.subheader("Monthly HIV-Related Medicaid Claims")
    st.line_chart(df_monthly.set_index("month")["total_claims"], use_container_width=True)

    st.markdown("---")

    st.subheader("Monthly Active HIV Service Providers")
    st.line_chart(df_monthly.set_index("month")["providers"], use_container_width=True)

    st.markdown("---")

    st.subheader("Monthly Beneficiaries Receiving HIV Services")
    st.line_chart(df_monthly.set_index("month")["total_beneficiaries"], use_container_width=True)

    st.markdown("---")

    st.subheader("Claims by HIV Service Category Over Time")
    if not df_cat_trend.empty:
        df_pivot = df_cat_trend.pivot_table(index="month", columns="category", values="total_claims", fill_value=0)
        st.line_chart(df_pivot, use_container_width=True)

    csv = df_monthly.to_csv(index=False)
    st.download_button("📥 Download Trends Data (CSV)", csv, "hiv_trends.csv", "text/csv")
