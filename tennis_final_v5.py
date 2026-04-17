import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ----------------------------
# TennisMatch class (same as before – keep it here)
# ----------------------------
# ... [INSERT YOUR FULL TennisMatch CLASS HERE] ...
# (I've omitted it for brevity, but you must copy the full class from the previous answer)

# ----------------------------
# Google Sheets helpers with safe error handling
# ----------------------------
def get_gsheet_client():
    """Return gspread client using Streamlit secrets. Returns None if secrets missing."""
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        # Fix private key newlines
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Failed to authenticate with Google Sheets: {e}")
        return None

def save_match_to_sheets(match, sheet_url_or_key):
    if not sheet_url_or_key:
        st.warning("SHEET_ID not configured. Match not saved.")
        return None
    client = get_gsheet_client()
    if not client:
        return None
    try:
        # Try to open by key (if it's a 44-char key) or by URL
        try:
            sh = client.open_by_key(sheet_url_or_key)
        except:
            sh = client.open(sheet_url_or_key)
    except Exception as e:
        st.error(f"Cannot open spreadsheet. Make sure the sheet is shared with the service account email. Error: {e}")
        return None
    
    # Create or get worksheets
    try:
        summary_ws = sh.worksheet("Match_Summary")
    except:
        summary_ws = sh.add_worksheet("Match_Summary", rows=1000, cols=20)
        summary_ws.append_row(["Match_ID", "Date", "Player A", "Player B", "Winner", "Sets", "Games", "Total Points"])
    
    try:
        points_ws = sh.worksheet("Points_Detail")
    except:
        points_ws = sh.add_worksheet("Points_Detail", rows=10000, cols=30)
        headers = ["Match_ID", "Point_Number", "Server", "Winner", "Serve_Outcome", "Serve_Type_1st", "Serve_Type_2nd",
                   "Return_Type", "Rally_Length", "Reason", "Winner_Detail", "Error_Detail",
                   "Point_Score_Before", "Point_Score_After", "Game_Score_Before", "Game_Score_After", "Set_Score_After"]
        points_ws.append_row(headers)
    
    match_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    score = match.get_current_score()
    summary_row = [
        match_id,
        datetime.now().isoformat(),
        match.player_a,
        match.player_b,
        match.winner if match.winner else "",
        score['sets'],
        score['games'],
        len(match.points)
    ]
    summary_ws.append_row(summary_row)
    
    for p in match.points:
        points_row = [
            match_id,
            p.get('point_number'),
            p.get('server'),
            p.get('winner'),
            p.get('serve_outcome'),
            p.get('serve_type_1st'),
            p.get('serve_type_2nd'),
            p.get('return_type'),
            p.get('rally_length'),
            p.get('reason'),
            p.get('winner_detail'),
            p.get('error_detail'),
            p.get('point_score_before'),
            p.get('point_score_after'),
            p.get('game_score_before'),
            p.get('game_score_after'),
            p.get('set_score_after'),
        ]
        points_ws.append_row(points_row)
    return match_id

def load_match_history(sheet_url_or_key):
    if not sheet_url_or_key:
        return pd.DataFrame()
    client = get_gsheet_client()
    if not client:
        return pd.DataFrame()
    try:
        try:
            sh = client.open_by_key(sheet_url_or_key)
        except:
            sh = client.open(sheet_url_or_key)
        ws = sh.worksheet("Match_Summary")
        data = ws.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Could not load match history: {e}")
        return pd.DataFrame()

def load_match_points(sheet_url_or_key, match_id):
    if not sheet_url_or_key:
        return pd.DataFrame()
    client = get_gsheet_client()
    if not client:
        return pd.DataFrame()
    try:
        try:
            sh = client.open_by_key(sheet_url_or_key)
        except:
            sh = client.open(sheet_url_or_key)
        ws = sh.worksheet("Points_Detail")
        all_data = ws.get_all_records()
        df = pd.DataFrame(all_data)
        return df[df['Match_ID'] == match_id]
    except Exception as e:
        st.error(f"Could not load match points: {e}")
        return pd.DataFrame()

# ----------------------------
# Streamlit UI (abbreviated – keep your existing UI)
# ----------------------------
st.set_page_config(page_title="Tennis Tracker", layout="wide", initial_sidebar_state="expanded")

st.title("🎾 Tennis Match Tracker")
st.caption("Live scoring • Optional Google Sheets save")

# Check Google Sheets configuration
try:
    SHEET_ID = st.secrets.get("SHEET_ID", "")
    if SHEET_ID:
        st.success("✅ Google Sheets configured. Matches can be saved.")
    else:
        st.info("📌 Google Sheets not configured. Use the CSV download button to save matches.")
except:
    SHEET_ID = ""
    st.info("📌 Google Sheets secrets missing. Use CSV download.")

# ... (rest of your UI code – keep everything else the same)
# Make sure to wrap save_match_to_sheets in a try/except when called.