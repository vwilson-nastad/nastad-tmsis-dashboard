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
    ["ℹ️ About", "🏠 State Overview", "🔬 HIV Services", "👩‍⚕️ Provider Directory", "📈 Trends"],
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
# PAGE 0: ABOUT
# ============================================================
if page == "ℹ️ About":
    st.title("ℹ️ About This Dashboard")

    st.markdown("""
    ## NASTAD TMSIS Medicaid Provider Analysis Dashboard

    This dashboard was developed by **NASTAD** (National Alliance of State & Territorial AIDS Directors) 
    to support health departments and Ryan White HIV/AIDS Program recipients in identifying Medicaid 
    providers delivering HIV-related services, conducting provider gap analyses, and strengthening 
    coordination between Medicaid and the Ryan White HIV/AIDS Program as part of the national 
    **Ending the HIV Epidemic (EHE)** initiative.

    ---

    ### 📊 Primary Data Sources

    **T-MSIS Analytic Files (TAF) — CMS**
    - **What it is:** The Transformed Medicaid Statistical Information System (T-MSIS) is CMS's 
      national Medicaid and CHIP claims database. It contains information on Medicaid beneficiaries, 
      providers, and the services they receive.
    - **What we use:** Provider-level utilization summary files covering **2018–2024**, which include 
      billing provider NPIs, HCPCS procedure codes, claim counts, total paid amounts, and unique 
      beneficiary counts.
    - **Volume:** Approximately **227 million** claim-level summary records across all states 
      and territories.
    - **Source:** [CMS T-MSIS Data](https://www.medicaid.gov/medicaid/data-systems/macbis/transformed-medicaid-statistical-information-system-t-msis/index.html)

    **National Plan and Provider Enumeration System (NPPES) — CMS**
    - **What it is:** The NPPES is CMS's registry of all healthcare providers assigned a National 
      Provider Identifier (NPI). It contains provider names, credentials, practice addresses, 
      organizational affiliations, and healthcare taxonomy codes.
    - **What we use:** Provider demographic and practice location data to enrich the TMSIS claims, 
      enabling identification of providers by name, organization, specialty, and geographic location.
    - **Source:** [CMS NPI Registry](https://npiregistry.cms.hhs.gov/)

    **HIV HCPCS Reference Table — NASTAD**
    - **What it is:** A curated crosswalk developed by NASTAD that maps HCPCS procedure codes to 
      HIV-specific service categories.
    - **Categories:** HIV Lab Testing, Antiretroviral Therapy, PrEP, Care Management, 
      Case Management, Opportunistic Infection Treatment, and Quality Measures.
    - **Codes tracked:** 27 HIV-related HCPCS codes across 7 service categories.

    ---

    ### 🏗️ Architecture

    | Component | Technology | Purpose |
    |-----------|-----------|---------|
    | **Data Warehouse** | MotherDuck (Cloud DuckDB) | Stores and queries the full 227M row enriched dataset |
    | **Data Enrichment** | DuckDB SQL | Joins TMSIS claims with NPI provider data via billing NPI |
    | **Front-End** | Streamlit | Interactive dashboard with live queries, filters, and CSV export |
    | **Hosting** | Streamlit Community Cloud | Free public hosting — no software install required for end users |
    | **Data Backup** | Cloudflare R2 | Object storage for raw data files |

    All queries run **live** against the full dataset — nothing is pre-aggregated or sampled. When you 
    filter by state or view the provider directory, MotherDuck processes the query across all 227 million 
    records and returns results in seconds.

    ---

    ### 🔍 How To Use This Dashboard

    **For Health Departments & Ryan White Recipients:**

    1. **Select your state(s)** in the sidebar filter to focus on your jurisdiction
    2. **State Overview** — See total Medicaid provider counts, claims, and spending in your state
    3. **HIV Services** — Understand which HIV service categories are being billed through Medicaid, 
       and at what volume
    4. **Provider Directory** — Identify specific providers billing for HIV services in your state, 
       including their NPI, organization name, address, and which HIV service categories they provide. 
       Use this for Ryan White provider network gap analysis.
    5. **Trends** — Track how HIV service utilization has changed over 2018–2024 in your jurisdiction
    6. **Download CSV** — Every page includes a download button so you can export data for your own analysis

    ---

    ### ⚠️ Important Caveats

    - **Beneficiary counts** may reflect the same individual counted multiple times across different 
      providers or service months. These are not deduplicated person-level counts.
    - **Small cell sizes:** In states or service categories with very few providers or beneficiaries, 
      exercise caution in interpretation to protect against potential re-identification.
    - **HCPCS code specificity:** Some codes in the reference table (particularly Care Management codes) 
      are not exclusively HIV-specific. They capture a broader set of services that may include non-HIV visits.
    - **Data currency:** This dashboard reflects TMSIS data through 2024. CMS releases data with a lag, 
      so the most recent months may be incomplete.
    - **Provider location** is based on the NPI registry practice address and may not reflect every 
      location where a provider delivers services.

    ---

    ### 📬 Contact

    For questions, feedback, or technical assistance, please contact **NASTAD** at 
    [nastad.org](https://www.nastad.org).

    *This dashboard is part of NASTAD's technical assistance to support public health departments 
    in ending the HIV epidemic through improved Medicaid and Ryan White program coordination.*
    """)


# ============================================================
# PAGE 1: STATE OVERVIEW
# ============================================================
elif page == "🏠 State Overview":
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
