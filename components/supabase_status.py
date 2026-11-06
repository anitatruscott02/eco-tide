"""
Eco-Tide: Supabase Cloud Database Status Component
Renders a discreet, production-grade cloud synchronization badge.
No sensitive credentials, passwords, or technical expanders are shown to citizens/users.
"""

import streamlit as st
from utils.supabase_client import is_connected, get_credentials, get_setup_sql, save_credentials


def render_supabase_connection_widget(expanded_default: bool = False, show_card: bool = True):
    """
    Renders an elegant, non-intrusive cloud database sync indicator.
    All credentials remain protected in the backend (.streamlit/secrets.toml).
    """
    connected = is_connected()

    if not show_card:
        return

    if connected:
        st.markdown(
            """
            <div style="background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.35); 
                        border-radius: 10px; padding: 10px 16px; margin-bottom: 16px;
                        display: flex; align-items: center; justify-content: space-between;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 1rem;">☁️</span>
                    <div>
                        <span style="font-size: 0.92rem; font-weight: 700; color: #10B981;">
                            Cloud Synchronized
                        </span>
                        <span style="font-size: 0.8rem; color: var(--text-secondary); margin-left: 6px;">
                            • Live Supabase PostgreSQL database active across all Lagos nodes
                        </span>
                    </div>
                </div>
                <div style="font-size: 0.72rem; font-weight: 700; letter-spacing: 0.5px;
                            background: rgba(16, 185, 129, 0.18); color: #10B981; 
                            padding: 3px 10px; border-radius: 12px; border: 1px solid rgba(16, 185, 129, 0.3);">
                    LIVE
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            """
            <div style="background: rgba(245, 158, 11, 0.08); border: 1px solid rgba(245, 158, 11, 0.35); 
                        border-radius: 10px; padding: 10px 16px; margin-bottom: 16px;
                        display: flex; align-items: center; justify-content: space-between;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 1rem;">💾</span>
                    <div>
                        <span style="font-size: 0.92rem; font-weight: 700; color: #F59E0B;">
                            Local Cache Storage Active
                        </span>
                        <span style="font-size: 0.8rem; color: var(--text-secondary); margin-left: 6px;">
                            • Reports & dialogue stored locally on this node
                        </span>
                    </div>
                </div>
                <div style="font-size: 0.72rem; font-weight: 700; letter-spacing: 0.5px;
                            background: rgba(245, 158, 11, 0.18); color: #F59E0B; 
                            padding: 3px 10px; border-radius: 12px; border: 1px solid rgba(245, 158, 11, 0.3);">
                    LOCAL
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
