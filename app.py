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
# Tabs for different views
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["📊 Dashboard", "🏛️ Election Politicians", "👥 Officials", "🗳️ Elections", "🗺️ Municipal Scraping", "💰 Funding", "📁 Files"])

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
    politicians_cleaned_df = load_csv_data("politicians_cleaned.csv")
    
    with col1:
        count = len(politicians_cleaned_df) if politicians_cleaned_df is not None else 0
        st.metric("🏛️ Politicians (Election Data)", count)
        if count > 0:
            st.caption("✅ 95.4% quality - 47 prefectures")
    
    with col2:
        count = len(elections_df) if elections_df is not None else 0
        st.metric("🗳️ Elections", count)
    
    with col3:
        count = len(officials_df) if officials_df is not None else 0
        st.metric("� Officials", count)
    
    with col4:
        count = len(social_df) if social_df is not None else 0
        st.metric("📱 SNS Profiles", count)
    
    st.markdown("---")
    
    # Recent data preview
    st.subheader("🔍 Recent Data Preview")
    
    # Add statistics for politicians data
    if politicians_cleaned_df is not None and not politicians_cleaned_df.empty:
        st.markdown("### 🏛️ Milestone 1 - Election Politicians Data")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Politicians", f"{len(politicians_cleaned_df):,}")
        
        with col2:
            prefectures = politicians_cleaned_df['prefecture'].nunique()
            st.metric("Prefectures", f"{prefectures}/47")
        
        with col3:
            with_date = politicians_cleaned_df['election_date'].notna().sum()
            date_pct = (with_date / len(politicians_cleaned_df) * 100)
            st.metric("With Election Date", f"{date_pct:.1f}%")
        
        with col4:
            elections = politicians_cleaned_df['election'].nunique()
            st.metric("Total Elections", f"{elections:,}")
        
        # Top prefectures
        st.markdown("**Top 5 Prefectures by Politicians**")
        top_prefectures = politicians_cleaned_df['prefecture'].value_counts().head(5)
        col1, col2 = st.columns([1, 2])
        
        with col1:
            for prefecture, count in top_prefectures.items():
                st.write(f"**{prefecture}**: {count}")
        
        with col2:
            st.bar_chart(top_prefectures)
        
        # Recent politicians
        st.markdown("**Latest 10 Politicians**")
        preview_columns = ['name', 'prefecture', 'election', 'election_date']
        preview = politicians_cleaned_df[preview_columns].head(10)
        st.dataframe(preview, use_container_width=True)
        
        st.markdown("---")
    
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

# Tab 2: Election Politicians (NEW - Milestone 1)
with tab2:
    st.subheader("🏛️ Election Politicians Data - Milestone 1")
    st.caption("7,336 politicians collected from 47 prefectures via public election results")
    
    politicians_cleaned_df = load_csv_data("politicians_cleaned.csv")
    
    if politicians_cleaned_df is not None and not politicians_cleaned_df.empty:
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Politicians", f"{len(politicians_cleaned_df):,}")
        
        with col2:
            prefectures = politicians_cleaned_df['prefecture'].nunique()
            st.metric("Prefectures Covered", f"{prefectures}/47")
        
        with col3:
            quality_score = 95.4  # From cleaning results
            st.metric("Data Quality", f"{quality_score}%")
        
        with col4:
            elections = politicians_cleaned_df['election'].nunique()
            st.metric("Total Elections", f"{elections:,}")
        
        st.markdown("---")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            prefectures = ["All"] + sorted(list(politicians_cleaned_df['prefecture'].dropna().unique()))
            selected_prefecture = st.selectbox("Prefecture", prefectures)
        
        with col2:
            search = st.text_input("Search by name", "", key="politician_search")
        
        with col3:
            # Year filter based on election_date
            years = ["All"]
            if 'election_date' in politicians_cleaned_df.columns:
                date_years = pd.to_datetime(politicians_cleaned_df['election_date'], errors='coerce').dt.year.dropna().unique()
                years += sorted([str(int(y)) for y in date_years], reverse=True)
            selected_year = st.selectbox("Election Year", years)
        
        # Apply filters
        filtered_df = politicians_cleaned_df.copy()
        if selected_prefecture != "All":
            filtered_df = filtered_df[filtered_df['prefecture'] == selected_prefecture]
        if search:
            filtered_df = filtered_df[filtered_df['name'].str.contains(search, na=False, case=False)]
        if selected_year != "All":
            filtered_df['year'] = pd.to_datetime(filtered_df['election_date'], errors='coerce').dt.year.astype(str)
            filtered_df = filtered_df[filtered_df['year'] == selected_year]
        
        st.write(f"Showing {len(filtered_df):,} of {len(politicians_cleaned_df):,} politicians")
        
        # Display dataframe
        if not filtered_df.empty:
            display_columns = ['name', 'prefecture', 'election', 'election_date']
            display_df = filtered_df[display_columns].copy()
            st.dataframe(display_df, use_container_width=True, height=400)
            
            # Statistics for filtered data
            st.markdown("---")
            st.markdown("**Filtered Data Statistics**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Top 10 Prefectures**")
                top_prefectures = filtered_df['prefecture'].value_counts().head(10)
                for prefecture, count in top_prefectures.items():
                    st.write(f"• {prefecture}: {count}")
            
            with col2:
                st.markdown("**Top 10 Elections by Candidates**")
                top_elections = filtered_df['election'].value_counts().head(10)
                for election, count in top_elections.items():
                    # Shorten election name for display
                    election_short = election[:50] + "..." if len(election) > 50 else election
                    st.write(f"• {election_short}: {count}")
            
            # Download button
            csv = filtered_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
            st.download_button(
                label="📥 Download Filtered Data as CSV",
                data=csv,
                file_name=f"politicians_filtered_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.warning("No politicians match the selected filters.")
    else:
        st.info("No election politicians data available.")
        st.markdown("""
        **To collect this data:**
        1. Run: `python scrape_elections.py --limit-per-prefecture 20`
        2. Then: `python clean_politician_data.py`
        """)

# Tab 3: Officials
with tab3:
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

# Tab 4: Elections
with tab4:
    st.subheader("🗳️ Election Schedules")
    st.caption("Scraping 1,747 municipalities across Japan")
    
    # Load municipal URLs and scraping results
    urls_df = load_csv_data("municipal_urls.csv")
    results_df = load_csv_data("municipal_scraping_results.csv")
    
    # Statistics
    if urls_df is not None:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Municipalities", len(urls_df))
        
        with col2:
            if results_df is not None:
                scraped = len(results_df['municipality'].unique()) if 'municipality' in results_df.columns else 0
                st.metric("Scraped", scraped)
            else:
                st.metric("Scraped", 0)
        
        with col3:
            if results_df is not None and 'name' in results_df.columns:
                st.metric("Officials Found", len(results_df))
            else:
                st.metric("Officials Found", 0)
        
        with col4:
            if results_df is not None and urls_df is not None:
                scraped_count = len(results_df['municipality'].unique()) if 'municipality' in results_df.columns else 0
                progress = (scraped_count / len(urls_df) * 100) if len(urls_df) > 0 else 0
                st.metric("Progress", f"{progress:.1f}%")
            else:
                st.metric("Progress", "0%")
    
    st.markdown("---")
    
    # Tabs for URLs and Results
    subtab1, subtab2 = st.tabs(["Generated URLs", "Scraping Results"])
    
    with subtab1:
        if urls_df is not None and not urls_df.empty:
            st.write(f"**{len(urls_df)} Municipal Website URLs**")
            
            # Filters
            col1, col2 = st.columns(2)
            with col1:
                if 'prefecture' in urls_df.columns:
                    prefectures = ["All"] + sorted(urls_df['prefecture'].dropna().unique().tolist())
                    selected_pref = st.selectbox("Filter by Prefecture", prefectures, key="muni_pref")
                else:
                    selected_pref = "All"
            
            with col2:
                search_city = st.text_input("Search by city name", "", key="muni_search")
            
            # Apply filters
            filtered_urls = urls_df.copy()
            if selected_pref != "All":
                filtered_urls = filtered_urls[filtered_urls['prefecture'] == selected_pref]
            if search_city:
                filtered_urls = filtered_urls[filtered_urls['city_name'].str.contains(search_city, na=False, case=False)]
            
            st.write(f"Showing {len(filtered_urls)} municipalities")
            
            # Display table
            display_cols = ['row_number', 'prefecture', 'city_name', 'url', 'romaji', 'confidence']
            available_cols = [col for col in display_cols if col in filtered_urls.columns]
            st.dataframe(filtered_urls[available_cols], width='stretch', height=400)
            
            # Download buttons
            col1, col2 = st.columns(2)
            with col1:
                csv = filtered_urls.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button(
                    label="📥 Download Filtered URLs (CSV)",
                    data=csv,
                    file_name=f"municipal_urls_filtered_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    key="download_urls_csv"
                )
            
            with col2:
                # Excel download (if openpyxl is available)
                try:
                    import io
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        filtered_urls.to_excel(writer, index=False, sheet_name='Municipal URLs')
                    buffer.seek(0)
                    
                    st.download_button(
                        label="📥 Download Filtered URLs (Excel)",
                        data=buffer,
                        file_name=f"municipal_urls_filtered_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="download_urls_excel"
                    )
                except ImportError:
                    st.caption("Install openpyxl for Excel export")
        else:
            st.info("No URL data available. Generate URLs first using: `python main.py generate-urls`")
    
    with subtab2:
        if results_df is not None and not results_df.empty:
            st.write(f"**{len(results_df)} Officials from Municipal Scraping**")
            
            # Filters
            col1, col2, col3 = st.columns(3)
            with col1:
                if 'municipality' in results_df.columns:
                    municipalities = ["All"] + sorted(results_df['municipality'].dropna().unique().tolist())
                    selected_muni = st.selectbox("Municipality", municipalities, key="result_muni")
                else:
                    selected_muni = "All"
            
            with col2:
                if 'prefecture' in results_df.columns:
                    prefs = ["All"] + sorted(results_df['prefecture'].dropna().unique().tolist())
                    selected_pref_result = st.selectbox("Prefecture", prefs, key="result_pref")
                else:
                    selected_pref_result = "All"
            
            with col3:
                search_official = st.text_input("Search official name", "", key="official_search")
            
            # Apply filters
            filtered_results = results_df.copy()
            if selected_muni != "All":
                filtered_results = filtered_results[filtered_results['municipality'] == selected_muni]
            if selected_pref_result != "All":
                filtered_results = filtered_results[filtered_results['prefecture'] == selected_pref_result]
            if search_official:
                filtered_results = filtered_results[filtered_results['name'].str.contains(search_official, na=False, case=False)]
            
            st.write(f"Showing {len(filtered_results)} officials")
            st.dataframe(filtered_results, width='stretch', height=400)
            
            # Download buttons
            col1, col2 = st.columns(2)
            with col1:
                csv = filtered_results.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button(
                    label="📥 Download Results (CSV)",
                    data=csv,
                    file_name=f"municipal_officials_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    key="download_results_csv"
                )
            
            with col2:
                try:
                    import io
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        filtered_results.to_excel(writer, index=False, sheet_name='Officials')
                    buffer.seek(0)
                    
                    st.download_button(
                        label="📥 Download Results (Excel)",
                        data=buffer,
                        file_name=f"municipal_officials_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="download_results_excel"
                    )
                except ImportError:
                    st.caption("Install openpyxl for Excel export")
        else:
            st.info("No scraping results yet. Run bulk scraping using: `python main.py scrape-bulk`")

# Tab 5: Municipal Scraping
with tab5:
    st.subheader("�️ Municipal Scraping Results")
    
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

# Tab 6: Funding
with tab6:
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

# Tab 7: Files
with tab7:
    st.subheader("📁 Output Files")
    
    output_dir = get_output_path()
    
    files = [
        ("politicians_cleaned.csv", "🏛️ Election Politicians (Cleaned - 7,336)"),
        ("politicians_from_elections.csv", "🏛️ Election Politicians (Raw - 7,693)"),
        ("officials.csv", "👥 Public Officials"),
        ("officials_social.csv", "📱 SNS Profiles"),
        ("municipal_urls.csv", "🗺️ Municipal URLs (1,747 cities)"),
        ("municipal_scraping_results.csv", "🗺️ Municipal Officials"),
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
