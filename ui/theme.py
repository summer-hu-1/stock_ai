"""
深色科技风 CSS — 统一 UI 主题
类 Bloomberg / TradingView 风格
"""
import streamlit as st

DARK_THEME_CSS = """
<style>
:root {
    --bg-0: #060914;
    --bg-1: #090f1d;
    --bg-2: #0d1528;
    --panel: rgba(13, 20, 36, 0.72);
    --panel-strong: rgba(14, 22, 40, 0.88);
    --panel-soft: rgba(255, 255, 255, 0.03);
    --line: rgba(111, 144, 255, 0.14);
    --line-strong: rgba(111, 144, 255, 0.24);
    --text-0: #f4f7ff;
    --text-1: #d9e4ff;
    --text-2: #9eafd2;
    --text-3: #6f7f9f;
    --green: #3ddc97;
    --yellow: #f7c948;
    --red: #ff6b6b;
    --blue: #54a8ff;
    --cyan: #2fe0ff;
    --orange: #ff944d;
    --shadow: 0 16px 40px rgba(0, 0, 0, 0.28);
    --shadow-soft: 0 10px 28px rgba(0, 0, 0, 0.18);
}

html, body, [class*="css"]  {
    -webkit-font-smoothing: antialiased;
    text-rendering: optimizeLegibility;
}

.stApp {
    background:
        radial-gradient(circle at 8% 0%, rgba(59, 130, 246, 0.16), transparent 26%),
        radial-gradient(circle at 92% 12%, rgba(255, 148, 77, 0.10), transparent 20%),
        radial-gradient(circle at 50% 100%, rgba(47, 224, 255, 0.05), transparent 30%),
        linear-gradient(180deg, var(--bg-0) 0%, var(--bg-1) 38%, var(--bg-2) 100%);
    color: var(--text-1);
}

[data-testid="stAppViewContainer"] {
    background: transparent;
}

[data-testid="stHeader"] {
    background: rgba(6, 9, 20, 0.62);
    backdrop-filter: blur(14px);
}

[data-testid="stAppViewBlockContainer"] {
    max-width: 1480px;
    padding-top: 1.2rem;
    padding-bottom: 3.25rem;
}

[data-testid="stMainBlockContainer"] > div {
    gap: 1.15rem;
}

h1, h2, h3, h4, h5, h6 {
    color: var(--text-0) !important;
    letter-spacing: -0.02em;
}

p, li, label, .stMarkdown, .stCaption {
    color: var(--text-1);
}

small, .stCaption, [data-testid="stCaptionContainer"] {
    color: var(--text-3) !important;
}

hr, .stDivider {
    border-color: rgba(118, 145, 220, 0.12) !important;
}

/* === Sidebar === */
[data-testid="stSidebar"] {
    background:
        linear-gradient(180deg, rgba(8, 12, 24, 0.92), rgba(9, 14, 28, 0.88));
    border-right: 1px solid rgba(98, 126, 206, 0.14);
    box-shadow: inset -1px 0 0 rgba(255, 255, 255, 0.03);
}

[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
    padding-top: 1rem;
    padding-bottom: 1.25rem;
}

[data-testid="stSidebar"] hr {
    border-color: rgba(118, 145, 220, 0.10) !important;
}

/* === Base cards === */
.market-card,
[data-testid="stMetric"],
[data-testid="stAlert"],
[data-testid="stExpander"],
[data-testid="stForm"],
[data-testid="stFileUploader"],
[data-testid="stDataFrame"],
div[data-baseweb="select"] > div,
div[data-baseweb="input"] > div,
.stDateInput > div > div,
.stTextArea textarea,
.stSlider,
.stMultiSelect [data-baseweb="select"] > div {
    background: linear-gradient(145deg, rgba(14, 22, 40, 0.84), rgba(10, 16, 30, 0.70));
    border: 1px solid var(--line);
    box-shadow:
        var(--shadow-soft),
        inset 0 1px 0 rgba(255, 255, 255, 0.03),
        inset 0 0 0 1px rgba(255, 255, 255, 0.01);
    backdrop-filter: blur(14px);
}

.market-card {
    border-radius: 18px;
    padding: 28px;
    margin: 14px 0;
    transition: transform 0.22s ease, box-shadow 0.22s ease, border-color 0.22s ease;
}

.market-card:hover,
[data-testid="stMetric"]:hover,
[data-testid="stAlert"]:hover,
[data-testid="stExpander"]:hover,
[data-testid="stDataFrame"]:hover {
    transform: translateY(-2px);
    border-color: var(--line-strong);
    box-shadow:
        0 18px 42px rgba(0, 0, 0, 0.28),
        0 0 0 1px rgba(88, 151, 255, 0.06),
        inset 0 1px 0 rgba(255, 255, 255, 0.03);
}

/* === Input system === */
.stSelectbox label,
.stDateInput label,
.stTextInput label,
.stTextArea label,
.stRadio label {
    color: var(--text-3) !important;
    font-size: 12px !important;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

div[data-baseweb="select"] > div,
div[data-baseweb="input"] > div,
.stDateInput > div > div,
.stTextArea textarea {
    min-height: 52px;
    border-radius: 18px !important;
    color: var(--text-0) !important;
    padding-left: 14px;
    transition: border-color 0.18s ease, box-shadow 0.18s ease, transform 0.18s ease;
}

.stTextArea textarea {
    min-height: 120px;
    padding-top: 14px;
    line-height: 1.6;
}

div[data-baseweb="select"] > div:hover,
div[data-baseweb="input"] > div:hover,
.stDateInput > div > div:hover,
.stTextArea textarea:hover {
    border-color: rgba(92, 164, 255, 0.26) !important;
}

div[data-baseweb="select"] > div:focus-within,
div[data-baseweb="input"] > div:focus-within,
.stDateInput > div > div:focus-within,
.stTextArea textarea:focus {
    border-color: rgba(92, 164, 255, 0.52) !important;
    box-shadow: 0 0 0 1px rgba(92, 164, 255, 0.18), 0 0 22px rgba(64, 151, 255, 0.14) !important;
    transform: translateY(-1px);
}

div[data-baseweb="select"] span,
div[data-baseweb="select"] input,
div[data-baseweb="input"] input,
.stDateInput input,
.stTextArea textarea {
    color: var(--text-0) !important;
}

div[data-baseweb="popover"] {
    border-radius: 18px !important;
    overflow: hidden;
    background: rgba(11, 16, 29, 0.94) !important;
    border: 1px solid var(--line) !important;
    box-shadow: 0 24px 48px rgba(0, 0, 0, 0.32) !important;
}

div[data-baseweb="menu"] {
    background: rgba(11, 16, 29, 0.96) !important;
}

div[data-baseweb="menu"] li {
    color: var(--text-1) !important;
}

div[data-baseweb="menu"] li:hover {
    background: rgba(84, 168, 255, 0.10) !important;
}

.stDateInput svg,
.stSelectbox svg {
    color: var(--text-3) !important;
}

/* === Radio chips === */
.stRadio [role="radiogroup"] {
    gap: 10px;
    padding: 6px;
    border-radius: 18px;
    border: 1px solid rgba(103, 127, 191, 0.12);
    background: rgba(8, 13, 24, 0.48);
}

.stRadio [role="radiogroup"] label {
    border-radius: 14px !important;
    padding: 8px 14px !important;
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid transparent;
    transition: all 0.18s ease;
    min-height: 42px;
}

.stRadio [role="radiogroup"] label:hover {
    background: rgba(84, 168, 255, 0.08);
    border-color: rgba(84, 168, 255, 0.20);
}

.stRadio [role="radiogroup"] label:has(input:checked) {
    background: linear-gradient(135deg, rgba(30, 86, 255, 0.24), rgba(0, 212, 255, 0.18));
    border-color: rgba(84, 168, 255, 0.35);
    box-shadow: inset 0 0 20px rgba(50, 122, 255, 0.08);
}

.stRadio [role="radiogroup"] label p {
    color: var(--text-1) !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    text-transform: none !important;
    letter-spacing: 0 !important;
}

/* === Buttons === */
div.stButton > button,
.stDownloadButton > button {
    min-height: 48px;
    border-radius: 16px;
    padding: 0.7rem 1rem;
    border: 1px solid rgba(97, 122, 189, 0.18);
    background: linear-gradient(145deg, rgba(16, 23, 42, 0.86), rgba(10, 15, 29, 0.86));
    color: var(--text-0);
    box-shadow:
        var(--shadow-soft),
        inset 0 1px 0 rgba(255, 255, 255, 0.03);
}

.stDownloadButton > button:hover,
div.stButton > button:hover {
    border-color: rgba(88, 151, 255, 0.32);
}

/* === Metrics === */
[data-testid="stMetric"] {
    border-radius: 18px;
    padding: 18px 18px 16px;
    min-height: 128px;
}

[data-testid="stMetricLabel"] {
    color: var(--text-3) !important;
    text-transform: uppercase;
    letter-spacing: 0.10em;
    font-size: 11px !important;
    font-weight: 700 !important;
}

[data-testid="stMetricValue"] {
    color: var(--text-0) !important;
    font-size: 30px !important;
    line-height: 1.1 !important;
    font-weight: 800 !important;
    letter-spacing: -0.03em;
}

[data-testid="stMetricDelta"] {
    font-size: 12px !important;
    font-weight: 700 !important;
}

[data-testid="stMetricDelta"] svg {
    width: 0.8rem;
    height: 0.8rem;
}

/* === Alerts === */
[data-testid="stAlert"] {
    border-radius: 18px;
    padding: 14px 16px;
}

[data-testid="stAlert"][kind="success"] {
    border-color: rgba(61, 220, 151, 0.24);
    box-shadow: inset 0 0 18px rgba(61, 220, 151, 0.06);
}

[data-testid="stAlert"][kind="warning"] {
    border-color: rgba(247, 201, 72, 0.24);
    box-shadow: inset 0 0 18px rgba(247, 201, 72, 0.05);
}

[data-testid="stAlert"][kind="error"] {
    border-color: rgba(255, 107, 107, 0.24);
    box-shadow: inset 0 0 18px rgba(255, 107, 107, 0.05);
}

/* === Expander === */
[data-testid="stExpander"] {
    border-radius: 18px;
    overflow: hidden;
}

[data-testid="stExpander"] details summary {
    padding: 0.35rem 0.45rem;
}

[data-testid="stExpander"] details summary p {
    color: var(--text-1) !important;
    font-weight: 700 !important;
}

[data-testid="stExpanderDetails"] {
    padding-top: 0.4rem;
}

/* === Tables / JSON / code === */
[data-testid="stDataFrame"] {
    border-radius: 18px;
    overflow: hidden;
    padding: 10px;
}

.stJson,
.stCodeBlock,
pre {
    border-radius: 18px !important;
    border: 1px solid var(--line) !important;
    background: rgba(8, 14, 26, 0.84) !important;
}

code {
    color: #9ed0ff !important;
}

/* === Caption / title / empty === */
.section-title {
    display: inline-block;
    font-size: 12px;
    font-weight: 700;
    color: var(--text-3);
    letter-spacing: 0.14em;
    text-transform: uppercase;
    margin-bottom: 10px;
}

.empty-state {
    text-align: center;
    padding: 64px 24px;
    color: var(--text-3);
    border: 1px dashed rgba(116, 143, 214, 0.12);
    border-radius: 18px;
    background: rgba(11, 17, 31, 0.45);
}

/* === Helpers === */
.state-tag {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px 14px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.04em;
}
.state-tag.green { background: rgba(61, 220, 151, 0.10); color: var(--green); border: 1px solid rgba(61, 220, 151, 0.20); }
.state-tag.cyan  { background: rgba(47, 224, 255, 0.10); color: var(--cyan); border: 1px solid rgba(47, 224, 255, 0.18); }
.state-tag.yellow{ background: rgba(247, 201, 72, 0.10); color: var(--yellow); border: 1px solid rgba(247, 201, 72, 0.18); }
.state-tag.red   { background: rgba(255, 107, 107, 0.10); color: var(--red); border: 1px solid rgba(255, 107, 107, 0.18); }
.state-tag.blue  { background: rgba(84, 168, 255, 0.10); color: var(--blue); border: 1px solid rgba(84, 168, 255, 0.18); }

.strength-bar {
    height: 8px;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.06);
    overflow: hidden;
}

.strength-bar-fill {
    height: 8px;
    border-radius: 999px;
    transition: width 0.5s ease;
    box-shadow: 0 0 18px rgba(84, 168, 255, 0.18);
}

.timeline-line {
    border-left: 1px solid rgba(108, 133, 201, 0.18);
    padding-left: 22px;
    margin-left: 8px;
}

.divider-glow {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(92, 145, 255, 0.28), transparent);
    margin: 28px 0;
}

.big-number {
    font-size: 52px;
    font-weight: 900;
    letter-spacing: -0.05em;
    line-height: 1;
    color: var(--text-0);
}

/* === Existing terminal blocks kept and refined === */
.terminal-hero {
    background: linear-gradient(160deg, rgba(8, 12, 22, 0.96) 0%, rgba(10, 15, 28, 0.88) 42%, rgba(8, 13, 24, 0.84) 100%);
    border: 1px solid rgba(109, 138, 215, 0.14);
    border-radius: 22px;
    padding: 38px 42px;
    margin: 8px 0 24px 0;
    position: relative;
    overflow: hidden;
    box-shadow:
        0 20px 46px rgba(0, 0, 0, 0.32),
        inset 0 1px 0 rgba(255, 255, 255, 0.03);
    backdrop-filter: blur(16px);
}

.terminal-hero::before {
    content: "";
    position: absolute;
    inset: 0;
    background:
        radial-gradient(ellipse at 18% 12%, rgba(47, 224, 255, 0.08) 0%, transparent 35%),
        radial-gradient(ellipse at 80% 14%, rgba(255, 148, 77, 0.08) 0%, transparent 28%);
    pointer-events: none;
}

.terminal-hero::after {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.08), transparent);
}

.terminal-state-label,
.terminal-metric-label,
.terminal-script-label,
.terminal-section-header {
    color: var(--text-3);
}

.terminal-state-value {
    color: var(--text-0);
    text-shadow: 0 0 22px rgba(84, 168, 255, 0.10);
}

.terminal-metric-col {
    padding: 0 24px;
    border-left: 1px solid rgba(106, 134, 201, 0.12);
}

.terminal-metric-col:first-child {
    border-left: none;
    padding-left: 0;
}

.terminal-metric-value {
    color: var(--text-1);
}

.terminal-risk-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 7px 16px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.08em;
}

.terminal-risk-badge.low    { background: rgba(61, 220, 151, 0.10); color: var(--green); border: 1px solid rgba(61, 220, 151, 0.20); }
.terminal-risk-badge.medium { background: rgba(247, 201, 72, 0.10); color: var(--yellow); border: 1px solid rgba(247, 201, 72, 0.20); }
.terminal-risk-badge.high   { background: rgba(255, 107, 107, 0.10); color: var(--red); border: 1px solid rgba(255, 107, 107, 0.20); }

.terminal-script-box {
    margin-top: 26px;
    padding: 16px 20px;
    background: rgba(255, 255, 255, 0.025);
    border-radius: 16px;
    border-left: 3px solid;
    font-size: 14px;
    color: var(--text-2);
    line-height: 1.75;
}

.terminal-sector-card {
    background: linear-gradient(145deg, rgba(12, 18, 32, 0.84), rgba(9, 14, 26, 0.72));
    border: 1px solid rgba(109, 138, 215, 0.12);
    border-radius: 18px;
    padding: 18px 22px;
    transition: border-color 0.22s ease, transform 0.22s ease, box-shadow 0.22s ease;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.02);
}

.terminal-sector-card:hover {
    border-color: rgba(109, 160, 255, 0.26);
    transform: translateY(-2px);
    box-shadow: 0 16px 36px rgba(0, 0, 0, 0.24);
}

.terminal-pulse {
    display: inline-block;
    width: 7px;
    height: 7px;
    border-radius: 50%;
    margin-right: 6px;
    animation: terminal-pulse-anim 2s ease-in-out infinite;
}

@keyframes terminal-pulse-anim {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.35; transform: scale(0.92); }
}

.terminal-danger-row {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 14px;
    margin-top: 8px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 700;
}

/* === Homepage Market Cockpit === */
.market-cockpit {
    position: relative;
    overflow: hidden;
    border-radius: 28px;
    padding: 30px 30px 24px;
    margin: 8px 0 28px 0;
    border: 1px solid rgba(98, 132, 214, 0.16);
    background:
        radial-gradient(circle at 12% 18%, rgba(255,255,255,0.04), transparent 20%),
        linear-gradient(145deg, rgba(9, 14, 27, 0.97), rgba(10, 16, 31, 0.90) 48%, rgba(8, 12, 24, 0.96));
    box-shadow:
        0 24px 54px rgba(0, 0, 0, 0.34),
        inset 0 1px 0 rgba(255, 255, 255, 0.04),
        inset 0 0 0 1px rgba(255, 255, 255, 0.01);
    backdrop-filter: blur(18px);
}

.market-cockpit::before {
    content: "";
    position: absolute;
    inset: 0;
    background:
        radial-gradient(circle at 0% 0%, rgba(var(--tone-rgb), 0.24), transparent 22%),
        radial-gradient(circle at 92% 12%, rgba(255, 148, 77, 0.10), transparent 18%);
    pointer-events: none;
}

.market-cockpit::after {
    content: "";
    position: absolute;
    inset: 1px;
    border-radius: 27px;
    border: 1px solid rgba(var(--tone-rgb), 0.16);
    box-shadow:
        0 0 0 1px rgba(var(--tone-rgb), 0.05),
        0 0 48px rgba(var(--tone-rgb), 0.10),
        inset 0 0 48px rgba(var(--tone-rgb), 0.05);
    pointer-events: none;
}

.market-cockpit.tone-green { --tone-rgb: 61, 220, 151; }
.market-cockpit.tone-yellow { --tone-rgb: 247, 201, 72; }
.market-cockpit.tone-red { --tone-rgb: 255, 107, 107; }
.market-cockpit.tone-blue { --tone-rgb: 84, 168, 255; }

.market-cockpit-grid {
    position: relative;
    z-index: 1;
    display: grid;
    grid-template-columns: minmax(320px, 1.35fr) minmax(340px, 1fr);
    gap: 22px;
    align-items: stretch;
}

.market-cockpit-left {
    display: flex;
    flex-direction: column;
    gap: 18px;
}

.market-cockpit-kicker {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    font-size: 11px;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: var(--text-3);
}

.market-cockpit-dot {
    width: 9px;
    height: 9px;
    border-radius: 50%;
    background: rgb(var(--tone-rgb));
    box-shadow: 0 0 16px rgba(var(--tone-rgb), 0.85);
    animation: terminal-pulse-anim 2s ease-in-out infinite;
}

.market-cockpit-title {
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    gap: 12px;
    flex-wrap: wrap;
}

.market-cockpit-state {
    font-size: 56px;
    line-height: 0.95;
    font-weight: 900;
    letter-spacing: -0.05em;
    color: rgb(var(--tone-rgb));
    text-shadow: 0 0 28px rgba(var(--tone-rgb), 0.20);
    margin: 6px 0 0;
}

.market-cockpit-action {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 10px 14px;
    border-radius: 999px;
    border: 1px solid rgba(var(--tone-rgb), 0.24);
    background: rgba(var(--tone-rgb), 0.10);
    color: #f4f7ff;
    font-size: 13px;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.market-cockpit-desc {
    max-width: 680px;
    color: var(--text-2);
    font-size: 15px;
    line-height: 1.8;
}

.market-cockpit-script {
    border-radius: 20px;
    padding: 18px 20px;
    background: linear-gradient(145deg, rgba(255, 255, 255, 0.045), rgba(255, 255, 255, 0.02));
    border: 1px solid rgba(var(--tone-rgb), 0.14);
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.03);
}

.market-cockpit-script-label {
    font-size: 11px;
    letter-spacing: 0.20em;
    text-transform: uppercase;
    color: var(--text-3);
    margin-bottom: 10px;
}

.market-cockpit-script-text {
    font-size: 17px;
    line-height: 1.85;
    color: var(--text-0);
    font-weight: 600;
}

.market-cockpit-panels {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 14px;
}

.market-cockpit-panel {
    min-height: 122px;
    border-radius: 20px;
    padding: 18px 18px 16px;
    background: linear-gradient(145deg, rgba(13, 20, 37, 0.86), rgba(10, 16, 30, 0.72));
    border: 1px solid rgba(103, 132, 208, 0.14);
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.03);
}

.market-cockpit-panel-label {
    font-size: 11px;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: var(--text-3);
    margin-bottom: 10px;
}

.market-cockpit-panel-value {
    font-size: 26px;
    line-height: 1.2;
    font-weight: 800;
    color: var(--text-0);
    letter-spacing: -0.03em;
}

.market-cockpit-panel-sub {
    margin-top: 8px;
    color: var(--text-2);
    font-size: 13px;
    line-height: 1.65;
}

.market-cockpit-panel-value.tone {
    color: rgb(var(--tone-rgb));
    text-shadow: 0 0 22px rgba(var(--tone-rgb), 0.16);
}

.market-cockpit-risk {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 8px 14px;
    border-radius: 999px;
    font-size: 13px;
    font-weight: 800;
    width: fit-content;
}

.market-cockpit-risk.low {
    color: var(--green);
    background: rgba(61, 220, 151, 0.10);
    border: 1px solid rgba(61, 220, 151, 0.20);
}

.market-cockpit-risk.medium {
    color: var(--yellow);
    background: rgba(247, 201, 72, 0.10);
    border: 1px solid rgba(247, 201, 72, 0.20);
}

.market-cockpit-risk.high {
    color: var(--red);
    background: rgba(255, 107, 107, 0.10);
    border: 1px solid rgba(255, 107, 107, 0.20);
}

.market-cockpit-signals {
    position: relative;
    z-index: 1;
    margin-top: 18px;
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
}

.market-cockpit-signal {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(108, 133, 201, 0.14);
    color: var(--text-2);
    font-size: 12px;
    font-weight: 600;
}

.market-cockpit-signal strong {
    color: var(--text-0);
}

.market-cockpit-danger-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-top: 4px;
}

.market-cockpit-danger {
    padding: 10px 12px;
    border-radius: 14px;
    font-size: 13px;
    line-height: 1.6;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(108, 133, 201, 0.12);
    color: var(--text-2);
}

.market-cockpit-danger strong {
    color: var(--text-0);
}

@media (max-width: 1080px) {
    .market-cockpit-grid {
        grid-template-columns: 1fr;
    }

    .market-cockpit-state {
        font-size: 44px;
    }

    .market-cockpit-panels {
        grid-template-columns: 1fr;
    }
}
</style>
"""

def inject_theme():
    """注入深色主题 CSS"""
    st.markdown(DARK_THEME_CSS, unsafe_allow_html=True)


def market_card(content: str, key: str = None):
    """包装内容为 market-card 容器"""
    return f'<div class="market-card">{content}</div>'


def state_tag(label: str, color: str) -> str:
    """生成状态标签 HTML"""
    return f'<span class="state-tag {color}">{label}</span>'


def strength_bar(value: int, max_val: int = 100, color: str = "#4ecdc4") -> str:
    """生成强度进度条 HTML"""
    pct = min(100, max(0, value / max_val * 100))
    return f"""
    <div class="strength-bar">
        <div class="strength-bar-fill" style="width:{pct}%; background:{color};"></div>
    </div>
    """


# 情绪周期 → 颜色映射
CYCLE_COLORS = {
    "冰点期": "blue",
    "试错期": "cyan",
    "发酵期": "cyan",
    "主升期": "green",
    "高潮期": "yellow",
    "分歧期": "yellow",
    "退潮期": "red",
    "修复期": "cyan",
}

CYCLE_HEX = {
    "冰点期": "#7b9fd4",
    "试错期": "#00d4ff",
    "发酵期": "#00d4ff",
    "主升期": "#4ecdc4",
    "高潮期": "#f5a623",
    "分歧期": "#f5a623",
    "退潮期": "#e74c3c",
    "修复期": "#00d4ff",
}

RISK_COLORS = {"low": "green", "medium": "yellow", "high": "red", "unknown": "blue"}
RISK_HEX = {"low": "#4ecdc4", "medium": "#f5a623", "high": "#e74c3c", "unknown": "#7b9fd4"}
