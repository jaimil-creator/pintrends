
import os

target_file = r"c:\Users\My-PC\Desktop\pintrends\ui\app.py"

new_logic = """
                                         if y_col in df_pred.columns:
                                             # Split into History vs Prediction (User Request)
                                             # Solid line for History, Dashed for Prediction
                                             
                                             is_pred_mask = pd.Series([False] * len(df_pred), index=df_pred.index)
                                             
                                             if 'isPrediction' in df_pred.columns:
                                                 is_pred_mask = df_pred['isPrediction'].fillna(False).astype(bool)
                                             elif 'predictedUpperBoundNormalizedCount' in df_pred.columns:
                                                 is_pred_mask = df_pred['predictedUpperBoundNormalizedCount'].notnull()
                                             
                                             df_hist = df_pred[~is_pred_mask]
                                             df_forecast = df_pred[is_pred_mask]
                                             
                                             # 1. Historical Line (Solid)
                                             fig.add_trace(go.Scatter(
                                                 x=df_hist['date'], 
                                                 y=df_hist[y_col],
                                                 mode='lines',
                                                 name='History',
                                                 line=dict(color='#E60023', width=3)
                                             ))
                                             
                                             # 2. Prediction Line (Dashed)
                                             if not df_forecast.empty:
                                                 # Connect lines: Add last history point to forecast trace if available
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
                                                     line=dict(color='#E60023', width=3, dash='dash')
                                                 ))

                                             # 3. Confidence Intervals
                                             lower_col = next((c for c in df_pred.columns if c.lower() in ['lower_bound', 'lowerbound', 'ymin']), None)
                                             upper_col = next((c for c in df_pred.columns if c.lower() in ['upper_bound', 'upperbound', 'ymax']), None)
                                             
                                             if lower_col and upper_col and not df_forecast.empty:
                                                  fig.add_trace(go.Scatter(
                                                     x=pd.concat([df_forecast['date'], df_forecast['date'][::-1]]),
                                                     y=pd.concat([df_forecast[upper_col], df_forecast[lower_col][::-1]]),
                                                     fill='toself',
                                                     fillcolor='rgba(230, 0, 35, 0.2)',
                                                     line=dict(color='rgba(255,255,255,0)'),
                                                     hoverinfo="skip",
                                                     showlegend=True,
                                                     name='Confidence Interval'
                                                 ))
                                             
                                             # 4. Optional: Prediction Divider Marker
                                             if not df_forecast.empty:
                                                  pred_start = df_forecast['date'].iloc[0]
                                                  fig.add_vline(x=pred_start, line_width=1, line_dash="dot", line_color="gray")

                                             st.plotly_chart(fig, use_container_width=True)
"""

def patch_file():
    with open(target_file, "r", encoding="utf-8") as f:
        content = f.read()

    start_marker = "if y_col in df_pred.columns:"
    end_marker = "st.plotly_chart(fig, use_container_width=True)"

    start_idx = content.find(start_marker)
    valid_end_marker_pos = -1
    
    # Locate the correct end marker (after the start)
    # Since existing code has st.plotly_chart inside the block
    if start_idx != -1:
        # We need to find the st.plotly_chart *inside* this block. 
        # But wait, looking at file, it's at the end of the block.
        # Let's search from start_idx
        end_idx = content.find(end_marker, start_idx)
        
        if end_idx != -1:
            # We want to replace everything from start_marker (inclusive) to end matching st.plotly_chart
            # Actually, I'll include the end_marker in replacement to be safe/clean
            # The new_logic includes the start_marker (indented) and end_marker logic.
            # But the start_marker in new_logic has indentation.
            # The file content start_marker also has indentation.
            
            # Let's verify indentation of finding
            # "                                         if y_col in df_pred.columns:"
            
            # I will just replace the chunk between start_idx and end_idx + len(end_marker)
            # Checking what I'm removing first
            chunk_to_remove = content[start_idx:end_idx + len(end_marker)]
            print(f"Replacing chunk of length: {len(chunk_to_remove)}")
            
            # Construct new content
            # Need to be careful about indentation of start_marker in `new_logic`
            # In `new_logic`, I indented it carefully.
            
            new_content = content[:start_idx] + new_logic.strip() + content[end_idx + len(end_marker):]
            
            with open(target_file, "w", encoding="utf-8") as f:
                f.write(new_content)
            print("Successfully patched ui/app.py")
            return

    print("Could not find start/end markers.")

if __name__ == "__main__":
    patch_file()
