import streamlit as st
import pandas as pd
from datetime import datetime

# ----------------------------
# Tennis scoring logic (full class)
# ----------------------------
class TennisMatch:
    def __init__(self, player_a, player_b, best_of=3, ad_scoring=True, tiebreak_points=7, final_set_tiebreak=10, first_server=None):
        self.player_a = player_a
        self.player_b = player_b
        self.best_of = best_of
        self.ad_scoring = ad_scoring
        self.tiebreak_points = tiebreak_points
        self.final_set_tiebreak = final_set_tiebreak
        
        self.points = []
        self.current_set = 1
        self.sets_won = {player_a: 0, player_b: 0}
        self.games = {player_a: 0, player_b: 0}
        self.point_score = {player_a: 0, player_b: 0}
        self.tiebreak_active = False
        self.match_over = False
        self.winner = None
        self.current_server = first_server if first_server else player_a
        
        self.state_history = []
        
    def _save_state(self):
        self.state_history.append({
            'points': self.points.copy(),
            'current_set': self.current_set,
            'sets_won': self.sets_won.copy(),
            'games': self.games.copy(),
            'point_score': self.point_score.copy(),
            'tiebreak_active': self.tiebreak_active,
            'match_over': self.match_over,
            'winner': self.winner,
            'current_server': self.current_server,
        })
    
    def undo_last_point(self):
        if self.state_history:
            last = self.state_history.pop()
            self.points = last['points']
            self.current_set = last['current_set']
            self.sets_won = last['sets_won']
            self.games = last['games']
            self.point_score = last['point_score']
            self.tiebreak_active = last['tiebreak_active']
            self.match_over = last['match_over']
            self.winner = last['winner']
            self.current_server = last['current_server']
            return True
        return False
    
    def _point_value(self, points):
        if points >= 3:
            return 40
        return [0, 15, 30][points]
    
    def get_point_score_display(self, server=None):
        if server is None:
            server = self.current_server
        receiver = self.player_b if server == self.player_a else self.player_a
        pa = self.point_score[self.player_a]
        pb = self.point_score[self.player_b]
        if self.tiebreak_active:
            if server == self.player_a:
                return f"{pa} - {pb}"
            else:
                return f"{pb} - {pa}"
        server_pts = pa if server == self.player_a else pb
        receiver_pts = pb if server == self.player_a else pa
        if server_pts >= 3 and receiver_pts >= 3:
            if server_pts == receiver_pts:
                return "Deuce"
            elif self.ad_scoring:
                advantage = self.player_a if server_pts > receiver_pts else self.player_b
                return f"Ad-{advantage}"
            else:
                return "Deciding Point"
        else:
            return f"{self._point_value(server_pts)}-{self._point_value(receiver_pts)}"
    
    def _is_game_won(self):
        pa = self.point_score[self.player_a]
        pb = self.point_score[self.player_b]
        if self.tiebreak_active:
            if pa >= self.tiebreak_points or pb >= self.tiebreak_points:
                if abs(pa - pb) >= 2:
                    return True
            return False
        if pa >= 4 or pb >= 4:
            if abs(pa - pb) >= 2:
                return True
        if not self.ad_scoring and pa >= 3 and pb >= 3:
            return abs(pa - pb) == 1
        return False
    
    def _game_winner(self):
        if self.tiebreak_active:
            return self.player_a if self.point_score[self.player_a] > self.point_score[self.player_b] else self.player_b
        else:
            return self.player_a if self.point_score[self.player_a] > self.point_score[self.player_b] else self.player_b
    
    def _is_set_won(self):
        ga = self.games[self.player_a]
        gb = self.games[self.player_b]
        if ga >= 6 and ga - gb >= 2:
            return True
        if gb >= 6 and gb - ga >= 2:
            return True
        return False
    
    def _set_winner(self):
        return self.player_a if self.games[self.player_a] > self.games[self.player_b] else self.player_b
    
    def _is_match_over(self):
        needed = (self.best_of + 1) // 2
        return self.sets_won[self.player_a] >= needed or self.sets_won[self.player_b] >= needed
    
    def add_point(self, winner, serve_type1=None, serve_type2=None, serve_outcome=None, return_type=None, rally_length=None, reason=None, winner_detail=None, error_detail=None):
        if self.match_over:
            return False
        
        if serve_outcome in ["Ace (1st)", "Ace (2nd)", "Missed Return (1st)", "Missed Return (2nd)"]:
            winner = self.current_server
        elif serve_outcome == "Double Fault":
            winner = self.player_b if self.current_server == self.player_a else self.player_a
        
        self._save_state()
        server = self.current_server
        no_rally = serve_outcome in ["Ace (1st)", "Ace (2nd)", "Missed Return (1st)", "Missed Return (2nd)", "Double Fault"] or return_type == "Winner"
        
        point_data = {
            'point_number': len(self.points) + 1,
            'server': server,
            'winner': winner,
            'serve_type_1st': serve_type1,
            'serve_type_2nd': serve_type2,
            'serve_outcome': serve_outcome,
            'return_type': return_type,
            'rally_length': rally_length if not no_rally else None,
            'reason': reason,
            'winner_detail': winner_detail if reason == "Winner" else None,
            'error_detail': error_detail if reason in ["Unforced Error", "Forced Error"] else None,
            'no_rally': no_rally,
            'set': self.current_set,
            'game_score_before': f"{self.games[self.player_a]}-{self.games[self.player_b]}",
            'point_score_before': self.get_point_score_display(server),
            'game_won': None,
            'set_won': None,
            'match_won': None,
        }
        
        game_won_before = self._is_game_won()
        if not self.tiebreak_active and self.get_point_score_display(server) in ["Deuce", "Deciding Point"]:
            if not self.ad_scoring and self.get_point_score_display(server) == "Deciding Point":
                self.point_score = {self.player_a: 0, self.player_b: 0}
                game_winner = winner
                self.games[game_winner] += 1
                point_data['game_won'] = game_winner
                self.current_server = self.player_b if self.current_server == self.player_a else self.player_a
            else:
                if winner == server:
                    if self.point_score[self.player_a] == self.point_score[self.player_b]:
                        self.point_score[winner] += 1
                    else:
                        self.point_score = {self.player_a: 0, self.player_b: 0}
                        game_winner = winner
                        self.games[game_winner] += 1
                        point_data['game_won'] = game_winner
                        self.current_server = self.player_b if self.current_server == self.player_a else self.player_a
                else:
                    if self.point_score[self.player_a] == self.point_score[self.player_b]:
                        self.point_score[winner] += 1
                    else:
                        self.point_score[self.player_a] = 3
                        self.point_score[self.player_b] = 3
        else:
            self.point_score[winner] += 1
            if self._is_game_won() and not game_won_before:
                game_winner = self._game_winner()
                self.games[game_winner] += 1
                point_data['game_won'] = game_winner
                self.point_score = {self.player_a: 0, self.player_b: 0}
                self.tiebreak_active = False
                self.current_server = self.player_b if self.current_server == self.player_a else self.player_a
                if self._is_set_won():
                    set_winner = self._set_winner()
                    self.sets_won[set_winner] += 1
                    point_data['set_won'] = set_winner
                    self.games = {self.player_a: 0, self.player_b: 0}
                    self.current_set += 1
                    if self._is_match_over():
                        self.match_over = True
                        self.winner = set_winner
                        point_data['match_won'] = self.winner
                else:
                    if self.games[self.player_a] == 6 and self.games[self.player_b] == 6:
                        self.tiebreak_active = True
                        self.point_score = {self.player_a: 0, self.player_b: 0}
        
        point_data['point_score_after'] = self.get_point_score_display(server)
        point_data['game_score_after'] = f"{self.games[self.player_a]}-{self.games[self.player_b]}"
        point_data['set_score_after'] = f"{self.sets_won[self.player_a]}-{self.sets_won[self.player_b]}"
        self.points.append(point_data)
        return True
    
    def get_current_score(self):
        return {
            'point': self.get_point_score_display(),
            'games': f"{self.games[self.player_a]}-{self.games[self.player_b]}",
            'sets': f"{self.sets_won[self.player_a]}-{self.sets_won[self.player_b]}",
            'tiebreak': self.tiebreak_active,
            'match_over': self.match_over,
            'winner': self.winner,
            'current_server': self.current_server,
        }
    
    def get_statistics(self):
        if not self.points:
            return {}
        df = pd.DataFrame(self.points)
        stats = {}
        for player in [self.player_a, self.player_b]:
            p = player
            opponent = self.player_b if p == self.player_a else self.player_a
            points_served = df[df['server'] == p]
            total_serves = len(points_served)
            first_serve_in = points_served[points_served['serve_outcome'].isin(['1st Serve In Play', 'Ace (1st)', 'Missed Return (1st)'])]
            first_serve_pct = len(first_serve_in) / total_serves if total_serves > 0 else 0
            first_serve_won = first_serve_in[first_serve_in['winner'] == p]
            first_serve_won_pct = len(first_serve_won) / len(first_serve_in) if len(first_serve_in) > 0 else 0
            second_serve_in = points_served[points_served['serve_outcome'].isin(['2nd Serve In Play', 'Ace (2nd)', 'Missed Return (2nd)'])]
            second_serve_won = second_serve_in[second_serve_in['winner'] == p]
            second_serve_won_pct = len(second_serve_won) / len(second_serve_in) if len(second_serve_in) > 0 else 0
            aces = len(points_served[points_served['serve_outcome'].isin(['Ace (1st)', 'Ace (2nd)'])])
            double_faults = len(points_served[points_served['serve_outcome'] == 'Double Fault'])
            game_won_points = df[df['game_won'] == p]
            service_games_won = game_won_points[game_won_points['server'] == p]
            service_games_played = len(df[df['server'] == p].drop_duplicates(subset=['game_score_before', 'set']))
            service_games_won_pct = len(service_games_won) / service_games_played if service_games_played > 0 else 0
            break_points_faced = df[(df['server'] == p) & (df['point_score_before'].isin(['30-40', '40-30', 'Deuce', 'Ad-Out']))]
            break_points_saved = break_points_faced[break_points_faced['winner'] == p]
            break_points_saved_pct = len(break_points_saved) / len(break_points_faced) if len(break_points_faced) > 0 else 0
            points_returned = df[df['server'] != p]
            total_return_points = len(points_returned)
            return_points_won = len(points_returned[points_returned['winner'] == p])
            return_points_won_pct = return_points_won / total_return_points if total_return_points > 0 else 0
            first_serve_against = points_returned[points_returned['serve_outcome'].isin(['1st Serve In Play', 'Ace (1st)', 'Missed Return (1st)'])]
            return_vs_1st_won = len(first_serve_against[first_serve_against['winner'] == p])
            return_vs_1st_pct = return_vs_1st_won / len(first_serve_against) if len(first_serve_against) > 0 else 0
            second_serve_against = points_returned[points_returned['serve_outcome'].isin(['2nd Serve In Play', 'Ace (2nd)', 'Missed Return (2nd)'])]
            return_vs_2nd_won = len(second_serve_against[second_serve_against['winner'] == p])
            return_vs_2nd_pct = return_vs_2nd_won / len(second_serve_against) if len(second_serve_against) > 0 else 0
            break_points_opp = df[(df['server'] == opponent) & (df['point_score_before'].isin(['30-40', '40-30', 'Deuce', 'Ad-Out']))]
            break_points_converted = break_points_opp[break_points_opp['winner'] == p]
            break_points_converted_pct = len(break_points_converted) / len(break_points_opp) if len(break_points_opp) > 0 else 0
            return_games_won = game_won_points[game_won_points['server'] == opponent]
            return_games_won_pct = len(return_games_won) / service_games_played if service_games_played > 0 else 0
            total_points = len(df)
            total_points_won = len(df[df['winner'] == p])
            total_points_pct = total_points_won / total_points if total_points > 0 else 0
            winners = len(df[(df['winner'] == p) & (df['reason'] == 'Winner')])
            unforced_errors = len(df[(df['winner'] != p) & (df['reason'] == 'Unforced Error')])
            rallies = df[df['rally_length'].notna()]
            short = rallies[rallies['rally_length'] == '1-4']
            medium = rallies[rallies['rally_length'] == '5-8']
            long = rallies[rallies['rally_length'] == '9+ shots']
            rally_patterns = {
                '1-4': len(short) / len(rallies) if len(rallies) > 0 else 0,
                '5-8': len(medium) / len(rallies) if len(rallies) > 0 else 0,
                '9+': len(long) / len(rallies) if len(rallies) > 0 else 0,
            }
            stats[p] = {
                'first_serve_pct': first_serve_pct,
                'first_serve_won_pct': first_serve_won_pct,
                'second_serve_won_pct': second_serve_won_pct,
                'aces': aces,
                'double_faults': double_faults,
                'service_games_won_pct': service_games_won_pct,
                'break_points_saved_pct': break_points_saved_pct,
                'return_points_won_pct': return_points_won_pct,
                'return_vs_1st_pct': return_vs_1st_pct,
                'return_vs_2nd_pct': return_vs_2nd_pct,
                'break_points_converted_pct': break_points_converted_pct,
                'return_games_won_pct': return_games_won_pct,
                'total_points_won_pct': total_points_pct,
                'winners': winners,
                'unforced_errors': unforced_errors,
                'rally_patterns': rally_patterns,
            }
        return stats

# ----------------------------
# Streamlit UI (always visible)
# ----------------------------
st.set_page_config(page_title="Tennis Tracker", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .stApp { background-color: #ffffff; font-family: 'Inter', sans-serif; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    div[data-testid="stMetricValue"] { font-size: 48px !important; font-weight: 600 !important; background: #f8fafc; padding: 12px 20px; border-radius: 24px; }
    div[data-testid="stMetricLabel"] { font-size: 16px !important; font-weight: 500 !important; color: #475569 !important; }
    div[role="radiogroup"] label { background-color: #f1f5f9; border-radius: 40px; padding: 10px 24px !important; margin: 4px 8px !important; border: 1px solid #e2e8f0; }
    div[role="radiogroup"] label:hover { background-color: #e2e8f0; }
    .stButton button { background-color: #0f172a; color: white; border-radius: 40px; font-size: 18px; padding: 10px 20px; }
    .stButton button:hover { background-color: #1e293b; }
</style>
""", unsafe_allow_html=True)

st.title("🎾 Tennis Match Tracker")
st.caption("Live scoring • CSV export • Optional cloud save (Google Sheets)")

# Initialize session state
if 'match' not in st.session_state:
    st.session_state.match = None
if 'first_serve_fault' not in st.session_state:
    st.session_state.first_serve_fault = False
if 'last_match_saved' not in st.session_state:
    st.session_state.last_match_saved = False

# ------------------------------------------------------------------
# Optional Google Sheets integration (fail‑safe)
# ------------------------------------------------------------------
GSHEET_AVAILABLE = False
SHEET_ID = None
try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    GSHEET_AVAILABLE = True
    # Try to load secrets
    try:
        SHEET_ID = st.secrets.get("SHEET_ID", "")
        GCP_SECRET = st.secrets.get("gcp_service_account", {})
        if not SHEET_ID or not GCP_SECRET:
            GSHEET_AVAILABLE = False
    except:
        GSHEET_AVAILABLE = False
except ImportError:
    pass

if GSHEET_AVAILABLE:
    st.success("✅ Google Sheets configured – you can save matches to the cloud.")
else:
    st.info("📥 Google Sheets not configured. Use the CSV download button to save matches.")

# ------------------------------------------------------------------
# Match setup (always visible)
# ------------------------------------------------------------------
st.markdown("### 🏟️ Match Setup")
col_setup1, col_setup2 = st.columns(2)
with col_setup1:
    player_a = st.text_input("Player A Name", "Roger Federer")
    player_b = st.text_input("Player B Name", "Rafael Nadal")
    first_server = st.radio("Who serves first?", [player_a, player_b], index=0)
with col_setup2:
    best_of = st.selectbox("Format", [3, 5], index=0)
    ad_scoring = st.checkbox("Ad Scoring (deuce)", value=True)
    tiebreak_pts = st.number_input("Tiebreak points to win", min_value=5, max_value=10, value=7)
    final_set_tiebreak = st.number_input("Final set tiebreak points", min_value=0, max_value=10, value=10)

if st.button("🆕 Start New Match", use_container_width=True):
    st.session_state.match = TennisMatch(
        player_a=player_a,
        player_b=player_b,
        best_of=best_of,
        ad_scoring=ad_scoring,
        tiebreak_points=tiebreak_pts,
        final_set_tiebreak=final_set_tiebreak,
        first_server=first_server
    )
    st.session_state.first_serve_fault = False
    st.session_state.last_match_saved = False
    st.rerun()

# ------------------------------------------------------------------
# Main match interface (only if a match exists)
# ------------------------------------------------------------------
if st.session_state.match:
    match = st.session_state.match
    score = match.get_current_score()
    
    # Scoreboard
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Point", score['point'])
    with col2:
        st.metric("Games", score['games'])
    with col3:
        st.metric("Sets", score['sets'])
    
    if score['tiebreak']:
        st.info("⚡ Tiebreak in progress")
    if score['match_over']:
        st.success(f"🏆 Match Winner: {score['winner']}")
        if not st.session_state.last_match_saved:
            # Download CSV (always available)
            df = pd.DataFrame(match.points)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("💾 Download Match CSV", csv, f"tennis_match_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", "text/csv", use_container_width=True)
            
            # Google Sheets save (if available)
            if GSHEET_AVAILABLE:
                if st.button("☁️ Save to Google Sheets", use_container_width=True):
                    try:
                        creds_dict = dict(st.secrets["gcp_service_account"])
                        if "private_key" in creds_dict:
                            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
                        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
                        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
                        client = gspread.authorize(creds)
                        sheet_id = st.secrets["SHEET_ID"]
                        try:
                            sh = client.open_by_key(sheet_id)
                        except:
                            sh = client.open(sheet_id)
                        
                        # Create/Get worksheets
                        try:
                            summary_ws = sh.worksheet("Match_Summary")
                        except:
                            summary_ws = sh.add_worksheet("Match_Summary", rows=1000, cols=20)
                            summary_ws.append_row(["Match_ID", "Date", "Player A", "Player B", "Winner", "Sets", "Games", "Total Points"])
                        try:
                            points_ws = sh.worksheet("Points_Detail")
                        except:
                            points_ws = sh.add_worksheet("Points_Detail", rows=10000, cols=30)
                            points_ws.append_row(["Match_ID", "Point_Number", "Server", "Winner", "Serve_Outcome", "Serve_Type_1st", "Serve_Type_2nd", "Return_Type", "Rally_Length", "Reason", "Winner_Detail", "Error_Detail", "Point_Score_Before", "Point_Score_After", "Game_Score_Before", "Game_Score_After", "Set_Score_After"])
                        
                        match_id = datetime.now().strftime("%Y%m%d_%H%M%S")
                        summary_ws.append_row([match_id, datetime.now().isoformat(), match.player_a, match.player_b, match.winner, score['sets'], score['games'], len(match.points)])
                        for p in match.points:
                            points_ws.append_row([match_id, p.get('point_number'), p.get('server'), p.get('winner'), p.get('serve_outcome'), p.get('serve_type_1st'), p.get('serve_type_2nd'), p.get('return_type'), p.get('rally_length'), p.get('reason'), p.get('winner_detail'), p.get('error_detail'), p.get('point_score_before'), p.get('point_score_after'), p.get('game_score_before'), p.get('game_score_after'), p.get('set_score_after')])
                        st.success(f"Match saved to Google Sheets with ID: {match_id}")
                        st.session_state.last_match_saved = True
                    except Exception as e:
                        st.error(f"Failed to save to Google Sheets: {e}")
    
    st.markdown("---")
    st.subheader("📝 Record Next Point")
    st.write(f"**Server:** {score['current_server']}")
    
    # Two‑stage serve interface
    if not st.session_state.first_serve_fault:
        serve_outcome_1st = st.selectbox("First Serve Outcome", [
            "1st Serve In Play", "Ace (1st)", "Missed Return (1st)", "Fault"
        ], key="first_serve")
        
        if serve_outcome_1st == "Fault":
            if st.button("📌 Second Serve", use_container_width=True):
                st.session_state.first_serve_fault = True
                st.rerun()
        else:
            serve_outcome = serve_outcome_1st
            if serve_outcome in ["Ace (1st)", "Missed Return (1st)"]:
                forced_winner = score['current_server']
                winner_disabled = True
                st.info(f"Winner automatically set to: **{forced_winner}**")
                winner = forced_winner
            else:
                winner_disabled = False
                winner = st.radio("Point Winner", [match.player_a, match.player_b], index=0, horizontal=True, key="winner_radio")
            
            with st.expander("🔍 Point Details (optional)", expanded=False):
                serve_type1 = st.selectbox("1st Serve Type", ["", "Flat Wide", "Slice Wide", "Flat T", "Slice T", "Body Flat", "Body Kick", "Kick Wide", "Kick T"])
                no_rally_serve = serve_outcome in ["Ace (1st)", "Missed Return (1st)"]
                return_type = st.selectbox("Return Type", ["", "Deep", "Short", "Winner", "Forced Error", "Unforced Error"], disabled=no_rally_serve)
                no_rally_return = (return_type == "Winner")
                rally_disabled = no_rally_serve or no_rally_return
                rally_length = st.selectbox("Rally Length", ["", "1-4", "5-8", "9+ shots"], disabled=rally_disabled)
                if rally_disabled:
                    st.caption("Rally length disabled because point ended on serve winner or return winner.")
                reason = st.selectbox("Reason Point Ended", ["", "Winner", "Unforced Error", "Forced Error"], disabled=no_rally_serve)
                winner_detail = None
                error_detail = None
                if reason == "Winner" and not no_rally_serve:
                    winner_detail = st.selectbox("Winner Detail", ["", "Forehand", "Attack Forehand", "Backhand", "Attack Backhand", "Smash", "Volley", "Drop Shot"])
                elif reason in ["Unforced Error", "Forced Error"] and not no_rally_serve:
                    error_detail = st.selectbox("Error Detail", ["", "Long forehand", "Wide forehand", "Net forehand", "Backhand Long", "Backhand Wide", "Backhand net", "Smash Net", "Smash long", "Smash Wide", "Volley Net", "Volley long", "Volley Wide", "Slice Long", "Slice Wide", "Slice Net", "Drop Net", "Drop wide"])
            
            if st.button("✅ Next Point", use_container_width=True):
                if not serve_outcome:
                    st.warning("Please select a serve outcome")
                elif not winner_disabled and not winner:
                    st.warning("Please select a winner")
                else:
                    success = match.add_point(
                        winner=winner,
                        serve_type1=serve_type1 if serve_type1 else None,
                        serve_type2=None,
                        serve_outcome=serve_outcome,
                        return_type=return_type if return_type else None,
                        rally_length=rally_length if rally_length else None,
                        reason=reason if reason else None,
                        winner_detail=winner_detail if winner_detail else None,
                        error_detail=error_detail if error_detail else None
                    )
                    if success:
                        st.success(f"Point recorded: {winner} won the point")
                        st.session_state.first_serve_fault = False
                        st.rerun()
                    else:
                        st.error("Match is already over!")
    else:
        # Second serve (first serve was fault)
        serve_outcome_2nd = st.selectbox("Second Serve Outcome", [
            "2nd Serve In Play", "Ace (2nd)", "Missed Return (2nd)", "Double Fault"
        ], key="second_serve")
        
        serve_outcome = serve_outcome_2nd
        if serve_outcome in ["Ace (2nd)", "Missed Return (2nd)"]:
            forced_winner = score['current_server']
            winner_disabled = True
            st.info(f"Winner automatically set to: **{forced_winner}**")
            winner = forced_winner
        elif serve_outcome == "Double Fault":
            forced_winner = match.player_b if score['current_server'] == match.player_a else match.player_a
            winner_disabled = True
            st.info(f"Winner automatically set to: **{forced_winner}** (Double Fault)")
            winner = forced_winner
        else:
            winner_disabled = False
            winner = st.radio("Point Winner", [match.player_a, match.player_b], index=0, horizontal=True, key="winner_radio_2nd")
        
        with st.expander("🔍 Point Details (optional)", expanded=False):
            serve_type1 = st.selectbox("1st Serve Type (missed)", ["", "Flat Wide", "Slice Wide", "Flat T", "Slice T", "Body Flat", "Body Kick", "Kick Wide", "Kick T"])
            serve_type2 = st.selectbox("2nd Serve Type", ["", "Flat Wide", "Slice Wide", "Flat T", "Slice T", "Body Flat", "Body Kick", "Kick Wide", "Kick T"])
            no_rally_serve = serve_outcome in ["Ace (2nd)", "Missed Return (2nd)", "Double Fault"]
            return_type = st.selectbox("Return Type", ["", "Deep", "Short", "Winner", "Forced Error", "Unforced Error"], disabled=no_rally_serve)
            no_rally_return = (return_type == "Winner")
            rally_disabled = no_rally_serve or no_rally_return
            rally_length = st.selectbox("Rally Length", ["", "1-4", "5-8", "9+ shots"], disabled=rally_disabled)
            if rally_disabled:
                st.caption("Rally length disabled because point ended on serve winner or return winner.")
            reason = st.selectbox("Reason Point Ended", ["", "Winner", "Unforced Error", "Forced Error"], disabled=no_rally_serve)
            winner_detail = None
            error_detail = None
            if reason == "Winner" and not no_rally_serve:
                winner_detail = st.selectbox("Winner Detail", ["", "Forehand", "Attack Forehand", "Backhand", "Attack Backhand", "Smash", "Volley", "Drop Shot"])
            elif reason in ["Unforced Error", "Forced Error"] and not no_rally_serve:
                error_detail = st.selectbox("Error Detail", ["", "Long forehand", "Wide forehand", "Net forehand", "Backhand Long", "Backhand Wide", "Backhand net", "Smash Net", "Smash long", "Smash Wide", "Volley Net", "Volley long", "Volley Wide", "Slice Long", "Slice Wide", "Slice Net", "Drop Net", "Drop wide"])
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("✅ Next Point", use_container_width=True):
                if not serve_outcome:
                    st.warning("Please select a serve outcome")
                elif not winner_disabled and not winner:
                    st.warning("Please select a winner")
                else:
                    success = match.add_point(
                        winner=winner,
                        serve_type1=serve_type1 if serve_type1 else None,
                        serve_type2=serve_type2 if serve_type2 else None,
                        serve_outcome=serve_outcome,
                        return_type=return_type if return_type else None,
                        rally_length=rally_length if rally_length else None,
                        reason=reason if reason else None,
                        winner_detail=winner_detail if winner_detail else None,
                        error_detail=error_detail if error_detail else None
                    )
                    if success:
                        st.success(f"Point recorded: {winner} won the point")
                        st.session_state.first_serve_fault = False
                        st.rerun()
                    else:
                        st.error("Match is already over!")
        with col_btn2:
            if st.button("↩️ Back to First Serve", use_container_width=True):
                st.session_state.first_serve_fault = False
                st.rerun()
    
    # Undo button
    if st.button("↩️ Undo Last Point", use_container_width=True):
        if match.undo_last_point():
            st.success("Last point undone")
            st.rerun()
        else:
            st.warning("No point to undo")
    
    # Statistics
    st.markdown("---")
    st.subheader("📊 Advanced Match Statistics")
    if match.points:
        stats = match.get_statistics()
        col_a, col_b = st.columns(2)
        for col, player in [(col_a, match.player_a), (col_b, match.player_b)]:
            with col:
                st.markdown(f"### {player}")
                p = stats[player]
                st.markdown("**Serving**")
                st.write(f"1st Serve %: {p['first_serve_pct']:.1%}")
                st.write(f"1st Serve Points Won: {p['first_serve_won_pct']:.1%}")
                st.write(f"**2nd Serve Points Won: {p['second_serve_won_pct']:.1%}**")
                st.write(f"Aces: {p['aces']}  |  Double Faults: {p['double_faults']}")
                st.write(f"Service Games Won: {p['service_games_won_pct']:.1%}")
                st.write(f"Break Points Saved: {p['break_points_saved_pct']:.1%}")
                st.markdown("**Return**")
                st.write(f"Return Points Won: {p['return_points_won_pct']:.1%}")
                st.write(f"  vs 1st Serve: {p['return_vs_1st_pct']:.1%}")
                st.write(f"  vs 2nd Serve: {p['return_vs_2nd_pct']:.1%}")
                st.write(f"Break Points Converted: {p['break_points_converted_pct']:.1%}")
                st.write(f"Return Games Won: {p['return_games_won_pct']:.1%}")
                st.markdown("**Rally & Point**")
                st.write(f"Total Points Won: {p['total_points_won_pct']:.1%}")
                st.write(f"Winners: {p['winners']}  |  Unforced Errors: {p['unforced_errors']}")
                st.write("Rally Length Distribution:")
                for length, pct in p['rally_patterns'].items():
                    st.write(f"  {length}: {pct:.1%}")
    else:
        st.info("No points recorded yet. Add points to see statistics.")
    
    with st.expander("📜 Point History"):
        if match.points:
            df = pd.DataFrame(match.points)
            display_cols = ['point_number', 'server', 'winner', 'serve_outcome', 'serve_type_1st', 'serve_type_2nd', 'return_type', 'rally_length', 'reason', 'winner_detail', 'error_detail', 'point_score_before', 'point_score_after', 'game_score_after']
            st.dataframe(df[display_cols], use_container_width=True)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download CSV (full history)", csv, f"tennis_match_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", "text/csv")
        else:
            st.write("No points yet.")
else:
    st.info("👆 Set up the match above and click 'Start New Match'")