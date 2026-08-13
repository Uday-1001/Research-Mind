# pyrefly: ignore [missing-import]
import streamlit as st
import time
import uuid
# pyrefly: ignore [missing-import]
from agents import build_reader_agent, build_search_agent, writer_chain, critic_chain
# pyrefly: ignore [missing-import]
from storage import init_db, save_session, get_all_sessions, delete_session

# Initialize database
init_db()

# Page config 
st.set_page_config(
    page_title="ResearchMind · AI Research Agent",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

#  Custom CSS 
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@300;400;500&display=swap');

/*  Reset & base  */
*, *::before, *::after { box-sizing: border-box; }

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    color: #e2ddd6;
}

.stApp {
    background: #080810;
    background-image:
        radial-gradient(ellipse 90% 55% at 15% -5%, rgba(255,120,40,0.14) 0%, transparent 55%),
        radial-gradient(ellipse 70% 45% at 85% 105%, rgba(255,60,20,0.09) 0%, transparent 50%),
        radial-gradient(ellipse 50% 50% at 50% 50%, rgba(20,10,40,0.5) 0%, transparent 80%);
    min-height: 100vh;
}

/*  Hide default streamlit chrome (display:none removes layout space, visibility:hidden does not)  */
#MainMenu { visibility: hidden; }
footer { display: none !important; }
header[data-testid="stHeader"] { background: transparent !important; }
.block-container {
    padding: 1.5rem 3rem 6rem !important;
    margin-top: 0 !important;
    max-width: 1280px !important;
}

/*  Scrollbar  */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,140,50,0.25); border-radius: 3px; }

/*  Hero  */
.hero-wrap {
    text-align: center;
    padding: 2.5rem 0 2rem;
    width: 100%;
}
.hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    background: rgba(255,120,40,0.1);
    border: 1px solid rgba(255,120,40,0.25);
    border-radius: 100px;
    padding: 0.3rem 1rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    font-weight: 500;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #ff8c32;
    margin-bottom: 1.2rem;
}
.hero-badge-dot {
    width: 6px; height: 6px;
    background: #ff8c32;
    border-radius: 50%;
    animation: pulse-dot 2s ease-in-out infinite;
}
@keyframes pulse-dot {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.4; transform: scale(0.7); }
}
.hero-title {
    font-size: clamp(2.8rem, 6vw, 4.8rem);
    font-weight: 900;
    line-height: 1;
    letter-spacing: -0.04em;
    color: #f5f0e8;
    margin: 0 0 0 !important;
}
.hero-title .accent { color: #ff8c32; }
.hero-title .dim { color: rgba(245,240,232,0.3); }
.hero-sub {
    font-size: 0.97rem;
    font-weight: 400;
    color: #706a60;
    max-width: 480px;
    margin: 0.2rem auto 0 !important;
    line-height: 1.7;
}

/*  Divider  */
.hr-glow {
    height: 1px;
    background: linear-gradient(90deg, transparent 0%, rgba(255,120,40,0.35) 30%, rgba(255,120,40,0.35) 70%, transparent 100%);
    margin: 2.5rem 0;
    position: relative;
}
.hr-glow::after {
    content: '';
    position: absolute;
    top: -2px; left: 50%; transform: translateX(-50%);
    width: 60px; height: 5px;
    background: rgba(255,120,40,0.55);
    filter: blur(6px);
    border-radius: 50%;
}

/*  Override Streamlit text input  */
.stTextInput > div > div > input {
    background: rgba(255,255,255,0.04) !important;
    border: 1.5px solid rgba(255,140,50,0.22) !important;
    border-radius: 12px !important;
    color: #f0ebe0 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 1rem !important;
    font-weight: 400 !important;
    padding: 0.85rem 1.1rem !important;
    caret-color: #ff8c32 !important;
    transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
}
.stTextInput > div > div > input::placeholder {
    color: rgba(160,152,144,0.4) !important;
}
.stTextInput > div > div > input:focus {
    border-color: rgba(255,140,50,0.55) !important;
    box-shadow: 0 0 0 4px rgba(255,140,50,0.08), 0 0 20px rgba(255,140,50,0.06) !important;
    outline: none !important;
}
.stTextInput > label {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.65rem !important;
    letter-spacing: 0.2em !important;
    text-transform: uppercase !important;
    color: #ff8c32 !important;
    font-weight: 500 !important;
    opacity: 0.9 !important;
    margin-bottom: 0.4rem !important;
}

/*  Run button  */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #ff9040 0%, #ff4d1a 100%) !important;
    color: #080810 !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.92rem !important;
    letter-spacing: 0.03em !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.8rem 2rem !important;
    cursor: pointer !important;
    width: 100% !important;
    transition: transform 0.18s ease, box-shadow 0.18s ease !important;
    box-shadow: 0 4px 24px rgba(255,120,40,0.35), 0 1px 0 rgba(255,255,255,0.15) inset !important;
    margin-top: 0.5rem !important;
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 32px rgba(255,120,40,0.5), 0 1px 0 rgba(255,255,255,0.15) inset !important;
}
.stButton > button[kind="primary"]:active { transform: translateY(0px) !important; }

/* Small delete buttons in the sidebar - always red */
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] > div:last-child button {
    background-color: #e63946 !important;
    color: white !important;
    border: 1px solid #d62828 !important;
    border-radius: 8px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    padding: 0 !important;
    min-height: 40px !important;
    transition: all 0.2s ease !important;
}
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] > div:last-child button:hover {
    background-color: #d62828 !important;
    border-color: #bc2020 !important;
    color: white !important;
}

/*  Chips  */
.example-topics {
    margin-top: 1.5rem;
}
.chip-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.6rem;
}
.chip-label {
    display: block;
    margin-bottom: 0.8rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    color: #6a6258;
    letter-spacing: 0.15em;
    text-transform: uppercase;
}
.chip {
    background: rgba(255,140,50,0.05);
    border: 1px solid rgba(255,140,50,0.15);
    border-radius: 100px;
    padding: 0.35rem 0.85rem;
    font-size: 0.75rem;
    font-weight: 500;
    color: #d0c8b8;
    font-family: 'Inter', sans-serif;
    transition: all 0.2s ease;
    cursor: pointer;
}
.chip:hover {
    background: rgba(255,140,50,0.15);
    border-color: rgba(255,140,50,0.4);
    color: #ffebcc;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(255,120,40,0.15);
}

/*  Pipeline label  */
.pipeline-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.62rem;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: #ff8c32;
    opacity: 0.85;
    margin-bottom: 1.1rem;
}

/*  Step cards  */
.step-card {
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 14px;
    padding: 1.5rem 1.8rem;
    margin-bottom: 1rem;
    position: relative;
    overflow: hidden;
    transition: border-color 0.35s ease, background 0.35s ease;
}
.step-card::before {
    content: '';
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 3px;
    border-radius: 14px 0 0 14px;
    background: rgba(255,255,255,0.04);
    transition: background 0.35s ease;
}
.step-card.active {
    border-color: rgba(255,140,50,0.35);
    background: rgba(255,140,50,0.04);
}
.step-card.active::before { background: #ff8c32; }
.step-card.done {
    border-color: rgba(72,199,116,0.28);
    background: rgba(72,199,116,0.03);
}
.step-card.error {
    border-color: rgba(230,57,70,0.35);
    background: rgba(230,57,70,0.04);
}
.step-card.error::before { background: #e63946; }

.step-top {
    display: flex;
    align-items: center;
    gap: 0.75rem;
}
.step-num {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.6rem;
    font-weight: 500;
    letter-spacing: 0.15em;
    color: rgba(255,140,50,0.6);
    min-width: 22px;
}
.step-icon { font-size: 1.2rem; line-height: 1; }
.step-name {
    font-size: 1.05rem;
    font-weight: 600;
    color: #e8e3db;
    flex: 1;
}
.step-badge {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.58rem;
    letter-spacing: 0.12em;
    padding: 0.2rem 0.55rem;
    border-radius: 5px;
    text-transform: uppercase;
}
.badge-wait { color: #3a3530; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.05); }
.badge-run  { color: #ff8c32; background: rgba(255,140,50,0.1); border: 1px solid rgba(255,140,50,0.2);
              animation: badge-pulse 1.5s ease-in-out infinite; }
.badge-done { color: #48c774; background: rgba(72,199,116,0.1); border: 1px solid rgba(72,199,116,0.2); }
.badge-error { color: #e63946; background: rgba(230,57,70,0.1); border: 1px solid rgba(230,57,70,0.2); }

@keyframes badge-pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

.step-desc {
    font-size: 0.85rem;
    color: #5a5550;
    margin-top: 0.5rem;
    padding-left: calc(22px + 0.75rem + 1.2rem + 0.75rem);
    line-height: 1.5;
}

/*  Live status bar (compact inline pill)  */
.live-status-wrap {
    display: flex;
    justify-content: flex-start;
    margin: 0.6rem 0 1rem;
}
.live-status {
    display: inline-flex;
    align-items: center;
    gap: 0.55rem;
    background: rgba(255,140,50,0.07);
    border: 1px solid rgba(255,140,50,0.2);
    border-radius: 100px;
    padding: 0.35rem 0.9rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    color: #c07830;
    letter-spacing: 0.05em;
    white-space: normal;
    word-break: break-word;
}
/* CSS spinner replacing static dot */
.live-spinner {
    width: 13px;
    height: 13px;
    border: 2px solid rgba(255,140,50,0.2);
    border-top-color: #ff8c32;
    border-radius: 50%;
    animation: spin 0.75s linear infinite;
    flex-shrink: 0;
}
@keyframes spin {
    to { transform: rotate(360deg); }
}

/*  Results header  */
.results-header {
    font-size: 1.4rem;
    font-weight: 800;
    color: #f0ebe0;
    letter-spacing: -0.02em;
    margin: 0 0 1.5rem;
}
.results-header .accent { color: #ff8c32; }

/*  Raw output  */
.raw-output {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    line-height: 1.75;
    color: #706a60;
    white-space: pre-wrap;
    word-break: break-word;
    padding: 0.5rem 0;
}

/*  Report & Critic Headers  */
.report-header {
    margin: 2.5rem 0 1.5rem;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid rgba(255,140,50,0.15);
}
.report-header-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #ff8c32;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.critic-header {
    margin: 3rem 0 1.5rem;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid rgba(72,199,116,0.15);
}
.critic-header-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #48c774;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

/*  Expander  */
.stExpander {
    background: rgba(255,255,255,0.025) !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 12px !important;
    margin-bottom: 0.75rem !important;
}

/* Force wrapping for alerts to prevent overflowing the window */
[data-testid="stAlert"] {
    white-space: normal !important;
    word-wrap: break-word !important;
    overflow-wrap: break-word !important;
}

/*  Download button  */
.stDownloadButton > button {
    background: rgba(255,140,50,0.08) !important;
    border: 1px solid rgba(255,140,50,0.25) !important;
    color: #ff8c32 !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    border-radius: 10px !important;
    padding: 0.6rem 1.5rem !important;
    transition: background 0.2s, border-color 0.2s !important;
}
.stDownloadButton > button:hover {
    background: rgba(255,140,50,0.14) !important;
    border-color: rgba(255,140,50,0.4) !important;
}

/*  Spinner  */
.stSpinner > div { color: #ff8c32 !important; }
</style>
""", unsafe_allow_html=True)

# Session state & Sidebar UI

for key in ("results", "running", "done", "error_step", "error_msg", "revision_count", "eval_msg"):
    if key not in st.session_state:
        if key == "results":
            st.session_state[key] = {}
        elif key in ["running", "done"]:
            st.session_state[key] = False
        elif key == "revision_count":
            st.session_state[key] = 0
        else:
            st.session_state[key] = None

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "topic_input" not in st.session_state:
    st.session_state.topic_input = ""

@st.dialog("Confirm Deletion")
def confirm_delete_dialog(sess_id):
    st.write("Are you sure you want to delete this session?")
    col1, col2 = st.columns(2)
    if col1.button("Yes, delete", use_container_width=True, type="primary"):
        delete_session(sess_id)
        if st.session_state.session_id == sess_id:
            st.session_state.session_id = str(uuid.uuid4())
            st.session_state.results = {}
            st.session_state.running = False
            st.session_state.done = False
            st.session_state.error_step = None
            st.session_state.error_msg = None
            st.session_state.topic_input = ""
            st.session_state.revision_count = 0
            st.session_state.eval_msg = None
        st.rerun()
    if col2.button("Cancel", use_container_width=True):
        st.rerun()

with st.sidebar:
    st.markdown('<div style="font-size: 1.2rem; font-weight: 800; margin-bottom: 1rem; color: #f5f0e8;">📚 Past Research</div>', unsafe_allow_html=True)
    
    if st.button("✨ New Research", use_container_width=True):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.results = {}
        st.session_state.running = False
        st.session_state.done = False
        st.session_state.error_step = None
        st.session_state.error_msg = None
        st.session_state.topic_input = ""
        st.session_state.revision_count = 0
        st.session_state.eval_msg = None
        st.rerun()
    
    st.markdown("<hr style='border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
    
    past_sessions = get_all_sessions()
    
    if not past_sessions:
        st.markdown('<div style="color: #8a8278; font-size: 0.8rem; text-align: center;">No history yet.</div>', unsafe_allow_html=True)
    else:
        def render_session_button(sess):
            c1, c2 = st.columns([5, 1])
            
            # Use truncated topic for the button label
            topic_label = sess["topic"] if sess["topic"] else "Untitled Research"
            if len(topic_label) > 28:
                topic_label = topic_label[:26] + "..."
                
            with c1:
                if st.button(f"{topic_label}", key=f"load_{sess['id']}", use_container_width=True):
                    st.session_state.session_id = sess["id"]
                    st.session_state.topic_input = sess["topic"]
                    st.session_state.results = sess["results"]
                    st.session_state.running = False
                    st.session_state.done = True
                    st.session_state.error_step = None
                    st.session_state.error_msg = None
                    st.session_state.revision_count = sess["results"].get("revision_count", 0)
                    st.session_state.eval_msg = sess["results"].get("eval_msg", None)
                    st.rerun()
            with c2:
                if st.button("🗑️", key=f"del_{sess['id']}", use_container_width=True):
                    confirm_delete_dialog(sess["id"])

        recent_sessions = past_sessions[:5]
        older_sessions = past_sessions[5:]

        for sess in recent_sessions:
            render_session_button(sess)
            
        if older_sessions:
            with st.expander("Your Past Researches 💬"):
                for sess in older_sessions:
                    render_session_button(sess)

PIPELINE_STEPS = ["search", "reader", "writer", "critic"]


# Helper: step card renderer

def render_step(num: str, icon: str, title: str, desc: str, state: str):
    card_cls   = {"running": "active", "done": "done", "error": "error"}.get(state, "")
    badge_cls  = {"running": "badge-run", "done": "badge-done", "waiting": "badge-wait", "error": "badge-error"}[state]
    badge_txt  = {"running": "● Running", "done": "✓ Done", "waiting": "Waiting", "error": "✖ Failed"}[state]
    st.markdown(f"""
    <div class="step-card {card_cls}">
        <div class="step-top">
            <span class="step-num">{num}</span>
            <span class="step-icon">{icon}</span>
            <span class="step-name">{title}</span>
            <span class="step-badge {badge_cls}">{badge_txt}</span>
        </div>
        <div class="step-desc">{desc}</div>
    </div>
    """, unsafe_allow_html=True)


def get_step_state(step: str) -> str:
    r = st.session_state.results
    if step in r:
        return "done"
    if st.session_state.get("error_step") == step:
        return "error"
    if st.session_state.running:
        for k in PIPELINE_STEPS:
            if k not in r:
                return "running" if k == step else "waiting"
    return "waiting"


# HERO — centered via a middle column

_, hero_col, _ = st.columns([1, 4, 1])
with hero_col:
    st.markdown("""
    <div class="hero-wrap">
        <div class="hero-badge">
            <span class="hero-badge-dot"></span>
            Multi-Agent AI System
        </div>
        <div class="hero-title">
            Research<span class="accent"> Mind</span><span class="dim">.</span>
        </div>
        <p class="hero-sub">
            Four specialized AI agents collaborate — searching the web, scraping content,
            writing a polished report, and critiquing it — so you get expert-level research instantly.
        </p>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<div class="hr-glow"></div>', unsafe_allow_html=True)



# LAYOUT — Input left | Pipeline right

col_left, col_gap, col_right = st.columns([5, 0.4, 4])

with col_left:
    topic = st.text_input(
        "Research Topic",
        placeholder="e.g. Quantum computing breakthroughs in 2025",
        key="topic_input",
        label_visibility="visible",
    )
    run_btn = st.button("💬 Run Research", type="primary", use_container_width=True)

    st.markdown("""
    <div class="example-topics">
        <span class="chip-label">Example Topics To Search ↓</span>
        <div class="chip-row">
            <span class="chip">LLM Agents 2025</span>
            <span class="chip">CRISPR Gene editing</span>
            <span class="chip">Fusion Energy progress</span>
            <span class="chip">Neuromorphic Chips</span>
            <span class="chip">Quantum Entanglement</span>
            <span class="chip">Dark matter & Gravitational waves</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Dynamically adjust spacer height to perfectly align with the right column
    # The right column is taller when the pipeline is running (due to the live status pill)
    is_running = st.session_state.get("running", False) and not st.session_state.get("done", False)
    spacer_height = 132 if is_running else 99
    st.markdown(f"<div style='height: {spacer_height}px;'></div>", unsafe_allow_html=True)
    
    if st.session_state.get("eval_msg"):
        msg = st.session_state.eval_msg
        if "passed" in msg:
            st.success(msg)
        else:
            st.warning(msg)

with col_right:
    st.markdown('<div class="pipeline-label">⬡ &nbsp;System Status</div>', unsafe_allow_html=True)
    status_box = st.empty()  # Placeholder for live status pill
    render_step("01", "🔍", "Search Agent",  "Queries the web for recent, reliable information", get_step_state("search"))
    render_step("02", "📃", "Reader Agent",  "Scrapes & extracts deep content from top sources",  get_step_state("reader"))
    render_step("03", "✍️", "Specialized Writer",  "Drafts a structured, professional research report",  get_step_state("writer"))
    render_step("04", "🧐", "Report Critic",  "Reviews accuracy, depth & quality of the report",   get_step_state("critic"))



# TRIGGER

if run_btn:
    if not topic.strip():
        st.warning("⚠️  Please enter a research topic first.")
    else:
        st.session_state.results = {}
        st.session_state.running = True
        st.session_state.done    = False
        st.session_state.error_step = None
        st.session_state.error_msg = None
        st.rerun()



# PIPELINE EXECUTION

if st.session_state.running and not st.session_state.done:
    results   = dict(st.session_state.results)
    topic_val = st.session_state.topic_input

    # We use the status_box defined earlier in col_right
    def show_status(msg: str):
        status_box.markdown(f"""
        <div class="live-status-wrap">
            <div class="live-status">
                <span class="live-spinner"></span>
                {msg}
            </div>
        </div>
        """, unsafe_allow_html=True)

    try:
        #  Step 1: Search  save → rerun so pipeline cards refresh
        if "search" not in results:
            show_status("Search Agent is searching the web…")
            search_agent = build_search_agent()
            sr = search_agent.invoke({
                "messages": [("user", f"Find recent, reliable and detailed information about: {topic_val}")]
            })
            results["search"] = sr["messages"][-1].content
            st.session_state.results = dict(results)
            save_session(st.session_state.session_id, topic_val, dict(results))
            # done to refresh the cards in real time
            st.rerun()   

        #  Step 2: Reader 
        if "reader" not in results:
            show_status("Reader Agent is scraping top sources…")
            reader_agent = build_reader_agent()
            rr = reader_agent.invoke({
                "messages": [("user",
                    f"Based on the following search results about '{topic_val}', "
                    f"pick the most relevant URL and scrape it for deeper content.\n\n"
                    f"Search Results:\n{results['search'][:1200]}"
                )]
            })
            results["reader"] = rr["messages"][-1].content
            st.session_state.results = dict(results)
            save_session(st.session_state.session_id, topic_val, dict(results))
            st.rerun()   

        #  Step 3: Writer 
        if "writer" not in results:
            show_status(f"Writer Chain is drafting the research report (Revision {st.session_state.revision_count}/3)...")
            research_combined = (
                f"SEARCH RESULTS:\n{results['search']}\n\n"
                f"DETAILED SCRAPED CONTENT:\n{results['reader']}"
            )
            feedback_text = ""
            if st.session_state.get("revision_count", 0) > 0 and "last_critic" in results:
                feedback_text = f"Previous Review Feedback to improve upon:\n{results['last_critic']}"
                
            results["writer"] = writer_chain.invoke({
                "topic":    topic_val,
                "research": research_combined,
                "feedback": feedback_text
            })
            st.session_state.results = dict(results)
            save_session(st.session_state.session_id, topic_val, dict(results))
            st.rerun()   

        #  Step 4: Critic 
        if "critic" not in results:
            show_status("Critic Chain is evaluating the report…")
            critic_result = critic_chain.invoke({
                "report": results["writer"]
            })
            
            import re
            match = re.search(r"Score:\s*([\d\.]+)", critic_result)
            score = 10
            if match:
                try:
                    score = float(match.group(1))
                except ValueError:
                    pass
            
            if score < 8 and st.session_state.get("revision_count", 0) < 3:
                st.session_state.revision_count = st.session_state.get("revision_count", 0) + 1
                results["last_critic"] = critic_result
                st.session_state.eval_msg = f"📝 The draft needs some improvements. Asking the writer to revise it based on feedback (Revision {st.session_state.revision_count} of 3)..."
                
                # Rerun writer
                del results["writer"]
                
                results["revision_count"] = st.session_state.revision_count
                results["eval_msg"] = st.session_state.eval_msg
                
                st.session_state.results = dict(results)
                save_session(st.session_state.session_id, topic_val, dict(results))
                st.rerun()
            else:
                results["critic"] = critic_result
                if score < 8:
                    st.session_state.eval_msg = "⚠️ We've reached the maximum number of revisions. Presenting the best version of the report!"
                else:
                    st.session_state.eval_msg = "✨ Great news! The report has passed our quality check and is ready for you."
                    
                results["revision_count"] = st.session_state.get("revision_count", 0)
                results["eval_msg"] = st.session_state.eval_msg
                
                st.session_state.results = dict(results)
                save_session(st.session_state.session_id, topic_val, dict(results))

        # All done
        st.session_state.running = False
        st.session_state.done    = True
        st.rerun()

    except Exception as e:
        error_msg = str(e)
        for k in PIPELINE_STEPS:
            if k not in results:
                st.session_state.error_step = k
                break
        
        if "429" in error_msg or "Rate limit" in error_msg or "rate_limit_exceeded" in error_msg:
            st.session_state.error_msg = "rate_limit"
        else:
            st.session_state.error_msg = error_msg
            
        st.session_state.running = False
        st.rerun()


# Result Display

if st.session_state.get("error_msg"):
    st.markdown('<div class="hr-glow"></div>', unsafe_allow_html=True)
    if st.session_state.error_msg == "rate_limit":
        st.error("⚠️ **AI is not available at the moment**\n\nThe provider is currently at capacity. Please wait a few moments and try again.")
    else:
        st.error("⚠️ **We encountered an unexpected issue while generating your report.**\n\nThis could be due to a temporary service interruption or a complex formatting problem in the background. Please try running your research again. If the issue persists, try modifying your research topic slightly.")
        with st.expander("Show detailed error log for troubleshooting"):
            st.code(st.session_state.error_msg, language="text")

r = st.session_state.results

if r:
    st.markdown('<div class="hr-glow"></div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="results-header">Research <span class="accent">Results</span></div>
    """, unsafe_allow_html=True)

    #  Raw outputs (Expanders) 
    if "search" in r:
        with st.expander("🔍  Search Agent — Raw output", expanded=False):
            st.markdown(f"```text\n{r['search']}\n```")

    if "reader" in r:
        with st.expander("📖  Reader Agent — Raw output", expanded=False):
            st.markdown(f"```text\n{r['reader']}\n```")

    #  Final report ─
    if "writer" in r:
        st.markdown(
            '<div class="report-header"><div class="report-header-label">📝 Final Research Report</div></div>',
            unsafe_allow_html=True,
        )
        st.markdown(r["writer"])

        dl_col1, dl_col2 = st.columns(2)
        with dl_col1:
            st.download_button(
                label="👇 Download Report (.md file)",
                data=r["writer"],
                file_name=f"Research_Report_{topic}.md",
                mime="text/markdown",
                use_container_width=True,
            )
        with dl_col2:
            import markdown
            from docx import Document
            from htmldocx import HtmlToDocx
            import io
            
            # Convert Markdown -> HTML -> DOCX
            try:
                html_content = markdown.markdown(r["writer"], extensions=['tables', 'fenced_code'])
                doc = Document()
                parser = HtmlToDocx()
                parser.add_html_to_document(html_content, doc)
                
                # Apply visible borders to all tables
                for table in doc.tables:
                    table.style = 'Table Grid'
                    
                docx_io = io.BytesIO()
                doc.save(docx_io)
                docx_bytes = docx_io.getvalue()
            except Exception as e:
                # Fallback to plain text if conversion fails
                docx_bytes = r["writer"].encode('utf-8')
            
            st.download_button(
                label="👇 Download Report (.docx file)",
                data=docx_bytes,
                file_name=f"Research_Report_{topic}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
            )

    #  Critic feedback ─
    if "critic" in r:
        st.markdown(
            '<div class="critic-header"><div class="critic-header-label">🧐 Critic Review &amp; Score</div></div>',
            unsafe_allow_html=True,
        )
        st.markdown(r["critic"])
