# vtm_dashboard.py  ← TypeError 수정판
import streamlit as st
import sqlite3
import pandas as pd
import io
from datetime import datetime, date, timedelta, timezone
import calendar
import time
import re

st.set_page_config(
    page_title="(주) 브이티엠 운영 대시보드",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

KST = timezone(timedelta(hours=9))

def now_kst() -> datetime:
    return datetime.now(tz=KST)

def today_str() -> str:
    return now_kst().strftime("%Y-%m-%d")

def now_str() -> str:
    return now_kst().strftime("%Y-%m-%d %H:%M:%S")

DB_PATH = "vtm_v3.db"

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS employees(
        id TEXT PRIMARY KEY, name TEXT NOT NULL, role TEXT NOT NULL,
        is_admin INTEGER DEFAULT 0, password TEXT DEFAULT '',
        active INTEGER DEFAULT 1, created_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS attendance(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        emp_id TEXT, emp_name TEXT, work_date TEXT,
        checkin TEXT, checkout TEXT,
        att_type TEXT DEFAULT '정상출근', created_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS reports(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        emp_id TEXT, emp_name TEXT, work_date TEXT,
        am_tasks TEXT, am_priority TEXT, am_notes TEXT,
        pm_done TEXT, pm_progress INTEGER DEFAULT 0,
        pm_tomorrow TEXT, pm_remarks TEXT,
        drive_link TEXT, result_link TEXT,
        status TEXT DEFAULT '대기중',
        admin_comment TEXT DEFAULT '',
        submitted_at TEXT, approved_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT, actor TEXT, target TEXT,
        detail TEXT, created_at TEXT)""")
    c.execute("SELECT COUNT(*) FROM employees WHERE id='admin_park'")
    if c.fetchone()[0] == 0:
        _now = now_str()
        c.executemany("INSERT INTO employees VALUES(?,?,?,?,?,?,?)",[
            ('admin_park','박동진 본부장','본부장',1,'5638',1,_now),
            ('emp_kim','김소원 대리','대리',0,'',1,_now),
            ('emp_seo','서아영 디자이너','디자이너',0,'',1,_now),
            ('emp_ahn','안효민 디렉터','디렉터',0,'',1,_now),
        ])
    conn.commit(); conn.close()

init_db()

def wlog(action, actor, target="", detail=""):
    try:
        conn = get_conn()
        conn.execute(
            "INSERT INTO logs(action,actor,target,detail,created_at) VALUES(?,?,?,?,?)",
            (action, actor, target, detail, now_str())
        )
        conn.commit(); conn.close()
    except:
        pass

def get_employees(active_only=True):
    conn = get_conn()
    q = ("SELECT * FROM employees WHERE active=1 ORDER BY is_admin DESC,name"
         if active_only else
         "SELECT * FROM employees ORDER BY is_admin DESC,name")
    df = pd.read_sql(q, conn); conn.close(); return df

def to_excel(dfs):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        for s, d in dfs.items():
            d.to_excel(w, sheet_name=s[:31], index=False)
    return buf.getvalue()

def safe_str(val):
    """NaN / None / 빈문자열이면 None 반환, 나머지는 str 반환"""
    if val is None:
        return None
    try:
        if pd.isna(val):
            return None
    except (TypeError, ValueError):
        pass
    s = str(val).strip()
    return s if s else None

for k, v in {"logged_in": False, "user_id": None, "user_name": None,
             "is_admin": False, "page": "home"}.items():
    if k not in st.session_state:
        st.session_state[k] = v

def logo_svg(size=72):
    return f"""<svg width="{size}" height="{size}" viewBox="0 0 80 80"
        xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="lg{size}" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style="stop-color:#00D4AA"/>
          <stop offset="100%" style="stop-color:#0EA5E9"/>
        </linearGradient>
      </defs>
      <circle cx="40" cy="40" r="38" fill="none"
              stroke="url(#lg{size})" stroke-width="2.2"/>
      <polygon points="40,10 66,25 66,55 40,70 14,55 14,25"
               fill="url(#lg{size})" opacity="0.10"/>
      <polygon points="40,16 62,29 62,51 40,64 18,51 18,29"
               fill="none" stroke="url(#lg{size})" stroke-width="1.4" opacity="0.6"/>
      <text x="40" y="48" text-anchor="middle"
            font-family="Inter,Arial,sans-serif" font-weight="900"
            font-size="21" fill="url(#lg{size})">VTM</text>
    </svg>"""

def inject_all():
    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');

html,body,.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"]>section,
[data-testid="stMain"],
[data-testid="stMainBlockContainer"],
.main,.main>div,block-container{{
    background:#0F172A !important;
    font-family:'Noto Sans KR',sans-serif !important;
}}

[data-testid="stSidebarCollapseButton"],
[data-testid="collapsedControl"],
button[kind="header"],
.st-emotion-cache-ztfqz8,
section[data-testid="stSidebar"] > div > div:first-child > div > div > button {{
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
    pointer-events: none !important;
    width: 0 !important;
    height: 0 !important;
}}
[data-testid="stSidebar"] {{
    background: linear-gradient(180deg,#0B1120 0%,#0F172A 100%) !important;
    border-right: 2px solid #1E3A5F !important;
    min-width: 235px !important;
    max-width: 255px !important;
    width: 245px !important;
    transform: none !important;
    visibility: visible !important;
    display: block !important;
    position: relative !important;
    flex-shrink: 0 !important;
    transition: none !important;
}}
[data-testid="stSidebar"][aria-expanded="false"] {{
    transform: none !important;
    margin-left: 0 !important;
    min-width: 235px !important;
    width: 245px !important;
    visibility: visible !important;
}}
[data-testid="stSidebar"] * {{ color: #F1F5F9 !important; }}
[data-testid="stMain"] {{ margin-left: 0 !important; padding-left: 8px !important; }}

[data-testid="stSidebar"] .stButton > button {{
    background: linear-gradient(135deg,#F6D365 0%,#D4AF37 55%,#B8860B 100%) !important;
    color: #000000 !important;
    font-weight: 900 !important;
    font-size: 0.86rem !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 10px 14px !important;
    width: 100% !important;
    cursor: pointer !important;
    box-shadow: 0 3px 10px rgba(212,175,55,0.30) !important;
    transition: transform 0.15s, box-shadow 0.15s !important;
    letter-spacing: 0.01em !important;
    text-align: left !important;
}}
[data-testid="stSidebar"] .stButton > button:hover {{
    background: linear-gradient(135deg,#FFE57A 0%,#F6D365 55%,#D4AF37 100%) !important;
    transform: translateX(3px) !important;
    box-shadow: 0 5px 16px rgba(212,175,55,0.50) !important;
}}
[data-testid="stSidebar"] .stButton > button *,
[data-testid="stSidebar"] .stButton > button p,
[data-testid="stSidebar"] .stButton > button span {{
    color: #000000 !important;
    font-weight: 900 !important;
}}

.stButton>button {{
    background: linear-gradient(135deg,#F6D365 0%,#D4AF37 55%,#B8860B 100%) !important;
    color: #000000 !important;
    font-weight: 900 !important;
    font-size: 0.92rem !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 10px 18px !important;
    width: 100% !important;
    cursor: pointer !important;
    box-shadow: 0 4px 14px rgba(212,175,55,0.38) !important;
    transition: transform 0.15s, box-shadow 0.15s !important;
    letter-spacing: 0.01em !important;
}}
.stButton>button:hover {{
    background: linear-gradient(135deg,#FFE57A 0%,#F6D365 55%,#D4AF37 100%) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 22px rgba(212,175,55,0.55) !important;
    color: #000000 !important;
}}
.stButton>button *,.stButton>button p,.stButton>button span {{
    color: #000000 !important;
    font-weight: 900 !important;
}}

.vtm-card {{
    background: #FFFFFF;
    border-radius: 14px;
    padding: 18px 22px;
    margin: 8px 0;
    box-shadow: 0 4px 18px rgba(0,0,0,0.25);
    border: 1px solid #E2E8F0;
    position: relative; z-index: 1;
}}
.vtm-card * {{ color: #1E293B !important; }}
.vtm-card h3 {{ font-weight: 900 !important; margin: 0 0 8px !important; font-size: 1rem !important; }}
.vtm-card p  {{ font-weight: 600 !important; margin: 3px 0 !important; font-size: 0.9rem !important; }}

.met-card {{
    background: linear-gradient(135deg,#1E293B 0%,#0F172A 100%);
    border: 1px solid #D4AF37;
    border-radius: 14px;
    padding: 18px 12px;
    text-align: center;
    position: relative; z-index: 1;
}}
.met-val {{ font-size:1.9rem; font-weight:900; color:#D4AF37 !important; display:block; }}
.met-lbl {{ font-size:0.78rem; color:#94A3B8 !important; font-weight:700; display:block; margin-top:4px; }}

.topbar {{
    background: linear-gradient(90deg,#1E293B 0%,#0F172A 100%);
    border-bottom: 2px solid #D4AF37;
    padding: 12px 18px;
    border-radius: 12px;
    margin-bottom: 14px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
    position: relative; z-index: 1;
}}
.tb-title {{ color:#D4AF37 !important; font-size:1.05rem; font-weight:900; }}
.tb-info  {{ color:#94A3B8 !important; font-size:0.8rem; font-weight:700; }}

.stTextInput>div>div>input,
.stNumberInput>div>div>input {{
    background: #1E293B !important; color: #F1F5F9 !important;
    border: 1px solid #334155 !important; border-radius: 8px !important; font-weight: 700 !important;
}}
.stTextArea textarea {{
    background: #1E293B !important; color: #F1F5F9 !important;
    border: 1px solid #334155 !important; border-radius: 8px !important; font-weight: 600 !important;
}}
.stSelectbox>div>div {{
    background: #1E293B !important; border: 1px solid #334155 !important; border-radius: 8px !important;
}}
.stSelectbox * {{ color: #F1F5F9 !important; font-weight: 700 !important; }}
.stDateInput>div>div>input {{
    background: #1E293B !important; color: #F1F5F9 !important;
    border: 1px solid #334155 !important; border-radius: 8px !important;
}}
.stMultiSelect>div>div {{
    background: #1E293B !important; border: 1px solid #334155 !important; border-radius: 8px !important;
}}
.stMultiSelect * {{ color: #F1F5F9 !important; font-weight: 700 !important; }}

label,.stTextInput label,.stSelectbox label,.stTextArea label,
.stSlider label,.stNumberInput label,.stDateInput label,.stMultiSelect label {{
    color: #94A3B8 !important; font-weight: 700 !important;
}}

[data-testid="stDataFrame"] * {{ color: #F1F5F9 !important; }}

.cal-tbl {{ width:100%; border-collapse:collapse; margin-top:8px; }}
.cal-tbl th {{
    background:#1E293B; color:#D4AF37 !important;
    padding:7px 3px; font-weight:900; text-align:center;
    border:1px solid #334155; font-size:0.82rem;
}}
.cal-tbl th.wk {{ background:#0F172A; color:#475569 !important; font-size:0.55rem; width:3%; }}
.cal-tbl td {{
    background:#1E293B; color:#F1F5F9 !important;
    padding:5px 3px; text-align:center;
    border:1px solid #334155; vertical-align:top; font-size:0.78rem;
}}
.cal-tbl td.wk {{ background:#0B1120; color:#374151 !important; width:3%; font-size:0.6rem; }}
.cal-tbl td.tday {{ background:#1E3A5F; border:2px solid #D4AF37 !important; }}
.tg-att {{ display:block; background:#10B981; color:#fff!important; border-radius:3px; padding:1px 2px; font-size:0.6rem; margin:1px 0; font-weight:700; }}
.tg-rep {{ display:block; background:#3B82F6; color:#fff!important; border-radius:3px; padding:1px 2px; font-size:0.6rem; margin:1px 0; font-weight:700; }}
.tg-ok  {{ display:block; background:#10B981; color:#fff!important; border-radius:3px; padding:1px 2px; font-size:0.6rem; margin:1px 0; font-weight:700; }}
.tg-no  {{ display:block; background:#374151; color:#9CA3AF!important; border-radius:3px; padding:1px 2px; font-size:0.6rem; margin:1px 0; }}

@media (max-width:768px) {{
    [data-testid="stSidebar"] {{
        min-width: 100% !important;
        max-width: 100% !important;
        width: 100% !important;
    }}
    .topbar {{ flex-direction:column; align-items:flex-start; }}
    .met-val {{ font-size:1.4rem; }}
    .vtm-card {{ padding:12px 14px; }}
    [data-testid="stMainBlockContainer"] {{ padding:8px !important; }}
    .cal-tbl th,.cal-tbl td {{ font-size:0.6rem; padding:3px 1px; }}
}}

#MainMenu, footer, header {{ visibility:hidden !important; }}
[data-testid="stDecoration"]  {{ display:none !important; }}

::-webkit-scrollbar {{ width:5px; height:5px; }}
::-webkit-scrollbar-track {{ background:#0F172A; }}
::-webkit-scrollbar-thumb {{ background:#D4AF37; border-radius:3px; }}

.sidebar-home-btn .stButton > button {{
    background: linear-gradient(135deg,#05F080 0%,#10B981 50%,#059669 100%) !important;
    color: #FFFFFF !important;
    font-weight: 900 !important;
    font-size: 0.90rem !important;
    border: 2px solid rgba(16,185,129,0.55) !important;
    border-radius: 14px !important;
    padding: 11px 14px !important;
    width: 100% !important;
    cursor: pointer !important;
    box-shadow:
        0 0 14px rgba(5,240,128,0.35),
        0 4px 14px rgba(16,185,129,0.40) !important;
    letter-spacing: 0.02em !important;
    text-align: left !important;
    transition: transform 0.15s, box-shadow 0.15s !important;
    position: relative !important;
    overflow: hidden !important;
}}
.sidebar-home-btn .stButton > button::before {{
    content: "";
    position: absolute;
    top: -40%; left: -40%;
    width: 60%; height: 180%;
    background: linear-gradient(120deg,
        rgba(255,255,255,0.00) 0%,
        rgba(255,255,255,0.22) 50%,
        rgba(255,255,255,0.00) 100%);
    transform: skewX(-20deg);
    pointer-events: none;
}}
.sidebar-home-btn .stButton > button:hover {{
    background: linear-gradient(135deg,#34FFA0 0%,#10B981 50%,#047857 100%) !important;
    transform: translateX(4px) scale(1.02) !important;
    box-shadow:
        0 0 22px rgba(5,240,128,0.60),
        0 6px 20px rgba(16,185,129,0.55) !important;
}}
.sidebar-home-btn .stButton > button *,
.sidebar-home-btn .stButton > button p,
.sidebar-home-btn .stButton > button span {{
    color: #FFFFFF !important;
    font-weight: 900 !important;
}}
.home-active-badge {{
    background: linear-gradient(135deg,#05F080,#10B981);
    border-radius: 13px;
    padding: 10px 13px;
    margin: 3px 4px;
    display: flex;
    align-items: center;
    gap: 8px;
    box-shadow: 0 0 16px rgba(5,240,128,0.40), 0 4px 12px rgba(16,185,129,0.35);
    border: 2px solid rgba(5,240,128,0.50);
    position: relative;
    overflow: hidden;
}}
.home-active-badge::before {{
    content:"";
    position:absolute;
    top:-30%; left:-20%;
    width:55%; height:160%;
    background:linear-gradient(120deg,
        rgba(255,255,255,0.00) 0%,
        rgba(255,255,255,0.18) 50%,
        rgba(255,255,255,0.00) 100%);
    transform:skewX(-20deg);
    pointer-events:none;
}}
.home-active-badge span {{
    color: #003322 !important;
    font-weight: 900 !important;
    font-size: 0.88rem !important;
    letter-spacing: 0.02em;
}}
.home-active-dot {{
    width: 8px; height: 8px;
    background: #fff;
    border-radius: 50%;
    box-shadow: 0 0 6px rgba(255,255,255,0.9);
    flex-shrink: 0;
}}

.sidebar-logout-btn .stButton > button {{
    background: linear-gradient(135deg,#FF6B6B,#EF4444) !important;
    color: #fff !important;
    font-weight: 900 !important;
    border-radius: 10px !important;
    border: none !important;
    box-shadow: 0 3px 12px rgba(239,68,68,0.40) !important;
}}
.sidebar-logout-btn .stButton > button * {{ color: #fff !important; }}
.sidebar-logout-btn .stButton > button:hover {{
    background: linear-gradient(135deg,#FF8A8A,#DC2626) !important;
    transform: translateX(3px) !important;
}}

.kst-badge {{
    display:inline-block;
    background:rgba(212,175,55,0.15);
    border:1px solid rgba(212,175,55,0.4);
    border-radius:6px;
    padding:2px 7px;
    font-size:0.7rem;
    font-weight:700;
    color:#D4AF37 !important;
    margin-left:6px;
    vertical-align:middle;
}}
</style>

<canvas id="vtm-stars" style="position:fixed;top:0;left:0;
    width:100vw;height:100vh;pointer-events:none;z-index:0;opacity:0.5;"></canvas>

<script>
(function(){{
    function hideSidebarToggle(){{
        var selectors=[
            '[data-testid="stSidebarCollapseButton"]',
            '[data-testid="collapsedControl"]',
            'button[kind="header"]'
        ];
        selectors.forEach(function(sel){{
            var els=document.querySelectorAll(sel);
            els.forEach(function(el){{
                el.style.cssText='display:none!important;visibility:hidden!important;'+
                    'opacity:0!important;pointer-events:none!important;'+
                    'width:0!important;height:0!important;';
            }});
        }});
    }}
    var obs=new MutationObserver(hideSidebarToggle);
    function startObs(){{
        obs.observe(document.body,{{childList:true,subtree:true}});
        hideSidebarToggle();
    }}
    if(document.body) startObs();
    else document.addEventListener('DOMContentLoaded',startObs);
    setInterval(hideSidebarToggle,800);

    function bootStars(){{
        var cv=document.getElementById('vtm-stars');
        if(!cv){{setTimeout(bootStars,500);return;}}
        var ctx=cv.getContext('2d');
        function resize(){{cv.width=window.innerWidth;cv.height=window.innerHeight;}}
        resize();
        window.addEventListener('resize',resize);
        var stars=[];
        for(var i=0;i<200;i++){{
            stars.push({{
                x:Math.random()*cv.width, y:Math.random()*cv.height,
                r:Math.random()*1.8+0.2,
                a:Math.random(),
                da:(Math.random()*0.007+0.002)*(Math.random()<0.5?1:-1),
                dx:(Math.random()-0.5)*0.15,
                dy:(Math.random()-0.5)*0.15,
                gold:Math.random()<0.28
            }});
        }}
        function draw(){{
            ctx.clearRect(0,0,cv.width,cv.height);
            for(var i=0;i<stars.length;i++){{
                var s=stars[i];
                s.a+=s.da;
                if(s.a>=1||s.a<=0)s.da*=-1;
                s.x+=s.dx; s.y+=s.dy;
                if(s.x<0)s.x=cv.width;
                if(s.x>cv.width)s.x=0;
                if(s.y<0)s.y=cv.height;
                if(s.y>cv.height)s.y=0;
                ctx.beginPath();
                ctx.arc(s.x,s.y,s.r,0,Math.PI*2);
                ctx.fillStyle=s.gold
                    ?'rgba(212,175,55,'+s.a.toFixed(2)+')'
                    :'rgba(180,210,255,'+s.a.toFixed(2)+')';
                ctx.shadowBlur=s.r*4;
                ctx.shadowColor=s.gold?'#D4AF37':'#93C5FD';
                ctx.fill();
            }}
            requestAnimationFrame(draw);
        }}
        draw();
    }}
    bootStars();
}})();
</script>
""", unsafe_allow_html=True)

def render_login():
    inject_all()
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        st.markdown(f"""
        <div style="margin-top:50px;background:rgba(15,23,42,0.92);
            border:1px solid rgba(212,175,55,0.45);border-radius:22px;
            padding:36px 32px;box-shadow:0 20px 55px rgba(0,0,0,0.6);
            position:relative;z-index:2;">
          <div style="text-align:center;margin-bottom:24px;">
            {logo_svg(76)}
            <h1 style="color:#D4AF37;font-size:1.5rem;font-weight:900;
                       margin:12px 0 4px;">(주) 브이티엠</h1>
            <p style="color:#94A3B8;font-size:0.87rem;font-weight:700;margin:0;">
                VTM 운영 대시보드 v1.0
            </p>
          </div>
          <div style="background:rgba(212,175,55,0.12);border:1px solid rgba(212,175,55,0.3);
                      border-radius:9px;padding:9px;text-align:center;margin-bottom:16px;">
            <span style="color:#D4AF37;font-weight:900;font-size:0.84rem;">
                🔐 시스템 접속 인증
            </span>
          </div>
        </div>
        """, unsafe_allow_html=True)

        emp_df  = get_employees(active_only=True)
        options = ["담당자를 선택하세요"] + [
            f"{r['name']} ({r['role']})" for _, r in emp_df.iterrows()
        ]
        sel = st.selectbox("👤 담당자 선택", options, key="login_sel")

        selected = None
        if sel != "담당자를 선택하세요":
            nm = sel.split(" (")[0]
            m  = emp_df[emp_df["name"] == nm]
            if not m.empty:
                selected = m.iloc[0]

        pw_input = ""
        if selected is not None:
            if str(selected["password"]).strip():
                pw_input = st.text_input("🔑 비밀번호", type="password",
                    placeholder="비밀번호 입력", key="login_pw")
            else:
                st.markdown("""
                <div style="background:rgba(16,185,129,0.15);border:1px solid #10B981;
                    border-radius:8px;padding:8px;text-align:center;margin:6px 0;">
                  <span style="color:#10B981;font-weight:700;font-size:0.84rem;">
                      🔓 비밀번호 없이 접속 가능
                  </span>
                </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        if st.button("🚀  시스템 접속", key="btn_login", use_container_width=True):
            if sel == "담당자를 선택하세요" or selected is None:
                st.error("⚠️ 담당자를 선택해 주세요.")
            else:
                pw_ok = (not str(selected["password"]).strip()) or \
                        (pw_input == str(selected["password"]))
                if pw_ok:
                    st.session_state.logged_in  = True
                    st.session_state.user_id    = selected["id"]
                    st.session_state.user_name  = selected["name"]
                    st.session_state.is_admin   = bool(int(selected["is_admin"]))
                    st.session_state.page       = "home"
                    wlog("LOGIN", selected["name"])
                    st.rerun()
                else:
                    st.error("❌ 비밀번호가 올바르지 않습니다.")

        st.markdown("""
        <div style="text-align:center;margin-top:16px;">
          <p style="color:#475569;font-size:0.75rem;font-weight:700;">
              개발자: 박동진 본부장
          </p>
        </div>""", unsafe_allow_html=True)

def render_sidebar():
    with st.sidebar:
        st.markdown(f"""
        <div style="text-align:center;padding:14px 6px 6px;">
          {logo_svg(38)}
          <h2 style="color:#D4AF37;font-size:0.9rem;font-weight:900;margin:5px 0 1px;">
              (주) 브이티엠</h2>
          <p style="color:#64748B;font-size:0.66rem;font-weight:700;margin:0;">
              VTM 운영 대시보드 v1.0</p>
        </div>
        <hr style="border-color:#1E3A5F;margin:7px 0;">
        """, unsafe_allow_html=True)

        role_txt = "🔴 관리자" if st.session_state.is_admin else "🟢 직원"
        kst_now = now_kst().strftime("%H:%M")
        kst_date = now_kst().strftime("%m/%d")
        st.markdown(f"""
        <div style="background:#1E293B;border-radius:10px;padding:8px 12px;
                    margin:4px;border-left:3px solid #D4AF37;">
          <p style="color:#D4AF37;font-weight:900;font-size:0.8rem;margin:0;">
              {role_txt}
              <span class="kst-badge">🇰🇷 KST {kst_date} {kst_now}</span>
          </p>
          <p style="color:#F1F5F9;font-weight:700;font-size:0.92rem;margin:3px 0 0;">
              {st.session_state.user_name}</p>
        </div>""", unsafe_allow_html=True)

        st.markdown("<hr style='border-color:#1E3A5F;margin:7px 0;'>", unsafe_allow_html=True)

        if st.session_state.is_admin:
            menus = [
                ("home",          "🏠 대시보드 홈",   True),
                ("admin_attend",  "📋 출퇴근 현황",   False),
                ("admin_tasks",   "📊 업무 현황",     False),
                ("admin_approve", "✅ 결과 승인",     False),
                ("admin_emp",     "👥 직원 관리",     False),
                ("admin_excel",   "📥 엑셀 다운로드", False),
                ("admin_logs",    "🔍 시스템 로그",   False),
            ]
        else:
            menus = [
                ("home",         "🏠 내 대시보드",   True),
                ("emp_attend",   "⏰ 출퇴근",        False),
                ("emp_report",   "📝 업무 보고",     False),
                ("emp_calendar", "📅 업무 달력",     False),
            ]

        for key, label, is_home in menus:
            is_active = (st.session_state.page == key)
            if is_home:
                if is_active:
                    st.markdown(f"""
                    <div class="home-active-badge">
                      <div class="home-active-dot"></div>
                      <span>{label}</span>
                    </div>""", unsafe_allow_html=True)
                else:
                    st.markdown('<div class="sidebar-home-btn">', unsafe_allow_html=True)
                    if st.button(label, key=f"nav_{key}", use_container_width=True):
                        st.session_state.page = key; st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
            else:
                if is_active:
                    st.markdown(f"""
                    <div style="background:linear-gradient(135deg,#F6D365,#D4AF37);
                        border-radius:10px;padding:10px 13px;margin:3px 4px;
                        border-left:4px solid #B8860B;">
                      <span style="color:#000!important;font-weight:900;font-size:0.86rem;">
                          {label}
                      </span>
                    </div>""", unsafe_allow_html=True)
                else:
                    if st.button(label, key=f"nav_{key}", use_container_width=True):
                        st.session_state.page = key; st.rerun()

        st.markdown("<hr style='border-color:#1E3A5F;margin:12px 0 5px;'>", unsafe_allow_html=True)
        st.markdown("""<p style="color:#475569;font-size:0.67rem;text-align:center;font-weight:700;">
            개발자: 박동진 본부장</p>""", unsafe_allow_html=True)

        st.markdown('<div class="sidebar-logout-btn">', unsafe_allow_html=True)
        if st.button("🚪 로그아웃", key="btn_logout", use_container_width=True):
            wlog("LOGOUT", st.session_state.user_name)
            for k in ["logged_in", "user_id", "user_name", "is_admin"]:
                st.session_state[k] = False if k == "logged_in" else None
            st.session_state.page = "home"; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

def topbar(title):
    kst = now_kst()
    day_kr = ["월","화","수","목","금","토","일"][kst.weekday()]
    st.markdown(f"""
    <div class="topbar">
      <span class="tb-title">{title}</span>
      <span class="tb-info">
          📅 {kst.strftime('%Y년 %m월 %d일')} ({day_kr})
          &nbsp;·&nbsp; 🇰🇷 KST {kst.strftime('%H:%M')}
          &nbsp;·&nbsp; 👤 {st.session_state.user_name}
      </span>
    </div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════
#  직원: 홈
# ═══════════════════════════════════════════
def page_emp_home():
    topbar("🏠 내 대시보드")
    uid = st.session_state.user_id; td = today_str()
    conn = get_conn()
    att = pd.read_sql("SELECT * FROM attendance WHERE emp_id=? AND work_date=? LIMIT 1",
                      conn, params=(uid, td))
    rep = pd.read_sql("SELECT * FROM reports WHERE emp_id=? AND work_date=? LIMIT 1",
                      conn, params=(uid, td))
    conn.close()

    ci  = safe_str(att.iloc[0]["checkin"])  if not att.empty else None
    co  = safe_str(att.iloc[0]["checkout"]) if not att.empty else None
    ci  = ci[-8:-3]  if ci  else "--:--"
    co  = co[-8:-3]  if co  else "--:--"
    atp = safe_str(att.iloc[0]["att_type"]) if not att.empty else "미출근"
    atp = atp or "미출근"
    prg = int(rep.iloc[0]["pm_progress"]) if not rep.empty else 0
    rst = safe_str(rep.iloc[0]["status"])  if not rep.empty else "미제출"
    rst = rst or "미제출"

    c1, c2, c3, c4 = st.columns(4)
    for col, lbl, val, sub in [
        (c1, "출근 시간", ci, atp), (c2, "퇴근 시간", co, ""),
        (c3, "업무 진행률", f"{prg}%", ""), (c4, "보고 상태", rst, "")]:
        col.markdown(f"""<div class="met-card">
          <span class="met-val">{val}</span>
          <span class="met-lbl">{lbl}</span>
          <span style="color:#64748B;font-size:0.66rem;font-weight:700;">{sub}</span>
        </div>""", unsafe_allow_html=True)

    if not rep.empty:
        s = safe_str(rep.iloc[0]["status"]) or ""
        c = safe_str(rep.iloc[0]["admin_comment"]) or ""
        if   s == "승인": st.success(f"✅ 관리자 승인 완료  |  💬 {c or '승인되었습니다.'}")
        elif s == "반려": st.error(  f"❌ 보고 반려  |  💬 {c or '수정 후 재제출 바랍니다.'}")
        elif s == "보류": st.warning(f"⏸ 보류 처리  |  💬 {c}")

    st.markdown(f"""<div class="vtm-card" style="margin-top:12px;">
      <h3>📌 오늘 현황</h3>
      <p>{'✅ 출근 완료 — '+atp if not att.empty else '❗ 아직 출근 체크 전'}</p>
      <p>{'📝 업무 보고: '+rst if not rep.empty else '📝 업무 보고 미제출'}</p>
      <p style="color:#64748B;font-size:0.8rem;margin-top:6px;">
          왼쪽 메뉴 → ⏰ 출퇴근 → 📝 업무 보고 순으로 진행하세요.
      </p>
    </div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════
#  직원: 출퇴근
# ═══════════════════════════════════════════
ATT_TYPES = ["정상출근","오전 반차","오후 반차","조퇴","연차","병가","공가"]

def page_emp_attend():
    topbar("⏰ 출퇴근")
    uid = st.session_state.user_id; uname = st.session_state.user_name; td = today_str()
    conn = get_conn()
    att = pd.read_sql("SELECT * FROM attendance WHERE emp_id=? AND work_date=? LIMIT 1",
                      conn, params=(uid, td))
    conn.close()

    c1, c2 = st.columns(2)
    ci_raw = safe_str(att.iloc[0]["checkin"])  if not att.empty else None
    co_raw = safe_str(att.iloc[0]["checkout"]) if not att.empty else None
    ci_t = ci_raw[-8:-3] if ci_raw else "--:--"
    co_t = co_raw[-8:-3] if co_raw else "--:--"
    atp  = safe_str(att.iloc[0]["att_type"]) if not att.empty else "미출근"
    atp  = atp or "미출근"

    kst_now_display = now_kst().strftime("%H:%M")

    with c1:
        st.markdown(f"""<div class="vtm-card" style="text-align:center;">
          <h3>🟢 출근 시간</h3>
          <p style="font-size:1.8rem;font-weight:900;color:#10B981;margin:8px 0;">{ci_t}</p>
          <p style="color:#64748B;">{atp}</p>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="vtm-card" style="text-align:center;">
          <h3>🔴 퇴근 시간</h3>
          <p style="font-size:1.8rem;font-weight:900;color:#EF4444;margin:8px 0;">{co_t}</p>
          <p style="color:#64748B;">현재 KST: {kst_now_display}</p>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")
    if att.empty:
        sel_type = st.selectbox("출근 유형", ATT_TYPES, key="sel_att")
        if st.button(f"✅  출근 체크인 ({sel_type})", key="btn_ci", use_container_width=True):
            conn = get_conn()
            conn.execute(
                "INSERT INTO attendance(emp_id,emp_name,work_date,checkin,att_type,created_at)"
                " VALUES(?,?,?,?,?,?)",
                (uid, uname, td, now_str(), sel_type, now_str())
            )
            conn.commit(); conn.close()
            wlog("CHECKIN", uname, "", sel_type)
            st.success(f"✅ 출근 완료! ({sel_type} {now_kst().strftime('%H:%M')} KST)")
            st.rerun()
    else:
        st.success(f"✅ 출근 완료 — {ci_t} ({atp})")
        if not co_raw:
            if st.button("🏠  퇴근 체크아웃", key="btn_co", use_container_width=True):
                conn = get_conn()
                conn.execute("UPDATE attendance SET checkout=? WHERE emp_id=? AND work_date=?",
                             (now_str(), uid, td))
                conn.commit(); conn.close()
                wlog("CHECKOUT", uname)
                st.success(f"🏠 퇴근 완료! ({now_kst().strftime('%H:%M')} KST)")
                st.rerun()
        else:
            st.success(f"🏠 퇴근 완료 — {co_t}")

    st.markdown("---")
    st.markdown("<div class='vtm-card'><h3>📋 최근 출퇴근 기록</h3></div>", unsafe_allow_html=True)
    conn = get_conn()
    hist = pd.read_sql(
        "SELECT work_date,att_type,checkin,checkout FROM attendance"
        " WHERE emp_id=? ORDER BY work_date DESC LIMIT 10",
        conn, params=(uid,)
    )
    conn.close()
    if not hist.empty:
        hist.columns = ["날짜","유형","출근","퇴근"]
        st.dataframe(hist, use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════
#  직원: 업무 보고
# ═══════════════════════════════════════════
def page_emp_report():
    topbar("📝 업무 보고")
    uid = st.session_state.user_id; uname = st.session_state.user_name; td = today_str()
    conn = get_conn()
    exist = pd.read_sql("SELECT * FROM reports WHERE emp_id=? AND work_date=? LIMIT 1",
                        conn, params=(uid, td))
    conn.close()

    if not exist.empty:
        s = safe_str(exist.iloc[0]["status"]) or ""
        c = safe_str(exist.iloc[0]["admin_comment"]) or ""
        st.success(f"✅ 오늘 업무보고 제출 완료  |  상태: {s}")
        if c: st.info(f"💬 관리자 코멘트: {c}")

    tab1, tab2 = st.tabs(["🌅 오전 업무 계획", "🌇 퇴근 결과 보고"])

    with tab1:
        st.markdown("<div class='vtm-card'><h3>🌅 오전 업무 계획</h3></div>", unsafe_allow_html=True)
        am_tasks = st.text_area("📌 오늘 할 업무",
            value=safe_str(exist.iloc[0]["am_tasks"]) or "" if not exist.empty else "",
            height=110, placeholder="예) 홈페이지 배너 수정, 미팅 자료 준비...")
        am_priority = st.selectbox("🎯 우선순위",
            ["🔴 긴급","🟠 높음","🟡 보통","🟢 낮음"], key="am_p")
        am_notes = st.text_area("📎 특이사항",
            value=safe_str(exist.iloc[0]["am_notes"]) or "" if not exist.empty else "",
            height=75, placeholder="회의 일정, 협업 요청 등...")
        if st.button("💾  오전 계획 저장", key="btn_am", use_container_width=True):
            conn = get_conn()
            if exist.empty:
                conn.execute(
                    "INSERT INTO reports(emp_id,emp_name,work_date,am_tasks,"
                    "am_priority,am_notes,status,submitted_at) VALUES(?,?,?,?,?,?,'대기중',?)",
                    (uid, uname, td, am_tasks, am_priority, am_notes, now_str())
                )
            else:
                conn.execute(
                    "UPDATE reports SET am_tasks=?,am_priority=?,am_notes=?,"
                    "submitted_at=? WHERE emp_id=? AND work_date=?",
                    (am_tasks, am_priority, am_notes, now_str(), uid, td)
                )
            conn.commit(); conn.close()
            wlog("AM_PLAN", uname, td)
            st.success("✅ 오전 계획 저장 완료!"); st.rerun()

    with tab2:
        st.markdown("<div class='vtm-card'><h3>🌇 퇴근 결과 보고</h3></div>", unsafe_allow_html=True)
        pm_done = st.text_area("✅ 완료한 업무",
            value=safe_str(exist.iloc[0]["pm_done"]) or "" if not exist.empty else "",
            height=100, placeholder="오늘 완료한 업무 상세히...")
        pm_progress = st.slider("📊 전체 진행률 (%)", 0, 100,
            value=int(exist.iloc[0]["pm_progress"]) if not exist.empty else 0, step=5)
        pm_tomorrow = st.text_area("📅 내일 예정",
            value=safe_str(exist.iloc[0]["pm_tomorrow"]) or "" if not exist.empty else "", height=75)
        pm_remarks = st.text_area("💬 특이사항",
            value=safe_str(exist.iloc[0]["pm_remarks"]) or "" if not exist.empty else "", height=75)
        st.markdown("""<div class='vtm-card'>
          <h3>🔗 산출물 링크</h3>
          <p style="font-size:0.8rem;color:#64748B;">
              완성본은 Google Drive에 날짜 폴더 생성 후 업로드해 주세요.
          </p></div>""", unsafe_allow_html=True)
        drive_link = st.text_input("📁 Google Drive 링크",
            value=safe_str(exist.iloc[0]["drive_link"]) or "" if not exist.empty else "",
            placeholder="https://drive.google.com/...")
        result_link = st.text_input("🔗 완성 결과물 링크",
            value=safe_str(exist.iloc[0]["result_link"]) or "" if not exist.empty else "",
            placeholder="https://...")
        if st.button("📤  업무보고 제출", key="btn_pm", use_container_width=True):
            conn = get_conn()
            if exist.empty:
                conn.execute(
                    "INSERT INTO reports(emp_id,emp_name,work_date,pm_done,pm_progress,"
                    "pm_tomorrow,pm_remarks,drive_link,result_link,status,submitted_at)"
                    " VALUES(?,?,?,?,?,?,?,?,?,'대기중',?)",
                    (uid, uname, td, pm_done, pm_progress, pm_tomorrow,
                     pm_remarks, drive_link, result_link, now_str())
                )
            else:
                conn.execute(
                    "UPDATE reports SET pm_done=?,pm_progress=?,pm_tomorrow=?,"
                    "pm_remarks=?,drive_link=?,result_link=?,status='대기중',"
                    "submitted_at=? WHERE emp_id=? AND work_date=?",
                    (pm_done, pm_progress, pm_tomorrow, pm_remarks,
                     drive_link, result_link, now_str(), uid, td)
                )
            conn.commit(); conn.close()
            wlog("REPORT", uname, td)
            st.success("✅ 업무보고가 완료되었습니다!")
            st.balloons(); st.rerun()

# ═══════════════════════════════════════════
#  직원: 달력
# ═══════════════════════════════════════════
def page_emp_calendar():
    topbar("📅 업무 달력")
    uid = st.session_state.user_id; today = now_kst().date()
    c1, c2, _ = st.columns([1, 1, 2])
    with c1: yr = st.number_input("연도", value=today.year,  min_value=2024, max_value=2030, key="cy")
    with c2: mo = st.number_input("월",   value=today.month, min_value=1,    max_value=12,   key="cm")
    yr = int(yr); mo = int(mo)

    conn = get_conn()
    att_df = pd.read_sql(
        "SELECT work_date,att_type FROM attendance WHERE emp_id=? AND work_date LIKE ?",
        conn, params=(uid, f"{yr}-{mo:02d}-%"))
    rep_df = pd.read_sql(
        "SELECT work_date,status,pm_progress FROM reports WHERE emp_id=? AND work_date LIKE ?",
        conn, params=(uid, f"{yr}-{mo:02d}-%"))
    conn.close()

    att_map = {r["work_date"]: r for _, r in att_df.iterrows()} if not att_df.empty else {}
    rep_map = {r["work_date"]: r for _, r in rep_df.iterrows()} if not rep_df.empty else {}

    cal = calendar.monthcalendar(yr, mo)
    html = """<table class="cal-tbl"><thead><tr>
        <th class="wk">일</th>
        <th>월</th><th>화</th><th>수</th><th>목</th><th>금</th>
        <th class="wk">토</th>
    </tr></thead><tbody>"""
    for week in cal:
        html += "<tr>"
        for i, day in enumerate(week):
            is_wk = (i == 0 or i == 6)
            if day == 0:
                html += f'<td class="{"wk" if is_wk else ""}"></td>'; continue
            d = f"{yr}-{mo:02d}-{day:02d}"
            cls = "wk" if is_wk else ""
            if d == today_str(): cls += " tday"
            if is_wk:
                html += f'<td class="{cls}"><span style="font-size:0.58rem">{day}</span></td>'
            else:
                inner = f'<strong>{day}</strong>'
                inner += (f'<span class="tg-att">✅{att_map[d]["att_type"]}</span>'
                          if d in att_map else '<span class="tg-no">미출근</span>')
                if d in rep_map:
                    r = rep_map[d]
                    inner += (f'<span class="tg-ok">✅{r["pm_progress"]}%</span>'
                              if r["status"] == "승인"
                              else f'<span class="tg-rep">📋{r["status"]}</span>')
                else:
                    inner += '<span class="tg-no">보고없음</span>'
                html += f'<td class="{cls}">{inner}</td>'
        html += "</tr>"
    html += "</tbody></table>"
    st.markdown(html, unsafe_allow_html=True)

# ═══════════════════════════════════════════
#  관리자: 홈  ← TypeError 수정 핵심
# ═══════════════════════════════════════════
def page_admin_home():
    topbar("🔴 관리자 대시보드")
    td = today_str(); conn = get_conn()
    total = pd.read_sql("SELECT COUNT(*) as c FROM employees WHERE active=1 AND is_admin=0", conn).iloc[0]["c"]
    t_att = pd.read_sql("SELECT COUNT(*) as c FROM attendance WHERE work_date=?", conn, params=(td,)).iloc[0]["c"]
    pend  = pd.read_sql("SELECT COUNT(*) as c FROM reports WHERE status='대기중'", conn).iloc[0]["c"]
    appr  = pd.read_sql("SELECT COUNT(*) as c FROM reports WHERE status='승인' AND work_date=?", conn, params=(td,)).iloc[0]["c"]
    emp_df  = pd.read_sql("SELECT id,name FROM employees WHERE active=1 AND is_admin=0", conn)
    att_td  = pd.read_sql("SELECT emp_id,att_type,checkin,checkout FROM attendance WHERE work_date=?", conn, params=(td,))
    rep_td  = pd.read_sql("SELECT emp_id,status,pm_progress FROM reports WHERE work_date=?", conn, params=(td,))
    conn.close()

    c1, c2, c3, c4 = st.columns(4)
    for col, lbl, val, sub in [
        (c1, "전체 직원", f"{total}명", ""),
        (c2, "오늘 출근", f"{t_att}명", f"/{total}명"),
        (c3, "승인 대기", f"{pend}건",  "검토 필요"),
        (c4, "오늘 승인", f"{appr}건",  "")]:
        col.markdown(f"""<div class="met-card">
          <span class="met-val">{val}</span>
          <span class="met-lbl">{lbl}</span>
          <span style="color:#64748B;font-size:0.66rem;font-weight:700;">{sub}</span>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # ── 안전한 lookup dict 구성 ──
    att_map = {}
    if not att_td.empty:
        for _, row in att_td.iterrows():
            att_map[row["emp_id"]] = row

    rep_map = {}
    if not rep_td.empty:
        for _, row in rep_td.iterrows():
            rep_map[row["emp_id"]] = row

    for _, emp in emp_df.iterrows():
        eid = emp["id"]; ename = emp["name"]
        a = att_map.get(eid)   # pandas Series or None
        r = rep_map.get(eid)   # pandas Series or None

        # ── 출근/퇴근 안전 추출 (NaN 방어) ──
        if a is not None:
            ci_raw = safe_str(a["checkin"])
            co_raw = safe_str(a["checkout"])
            ci  = ci_raw[-8:-3] if ci_raw else "--:--"
            co  = co_raw[-8:-3] if co_raw else "퇴근전"
            atp = safe_str(a["att_type"]) or "정상출근"
        else:
            ci = "--:--"; co = "퇴근전"; atp = "미출근"

        # ── 보고 상태 안전 추출 ──
        if r is not None:
            rs = safe_str(r["status"]) or "미제출"
            try:
                prg = int(r["pm_progress"]) if safe_str(str(r["pm_progress"])) else 0
            except (ValueError, TypeError):
                prg = 0
        else:
            rs = "미제출"; prg = 0

        ci_c = "#10B981" if a is not None else "#EF4444"
        rs_c = {"승인":"#10B981","대기중":"#F59E0B","반려":"#EF4444"}.get(rs,"#6B7280")
        st.markdown(f"""<div class="vtm-card" style="padding:12px;margin:3px 0;">
          <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:6px;">
            <span style="font-size:0.96rem;font-weight:900;">{ename}</span>
            <div style="display:flex;gap:10px;flex-wrap:wrap;font-weight:700;font-size:0.84rem;">
              <span style="color:{ci_c};">✅ 출근:{ci}</span>
              <span style="color:#64748B;">🏠 퇴근:{co}</span>
              <span>📋 {atp}</span>
              <span style="color:{rs_c};">
                  {'미제출(출근전)' if rs=='미제출' else '보고:'+rs}
              </span>
              <span>📊{prg}%</span>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════
#  관리자: 출퇴근 현황
# ═══════════════════════════════════════════
def page_admin_attend():
    topbar("📋 출퇴근 현황")
    c1, c2 = st.columns(2)
    with c1: sel_date = st.date_input("날짜", value=now_kst().date(), key="aad")
    with c2:
        emp_df = get_employees(); names = ["전체"] + list(emp_df["name"])
        sel_emp = st.selectbox("직원", names, key="aae")
    conn = get_conn()
    q = "SELECT emp_name,att_type,checkin,checkout,work_date FROM attendance WHERE work_date=?"
    p = [str(sel_date)]
    if sel_emp != "전체": q += " AND emp_name=?"; p.append(sel_emp)
    att = pd.read_sql(q + " ORDER BY checkin", conn, params=p); conn.close()
    if att.empty:
        st.info(f"📭 {sel_date} 출퇴근 기록 없음")
    else:
        att.columns = ["직원명","유형","출근","퇴근","날짜"]
        st.dataframe(att, use_container_width=True, hide_index=True)
    if sel_emp == "전체":
        all_emp = get_employees()
        checked = set(att["직원명"].tolist()) if not att.empty else set()
        absent  = all_emp[(~all_emp["name"].isin(checked)) & (all_emp["is_admin"] == 0)]
        if not absent.empty:
            st.markdown("---")
            for _, row in absent.iterrows():
                st.markdown(f"""<div style="background:rgba(239,68,68,0.1);border:1px solid #EF4444;
                    border-radius:10px;padding:10px;margin:3px 0;">
                  <span style="color:#EF4444;font-weight:900;">
                      ❗ {row['name']} — 미출근 / 출근 전
                  </span></div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════
#  관리자: 업무 현황
# ═══════════════════════════════════════════
def page_admin_tasks():
    topbar("📊 업무 현황")
    c1, c2 = st.columns(2)
    with c1: sel_date = st.date_input("날짜", value=now_kst().date(), key="atd")
    with c2:
        emp_df = get_employees(); names = ["전체"] + list(emp_df["name"])
        sel_emp = st.selectbox("직원", names, key="ate")
    conn = get_conn()
    q = "SELECT * FROM reports WHERE work_date=?"
    p = [str(sel_date)]
    if sel_emp != "전체": q += " AND emp_name=?"; p.append(sel_emp)
    reps = pd.read_sql(q, conn, params=p); conn.close()
    if reps.empty: st.info("📭 해당 조건 업무 보고 없음"); return

    def do_approve_task(rid, status, emp, comment):
        c2 = get_conn()
        c2.execute("UPDATE reports SET status=?,admin_comment=?,approved_at=? WHERE id=?",
                   (status, comment, now_str(), rid))
        c2.commit(); c2.close()
        wlog(f"APPROVE_{status}", st.session_state.user_name, emp, comment)
        st.rerun()

    for _, r in reps.iterrows():
        rid    = int(r["id"])
        status = safe_str(r["status"]) or "대기중"
        sc     = {"승인":"#10B981","대기중":"#F59E0B","반려":"#EF4444"}.get(status, "#6B7280")
        dl_val = safe_str(r["drive_link"])
        rl_val = safe_str(r["result_link"])
        dl = (f'<a href="{dl_val}" target="_blank" style="color:#3B82F6;">링크</a>'
              if dl_val else "없음")
        rl = (f'<a href="{rl_val}" target="_blank" style="color:#3B82F6;">링크</a>'
              if rl_val else "없음")
        cmt_val = safe_str(r["admin_comment"]) or ""
        cmt_html = f'<p><b>💬 코멘트:</b> {cmt_val}</p>' if cmt_val else ''

        # ── HTML 카드 (버튼 제외) ──
        st.markdown(f"""<div class="vtm-card">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
            <h3 style="margin:0;">{r['emp_name']} — {r['work_date']}</h3>
            <span style="background:{sc};color:#fff;padding:3px 12px;
                border-radius:12px;font-weight:900;font-size:0.76rem;">{status}</span>
          </div>
          <p><b>🌅 오전:</b> {safe_str(r['am_tasks']) or '미입력'}</p>
          <p><b>🌇 완료:</b> {safe_str(r['pm_done']) or '미입력'}</p>
          <p><b>📊 진행률:</b> {r['pm_progress']}%</p>
          <p><b>📁 Drive:</b> {dl} &nbsp; <b>🔗 결과물:</b> {rl}</p>
          {cmt_html}
        </div>""", unsafe_allow_html=True)

        # ── 승인/반려/보류 버튼 (Streamlit 위젯, HTML 밖에 배치) ──
        cmt_input = st.text_input("💬 코멘트 입력", key=f"tcmt_{rid}",
                                  placeholder="승인 메시지 또는 반려 사유...")
        ba, bb, bc = st.columns(3)
        with ba:
            if st.button("✅ 승인", key=f"tap_{rid}", use_container_width=True):
                do_approve_task(rid, "승인", r['emp_name'], cmt_input or "승인")
        with bb:
            if st.button("❌ 반려", key=f"trj_{rid}", use_container_width=True):
                do_approve_task(rid, "반려", r['emp_name'], cmt_input or "반려 사유를 입력해 주세요.")
        with bc:
            if st.button("⏸ 보류", key=f"thl_{rid}", use_container_width=True):
                do_approve_task(rid, "보류", r['emp_name'], cmt_input or "보류")
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════
#  관리자: 결과 승인
# ═══════════════════════════════════════════
def page_admin_approve():
    topbar("✅ 결과 승인")
    conn = get_conn()
    pend = pd.read_sql("SELECT * FROM reports WHERE status='대기중' ORDER BY submitted_at DESC", conn)
    conn.close()
    if pend.empty: st.success("✅ 승인 대기 보고 없음"); return
    st.markdown(f"<div class='vtm-card'><h3>📋 대기 {len(pend)}건</h3></div>", unsafe_allow_html=True)
    for _, r in pend.iterrows():
        with st.expander(f"📝 {r['emp_name']}  ·  {r['work_date']}  ·  {r['pm_progress']}%"):
            st.markdown(f"""
**🌅 오전 계획:** {safe_str(r['am_tasks']) or '없음'}

**🌇 완료 업무:** {safe_str(r['pm_done']) or '없음'}

**📅 내일 예정:** {safe_str(r['pm_tomorrow']) or '없음'}

**💬 특이사항:** {safe_str(r['pm_remarks']) or '없음'}
""")
            dl_val = safe_str(r.get("drive_link"))
            rl_val = safe_str(r.get("result_link"))
            if dl_val:  st.markdown(f"📁 [Google Drive]({dl_val})")
            if rl_val: st.markdown(f"🔗 [결과물 링크]({rl_val})")
            cmt = st.text_input("💬 코멘트", key=f"cmt_{r['id']}")
            ca, cb, cc = st.columns(3)
            def do_approve(rid, status, emp, comment):
                c2 = get_conn()
                c2.execute("UPDATE reports SET status=?,admin_comment=?,approved_at=? WHERE id=?",
                           (status, comment, now_str(), rid))
                c2.commit(); c2.close()
                wlog(f"APPROVE_{status}", st.session_state.user_name, emp, comment)
                st.rerun()
            with ca:
                if st.button("✅ 승인", key=f"ap_{r['id']}", use_container_width=True):
                    do_approve(r['id'], "승인", r['emp_name'], cmt or "승인")
            with cb:
                if st.button("❌ 반려", key=f"rj_{r['id']}", use_container_width=True):
                    do_approve(r['id'], "반려", r['emp_name'], cmt or "반려")
            with cc:
                if st.button("⏸ 보류", key=f"hl_{r['id']}", use_container_width=True):
                    do_approve(r['id'], "보류", r['emp_name'], cmt or "보류")

# ═══════════════════════════════════════════
#  관리자: 직원 관리
# ═══════════════════════════════════════════
def page_admin_emp():
    topbar("👥 직원 관리")
    emp_df = get_employees(active_only=False)
    st.markdown("<div class='vtm-card'><h3>👥 전체 직원 목록</h3></div>", unsafe_allow_html=True)
    for _, emp in emp_df.iterrows():
        ac  = "#10B981" if emp["active"] else "#EF4444"
        at  = "재직 중" if emp["active"] else "퇴직"
        adm = "🔴 관리자" if emp["is_admin"] else "🟢 직원"
        ci, cb = st.columns([5, 1])
        with ci:
            st.markdown(f"""<div class="vtm-card" style="padding:9px 15px;margin:2px 0;">
              <span style="font-weight:900;">{emp['name']}</span>
              &nbsp;<span style="color:#64748B;font-weight:700;">{emp['role']}</span>
              &nbsp;<span style="color:{ac};font-weight:700;">{at}</span>
              &nbsp;<span style="font-weight:700;">{adm}</span>
            </div>""", unsafe_allow_html=True)
        with cb:
            if emp["active"] and not emp["is_admin"]:
                if st.button("🗑 퇴직", key=f"del_{emp['id']}", use_container_width=True):
                    c2 = get_conn()
                    c2.execute("UPDATE employees SET active=0 WHERE id=?", (emp["id"],))
                    c2.commit(); c2.close()
                    wlog("EMP_DEL", st.session_state.user_name, emp["name"])
                    st.success(f"'{emp['name']}' 퇴직 처리"); st.rerun()
            elif not emp["active"]:
                if st.button("♻ 복직", key=f"act_{emp['id']}", use_container_width=True):
                    c2 = get_conn()
                    c2.execute("UPDATE employees SET active=1 WHERE id=?", (emp["id"],))
                    c2.commit(); c2.close()
                    wlog("EMP_ACT", st.session_state.user_name, emp["name"])
                    st.success(f"'{emp['name']}' 복직 완료"); st.rerun()
    st.markdown("---")
    st.markdown("<div class='vtm-card'><h3>➕ 신규 직원 등록</h3></div>", unsafe_allow_html=True)
    with st.form("form_emp", clear_on_submit=True):
        f1, f2 = st.columns(2)
        with f1:
            new_name  = st.text_input("이름", placeholder="홍길동")
            new_role  = st.text_input("직책", placeholder="대리 / 디자이너 ...")
        with f2:
            new_pw    = st.text_input("비밀번호 (없으면 빈칸)", type="password")
            new_admin = st.checkbox("관리자 권한 부여")
        if st.form_submit_button("✅  직원 등록", use_container_width=True):
            if not new_name.strip() or not new_role.strip():
                st.error("이름과 직책을 입력하세요.")
            else:
                new_id = "emp_" + re.sub(r'[^a-z0-9]','', new_name.lower()) + str(int(time.time()))[-5:]
                try:
                    c2 = get_conn()
                    c2.execute(
                        "INSERT INTO employees(id,name,role,is_admin,password,active,created_at)"
                        " VALUES(?,?,?,?,?,1,?)",
                        (new_id, new_name.strip(), new_role.strip(),
                         1 if new_admin else 0, new_pw, now_str())
                    )
                    c2.commit(); c2.close()
                    wlog("EMP_ADD", st.session_state.user_name, new_name)
                    st.success(f"✅ '{new_name}' 등록 완료!"); st.rerun()
                except Exception as e:
                    st.error(f"등록 실패: {e}")

# ═══════════════════════════════════════════
#  관리자: 엑셀 다운로드
# ═══════════════════════════════════════════
def page_admin_excel():
    topbar("📥 엑셀 다운로드")
    st.markdown("<div class='vtm-card'><h3>📥 다운로드 조건 설정</h3></div>", unsafe_allow_html=True)
    emp_df = get_employees(); names = ["전체 인원"] + list(emp_df["name"])
    c1, c2 = st.columns(2)
    with c1:
        sel_emp  = st.selectbox("👤 대상 인원", names, key="ex_emp")
        rec_types = st.multiselect("📋 기록 유형", ["출퇴근 기록","업무 보고"],
                                   default=["출퇴근 기록","업무 보고"])
    with c2:
        period = st.selectbox("📅 기간", ["날짜별","주간","월간","전체"], key="ex_period")
        kst_today = now_kst().date()
        if period == "날짜별":
            df_ = st.date_input("시작", value=kst_today, key="ex_df")
            dt_ = st.date_input("종료", value=kst_today, key="ex_dt")
            d_from, d_to = str(df_), str(dt_)
        elif period == "주간":
            we  = st.date_input("주 종료일", value=kst_today, key="ex_we")
            ws  = we - timedelta(days=we.weekday())
            d_from, d_to = str(ws), str(we)
            st.markdown(f"<span style='color:#D4AF37;font-weight:700;font-size:0.84rem;'>"
                        f"📅 {ws} ~ {we}</span>", unsafe_allow_html=True)
        elif period == "월간":
            my = st.number_input("연도", value=kst_today.year,  min_value=2024, max_value=2030, key="ex_my")
            mm = st.number_input("월",   value=kst_today.month, min_value=1,    max_value=12,   key="ex_mm")
            ld = calendar.monthrange(int(my), int(mm))[1]
            d_from = str(date(int(my), int(mm), 1))
            d_to   = str(date(int(my), int(mm), ld))
        else:
            d_from, d_to = "2024-01-01", "2030-12-31"

    if st.button("📥  엑셀 생성", key="btn_excel", use_container_width=True):
        if not rec_types: st.error("기록 유형을 선택하세요."); return
        conn = get_conn(); sheets = {}
        if "출퇴근 기록" in rec_types:
            q = ("SELECT emp_name,work_date,att_type,checkin,checkout"
                 " FROM attendance WHERE work_date BETWEEN ? AND ?")
            p = [d_from, d_to]
            if sel_emp != "전체 인원": q += " AND emp_name=?"; p.append(sel_emp)
            df = pd.read_sql(q + " ORDER BY work_date,emp_name", conn, params=p)
            if not df.empty:
                df.columns = ["직원명","날짜","유형","출근","퇴근"]
                sheets["출퇴근 기록"] = df
        if "업무 보고" in rec_types:
            q = ("SELECT emp_name,work_date,am_tasks,am_priority,pm_done,pm_progress,"
                 "pm_tomorrow,pm_remarks,drive_link,result_link,status,admin_comment,submitted_at"
                 " FROM reports WHERE work_date BETWEEN ? AND ?")
            p = [d_from, d_to]
            if sel_emp != "전체 인원": q += " AND emp_name=?"; p.append(sel_emp)
            df = pd.read_sql(q + " ORDER BY work_date,emp_name", conn, params=p)
            if not df.empty:
                df.columns = ["직원명","날짜","오전계획","우선순위","완료업무",
                              "진행률","내일예정","특이사항","Drive","결과링크","상태","코멘트","제출시간"]
                sheets["업무 보고"] = df
        conn.close()
        if not sheets: st.warning("해당 조건 데이터 없음"); return
        label = sel_emp.replace(" ","_") if sel_emp != "전체 인원" else "전체"
        fname = f"VTM_{label}_{period}_{d_from}~{d_to}.xlsx"
        st.download_button(
            label=f"💾  {fname} 저장", data=to_excel(sheets),
            file_name=fname,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        st.success("✅ 파일 준비 완료! 위 버튼을 눌러 저장하세요.")

# ═══════════════════════════════════════════
#  관리자: 로그
# ═══════════════════════════════════════════
def page_admin_logs():
    topbar("🔍 시스템 로그")
    conn = get_conn()
    logs = pd.read_sql(
        "SELECT created_at,action,actor,target,detail FROM logs"
        " ORDER BY created_at DESC LIMIT 300", conn)
    conn.close()
    if logs.empty:
        st.info("로그 없음")
    else:
        logs.columns = ["시간","액션","실행자","대상","상세"]
        st.dataframe(logs, use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════
#  메인 라우터
# ═══════════════════════════════════════════
inject_all()

if not st.session_state.logged_in:
    render_login()
else:
    render_sidebar()

    if st.session_state.is_admin:
        pages = {
            "home":          page_admin_home,
            "admin_attend":  page_admin_attend,
            "admin_tasks":   page_admin_tasks,
            "admin_approve": page_admin_approve,
            "admin_emp":     page_admin_emp,
            "admin_excel":   page_admin_excel,
            "admin_logs":    page_admin_logs,
        }
    else:
        pages = {
            "home":         page_emp_home,
            "emp_attend":   page_emp_attend,
            "emp_report":   page_emp_report,
            "emp_calendar": page_emp_calendar,
        }

    pages.get(st.session_state.page, list(pages.values())[0])()

    st.markdown("""
    <div style="text-align:center;padding:20px;color:#475569;
                font-size:0.74rem;font-weight:700;position:relative;z-index:1;">
        © 2026 (주) 브이티엠 운영 대시보드 v1.0 &nbsp;|&nbsp; 개발자: 박동진 본부장
    </div>""", unsafe_allow_html=True)
