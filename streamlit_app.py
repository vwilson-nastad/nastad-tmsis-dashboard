import streamlit as st
import duckdb
import pandas as pd

st.set_page_config(page_title="NASTAD TMSIS Dashboard", page_icon="🏥", layout="wide")

# ============================================================
# NASTAD BRAND THEMING
# Colors from NASTAD Style Guide (January 2022)
# Primary Blue: #019DE0 | Light Blue: #68D2F2 | Dark Blue: #0F369B
# Black: #060606 | Light Gray: #EBEBEB | Red: #EB3F21 | Yellow: #FFCC11
# ============================================================
st.markdown("""
<style>
    /* --- NASTAD Brand Colors --- */
    :root {
        --nastad-blue: #019DE0;
        --nastad-light-blue: #68D2F2;
        --nastad-dark-blue: #0F369B;
        --nastad-black: #060606;
        --nastad-gray: #EBEBEB;
        --nastad-red: #EB3F21;
        --nastad-yellow: #FFCC11;
    }

    /* Header bar - keep light so icons are visible */
    header[data-testid="stHeader"] {
        background-color: #FFFFFF !important;
        border-bottom: 2px solid #019DE0;
    }
    /* Ensure header icons and buttons stay visible */
    header[data-testid="stHeader"] * {
        color: #060606 !important;
    }
    header[data-testid="stHeader"] button {
        color: #060606 !important;
    }
    header[data-testid="stHeader"] svg {
        fill: #060606 !important;
    }

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #060606;
        color: white;
    }
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown li,
    section[data-testid="stSidebar"] label {
        color: white !important;
    }
    section[data-testid="stSidebar"] hr {
        border-color: #333333;
    }

    /* Radio button labels in sidebar */
    section[data-testid="stSidebar"] .stRadio label,
    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label,
    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label p,
    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label span,
    section[data-testid="stSidebar"] .stRadio div[data-testid="stMarkdownContainer"] p,
    section[data-testid="stSidebar"] [data-baseweb="radio"] label,
    section[data-testid="stSidebar"] [data-baseweb="radio"] div {
        color: white !important;
    }

    /* Radio button circles */
    section[data-testid="stSidebar"] [data-baseweb="radio"] div[data-testid="stMarkdownContainer"] {
        color: white !important;
    }
    section[data-testid="stSidebar"] .stRadio > div {
        color: white !important;
    }

    /* Multiselect filter labels and text */
    section[data-testid="stSidebar"] .stMultiSelect label,
    section[data-testid="stSidebar"] .stMultiSelect span,
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stSelectbox span {
        color: white !important;
    }

    /* All text inside sidebar - force white */
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"],
    section[data-testid="stSidebar"] .stRadio div,
    section[data-testid="stSidebar"] [data-baseweb="radio"] div {
        color: white !important;
    }
    /* Keep multiselect dropdown and input readable */
    section[data-testid="stSidebar"] [data-baseweb="select"] [data-baseweb="tag"] {
        color: white !important;
        background-color: #019DE0 !important;
    }
    section[data-testid="stSidebar"] [data-baseweb="popover"] * {
        color: #060606 !important;
    }

    /* Metric cards */
    div[data-testid="stMetric"] {
        background-color: #EBEBEB;
        border-left: 4px solid #019DE0;
        padding: 12px 16px;
        border-radius: 4px;
    }
    div[data-testid="stMetric"] label {
        color: #0F369B !important;
        font-weight: 600;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #060606 !important;
    }

    /* Primary buttons */
    .stDownloadButton button {
        background-color: #019DE0 !important;
        color: white !important;
        border: none !important;
        border-radius: 4px;
    }
    .stDownloadButton button:hover {
        background-color: #0F369B !important;
    }

    /* Tab styling */
    button[data-baseweb="tab"] {
        color: #0F369B !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        border-bottom-color: #019DE0 !important;
    }

    /* Info and warning boxes */
    div[data-testid="stAlert"] {
        border-radius: 4px;
    }

    /* Page titles */
    h1 {
        color: #0F369B !important;
    }
    h2, h3 {
        color: #060606 !important;
    }

    /* Links */
    a {
        color: #019DE0 !important;
    }
    a:hover {
        color: #0F369B !important;
    }

    /* Dataframe header */
    .stDataFrame th {
        background-color: #019DE0 !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

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
st.sidebar.markdown("""
<div style="text-align: center; padding: 10px 0 5px 0;">
    <span style="color: #68D2F2; font-size: 28px; font-weight: bold;">NASTAD</span>
    <br>
    <span style="color: white; font-size: 14px;">TMSIS Medicaid Dashboard</span>
</div>
""", unsafe_allow_html=True)
st.sidebar.markdown(
    '<p style="color: #68D2F2; text-align: center; font-size: 13px;">'
    'Medicaid Provider Analysis for<br><strong>Ending the HIV Epidemic</strong></p>',
    unsafe_allow_html=True
)
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigate",
    ["ℹ️ About", "📋 HCPCS Reference", "🏠 State Overview", "🔬 HIV Services", "👩‍⚕️ Provider Directory", "📈 Trends"],
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

# Load years for filter
years_df = run_query("""
    SELECT DISTINCT LEFT(CLAIM_FROM_MONTH, 4) AS year
    FROM tmsis_enriched
    WHERE CLAIM_FROM_MONTH IS NOT NULL
    ORDER BY year
""")

selected_years = st.sidebar.multiselect(
    "Filter by Year(s)",
    years_df["year"].tolist(),
    default=None,
    help="Leave empty to show all years. Does not apply to Trends page."
)

# Build WHERE clause helpers
def state_filter(alias=""):
    col = f'{alias}"Provider Business Practice Location Address State Name"' if alias else '"Provider Business Practice Location Address State Name"'
    if selected_states:
        state_list = ", ".join([f"'{s}'" for s in selected_states])
        return f"AND {col} IN ({state_list})"
    return ""

def year_filter(alias=""):
    col = f'{alias}CLAIM_FROM_MONTH' if alias else 'CLAIM_FROM_MONTH'
    if selected_years:
        year_list = ", ".join([f"'{y}'" for y in selected_years])
        return f"AND LEFT({col}, 4) IN ({year_list})"
    return ""

st.sidebar.markdown("---")
st.sidebar.markdown(
    '<p style="color: #68D2F2; font-size: 11px;">'
    '<strong>Data:</strong> CMS T-MSIS 2018–2024<br>'
    '<strong>Records:</strong> 227M enriched claims<br>'
    '<strong>Updated:</strong> February 2026<br><br>'
    'Built by <strong>NASTAD</strong></p>',
    unsafe_allow_html=True
)


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
    - **What it is:** The NPPES is CMS's registry of all health care providers assigned a National 
      Provider Identifier (NPI). It contains provider names, credentials, practice addresses, 
      organizational affiliations, and health care taxonomy codes.
    - **What we use:** Provider demographic and practice location data to enrich the TMSIS claims, 
      enabling identification of providers by name, organization, specialty, and geographic location.
    - **Source:** [CMS NPI Registry](https://npiregistry.cms.hhs.gov/)

    **HIV HCPCS Reference Table — NASTAD**
    - **What it is:** A curated crosswalk developed by NASTAD that maps HCPCS procedure codes to 
      HIV-specific service categories. This table was built using the **CMS HCPCS 2025 Annual Code File** 
      and validated against published HIV claims-based case-finding algorithms, including Macinski et al. 
      (2019), *"Validation of an Optimized Algorithm for Identifying Persons Living with Diagnosed HIV 
      From New York State Medicaid Data, 2006–2014."*
    - **Categories:** HIV Screening & Diagnosis, HIV Lab Monitoring, Antiretroviral Therapy, PrEP, 
      OI Prophylaxis & Treatment, HIV Quality Measures, and HIV Supportive Services.
    - **Codes tracked:** 67 HIV-related HCPCS codes across 7 service categories.
    - **Full transparency:** See the **📋 HCPCS Reference** page for the complete code table with 
      every code, category, and description.

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
    - **HCPCS code specificity:** The HIV HCPCS reference table prioritizes codes that are explicitly 
      HIV-related. Some OI treatment codes (e.g., amphotericin B, ganciclovir) are used for conditions 
      beyond HIV but are included because they are standard treatments for HIV-associated opportunistic 
      infections. See the **📋 HCPCS Reference** page for the full code list and methodology.
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
# PAGE 0B: HCPCS REFERENCE
# ============================================================
elif page == "📋 HCPCS Reference":
    st.title("📋 HIV HCPCS Code Reference")
    st.markdown("""
    This page provides full transparency into the HCPCS codes used to identify HIV-related services 
    throughout this dashboard. Every code listed below is used when filtering the TMSIS claims data 
    to the **HIV Services**, **Provider Directory**, and **Trends** pages.
    """)

    st.markdown("---")

    # Load the live table from MotherDuck
    df_hcpcs = run_query("""
        SELECT hcpcs_code, category, description
        FROM hiv_hcpcs_reference
        ORDER BY category, hcpcs_code
    """)

    # Summary metrics
    col1, col2 = st.columns(2)
    col1.metric("Total HCPCS Codes", len(df_hcpcs))
    col2.metric("Service Categories", df_hcpcs["category"].nunique())

    st.markdown("---")

    # Category summary
    st.subheader("Codes by Category")
    df_cat_count = df_hcpcs.groupby("category").size().reset_index(name="code_count").sort_values("code_count", ascending=False)
    st.bar_chart(df_cat_count.set_index("category")["code_count"], use_container_width=True)

    st.markdown("---")

    # Category filter
    selected_category = st.selectbox(
        "Filter by Category",
        ["All Categories"] + sorted(df_hcpcs["category"].unique().tolist())
    )

    if selected_category != "All Categories":
        df_display = df_hcpcs[df_hcpcs["category"] == selected_category]
    else:
        df_display = df_hcpcs

    st.markdown(f"**{len(df_display)} codes displayed**")

    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        height=600,
        column_config={
            "hcpcs_code": "HCPCS Code",
            "category": "Service Category",
            "description": "Description",
        }
    )

    # Download
    csv = df_hcpcs.to_csv(index=False)
    st.download_button("📥 Download Full HCPCS Reference Table (CSV)", csv, "hiv_hcpcs_reference.csv", "text/csv")

    st.markdown("---")

    st.subheader("Methodology & Sources")
    st.markdown("""
    **Code Selection Criteria**

    Codes were selected based on two principles: (1) the code must be **explicitly related to HIV 
    prevention, diagnosis, treatment, monitoring, or associated opportunistic infection management**, 
    and (2) the code must appear in established HIV claims-based identification algorithms or official 
    CMS HIV-specific code sets.

    Broad, non-HIV-specific codes (e.g., general clinic visits, telephone evaluations, generic case 
    management) were intentionally excluded to minimize false positives and ensure that the HIV service 
    flag is meaningful for provider gap analysis.

    **Sources Used**

    1. **CMS HCPCS 2025 Annual Code File** (January 2025 release) — The official federal code set was 
       searched systematically for all codes with HIV, antiretroviral, PrEP, viral load, CD4, and 
       opportunistic infection keywords. This identified PrEP-specific codes (J0739, J0750, J0751, 
       G0011–G0013, Q0516–Q0521), injectable ARV codes (J0741, J1746, J1961), HIV screening codes 
       (G0432, G0433, G0435, G0475), and HIV quality measure codes (G9242–G9247, G8500).

    2. **Macinski SE, Gunn JKL, Goyal M, et al.** *"Validation of an Optimized Algorithm for Identifying 
       Persons Living with Diagnosed HIV From New York State Medicaid Data, 2006–2014."* American Journal 
       of Epidemiology, 2019. — This validated algorithm uses specific lab test codes (87536, 87901, 87903, 
       87904, 87906), ARV claims, and opportunistic infection treatments as markers for identifying PLWDH 
       in Medicaid claims. The OI treatment codes in our reference table (pentamidine, amphotericin B, 
       ganciclovir, foscarnet, cidofovir) align with this algorithm.

    **Category Definitions**

    | Category | Definition |
    |----------|-----------|
    | **HIV Screening & Diagnosis** | Laboratory tests and assays used to screen for or confirm HIV infection |
    | **HIV Lab Monitoring** | Ongoing lab tests for managing HIV (viral load, CD4 counts, resistance testing) |
    | **Antiretroviral Therapy** | Injectable or infusion antiretroviral medications billed via HCPCS J-codes |
    | **PrEP** | Pre-exposure prophylaxis drugs, counseling, injection, and pharmacy supply fees |
    | **OI Prophylaxis & Treatment** | Medications for preventing or treating HIV-associated opportunistic infections (PCP, CMV, cryptococcal/fungal infections) |
    | **HIV Quality Measure** | CMS quality reporting codes specific to HIV care processes and outcomes |
    | **HIV Supportive Services** | Services addressing HIV treatment side effects or home-based HIV medication administration |

    *This reference table is maintained by NASTAD and will be updated as CMS releases new HCPCS codes 
    or as clinical guidelines evolve. The table was last updated in February 2026.*
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
        {year_filter()}
        GROUP BY 1
        ORDER BY total_claims DESC
    """)

    # Active filters display
    filter_desc = []
    if selected_states:
        filter_desc.append(f"States: {', '.join(selected_states)}")
    if selected_years:
        filter_desc.append(f"Years: {', '.join(selected_years)}")
    if filter_desc:
        st.caption("Active filters: " + " | ".join(filter_desc))

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
        {year_filter("t.")}
        GROUP BY 1
        ORDER BY total_claims DESC
    """)

    # Active filters display
    filter_desc = []
    if selected_states:
        filter_desc.append(f"States: {', '.join(selected_states)}")
    if selected_years:
        filter_desc.append(f"Years: {', '.join(selected_years)}")
    if filter_desc:
        st.caption("Active filters: " + " | ".join(filter_desc))

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
        {year_filter("t.")}
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
        {year_filter("t.")}
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
                {year_filter("t.")}
                GROUP BY 1, 2, 3, 4, 5, 6, 7, 8
                ORDER BY total_hiv_claims DESC
            """)

        # Active filters display
        filter_desc = []
        if selected_states:
            filter_desc.append(f"States: {', '.join(selected_states)}")
        if selected_years:
            filter_desc.append(f"Years: {', '.join(selected_years)}")
        if filter_desc:
            st.caption("Active filters: " + " | ".join(filter_desc))

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

    if selected_years:
        st.info("ℹ️ The **Year filter** does not apply to this page — all years are shown to display the full trend.")

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
