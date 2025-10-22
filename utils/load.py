import pandas as pd
import streamlit as st

# ============================================================
# ✅ Configuration
# ============================================================

REQUIRED_COLUMNS = [
    "Order ID", "Order Date", "Ship Date", "Region", "Category",
    "Sales", "Profit", "Discount", "Quantity"
]

COLUMN_GROUPS = {
    "Temporal": ["Order Date", "Ship Date"],
    "Geography": ["Region", "State", "City", "Country"],
    "Customer": ["Customer ID", "Customer Name", "Segment"],
    "Product": ["Category", "Sub-Category", "Product ID", "Product Name"],
    "Transactional": ["Sales", "Profit", "Discount", "Quantity", "Order ID"],
    "Logistic": ["Ship Mode"]
}


# ============================================================
# ⚙️ Utility Functions
# ============================================================

def preprocess(df):
    """Clean and format dataframe."""
    df["Order Date"] = pd.to_datetime(df["Order Date"], errors="coerce")
    df["Ship Date"] = pd.to_datetime(df["Ship Date"], errors="coerce")
    df = df.dropna(subset=["Order Date", "Sales", "Profit"])
    return df


def validate_columns(df):
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        st.sidebar.error(f"❌ Missing required columns: {', '.join(missing)}")
        return False
    return True


def load_sample_data():
    """Load built-in sample dataset."""
    df = pd.read_csv("data/sample.csv", encoding="latin-1")
    df = preprocess(df)
    return df


# ============================================================
# 🧠 Sidebar Dataset Audit
# ============================================================

def dataset_audit(df):
    """Analyze what column groups are available and what's missing."""
    with st.sidebar.expander("Summary & Coverage", expanded=False):
        available, missing = {}, {}
        for group, cols in COLUMN_GROUPS.items():
            present_cols = [c for c in cols if c in df.columns]
            missing_cols = [c for c in cols if c not in df.columns]
            available[group] = present_cols
            missing[group] = missing_cols

        st.markdown("#### Column Availability")
        for group in COLUMN_GROUPS.keys():
            if available[group]:
                st.success(f"✅ **{group}**: {', '.join(available[group])}")
            else:
                st.warning(f"⚠️ **{group}** data missing")

        st.markdown("---")
        st.markdown("#### 💡 Feature Coverage")

        features = []
        if available["Temporal"]:
            features.append("📅 Time-based trends")
        if available["Product"]:
            features.append("📦 Product insights")
        if available["Customer"]:
            features.append("👥 Segment patterns")
        if available["Geography"]:
            features.append("🗺️ Regional mapping")
        if available["Transactional"]:
            features.append("💰 KPI and profit metrics")

        if features:
            for f in features:
                st.markdown(f"- {f}")
        else:
            st.error("❌ No relevant columns found for dashboard generation.")

        st.info(
            "📊 This summary shows which features are active or unavailable "
            "based on the uploaded dataset."
        )

    st.sidebar.markdown("---")
    st.sidebar.markdown(" by PandeAkshat  [📧](mailto:mail@pandeakshat.com) [🌐](https://pandeakshat.com)")


# ============================================================
# 📥 Main Loader
# ============================================================

def load_data():
    """Load dataset with choice between sample or custom CSV."""
    st.sidebar.header("📁 Data Configuration")
    choice = st.sidebar.radio(
        "Select Data Source",
        ["Use Sample Data", "Upload Custom Data"],
        horizontal=True
    )

    if choice == "Use Sample Data":
        df = load_sample_data()
        if df is not None:
            dataset_audit(df)
        return df

    else:
        st.sidebar.markdown("""
        #### 📋 Required Data Format
        Please ensure your file includes these columns:  
        `Order ID`, `Order Date`, `Ship Date`, `Region`, `Category`,  
        `Sales`, `Profit`, `Discount`, `Quantity`  
        """)
        uploaded_file = st.sidebar.file_uploader("Upload your CSV", type=["csv"])

        if uploaded_file:
            try:
                df = pd.read_csv(uploaded_file)
                if not validate_columns(df):
                    st.sidebar.warning("⚠️ The uploaded file is not formatted properly.")
                    return None
                df = preprocess(df)
                st.sidebar.success("✅ Data successfully loaded and validated.")
                dataset_audit(df)
                return df
            except Exception as e:
                st.sidebar.error(f"Error reading file: {e}")
                return None
        else:
            st.sidebar.info("📤 Upload a CSV to continue.")
            return None
