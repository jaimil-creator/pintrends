import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
from scraper.trends import fetch_trend_prediction
import json

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
                         # Fetch suggestion objects
                         suggestions_objs = db.query(Suggestion).filter(Suggestion.parent_keyword_id == kw_obj.id).all()
                         
                         if suggestions_objs:
                             st.markdown(f"**Autocomplete Suggestions ({len(suggestions_objs)}):**")
                             # Limit display to top 10 to save space
                             sugg_list = [f"- {s.suggestion}" for s in suggestions_objs[:10]]
                             if len(suggestions_objs) > 10:
                                 sugg_list.append(f"...and {len(suggestions_objs)-10} more")
                             st.markdown("\n".join(sugg_list))
                         else:
                             st.info("No suggestions found yet.")
                             if st.button("🚀 Scrape Suggestions Now"):
                                 try:
                                     with st.spinner("Scraping Pinterest Autocomplete..."):
                                         rh = requests.post(f"{API_URL}/scrape-suggestions", json={"keyword": selected_keyword})
                                         if rh.status_code == 200:
                                             res = rh.json()
                                             if res['count'] > 0:
                                                 st.success(f"Found {res['count']} suggestions!")
                                                 time.sleep(1)
                                                 st.rerun()
                                             else:
                                                 st.warning("No suggestions were passed back.")
                                         else:
                                             st.error(f"API Error: {rh.text}")
                                 except Exception as e:
                                     st.error(f"Connection Failed: {e}")
                     
                     with col_act:
                         st.write("Ready to analyze metrics?")
                         if st.button(f"Analyze '{selected_keyword}'", key="analyze_trend"):
                             st.session_state['current_keyword'] = selected_keyword
                             st.session_state['force_refresh'] = False
                             st.session_state['navigation'] = "Dashboard"
                             st.rerun()

                     # --- Prediction Graph ---
                     # Find data record in current list
                     selected_trend_record = next((t for t in trends if t.keyword == selected_keyword), None)
                     
                     if selected_trend_record:
                         st.divider()
                         st.subheader("📈 Prediction & History")
                         
                         if not selected_trend_record.prediction_data:
                             # Auto-fetch immediately without button
                             with st.spinner(f"Auto-fetching prediction data for '{selected_keyword}'..."):
                                 try:
                                     # Default to US if country not set
                                     country_code = selected_trend_record.country or "US"
                                     p_data_list = fetch_trend_prediction(selected_trend_record.keyword, country_code)
                                     
                                     if p_data_list:
                                         selected_trend_record.prediction_data = json.dumps(p_data_list)
                                         db.commit()
                                         st.success("Data fetched!")
                                         time.sleep(0.5)
                                         st.rerun()
                                     else:
                                         st.error("No prediction data received from Pinterest API.")
                                 except Exception as e:
                                     st.error(f"Error fetching data: {e}")
                         
                         # Graph Logic
                         try:
                             # Parse string
                             p_data = selected_trend_record.prediction_data
                             if p_data:
                                 if isinstance(p_data, str):
                                     pred_list = json.loads(p_data)
                                 else:
                                     pred_list = p_data 
                                 
                                 if pred_list:
                                     # Handle Dict vs List format
                                     if isinstance(pred_list, dict):
                                          pred_list = [{"date": k, "count": v} for k, v in pred_list.items()]
                                     
                                     df_pred = pd.DataFrame(pred_list)
                                     
                                     if not df_pred.empty:
                                         # Normalize Date
                                         if 'date' in df_pred.columns:
                                             try:
                                                 df_pred['date'] = pd.to_datetime(df_pred['date'], errors='coerce')
                                                 df_pred = df_pred.dropna(subset=['date'])
                                                 
                                                 fig = go.Figure()
                                                 
                                                 # Identify Y column and Bounds
                                                 y_col = 'count'
                                                 if 'normalizedCount' in df_pred.columns:
                                                     y_col = 'normalizedCount'
                                                 elif 'value' in df_pred.columns:
                                                     y_col = 'value'
                                                 
                                                 if y_col in df_pred.columns:
                                                     # Split into History vs Prediction
                                                     # Logic: Prediction data usually has the 'predictedUpperBound' field populated
                                                     is_pred_mask = pd.Series([False] * len(df_pred), index=df_pred.index)
                                                     
                                                     if 'predictedUpperBoundNormalizedCount' in df_pred.columns:
                                                         is_pred_mask = df_pred['predictedUpperBoundNormalizedCount'].notnull()
                                                     
                                                     df_hist = df_pred[~is_pred_mask]
                                                     df_forecast = df_pred[is_pred_mask]
                                                     
                                                     # 1. Historical Line (Solid)
                                                     fig.add_trace(go.Scatter(
                                                         x=df_hist['date'], 
                                                         y=df_hist[y_col],
                                                         mode='lines',
                                                         name='History',
                                                         line=dict(color='#E60023', width=3),
                                                         hovertemplate='<b>Date:</b> %{x|%b %d, %Y}<br><b>Value:</b> %{y}<extra></extra>'
                                                     ))
                                                     
                                                     # 2. Prediction Line (Dashed)
                                                     if not df_forecast.empty:
                                                         # Connect lines: Add last history point to ensure continuity
                                                         if not df_hist.empty:
                                                             last_hist = df_hist.iloc[[-1]]
                                                             df_forecast_plot = pd.concat([last_hist, df_forecast])
                                                         else:
                                                             df_forecast_plot = df_forecast

                                                         fig.add_trace(go.Scatter(
                                                             x=df_forecast_plot['date'], 
                                                             y=df_forecast_plot[y_col],
                                                             mode='lines',
                                                             name='Prediction',
                                                             line=dict(color='#E60023', width=3, dash='dash'),
                                                             hovertemplate='<b>Week ending:</b> %{x|%b %d, %Y}<br><b>Prediction:</b> %{y}<extra></extra>'
                                                         ))
                                                         
                                                         # Vertical Line at transition
                                                         if not df_hist.empty:
                                                              transition_date = df_hist['date'].max()
                                                              fig.add_vline(x=transition_date, line_width=1, line_dash="solid", line_color="white")

                                                     # 3. Confidence Intervals
                                                     ub_col = 'predictedUpperBoundNormalizedCount'
                                                     if ub_col in df_pred.columns:
                                                         df_forecast_band = df_pred.dropna(subset=[ub_col])
                                                         if not df_forecast_band.empty:
                                                             # Upper Bound (transparent line)
                                                             fig.add_trace(go.Scatter(
                                                                 x=df_forecast_band['date'],
                                                                 y=df_forecast_band[ub_col],
                                                                 mode='lines',
                                                                 line=dict(width=0),
                                                                 showlegend=False,
                                                                 hoverinfo='skip'
                                                             ))
                                                             
                                                             # Lower Bound (Fill to Upper)
                                                             lb_col = 'predictedLowerBoundNormalizedCount'
                                                             y_lower = df_forecast_band[lb_col] if lb_col in df_forecast_band.columns else df_forecast_band[y_col]
                                                             
                                                             fig.add_trace(go.Scatter(
                                                                 x=df_forecast_band['date'],
                                                                 y=y_lower,
                                                                 mode='lines',
                                                                 name='Confidence Interval',
                                                                 line=dict(width=0),
                                                                 fill='tonexty',
                                                                 fillcolor='rgba(230, 0, 35, 0.2)',
                                                                 hoverinfo='skip'
                                                             ))

                                                     fig.update_layout(
                                                         title="Interest over time",
                                                         template="plotly_dark",
                                                         height=400,
                                                         hovermode="x unified",
                                                         legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                                                     )
                                                     
                                                     st.plotly_chart(fig, use_container_width=True)
                                                 else:
                                                     st.warning(f"Could not determine value column. Keys: {df_pred.columns.tolist()}")
                                             except Exception as e:
                                                  st.warning(f"Graph Error details: {e}")
                                         else:
                                             st.warning("Date column missing in prediction data.")
                         except Exception as e:
                             st.warning(f"Could not render prediction graph: {e}")

                     # --- SEO & Content Generator (NEW) ---
                     st.divider()
                     st.subheader("✍️ Content Studio")
                     
                     from scraper.content_generator import ContentGenerator
                     
                     # Initialize Logic
                     if 'seo_keywords' not in st.session_state:
                         st.session_state['seo_keywords'] = []
                     
                     c_gen1, c_gen2 = st.columns([1, 1.5])
                     
                     with c_gen1:
                         st.markdown("###### 1. Keyword Strategy")
                         if suggestions_objs:
                             if st.button("Generate SEO Combos", help="Mix Trend + Suggestions"):
                                 try:
                                     sugg_texts = [s.suggestion for s in suggestions_objs]
                                     gen = ContentGenerator()
                                     raw_seo = gen.generate_seo_keywords(selected_keyword, sugg_texts)
                                     
                                     if raw_seo:
                                         st.session_state['seo_keywords'] = raw_seo
                                         st.success(f"Generated {len(raw_seo)} keywords!")
                                     else:
                                          st.warning("Not enough suggestions to combine.")
                                 except Exception as e:
                                     st.error(f"Error: {e}")
                         else:
                             st.info("💡 Scrape suggestions above to enable keyword combos.")

                     with c_gen2:
                         if st.session_state['seo_keywords']:
                             st.markdown("###### 2. Create Content")
                             target_kw = st.selectbox("Select Target SEO Keyword", st.session_state['seo_keywords'])
                             
                             if st.button(f"✨ Generate Content for '{target_kw}'", type="primary"):
                                 with st.status("AI is writing...", expanded=True):
                                     try:
                                         gen = ContentGenerator()
                                         
                                         st.write("Generating Titles...")
                                         titles = gen.generate_titles(target_kw, count=3)
                                         
                                         results = []
                                         st.write("Generating Descriptions...")
                                         for t in titles:
                                              desc = gen.generate_descriptions(target_kw, t)
                                              results.append({"title": t, "desc": desc})
                                         
                                         st.session_state['gen_results'] = results
                                         st.write("Done!")
                                     except Exception as e:
                                         st.error(f"AI Error: {e}")
                             
                             # Display Results
                             if 'gen_results' in st.session_state:
                                  st.markdown("### 🎨 Generated Pins")
                                  for idx, item in enumerate(st.session_state['gen_results']):
                                      with st.expander(f"📌 Option {idx+1}: {item['title']}", expanded=True):
                                          st.markdown(f"**Title:** {item['title']}")
                                          st.markdown(f"**Description:**\n{item['desc']}")
                                          st.code(f"{item['title']}\n\n{item['desc']}")
                         else:
                             if suggestions_objs:
                                  st.info("👈 Generate keywords to start creating content.")
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

def show_keyword_generator():
    st.markdown("## 🧠 AI Keyword Generator")
    st.markdown("*Generate SEO-optimized long-tail keywords using basic keywords + suggestions.*")
    
    # Session State for Generator
    if "gen_suggestions" not in st.session_state:
        st.session_state.gen_suggestions = ""
    if "gen_results" not in st.session_state:
        st.session_state.gen_results = []
        
    c1, c2 = st.columns([1, 1])
    
    with c1:
        st.subheader("1. Configuration")
        base_keyword = st.text_input("Base Keyword", placeholder="e.g. valentines nails")
        api_key = st.text_input("OpenRouter API Key", type="password", help="Required for AI generation")
        
        st.markdown("### Suggestions")
        st.caption("Enter suggestion words (comma separated) or fetch from DB.")
        
        # Fetch from DB button
        if st.button("Fetch Suggestions from DB"):
            if not base_keyword:
                st.warning("Please enter a base keyword first.")
            else:
                db = SessionLocal()
                try:
                    kw_obj = db.query(KeywordModel).filter(KeywordModel.keyword == base_keyword).first()
                    if kw_obj and kw_obj.suggestions:
                        sugg_list = [s.suggestion for s in kw_obj.suggestions]
                        st.session_state.gen_suggestions = ", ".join(sugg_list)
                        st.success(f"Loaded {len(sugg_list)} suggestions!")
                    else:
                        st.info("No suggestions found in DB for this keyword. Try analyzing it first in Dashboard.")
                except Exception as e:
                    st.error(f"DB Error: {e}")
                finally:
                    db.close()
        
        # Text Area for suggestions
        suggestions_input = st.text_area(
            "Suggestion Words", 
            value=st.session_state.gen_suggestions,
            height=150,
            placeholder="Designs, Art, Simple, Ideas..."
        )
        
        # Update state on manual edit
        if suggestions_input != st.session_state.gen_suggestions:
            st.session_state.gen_suggestions = suggestions_input
            
        st.write("")
        if st.button("✨ Generate Combinations", type="primary"):
            if not api_key:
                st.error("Please provide an OpenRouter API Key.")
            elif not base_keyword:
                st.error("Please provide a base keyword.")
            elif not suggestions_input:
                st.error("Please provide some suggestion words.")
            else:
                # Call API
                with st.spinner("Generating creative combinations..."):
                    try:
                        sugg_list = [s.strip() for s in suggestions_input.split(",") if s.strip()]
                        payload = {
                            "keyword": base_keyword,
                            "suggestions": sugg_list,
                            "api_key": api_key
                        }
                        r = requests.post(f"{API_URL}/generate-combinations", json=payload)
                        if r.status_code == 200:
                            st.session_state.gen_results = r.json()
                            st.success(f"Generated {len(st.session_state.gen_results)} keywords!")
                        else:
                            st.error(f"Error: {r.text}")
                    except Exception as e:
                        st.error(f"Connection Error: {e}")

    with c2:
        st.subheader("2. Results")
        if st.session_state.gen_results:
            df = pd.DataFrame(st.session_state.gen_results, columns=["Generated Keywords"])
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Download
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"gen_keywords_{base_keyword.replace(' ', '_')}.csv",
                mime="text/csv",
                type="primary"
            )
        else:
            st.info("Generated keywords will appear here.")
            st.markdown("""
            **How it works:**
            1. Enter a **Base Keyword** (e.g. 'summer outfit').
            2. Add **Suggestion Words** (e.g. 'casual, beach, 2024').
            3. The AI will mix them to create natural search content like:
               - 'casual summer outfit beach'
               - 'summer outfit ideas 2024'
            """)

# --- Sidemenu ---
st.sidebar.markdown("# 📌 PinTrends")
st.sidebar.markdown("---")

# Use session state to control navigation
if 'navigation' not in st.session_state:
    st.session_state['navigation'] = "Trends Explorer"

# Styled Radio Button
selected_page = st.sidebar.radio(
    "Navigation", 
    ["Dashboard", "Trends Explorer", "Outputs", "Keyword Generator"],
    index=0 if st.session_state['navigation'] == "Dashboard" else (1 if st.session_state['navigation'] == "Trends Explorer" else (2 if st.session_state['navigation'] == "Outputs" else 3)),
    format_func=lambda x: f"📊 {x}" if x == "Dashboard" else (f"🌍 {x}" if x == "Trends Explorer" else (f"📤 {x}" if x == "Outputs" else f"🧠 {x}"))
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
elif st.session_state['navigation'] == "Keyword Generator":
    show_keyword_generator()
