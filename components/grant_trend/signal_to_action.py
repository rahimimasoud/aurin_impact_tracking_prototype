"""
Section 4 — Signal-to-Action.

Rule-based recommended actions for AURIN based on grant momentum signals
for the top trending FOR fields.
"""
import pandas as pd
import streamlit as st


def render_signal_to_action(top10_rows: pd.DataFrame) -> None:
    st.subheader("Signal-to-Action")
    st.caption(
        "Recommended actions for AURIN based on grant momentum signals "
        "in the top 10 trending FOR fields."
    )

    for _, row in top10_rows.iterrows():
        momentum = row["momentum_pct"]

        if momentum > 30:
            action       = "High momentum — consider targeted engagement with active funders"
            border_color = "#22c55e"
            bg_color     = "#f0fdf4"
            label        = "HIGH"
        elif momentum >= 10:
            action       = "Rising — monitor funding landscape and prepare partnership content"
            border_color = "#f59e0b"
            bg_color     = "#fffbeb"
            label        = "RISING"
        elif momentum >= 0:
            action       = "Steady — flag for next funding opportunity review cycle"
            border_color = "#3b82f6"
            bg_color     = "#eff6ff"
            label        = "STEADY"
        else:
            action       = "Declining — review whether engagement in this area remains a priority"
            border_color = "#ef4444"
            bg_color     = "#fef2f2"
            label        = "DECLINING"

        sign = "+" if momentum >= 0 else ""
        st.markdown(
            f"""
            <div style="border-left:4px solid {border_color}; background:{bg_color};
                        padding:12px 16px; margin-bottom:10px;
                        border-radius:0 8px 8px 0;">
              <div style="display:flex; justify-content:space-between;
                           align-items:center; margin-bottom:4px;">
                <span style="font-weight:600; color:#111827; font-size:14px;">
                  {row["display_name"]}
                  <span style="font-weight:400; color:#6b7280; font-size:12px;">
                    &nbsp;(FOR {row["for_division"]})
                  </span>
                </span>
                <span style="background:{border_color}; color:#fff; font-size:10px;
                             font-weight:700; padding:2px 8px; border-radius:4px;
                             letter-spacing:0.05em;">{label}</span>
              </div>
              <div style="color:#374151; font-size:13px; margin-bottom:2px;">
                {action}
              </div>
              <div style="color:#6b7280; font-size:11px;">
                Momentum: {sign}{momentum:.0f}% &nbsp;|&nbsp;
                Current window: {row["current_count"]:,} grants
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
