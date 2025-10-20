"""
Streamlit Web Dashboard for Japanese Public Officials Data Collector
A beautiful, interactive UI for running scrapers and viewing results.
"""

import streamlit as st
import pandas as pd
import os
from datetime import datetime
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.scrapers.officials import OfficialsScraper
from src.scrapers.elections import ElectionsScraper
from src.scrapers.funding import FundingScraper
from src.core.csv_exporter import CSVExporter
from src.core.logger import get_logger

# Page configuration
st.set_page_config(
    page_title="Japanese Officials Data Collector",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #1f77b4;
        color: white;
        font-weight: bold;
        border-radius: 5px;
        padding: 0.5rem;
    }
    .stButton>button:hover {
        background-color: #145a8c;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'scraping_status' not in st.session_state:
    st.session_state.scraping_status = "Ready"
if 'last_results' not in st.session_state:
    st.session_state.last_results = {}
if 'scraping_in_progress' not in st.session_state:
    st.session_state.scraping_in_progress = False

# Logger
logger = get_logger(__name__)

# Helper functions
def get_output_path():
    """Get output directory path."""
    return Path("data/outputs")

def load_csv_data(filename):
    """Load CSV file if it exists."""
    filepath = get_output_path() / filename
    if filepath.exists():
        try:
            return pd.read_csv(filepath, encoding='utf-8-sig')
        except Exception as e:
            st.error(f"Error loading {filename}: {e}")
            return None
    return None

def get_file_info(filename):
    """Get file modification time and size."""
    filepath = get_output_path() / filename
    if filepath.exists():
        stat = filepath.stat()
        mod_time = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        size_kb = stat.st_size / 1024
        return mod_time, size_kb
    return None, None

def scrape_officials(limit=None):
    """Run officials scraper."""
    try:
        with st.spinner('🏛️ Scraping officials data...'):
            scraper = OfficialsScraper()
            results = scraper.scrape(limit=limit)
            
            # Export to CSV
            exporter = CSVExporter(output_dir="data/outputs")
            exporter.export(results, "officials.csv")
            
            # Export social profiles
            social_profiles = []
            for official in results:
                official_id = official.get('official_id')
                for social in official.get('social_media', []):
                    social_profiles.append({
                        'official_id': official_id,
                        **social
                    })
            
            if social_profiles:
                exporter.export(social_profiles, "officials_social.csv")
            
            return len(results), len(social_profiles)
    except Exception as e:
        logger.error(f"Error scraping officials: {e}")
        raise

def scrape_elections(limit=None):
    """Run elections scraper."""
    try:
        with st.spinner('🗳️ Scraping election data...'):
            scraper = ElectionsScraper()
            results = scraper.scrape(limit=limit)
            election_results = scraper.get_election_results()
            
            # Export to CSV
            exporter = CSVExporter(output_dir="data/outputs")
            if results:
                exporter.export(results, "elections.csv")
            if election_results:
                exporter.export(election_results, "election_results.csv")
            
            return len(results), len(election_results)
    except Exception as e:
        logger.error(f"Error scraping elections: {e}")
        raise

def scrape_funding(limit=None):
    """Run funding scraper."""
    try:
        with st.spinner('💰 Scraping funding data...'):
            scraper = FundingScraper()
            results = scraper.scrape(limit=limit)
            
            # Export to CSV
            if results:
                exporter = CSVExporter(output_dir="data/outputs")
                exporter.export(results, "funding.csv")
            
            return len(results)
    except Exception as e:
        logger.error(f"Error scraping funding: {e}")
        raise

# Header
st.markdown('<div class="main-header">🏛️ Japanese Public Officials Data Collector</div>', unsafe_allow_html=True)
st.markdown("---")

# Sidebar - Controls
with st.sidebar:
    st.header("⚙️ Scraper Controls")
    
    # Cache management
    st.subheader("🗑️ Cache")
    if st.button("Clear Cache", help="Clear old cached data and force fresh scraping with correct encoding"):
        import shutil
        from pathlib import Path
        
        cache_dir = Path("data/cache")
        if cache_dir.exists():
            try:
                shutil.rmtree(cache_dir)
                cache_dir.mkdir(parents=True, exist_ok=True)
                st.success("✅ Cache cleared! Next scrape will fetch fresh data.")
                st.info("💡 Tip: If you see garbled Japanese characters, clear cache and re-scrape.")
            except Exception as e:
                st.error(f"❌ Error clearing cache: {e}")
        else:
            st.info("No cache found")
    
    st.markdown("---")
    
    # Scraping options
    st.subheader("Options")
    limit_enabled = st.checkbox("Limit results (for testing)", value=True)
    limit_value = st.number_input("Limit", min_value=1, max_value=1000, value=5, disabled=not limit_enabled)
    
    st.markdown("---")
    
    # Individual scrapers
    st.subheader("Individual Scrapers")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🏛️ Officials", disabled=st.session_state.scraping_in_progress):
            st.session_state.scraping_in_progress = True
            try:
                limit = limit_value if limit_enabled else None
                officials_count, social_count = scrape_officials(limit)
                st.session_state.last_results = {
                    'type': 'officials',
                    'officials': officials_count,
                    'social': social_count,
                    'time': datetime.now().strftime("%H:%M:%S")
                }
                st.success(f"✅ {officials_count} officials, {social_count} SNS")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
            finally:
                st.session_state.scraping_in_progress = False
                st.rerun()
    
    with col2:
        if st.button("🗳️ Elections", disabled=st.session_state.scraping_in_progress):
            st.session_state.scraping_in_progress = True
            try:
                limit = limit_value if limit_enabled else None
                schedules, results = scrape_elections(limit)
                st.session_state.last_results = {
                    'type': 'elections',
                    'schedules': schedules,
                    'results': results,
                    'time': datetime.now().strftime("%H:%M:%S")
                }
                st.success(f"✅ {schedules} schedules, {results} results")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
            finally:
                st.session_state.scraping_in_progress = False
                st.rerun()
    
    if st.button("💰 Funding", disabled=st.session_state.scraping_in_progress):
        st.session_state.scraping_in_progress = True
        try:
            limit = limit_value if limit_enabled else None
            funding_count = scrape_funding(limit)
            st.session_state.last_results = {
                'type': 'funding',
                'records': funding_count,
                'time': datetime.now().strftime("%H:%M:%S")
            }
            st.success(f"✅ {funding_count} funding records")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
        finally:
            st.session_state.scraping_in_progress = False
            st.rerun()
    
    st.markdown("---")
    
    # Run all button
    if st.button("🚀 Run All Scrapers", type="primary", disabled=st.session_state.scraping_in_progress):
        st.session_state.scraping_in_progress = True
        try:
            limit = limit_value if limit_enabled else None
            
            # Run all scrapers
            officials_count, social_count = scrape_officials(limit)
            schedules, results = scrape_elections(limit)
            funding_count = scrape_funding(limit)
            
            st.session_state.last_results = {
                'type': 'all',
                'officials': officials_count,
                'social': social_count,
                'schedules': schedules,
                'results': results,
                'funding': funding_count,
                'time': datetime.now().strftime("%H:%M:%S")
            }
            st.success("✅ All scrapers completed!")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
        finally:
            st.session_state.scraping_in_progress = False
            st.rerun()
    
    st.markdown("---")
    st.caption("Version 1.1.1")

# Main content area
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Dashboard", "👥 Officials", "🗳️ Elections", "💰 Funding", "📁 Files"])

# Tab 1: Dashboard
with tab1:
    # Status section
    st.subheader("📈 Collection Status")
    
    if st.session_state.last_results:
        results = st.session_state.last_results
        st.markdown(f'<div class="success-box">✅ <b>Last run:</b> {results.get("time")} - <b>Type:</b> {results.get("type")}</div>', unsafe_allow_html=True)
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    # Load current data
    officials_df = load_csv_data("officials.csv")
    elections_df = load_csv_data("elections.csv")
    election_results_df = load_csv_data("election_results.csv")
    funding_df = load_csv_data("funding.csv")
    social_df = load_csv_data("officials_social.csv")
    
    with col1:
        count = len(officials_df) if officials_df is not None else 0
        st.metric("👥 Officials", count)
    
    with col2:
        count = len(elections_df) if elections_df is not None else 0
        st.metric("🗳️ Elections", count)
    
    with col3:
        count = len(funding_df) if funding_df is not None else 0
        st.metric("💰 Funding Records", count)
    
    with col4:
        count = len(social_df) if social_df is not None else 0
        st.metric("📱 SNS Profiles", count)
    
    st.markdown("---")
    
    # Recent data preview
    st.subheader("🔍 Recent Data Preview")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Officials (Latest 5)**")
        if officials_df is not None and not officials_df.empty:
            preview = officials_df[['name', 'age', 'faction', 'office_type']].head(5)
            st.dataframe(preview, width='stretch')
        else:
            st.info("No officials data available")
    
    with col2:
        st.markdown("**Elections (Latest 5)**")
        if elections_df is not None and not elections_df.empty:
            preview = elections_df[['name', 'jurisdiction', 'scheduled_date']].head(5)
            st.dataframe(preview, width='stretch')
        else:
            st.info("No election data available")

# Tab 2: Officials
with tab2:
    st.subheader("👥 Public Officials Data")
    
    officials_df = load_csv_data("officials.csv")
    
    if officials_df is not None and not officials_df.empty:
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            office_types = ["All"] + list(officials_df['office_type'].dropna().unique())
            selected_office = st.selectbox("Office Type", office_types)
        
        with col2:
            factions = ["All"] + list(officials_df['faction'].dropna().unique())
            selected_faction = st.selectbox("Faction", factions)
        
        with col3:
            search = st.text_input("Search by name", "")
        
        # Apply filters
        filtered_df = officials_df.copy()
        if selected_office != "All":
            filtered_df = filtered_df[filtered_df['office_type'] == selected_office]
        if selected_faction != "All":
            filtered_df = filtered_df[filtered_df['faction'] == selected_faction]
        if search:
            filtered_df = filtered_df[filtered_df['name'].str.contains(search, na=False, case=False)]
        
        st.write(f"Showing {len(filtered_df)} of {len(officials_df)} officials")
        st.dataframe(filtered_df, width='stretch', height=400)
        
        # Download button
        csv = filtered_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
        st.download_button(
            label="📥 Download Filtered Data as CSV",
            data=csv,
            file_name=f"officials_filtered_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    else:
        st.info("No officials data available. Run the scraper to collect data.")

# Tab 3: Elections
with tab3:
    st.subheader("🗳️ Election Data")
    
    elections_df = load_csv_data("elections.csv")
    
    if elections_df is not None and not elections_df.empty:
        # Filters
        col1, col2 = st.columns(2)
        
        with col1:
            jurisdictions = ["All"] + list(elections_df['jurisdiction'].dropna().unique())
            selected_jurisdiction = st.selectbox("Jurisdiction", jurisdictions)
        
        with col2:
            levels = ["All"] + list(elections_df['level'].dropna().unique())
            selected_level = st.selectbox("Level", levels)
        
        # Apply filters
        filtered_df = elections_df.copy()
        if selected_jurisdiction != "All":
            filtered_df = filtered_df[filtered_df['jurisdiction'] == selected_jurisdiction]
        if selected_level != "All":
            filtered_df = filtered_df[filtered_df['level'] == selected_level]
        
        st.write(f"Showing {len(filtered_df)} of {len(elections_df)} elections")
        st.dataframe(filtered_df, width='stretch', height=400)
        
        # Download button
        csv = filtered_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
        st.download_button(
            label="📥 Download Filtered Data as CSV",
            data=csv,
            file_name=f"elections_filtered_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    else:
        st.info("No election data available. Run the scraper to collect data.")

# Tab 4: Funding
with tab4:
    st.subheader("💰 Funding Data")
    
    funding_df = load_csv_data("funding.csv")
    
    if funding_df is not None and not funding_df.empty:
        st.dataframe(funding_df, width='stretch', height=400)
        
        # Download button
        csv = funding_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
        st.download_button(
            label="📥 Download Data as CSV",
            data=csv,
            file_name=f"funding_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    else:
        st.info("No funding data available. Run the scraper to collect data.")

# Tab 5: Files
with tab5:
    st.subheader("📁 Output Files")
    
    output_dir = get_output_path()
    
    files = [
        ("officials.csv", "👥 Public Officials"),
        ("officials_social.csv", "📱 SNS Profiles"),
        ("elections.csv", "🗳️ Election Schedules"),
        ("election_results.csv", "📊 Election Results"),
        ("funding.csv", "💰 Funding Reports")
    ]
    
    for filename, description in files:
        mod_time, size_kb = get_file_info(filename)
        
        col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
        
        with col1:
            st.write(f"**{description}**")
            st.caption(filename)
        
        with col2:
            if mod_time:
                st.write(f"📅 {mod_time}")
            else:
                st.write("❌ Not found")
        
        with col3:
            if size_kb:
                st.write(f"📦 {size_kb:.1f} KB")
            else:
                st.write("-")
        
        with col4:
            filepath = output_dir / filename
            if filepath.exists():
                with open(filepath, 'rb') as f:
                    st.download_button(
                        label="📥 Download",
                        data=f,
                        file_name=filename,
                        mime="text/csv",
                        key=f"download_{filename}"
                    )
        
        st.markdown("---")
    
    # Open folder button
    if st.button("📂 Open Output Folder"):
        import subprocess
        subprocess.Popen(f'explorer "{output_dir.absolute()}"')

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; padding: 1rem;'>
        <p><b>Japanese Public Officials Data Collector</b> v1.1.1</p>
        <p>For research and educational purposes</p>
    </div>
    """,
    unsafe_allow_html=True
)
