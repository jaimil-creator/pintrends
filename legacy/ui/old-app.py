import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time

# --- Configuration ---
API_URL = "http://localhost:8000"
st.set_page_config(page_title="PinTrends Private", page_icon="📌", layout="wide")

# --- Custom CSS for Premium Feel ---
st.markdown("""
<style>
    /* Dark Theme enhancement */
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    
    /* Custom Input fields */
    div[data-baseweb="input"] > div {
        background-color: #262730;
        border-radius: 8px;
        color: white;
    }

    /* Buttons */
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        font-weight: 600;
        background-color: #E60023; /* Pinterest Red */
        color: white;
        border: none;
        padding: 0.6rem 1rem;
    }
    .stButton > button:hover {
        background-color: #ad081b;
        color: white;
    }
    
    /* Metric Cards */
    div[data-testid="stMetricValue"] {
        font-size: 2rem;
        color: #E60023;
    }
    
    /* Table Styling */
    div[data-testid="stDataFrame"] {
        background-color: #262730;
        border-radius: 8px;
        padding: 10px;
    }
    
    h1, h2, h3 {
        font-family: 'Inter', sans-serif;
    }
</style>
""", unsafe_allow_html=True)

# --- Components ---

def get_data(keyword, force=False):
    """Call API to Analyze/Get data"""
    # Trigger Analysis
    try:
        if force:
            requests.post(f"{API_URL}/analyze-keyword", json={"keyword": keyword, "force_rescrape": True})
        else:
            # Check if exists first to avoid re-triggering if not needed? 
            # Actually POST returns cached=True if it exists.
            resp = requests.post(f"{API_URL}/analyze-keyword", json={"keyword": keyword, "force_rescrape": False})
            if resp.status_code != 200:
                st.error(f"Error starting analysis: {resp.text}")
                return None
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return None

    # Poll for result
    with st.spinner(f"Analyzing '{keyword}'... (This takes 10-20s)"):
        for _ in range(20): # Retry 20 times (approx 40-60s)
            try:
                r = requests.get(f"{API_URL}/keyword/{keyword}")
                if r.status_code == 200:
                    return r.json()
            except:
                pass
            time.sleep(2)
        st.error("Timeout waiting for results. Check backend logs.")
        return None

def show_dashboard():
    st.title("📌 PinTrends Private")
    st.caption("Personal Pinterest Research Tool")

    col1, col2 = st.columns([3, 1])
    with col1:
        keyword = st.text_input("Enter Keyword", placeholder="e.g. 'home office decor'")
    with col2:
        st.write("") # Spacer
        st.write("") 
        if st.button("Analyze"):
            if keyword:
                st.session_state['current_keyword'] = keyword
                st.session_state['force_refresh'] = False
                st.rerun()

    # Handle Analysis
    if 'current_keyword' in st.session_state:
        keyword_to_load = st.session_state['current_keyword']
        force = st.session_state.get('force_refresh', False)
        
        data = get_data(keyword_to_load, force=force)
        
        if data:
            # Layout
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Popularity Score", f"{data['current_score']}", delta=data['bucket'])
            
            pins = data['pins']
            m2.metric("Pins Found", len(pins))
            
            # Helper for metrics
            saves_list = [p['saves'] for p in pins]
            avg_saves = sum(saves_list) / len(saves_list) if saves_list else 0
            m3.metric("Avg Saves / Pin", f"{avg_saves:.1f}")
            
            # Display Last Scraped
            last = data['last_scraped']
            if last:
                try:
                    # Clean date string if needed, or display as is
                    last_str = last.split("T")[0]
                except:
                    last_str = last
            else:
                last_str = "Just now"
            m4.metric("Last Updated", last_str)

            # Charts
            st.divider()
            c1, c2 = st.columns([2, 1])
            
            with c1:
                st.subheader("Trend History")
                history = data['history']
                if history:
                    df_hist = pd.DataFrame(history)
                    fig = px.line(df_hist, x='date', y='score', markers=True, 
                                  title=f"Trend: {data['keyword']}",
                                  template="plotly_dark")
                    fig.update_traces(line_color='#E60023')
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No history yet.")

            with c2:
                st.subheader("Actions")
                if st.button("Resource (Force Update)"):
                    st.session_state['force_refresh'] = True
                    st.rerun()
                
                st.write("")
                if st.button("Clear Results"):
                    if 'current_keyword' in st.session_state:
                        del st.session_state['current_keyword']
                    st.rerun()

            # Top Pins Table
            st.subheader("Top Pins")
            if pins:
                df_pins = pd.DataFrame(pins)
                # Make clickable link
                df_pins['Link'] = df_pins['url'].apply(lambda x: f'<a href="{x}" target="_blank">View Pin</a>')
                # Reorder
                df_pins = df_pins[['title', 'saves', 'Link']]
                st.write(df_pins.to_html(escape=False, index=False), unsafe_allow_html=True)
            else:
                st.warning("No pins found.")

import sys
import os
# Ensure root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import SessionLocal
from database.models import TrendKeyword, Suggestion, Keyword as KeywordModel


def show_trends():
    st.markdown("## 🌍 Trends Explorer")
    st.markdown("*Discover what's trending across regions and demographics.*")
    
    db = SessionLocal()
    try:
         # Metric Overview
         total_trends = db.query(TrendKeyword).count()
         last_scrape = db.query(TrendKeyword).order_by(TrendKeyword.detected_at.desc()).first()
         last_scrape_time = last_scrape.detected_at.strftime("%H:%M") if last_scrape else "N/A"
         
         m1, m2, m3 = st.columns(3)
         m1.metric("Total Trends Database", total_trends)
         m2.metric("Last Scrape Time", last_scrape_time)
         m3.metric("Supported Regions", 26)
         
         st.divider()
         
         # --- Filter Controls ---
         with st.container():
             st.markdown("### ⚙️ Configuration")
             c1, c2, c3 = st.columns([1, 1, 1])
             with c1:
                 # Standardized Region Mapping
                 REGION_MAP = {
                     "United States": "US",
                     "Great Britain and Ireland": "GB+IE",
                     "Canada": "CA",
                     "Southern Europe (GR, IT, MT, PT, ES)": "IT+ES+PT+GR+MT",
                     "Italy": "IT",
                     "Spain": "ES",
                     "Germanic countries (DE, AT, CH)": "DE+AT+CH",
                     "Germany": "DE",
                     "France": "FR",
                     "Nordic countries (NO, FI, DK, SE)": "SE+DK+FI+NO",
                     "Benelux (NL, BE, LU)": "NL+BE+LU",
                     "Eastern Europe (HU, PL, RO, SK, CZ)": "PL+RO+HU+SK+CZ",
                     "Hispanic LatAm (CL, CO, AR, MX)": "MX+AR+CO+CL",
                     "Colombia": "CO",
                     "Argentina": "AR",
                     "Mexico": "MX",
                     "Brazil": "BR",
                     "Australasia (AU, NZ)": "AU+NZ",
                     # New User Regions
                     "Malaysia": "MY",
                     "Philippines": "PH",
                     "Thailand": "TH",
                     "Egypt": "EG",
                     "Turkey": "TR",
                     "Korea": "KR",
                     "Latin America & Caribbean (CR, DO, EC, GT, PE)": "CR+DO+EC+GT+PE",
                     "Eastern Europe & Mediterranean (CY, CZ, GR, HU, MT, PL, RO, SK)": "CY+CZ+GR+HU+MT+PL+RO+SK"
                 }
                 
                 selected_region_name = st.selectbox("Region", options=list(REGION_MAP.keys()), index=0)
                 selected_country = REGION_MAP[selected_region_name] # internal code
             
             with c2:
                 type_options = ["growing", "seasonal", "monthly", "yearly"]
                 selected_type = st.selectbox("Trend Type", type_options, index=0)
                 
             with c3:
                 st.write("") # Spacer
                 st.write("")
                 scrape_btn = st.button("🚀 Scrape New Trends", type="primary")

             # Advanced Demographic Filters
             st.markdown("#### 🎯 Demographic Filters")
             with st.expander("Expand to filter by Interest, Age, or Gender", expanded=False):
                 f1, f2, f3 = st.columns(3)
                 with f1:
                     interest_opts = ["Animals", "Architecture", "Art", "Beauty", "Children's Fashion", "Design", "DIY and Crafts", "Education", "Electronics", "Entertainment", "Event Planning", "Finance", "Food and Drinks", "Gardening", "Health", "Home Decor", "Men's Fashion", "Parenting", "Quotes", "Sport", "Travel", "Vehicles", "Wedding", "Women's Fashion"]
                     sel_interests = st.multiselect("Interests", interest_opts)
                 with f2:
                     age_opts = ["18-24", "25-34", "35-44", "45-49", "50-54", "55-64", "65+"]
                     sel_ages = st.multiselect("Ages", age_opts)
                 with f3:
                     gender_opts = ["female", "male", "unspecified"]
                     sel_genders = st.multiselect("Genders", gender_opts)

         if scrape_btn:
             try:
                 with st.status("Scraping in progress...", expanded=True) as status:
                     st.write("Initializing request...")
                     payload = {
                         "country": selected_country, 
                         "trend_type": selected_type,
                         "interests": sel_interests,
                         "ages": sel_ages,
                         "genders": sel_genders
                     }
                     r = requests.post(f"{API_URL}/scrape-trends", json=payload)
                     if r.status_code == 200:
                         st.write("Rocketing scraper launched! 🚀")
                         time.sleep(1)
                         status.update(label="Scraping started! Check back in a minute.", state="complete", expanded=False)
                         st.balloons()
                     else:
                         status.update(label="Error launching scraper.", state="error")
                         st.error(f"Error: {r.text}")
             except Exception as e:
                 st.error(f"Connect Error: {e}")

         st.divider()

         # Fetch Top Trends
         try:
             # Logic: Get the latest 'seen' date for this filter context
             from sqlalchemy import func
             
             query = db.query(TrendKeyword).filter(
                 TrendKeyword.country == selected_country,
                 TrendKeyword.trend_type == selected_type
             )
             
             max_date = query.with_entities(func.max(TrendKeyword.detected_at)).scalar()
             
             if max_date:
                 from datetime import timedelta
                 start_window = max_date - timedelta(hours=1)
                 
                 query = db.query(TrendKeyword).filter(
                     TrendKeyword.country == selected_country,
                     TrendKeyword.trend_type == selected_type,
                     TrendKeyword.detected_at >= start_window
                 )
                 
                 trends = query.order_by(TrendKeyword.detected_at.desc()).all()
             else:
                 trends = []
         except Exception as e:
             st.error(f"Database Error: {e}")
             return

         if trends:
             # Convert to DataFrame
             data = []
             for t in trends:
                 # Show non-empty filters
                 filters = []
                 if t.filter_interests: filters.append(f"🏷️ {t.filter_interests}")
                 if t.filter_ages: filters.append(f"👶 {t.filter_ages}")
                 if t.filter_genders: filters.append(f"⚧ {t.filter_genders}")
                 filter_str = "  ".join(filters) if filters else "All"
                 
                 data.append({
                     "Keyword": t.keyword, 
                     "Country": t.country, 
                     "Type": t.trend_type,
                     "Demographics": filter_str
                 })
             
             df = pd.DataFrame(data)
             
             st.subheader(f"🔥 Latest {selected_type.title()} Trends ({selected_country})")
             st.markdown(f"Found **{len(df)}** trends from the last scrape.")
             st.dataframe(df, use_container_width=True, hide_index=True)
             
             # Drill down
             st.divider()
             st.subheader("🔍 Deep Dive & Suggestions")
             
             c_sel, c_act = st.columns([3, 1])
             with c_sel:
                 selected_keyword = st.selectbox("Select a Trend to Analyze", df['Keyword'].unique())
             
             if selected_keyword:
                 kw_obj = db.query(KeywordModel).filter(KeywordModel.keyword == selected_keyword).first()
                 
                 if kw_obj:
                     col_sugg, col_act = st.columns([2, 1])
                     
                     with col_sugg:
                         suggestions = db.query(Suggestion).filter(Suggestion.parent_keyword_id == kw_obj.id).all()
                         if suggestions:
                             st.markdown("**Autocomplete Suggestions:**")
                             sugg_list = [f"- {s.suggestion}" for s in suggestions]
                             st.markdown("\n".join(sugg_list))
                         else:
                             st.info("No suggestions available.")
                     
                     with col_act:
                         st.write("Ready to analyze metrics?")
                         if st.button(f"Analyze '{selected_keyword}'", key="analyze_trend"):
                             st.session_state['current_keyword'] = selected_keyword
                             st.session_state['force_refresh'] = False
                             st.session_state['navigation'] = "Dashboard"
                             st.rerun()
                 else:
                     st.warning("Trend details missing.")
         else:
             st.info("No trends found matching this criteria. Launch a scrape above!")
             
    except Exception as e:
        st.error(f"Database Error: {e}")
            
    finally:
        db.close()

def show_outputs():
    st.markdown("## 📤 Output Center")
    st.markdown("*Review, filter, and export your trend data.*")

    tab1, tab2 = st.tabs(["🔍 Unified Filter View", "📚 Scrape Batches"])
    
    db = SessionLocal()
    try:
        # Pre-fetch basic info for filters
        distinct_countries = [r[0] for r in db.query(TrendKeyword.country).distinct().all()]
        distinct_types = [r[0] for r in db.query(TrendKeyword.trend_type).distinct().all()]
        
        # --- TAB 1: Unified Filter View ---
        with tab1:
            st.markdown("### Custom Filters")
            
            c1, c2, c3 = st.columns(3)
            with c1:
                sel_countries = st.multiselect("Filter by Country", distinct_countries, default=[])
            with c2:
                sel_types = st.multiselect("Filter by Trend Type", distinct_types, default=[])
            with c3:
                # Date filter? For now, maybe simple row limit or keyword search
                search_term = st.text_input("Search Keyword", "")

            # Build Query
            query = db.query(TrendKeyword).order_by(TrendKeyword.detected_at.desc())
            
            if sel_countries:
                query = query.filter(TrendKeyword.country.in_(sel_countries))
            if sel_types:
                query = query.filter(TrendKeyword.trend_type.in_(sel_types))
            if search_term:
                query = query.filter(TrendKeyword.keyword.contains(search_term))
                
            trends = query.limit(2000).all() # Safety limit
            
            if trends:
                # Helper for Data Prep
                def prep_dataframe(trend_list):
                    # Fetch suggestions
                    unique_kws = list(set([t.keyword for t in trend_list]))
                    kw_records = db.query(KeywordModel).filter(KeywordModel.keyword.in_(unique_kws)).all()
                    sugg_map = {}
                    for k in kw_records:
                        sugg_list = [s.suggestion for s in k.suggestions]
                        sugg_map[k.keyword] = ", ".join(sugg_list)

                    data = []
                    for t in trend_list:
                         dems = []
                         if t.filter_interests: dems.append(f"Interest: {t.filter_interests}")
                         if t.filter_ages: dems.append(f"Age: {t.filter_ages}")
                         if t.filter_genders: dems.append(f"Gender: {t.filter_genders}")
                         demographics_str = " | ".join(dems) if dems else "General"
                         
                         data.append({
                             "Detected": t.detected_at,
                             "Keywords": t.keyword,
                             "Country": t.country,
                             "Type": t.trend_type,
                             "Demographics": demographics_str,
                             "Suggestions": sugg_map.get(t.keyword, "")
                         })
                    return pd.DataFrame(data)

                df = prep_dataframe(trends)
                
                st.write(f"Showing **{len(df)}** results.")
                st.dataframe(df, use_container_width=True)
                
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download Filtered CSV",
                    data=csv,
                    file_name="pintrends_filtered.csv",
                    mime="text/csv",
                    type="primary"
                )
            else:
                st.info("No trends match your filters.")

        # --- TAB 2: Batch History ---
        with tab2:
            st.markdown("### 📂 Scrape History (Batches)")
            st.markdown("Select a past scrape session to download separate CSVs.")
            
            # Logic to group sessions.
            # We group by Country + Type + Time Window (e.g. same hour or 5 mins)
            # Since SQL group_by on time window is dialect specific, let's do python processing for simplicity 
            # or fetching distinct dates.
            # Efficient approach: Fetch distinct (country, trend_type, date_trunc('minute', detected_at))
            # SQLite doesn't have date_trunc easily.
            
            # Let's just fetch all dates/metadata and group in Python. 
            # Ensure we only fetch metadata columns, not full text.
            metas = db.query(TrendKeyword.country, TrendKeyword.trend_type, TrendKeyword.detected_at).all()
            
            from collections import defaultdict
            batches = defaultdict(int)
            
            # Group keys: (Country, Type, TimeString)
            for m in metas:
                # Round to minute
                ts_str = m.detected_at.strftime("%Y-%m-%d %H:%M")
                key = (m.country, m.trend_type, ts_str)
                batches[key] += 1
            
            # Create list of batches
            batch_list = []
            for (c, t, ts), count in batches.items():
                batch_list.append({
                    "Date": ts,
                    "Country": c,
                    "Type": t,
                    "Count": count,
                    "Label": f"[{ts}] {c} - {t} ({count} items)"
                })
            
            # Sort desc
            batch_list.sort(key=lambda x: x['Date'], reverse=True)
            
            if batch_list:
                sel_batch_label = st.selectbox("Select Batch", [b['Label'] for b in batch_list])
                
                # Find selected batch object
                sel_batch = next(b for b in batch_list if b['Label'] == sel_batch_label)
                
                st.write(f"Creating CSV for **{sel_batch_label}**...")
                
                # Re-query precisely
                # Note: This checks string match on minute, so we filter by range
                from datetime import datetime, timedelta
                
                # Parse ts
                base_time = datetime.strptime(sel_batch['Date'], "%Y-%m-%d %H:%M")
                end_time = base_time + timedelta(minutes=1)
                
                batch_trends = db.query(TrendKeyword).filter(
                    TrendKeyword.country == sel_batch['Country'],
                    TrendKeyword.trend_type == sel_batch['Type'],
                    TrendKeyword.detected_at >= base_time,
                    TrendKeyword.detected_at < end_time
                ).all()
                
                if batch_trends:
                     df_batch = prep_dataframe(batch_trends)
                     st.dataframe(df_batch, hide_index=True)
                     
                     csv_b = df_batch.to_csv(index=False).encode('utf-8')
                     fname = f"pintrends_{sel_batch['Country']}_{sel_batch['Type']}_{sel_batch['Date'].replace(':','-').replace(' ','_')}.csv"
                     
                     st.download_button(
                        label=f"Download Selection",
                        data=csv_b,
                        file_name=fname,
                        mime="text/csv",
                        type="primary"
                    )
                else:
                    st.error("Error retrieving batch data.")
            else:
                st.info("No scrape history found.")

    except Exception as e:
        st.error(f"Error loading data: {e}")
    finally:
        db.close()

# --- Sidemenu ---
st.sidebar.markdown("# 📌 PinTrends")
st.sidebar.markdown("---")

# Use session state to control navigation
if 'navigation' not in st.session_state:
    st.session_state['navigation'] = "Trends Explorer"

# Styled Radio Button
selected_page = st.sidebar.radio(
    "Navigation", 
    ["Dashboard", "Trends Explorer", "Outputs"],
    index=0 if st.session_state['navigation'] == "Dashboard" else (1 if st.session_state['navigation'] == "Trends Explorer" else 2),
    format_func=lambda x: f"📊 {x}" if x == "Dashboard" else (f"🌍 {x}" if x == "Trends Explorer" else f"📤 {x}")
)

# Sync with session state
if selected_page != st.session_state['navigation']:
    st.session_state['navigation'] = selected_page
    st.rerun()

if st.session_state['navigation'] == "Dashboard":
    show_dashboard()
elif st.session_state['navigation'] == "Trends Explorer":
    show_trends()
elif st.session_state['navigation'] == "Outputs":
    show_outputs()
