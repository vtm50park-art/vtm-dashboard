# vtm_dashboard.py  ← Supabase 마이그레이션 버전
import streamlit as st
import pandas as pd
from supabase import create_client, Client
import io
from datetime import datetime, date, timedelta, timezone
import calendar
import time
import re
 
st.set_page_config(
    page_title="(주) 브이티엠 운영 대시보드",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed"
)
 
KST = timezone(timedelta(hours=9))
 
def now_kst() -> datetime:
    return datetime.now(tz=KST)
 
def today_str() -> str:
    return now_kst().strftime("%Y-%m-%d")
 
def now_str() -> str:
    return now_kst().strftime("%Y-%m-%d %H:%M:%S")
 

@st.cache_resource
def get_supabase() -> "Client":
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"⚠️ Supabase 연결 실패: {e}")
        st.info("Streamlit Cloud → 앱 Settings → Secrets 탭에 SUPABASE_URL과 SUPABASE_KEY를 등록해주세요.")
        st.stop()

def _sb():
    return get_supabase()

# ── VTM OS 2.0.3 로그인 리디자인 자산 ──
VTM_LOGO_URL     = "https://i.postimg.cc/TwMLPgWj/beu-itiem-logo.png"
VTM_BG_VIDEO_URL = "https://pwaqbxfaokaliclhmixo.supabase.co/storage/v1/object/public/assets/vtm.mp4"

# ── 관리자(본부장) 화면 배경 영상 자산 ──
VTM_ADMIN_BG_VIDEO_URL = "https://pwaqbxfaokaliclhmixo.supabase.co/storage/v1/object/public/assets/vtm01.mp4"

# ── 디렉터/직원 홈 화면 배경 영상 자산 (VTM OS 2.0.8 신규) ──
VTM_DIR_BG_VIDEO_URL = "https://pwaqbxfaokaliclhmixo.supabase.co/storage/v1/object/public/assets/vtm02.mp4"

# ── 관리자 대시보드 표시용 AI 직원 (표시 전용 · DB 무관) ──
AI_STAFF = [
    ("몽해 블로그 작업 AI직원",   "블로그 작성중"),
    ("탈모 블로그 작업 AI직원",   "블로그 작성중"),
    ("강민호 전략실장 AI직원",    "몽해 비즈니스 전략 수립중"),
    ("최도윤 영업팀장 AI직원",    "덴탈 팩토리 세일즈 계획수립중"),
    ("김하린 마케팅 팀장 AI직원", "몽해 마케팅 진행중"),
    ("VTM AI 총괄과장 AI직원",   "AI직원 역할분담 수행중"),
    ("서윤 비서 실장 AI직원",     "본부장 스케줄 체크중"),
]

def init_data():
    """앱 세션 시작 시 기본 직원 데이터 확인 및 초기화 (세션당 1회 실행)"""
    if st.session_state.get("_db_init_done"):
        return

    try:
        sb = _sb()
        test = sb.table("employees").select("id").limit(1).execute()

        check = sb.table("employees").select("id").eq("id","admin_park").execute()
        if not check.data:
            _now = now_str()
            sb.table("employees").insert([
                {"id":"admin_park","name":"박동진 본부장","role":"본부장",
                 "is_admin":1,"password":"5638","active":1,"created_at":_now},
                {"id":"emp_ahn","name":"안효민 디렉터","role":"디렉터",
                 "is_admin":0,"password":"","active":1,"created_at":_now},
            ]).execute()

        try:
            sb.table("employees").update({"active":0}).eq("id","emp_kim").execute()
        except Exception:
            pass

        try:
            sb.table("employees").update({"active":0}).eq("id","emp_seo").execute()
        except Exception:
            pass

        st.session_state["_db_init_done"] = True

    except Exception as e:
        st.error(f"⚠️ DB 초기화 오류: {e}")
        st.warning(
            "아래 두 가지를 확인해주세요:\n"
            "1. Streamlit Cloud → Settings → Secrets 에 SUPABASE_URL / SUPABASE_KEY 등록\n"
            "2. Supabase SQL Editor에서 supabase_schema.sql 실행 (RLS 비활성화 포함)"
        )
        st.stop()


# 세션 상태 기본값 설정 먼저
for _k, _v in {"logged_in": False, "user_id": None, "user_name": None,
               "is_admin": False, "page": "home"}.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# DB 초기화 (세션당 1회)
init_data()

 
def wlog(action, actor, target="", detail=""):
    try:
        _sb().table("logs").insert({
            "action": action, "actor": actor,
            "target": target, "detail": detail, "created_at": now_str()
        }).execute()
    except Exception:
        pass
 
def get_employees(active_only=True):
    sb = _sb()
    q = sb.table("employees").select("*")
    if active_only:
        q = q.eq("active", 1)
    r = q.order("is_admin", desc=True).order("name").execute()
    return pd.DataFrame(r.data) if r.data else pd.DataFrame(
        columns=["id","name","role","is_admin","password","active","created_at"])
 
def to_excel(dfs):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        for s, d in dfs.items():
            d.to_excel(w, sheet_name=s[:31], index=False)
    return buf.getvalue()
 
def safe_str(val):
    if val is None:
        return None
    try:
        if pd.isna(val):
            return None
    except (TypeError, ValueError):
        pass
    s = str(val).strip()
    return s if s else None
 
 
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
    st.markdown('<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes">', unsafe_allow_html=True)
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
 
[data-testid="stSidebar"],
[data-testid="stSidebarCollapseButton"],
[data-testid="collapsedControl"],
button[kind="header"],
.st-emotion-cache-ztfqz8 {{
    display: none !important;
    width: 0 !important;
    min-width: 0 !important;
    max-width: 0 !important;
    visibility: hidden !important;
    overflow: hidden !important;
    position: absolute !important;
    pointer-events: none !important;
}}
[data-testid="stMain"] {{ margin-left: 0 !important; padding-left: 8px !important; width:100% !important; }}
 
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
    background: linear-gradient(135deg,#FFFFF0 0%,#FFF8E7 50%,#FAEBD7 100%) !important;
    color: #111111 !important;
    border: 1.5px solid #C8A84B !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
}}
.stTextInput>div>div>input::placeholder,
.stNumberInput>div>div>input::placeholder {{
    color: #7A6030 !important;
    font-weight: 500 !important;
    opacity: 1 !important;
}}
.stTextArea textarea {{
    background: linear-gradient(135deg,#FFFFF0 0%,#FFF8E7 50%,#FAEBD7 100%) !important;
    color: #111111 !important;
    border: 1.5px solid #C8A84B !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}}
.stTextArea textarea::placeholder {{
    color: #7A6030 !important;
    font-weight: 500 !important;
    opacity: 1 !important;
}}
.stSelectbox>div>div {{
    background: linear-gradient(135deg,#FFFFF0 0%,#FFF8E7 100%) !important;
    border: 1.5px solid #C8A84B !important;
    border-radius: 8px !important;
}}
.stSelectbox * {{ color: #111111 !important; font-weight: 700 !important; }}
.stDateInput>div>div>input {{
    background: linear-gradient(135deg,#FFFFF0 0%,#FAEBD7 100%) !important;
    color: #111111 !important;
    border: 1.5px solid #C8A84B !important;
    border-radius: 8px !important;
}}
.stMultiSelect>div>div {{
    background: linear-gradient(135deg,#FFFFF0 0%,#FFF8E7 100%) !important;
    border: 1.5px solid #C8A84B !important;
    border-radius: 8px !important;
}}
.stMultiSelect * {{ color: #111111 !important; font-weight: 700 !important; }}
 
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
 
[data-testid="stExpander"] details {{
    background: #1E293B !important;
    border: 1px solid #334155 !important;
    border-radius: 10px !important;
}}
[data-testid="stExpander"] summary {{
    color: #F1F5F9 !important;
    font-weight: 700 !important;
}}
[data-testid="stExpander"] summary:hover {{
    color: #D4AF37 !important;
}}
[data-testid="stExpander"] [data-testid="stMarkdownContainer"] p,
[data-testid="stExpander"] [data-testid="stMarkdownContainer"] li,
[data-testid="stExpander"] [data-testid="stMarkdownContainer"] span,
[data-testid="stExpander"] [data-testid="stMarkdownContainer"] strong {{
    color: #F1F5F9 !important;
    font-weight: 600 !important;
}}

#MainMenu, footer, header {{ visibility:hidden !important; }}
[data-testid="stDecoration"]  {{ display:none !important; }}
 
::-webkit-scrollbar {{ width:5px; height:5px; }}
::-webkit-scrollbar-track {{ background:#0F172A; }}
::-webkit-scrollbar-thumb {{ background:#D4AF37; border-radius:3px; }}
 
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

    if not st.session_state.get("logged_in", False):
        st.markdown("""
<style>
html {
    background:
        radial-gradient(1100px 640px at 16% 26%, rgba(20,224,184,0.12) 0%, transparent 60%),
        radial-gradient(920px 560px at 86% 78%, rgba(14,165,233,0.11) 0%, transparent 60%),
        linear-gradient(180deg, #050B14 0%, #081222 48%, #04090F 100%) !important;
}
body { background: transparent !important; }
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"]>section,
[data-testid="stMain"],
[data-testid="stMainBlockContainer"],
.main, .main>div {
    background: transparent !important;
}

.vtm-video-bg {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    object-fit: cover;
    z-index: -2;
    pointer-events: none;
    opacity: 1;
}
.vtm-bgoverlay {
    position: fixed;
    inset: 0;
    z-index: -1;
    pointer-events: none;
    background:
        radial-gradient(ellipse at 26% 38%, rgba(20,224,184,0.08) 0%, transparent 55%),
        linear-gradient(180deg, rgba(0,0,0,0.62) 0%, rgba(0,0,0,0.48) 45%, rgba(0,0,0,0.72) 100%);
}

html, body,
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"]>section {
    height: 100vh !important;
    max-height: 100vh !important;
    overflow: hidden !important;
}
[data-testid="stMain"] {
    height: 100vh !important;
    max-height: 100vh !important;
    overflow: hidden !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}
[data-testid="stMainBlockContainer"] {
    max-width: 1180px !important;
    width: 100% !important;
    padding-top: 0 !important;
    padding-bottom: 0 !important;
    margin: 0 auto !important;
}
[data-testid="stHorizontalBlock"] {
    zoom: 0.93;
}

[data-testid="stHorizontalBlock"] { align-items: center !important; }

@keyframes vtmEnterBrand {
    from { opacity: 0; transform: translateY(15px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes vtmEnterCard {
    from { opacity: 0; transform: translateY(20px); }
    to   { opacity: 1; transform: translateY(0); }
}

.vtm-brand {
    padding: 0 26px 0 4px;
    animation: vtmEnterBrand 0.7s cubic-bezier(0.22, 1, 0.36, 1) 0.05s backwards;
}
.vtm-brand-logo img {
    width: 150px; max-width: 42vw; height: auto; display: block;
    filter: drop-shadow(0 0 26px rgba(20,224,184,0.35));
    margin-bottom: 26px;
}
.vtm-brand-title {
    color: #E8FFFA; font-size: 2.45rem; font-weight: 900;
    letter-spacing: 0.12em; line-height: 1.05; margin: 0;
    background: linear-gradient(120deg, #7FF7DE 0%, #2DD4BF 45%, #38BDF8 100%);
    -webkit-background-clip: text; background-clip: text;
    -webkit-text-fill-color: transparent;
}
.vtm-brand-sub {
    color: #5EEAD4; font-size: 0.98rem; font-weight: 700;
    letter-spacing: 0.42em; margin: 10px 0 0 2px;
}

.vtm-hx-badge {
    display: inline-block; margin: 26px 0 0;
    padding: 6px 14px; border-radius: 999px;
    background: rgba(45,212,191,0.10);
    border: 1px solid rgba(45,212,191,0.42);
    color: #7FF7DE; font-size: 0.82rem; font-weight: 900;
    letter-spacing: 0.14em;
}
.vtm-hx-line1 {
    color: #DCE8F5; font-size: 1.02rem; font-weight: 700;
    margin: 16px 0 0; letter-spacing: 0.01em;
}
.vtm-hx-line2 {
    font-size: 0.92rem; font-weight: 800; margin: 6px 0 0;
    background: linear-gradient(90deg, #7FF7DE 0%, #38BDF8 100%);
    -webkit-background-clip: text; background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: 0.04em;
}
.vtm-brand-tag {
    color: #7E93AB; font-size: 0.84rem; font-weight: 500;
    margin: 12px 0 0; letter-spacing: 0.02em;
}

.vtm-feat-row { display: flex; gap: 34px; margin-top: 36px; flex-wrap: wrap; }
.vtm-feat { text-align: center; min-width: 86px; }
.vtm-feat svg { width: 28px; height: 28px; margin-bottom: 8px; }
.vtm-feat-t { color: #F1F5F9; font-size: 0.84rem; font-weight: 800; margin: 0; }
.vtm-feat-d { color: #7E93AB; font-size: 0.74rem; font-weight: 500; margin: 4px 0 0; }

.vtm-wf-panel {
    margin-top: 32px; max-width: 480px;
    background: rgba(18,24,38,0.42);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(94,234,212,0.16);
    border-radius: 16px;
    padding: 16px 18px 14px;
    box-shadow: 0 16px 44px rgba(0,0,0,0.4);
}
.vtm-wf-head {
    color: #5EEAD4; font-size: 0.72rem; font-weight: 900;
    letter-spacing: 0.2em; margin-bottom: 12px;
    display: flex; align-items: center; gap: 7px;
}
.vtm-wf-head-dot {
    width: 7px; height: 7px; border-radius: 50%;
    background: #2DD4BF; display: inline-block;
    box-shadow: 0 0 8px rgba(45,212,191,0.9);
    animation: vtmPulse 2s ease-in-out infinite;
}
.vtm-wf-grid { display: flex; gap: 10px; }
.vtm-wf-item {
    flex: 1; text-align: center;
    background: rgba(8,17,31,0.55);
    border: 1px solid rgba(94,234,212,0.10);
    border-radius: 12px; padding: 12px 6px 10px;
}
.vtm-wf-num {
    display: block; font-size: 1.55rem; font-weight: 900; line-height: 1;
    background: linear-gradient(120deg, #7FF7DE 0%, #38BDF8 100%);
    -webkit-background-clip: text; background-clip: text;
    -webkit-text-fill-color: transparent;
}
.vtm-wf-lbl {
    display: block; color: #A9BDD3; font-size: 0.68rem;
    font-weight: 700; margin-top: 6px; letter-spacing: 0.02em;
}
.vtm-wf-state {
    display: inline-block; margin-top: 6px;
    font-size: 0.62rem; font-weight: 800;
    padding: 2px 8px; border-radius: 999px;
}
.vtm-wf-state.on    { color: #34D399; background: rgba(52,211,153,0.12); border: 1px solid rgba(52,211,153,0.35); }
.vtm-wf-state.run   { color: #38BDF8; background: rgba(56,189,248,0.12); border: 1px solid rgba(56,189,248,0.35); }
.vtm-wf-state.total { color: #7FF7DE; background: rgba(45,212,191,0.12); border: 1px solid rgba(45,212,191,0.35); }
.vtm-wf-foot {
    margin-top: 12px; padding-top: 10px;
    border-top: 1px solid rgba(94,234,212,0.10);
    display: flex; justify-content: space-between; align-items: center;
    color: #7E93AB; font-size: 0.74rem; font-weight: 700;
}
.vtm-op {
    color: #34D399; font-weight: 900;
    display: inline-flex; align-items: center; gap: 6px;
}
.vtm-op-dot {
    width: 8px; height: 8px; border-radius: 50%;
    background: #34D399; display: inline-block;
    box-shadow: 0 0 10px rgba(52,211,153,0.9);
    animation: vtmPulse 1.6s ease-in-out infinite;
}
@keyframes vtmPulse {
    0%, 100% { opacity: 1;   transform: scale(1); }
    50%      { opacity: 0.45; transform: scale(0.82); }
}

.vtm-copy { color: #55677E; font-size: 0.72rem; font-weight: 500; margin-top: 30px; }

[data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child,
[data-testid="stHorizontalBlock"] > div[data-testid="column"]:last-child {
    position: relative;
    background: rgba(18,24,38,0.42);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(94,234,212,0.10);
    border-radius: 24px;
    padding: 34px 30px 24px;
    box-shadow: 0 34px 90px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,255,255,0.06);
    animation: vtmEnterCard 0.9s cubic-bezier(0.22, 1, 0.36, 1) 0.18s backwards;
    transition: transform 0.45s cubic-bezier(0.22, 1, 0.36, 1),
                box-shadow 0.45s cubic-bezier(0.22, 1, 0.36, 1);
    will-change: transform;
}

[data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child:hover,
[data-testid="stHorizontalBlock"] > div[data-testid="column"]:last-child:hover {
    transform: scale(1.01);
    box-shadow: 0 40px 100px rgba(0,0,0,0.65), inset 0 1px 0 rgba(255,255,255,0.07);
}
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child:hover::before,
[data-testid="stHorizontalBlock"] > div[data-testid="column"]:last-child:hover::before {
    opacity: 1;
}
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child:hover::after,
[data-testid="stHorizontalBlock"] > div[data-testid="column"]:last-child:hover::after {
    opacity: 1;
}

@property --vtm-a {
    syntax: '<angle>';
    initial-value: 0deg;
    inherits: false;
}
@keyframes vtmNeonOrbit {
    to { --vtm-a: 360deg; }
}
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child::before,
[data-testid="stHorizontalBlock"] > div[data-testid="column"]:last-child::before {
    content: "";
    position: absolute;
    inset: -1.5px;
    border-radius: 25px;
    padding: 3px;
    background: conic-gradient(from var(--vtm-a, 0deg),
        transparent 0deg,
        transparent 205deg,
        rgba(34,211,238,0.30) 240deg,
        rgba(34,211,238,0.85) 275deg,
        rgba(59,130,246,0.95) 310deg,
        rgba(139,92,246,0.85) 338deg,
        rgba(139,92,246,0.25) 355deg,
        transparent 360deg);
    -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
    -webkit-mask-composite: xor;
            mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
            mask-composite: exclude;
    animation: vtmNeonOrbit 9s linear infinite;
    pointer-events: none;
    opacity: 0.92;
    transition: opacity 0.45s ease;
}
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child::after,
[data-testid="stHorizontalBlock"] > div[data-testid="column"]:last-child::after {
    content: "";
    position: absolute;
    inset: -3px;
    border-radius: 27px;
    padding: 6px;
    background: conic-gradient(from var(--vtm-a, 0deg),
        transparent 0deg,
        transparent 215deg,
        rgba(34,211,238,0.30) 262deg,
        rgba(59,130,246,0.42) 310deg,
        rgba(139,92,246,0.30) 345deg,
        transparent 360deg);
    -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
    -webkit-mask-composite: xor;
            mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
            mask-composite: exclude;
    filter: blur(8px);
    animation: vtmNeonOrbit 9s linear infinite;
    pointer-events: none;
    opacity: 0.8;
    transition: opacity 0.45s ease;
}

@media (prefers-reduced-motion: reduce) {
    .vtm-brand,
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child,
    [data-testid="stHorizontalBlock"] > div[data-testid="column"]:last-child,
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child::before,
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child::after {
        animation: none !important;
        transition: none !important;
    }
}
.vtm-login-card { text-align: center; margin-bottom: 16px; }
.vtm-login-card img {
    width: 56px; height: auto;
    filter: drop-shadow(0 0 14px rgba(20,224,184,0.45));
}
.vtm-card-os {
    color: #2DD4BF; font-size: 1rem; font-weight: 900;
    letter-spacing: 0.24em; margin: 10px 0 4px;
}
.vtm-card-welcome { color: #FFFFFF; font-size: 1.68rem; font-weight: 900; margin: 0; }
.vtm-card-sub { color: #8CA3BC; font-size: 0.85rem; font-weight: 500; margin: 8px 0 0; }
.vtm-nopw {
    background: rgba(45,212,191,0.10);
    border: 1px solid rgba(45,212,191,0.45);
    border-radius: 10px; padding: 9px; text-align: center; margin: 6px 0;
}
.vtm-nopw span { color: #2DD4BF; font-weight: 700; font-size: 0.84rem; }
.vtm-ver {
    text-align: center; color: #5E7490; font-size: 0.75rem;
    font-weight: 600; margin-top: 14px;
}
.vtm-ver b { color: #7E93AB; }

.stSelectbox>div>div {
    background: rgba(8,17,31,0.75) !important;
    border: 1px solid rgba(94,234,212,0.22) !important;
    border-radius: 12px !important;
}
.stSelectbox * { color: #E2E8F0 !important; font-weight: 600 !important; }
.stSelectbox svg { fill: #5EEAD4 !important; }

.stTextInput>div>div>input {
    background: rgba(8,17,31,0.75) !important;
    color: #E2E8F0 !important;
    border: 1px solid rgba(94,234,212,0.22) !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
}
.stTextInput>div>div>input::placeholder {
    color: #64748B !important; font-weight: 500 !important; opacity: 1 !important;
}
.stTextInput>div>div>input:focus,
.stSelectbox>div>div:focus-within {
    border-color: #2DD4BF !important;
    box-shadow: 0 0 0 3px rgba(45,212,191,0.18) !important;
}
.stTextInput button {
    background: transparent !important;
    border: none !important;
    color: #7E93AB !important;
    box-shadow: none !important;
}
.stTextInput button:hover { color: #2DD4BF !important; }

label, .stTextInput label, .stSelectbox label {
    color: #A9BDD3 !important; font-weight: 700 !important;
}

[data-baseweb="popover"] [role="listbox"],
[data-baseweb="popover"] ul {
    background: #0B1526 !important;
    border: 1px solid rgba(94,234,212,0.22) !important;
    border-radius: 12px !important;
}
[data-baseweb="popover"] li,
[data-baseweb="popover"] [role="option"] {
    color: #E2E8F0 !important;
    background: transparent !important;
}
[data-baseweb="popover"] li:hover,
[data-baseweb="popover"] [role="option"]:hover,
[data-baseweb="popover"] [aria-selected="true"] {
    background: rgba(45,212,191,0.14) !important;
    color: #7FF7DE !important;
}

.stButton>button {
    background: linear-gradient(90deg, #14E0B8 0%, #22C9DD 55%, #0EA5E9 100%) !important;
    color: #04121F !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 13px 18px !important;
    font-weight: 900 !important;
    font-size: 0.98rem !important;
    letter-spacing: 0.02em !important;
    box-shadow: 0 12px 34px rgba(20,224,184,0.34) !important;
}
.stButton>button:hover {
    background: linear-gradient(90deg, #3BF0CC 0%, #38D6EA 55%, #38BDF8 100%) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 16px 44px rgba(20,224,184,0.5) !important;
    color: #04121F !important;
}
.stButton>button *, .stButton>button p, .stButton>button span {
    color: #04121F !important; font-weight: 900 !important;
}

#vtm-stars { opacity: 0.35 !important; }

@media (max-width: 920px) {
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child,
    [data-testid="stHorizontalBlock"] > div[data-testid="column"]:first-child {
        display: none !important;
    }
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child,
    [data-testid="stHorizontalBlock"] > div[data-testid="column"]:last-child {
        width: 100% !important; flex: 1 1 100% !important;
        padding: 26px 20px 20px; border-radius: 20px;
    }
    [data-testid="stMainBlockContainer"] {
        padding-top: 0 !important;
        max-width: 460px !important;
    }
    .vtm-card-welcome { font-size: 1.48rem; }
}

@media (max-height: 760px) {
    [data-testid="stHorizontalBlock"] { zoom: 0.84; }
}
@media (max-height: 640px) {
    [data-testid="stHorizontalBlock"] { zoom: 0.74; }
}
</style>
""", unsafe_allow_html=True)


def inject_admin_theme():
    st.markdown(f"""
<style>
html {{
    background:
        radial-gradient(1200px 700px at 14% 20%, rgba(45,212,191,0.10) 0%, transparent 60%),
        radial-gradient(1000px 640px at 88% 82%, rgba(139,92,246,0.10) 0%, transparent 60%),
        linear-gradient(180deg, #050B14 0%, #081222 48%, #04090F 100%) !important;
}}
body {{ background: transparent !important; }}

.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"]>section,
[data-testid="stMain"],
[data-testid="stMainBlockContainer"],
.main, .main>div {{
    background: transparent !important;
}}

html, body,
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"]>section {{
    height: 100vh !important;
    max-height: 100vh !important;
    overflow: hidden !important;
    scrollbar-width: none !important;
    -ms-overflow-style: none !important;
}}
html::-webkit-scrollbar,
body::-webkit-scrollbar,
.stApp::-webkit-scrollbar,
[data-testid="stAppViewContainer"]::-webkit-scrollbar,
[data-testid="stAppViewContainer"]>section::-webkit-scrollbar {{
    width: 0 !important; height: 0 !important; display: none !important;
}}
[data-testid="stMain"] {{
    height: 100vh !important;
    max-height: 100vh !important;
    overflow-y: auto !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: flex-start !important;
    scrollbar-width: none !important;
    -ms-overflow-style: none !important;
}}
[data-testid="stMain"]::-webkit-scrollbar {{
    width: 0 !important; height: 0 !important; display: none !important;
}}
[data-testid="stMainBlockContainer"] {{
    max-width: 1400px !important;
    width: 100% !important;
    margin: 0 auto !important;
    padding-top: 8px !important;
    padding-bottom: 8px !important;
}}

.vtm-admin-video {{
    position: fixed;
    top: 0; left: 0;
    width: 100vw; height: 100vh;
    object-fit: cover;
    z-index: -2;
    pointer-events: none;
    opacity: 1;
}}
.vtm-admin-overlay {{
    position: fixed;
    inset: 0;
    z-index: -1;
    pointer-events: none;
    background:
        radial-gradient(ellipse at 22% 30%, rgba(45,212,191,0.07) 0%, transparent 55%),
        radial-gradient(ellipse at 82% 78%, rgba(139,92,246,0.07) 0%, transparent 55%),
        linear-gradient(180deg, rgba(4,9,18,0.80) 0%, rgba(6,14,26,0.72) 45%, rgba(4,9,15,0.86) 100%);
}}

#vtm-stars {{ opacity: 0.28 !important; }}

.vtm-card {{
    background: rgba(18,24,38,0.42) !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
    border: 1px solid rgba(94,234,212,0.14) !important;
    border-radius: 16px !important;
    box-shadow: 0 12px 40px rgba(0,0,0,0.45) !important;
}}
.vtm-card * {{ color: #E7EEF7 !important; }}
.vtm-card h3 {{ color: #7FF7DE !important; }}

.met-card {{
    background: rgba(18,24,38,0.42) !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
    border: 1px solid rgba(94,234,212,0.18) !important;
    border-radius: 16px !important;
    box-shadow: 0 12px 36px rgba(0,0,0,0.45) !important;
}}
.met-val {{
    background: linear-gradient(120deg, #7FF7DE 0%, #38BDF8 100%) !important;
    -webkit-background-clip: text !important; background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    color: #7FF7DE !important;
}}
.met-lbl {{ color: #A9BDD3 !important; }}

.topbar {{
    background: rgba(18,24,38,0.42) !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
    border-bottom: 2px solid rgba(45,212,191,0.55) !important;
    box-shadow: 0 8px 28px rgba(0,0,0,0.4) !important;
}}
.tb-title {{ color: #7FF7DE !important; }}

.stButton>button {{
    background: linear-gradient(90deg, #14E0B8 0%, #22C9DD 55%, #0EA5E9 100%) !important;
    color: #04121F !important;
    border: none !important;
    border-radius: 12px !important;
    box-shadow: 0 8px 24px rgba(20,224,184,0.28) !important;
}}
.stButton>button:hover {{
    background: linear-gradient(90deg, #3BF0CC 0%, #38D6EA 55%, #38BDF8 100%) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 12px 34px rgba(20,224,184,0.44) !important;
    color: #04121F !important;
}}
.stButton>button *, .stButton>button p, .stButton>button span {{
    color: #04121F !important; font-weight: 900 !important;
}}

.stTextInput>div>div>input,
.stNumberInput>div>div>input,
.stDateInput>div>div>input {{
    background: rgba(8,17,31,0.72) !important;
    color: #E7EEF7 !important;
    border: 1px solid rgba(94,234,212,0.22) !important;
    border-radius: 10px !important;
}}
.stTextInput>div>div>input::placeholder {{ color: #6B7E96 !important; }}
.stTextArea textarea {{
    background: rgba(8,17,31,0.72) !important;
    color: #E7EEF7 !important;
    border: 1px solid rgba(94,234,212,0.22) !important;
    border-radius: 10px !important;
}}
.stTextArea textarea::placeholder {{ color: #6B7E96 !important; }}
.stSelectbox>div>div,
.stMultiSelect>div>div {{
    background: rgba(8,17,31,0.72) !important;
    border: 1px solid rgba(94,234,212,0.22) !important;
    border-radius: 10px !important;
}}
.stSelectbox *, .stMultiSelect * {{ color: #E7EEF7 !important; }}
.stSelectbox svg, .stMultiSelect svg {{ fill: #5EEAD4 !important; }}

label,.stTextInput label,.stSelectbox label,.stTextArea label,
.stSlider label,.stNumberInput label,.stDateInput label,.stMultiSelect label {{
    color: #A9BDD3 !important;
}}

[data-baseweb="popover"] [role="listbox"],
[data-baseweb="popover"] ul {{
    background: #0B1526 !important;
    border: 1px solid rgba(94,234,212,0.22) !important;
    border-radius: 12px !important;
}}
[data-baseweb="popover"] li,
[data-baseweb="popover"] [role="option"] {{
    color: #E2E8F0 !important; background: transparent !important;
}}
[data-baseweb="popover"] li:hover,
[data-baseweb="popover"] [role="option"]:hover,
[data-baseweb="popover"] [aria-selected="true"] {{
    background: rgba(45,212,191,0.14) !important; color: #7FF7DE !important;
}}

[data-testid="stDataFrame"] {{
    background: rgba(11,18,32,0.6) !important;
    border: 1px solid rgba(94,234,212,0.14) !important;
    border-radius: 12px !important;
}}

.vadm-hero {{
    display:flex; align-items:center; justify-content:space-between;
    flex-wrap:wrap; gap:14px;
    background: rgba(18,24,38,0.42);
    backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(94,234,212,0.16);
    border-radius: 18px;
    padding: 18px 26px;
    margin-bottom: 16px;
    box-shadow: 0 14px 44px rgba(0,0,0,0.45);
}}
.vadm-hero-left {{ display:flex; align-items:center; gap:16px; }}
.vadm-hero-logo img {{
    width: 48px; height: auto; display: block;
    filter: drop-shadow(0 0 14px rgba(20,224,184,0.45));
}}
.vadm-hero-title {{
    font-size: 1.35rem; font-weight: 900; margin:0; letter-spacing:0.02em;
    background: linear-gradient(120deg,#7FF7DE 0%,#38BDF8 55%,#8B5CF6 100%);
    -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent;
}}
.vadm-hero-sub {{ color:#94A3B8; font-size:0.8rem; font-weight:700; margin:4px 0 0; }}
.vadm-hero-badge {{
    display:inline-flex; align-items:center; gap:7px;
    background: rgba(52,211,153,0.12);
    border: 1px solid rgba(52,211,153,0.4);
    color:#34D399; font-weight:900; font-size:0.82rem;
    padding:7px 16px; border-radius:999px;
}}
.vadm-hero-dot {{
    width:8px; height:8px; border-radius:50%; background:#34D399;
    box-shadow:0 0 10px rgba(52,211,153,0.9);
    animation: vtmPulse 1.6s ease-in-out infinite;
}}

.vadm-kpi {{
    position:relative; overflow:hidden;
    background: rgba(18,24,38,0.42);
    backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(94,234,212,0.16);
    border-radius: 18px;
    padding: 20px 20px 18px;
    box-shadow: 0 14px 40px rgba(0,0,0,0.42);
    min-height: 132px;
}}
.vadm-kpi::before {{
    content:""; position:absolute; top:-40%; right:-30%;
    width:180px; height:180px; border-radius:50%;
    background: radial-gradient(circle, var(--glow,rgba(45,212,191,0.30)) 0%, transparent 70%);
    filter: blur(6px);
}}
.vadm-kpi .k-top {{ display:flex; align-items:flex-start; justify-content:space-between; }}
.vadm-kpi .k-num {{
    font-size: 2.4rem; font-weight:900; line-height:1;
    color:#F1F5F9; letter-spacing:-0.01em;
}}
.vadm-kpi .k-unit {{ font-size:1rem; font-weight:800; color:#94A3B8; margin-left:3px; }}
.vadm-kpi .k-lbl {{ color:#E2E8F0; font-size:0.92rem; font-weight:800; margin:10px 0 2px; }}
.vadm-kpi .k-en  {{ color:#7E93AB; font-size:0.68rem; font-weight:700; letter-spacing:0.14em; }}
.vadm-kpi .k-ico {{
    width:44px; height:44px; border-radius:12px;
    display:flex; align-items:center; justify-content:center; font-size:1.3rem;
    border:1px solid rgba(255,255,255,0.08);
}}
.vadm-kpi.c-teal   {{ --glow:rgba(45,212,191,0.30); }}
.vadm-kpi.c-teal   .k-ico {{ background:rgba(45,212,191,0.14); }}
.vadm-kpi.c-violet {{ --glow:rgba(139,92,246,0.30); }}
.vadm-kpi.c-violet .k-ico {{ background:rgba(139,92,246,0.16); }}
.vadm-kpi.c-cyan   {{ --glow:rgba(56,189,248,0.30); }}
.vadm-kpi.c-cyan   .k-ico {{ background:rgba(56,189,248,0.14); }}
.vadm-kpi.c-gold   {{ --glow:rgba(212,175,55,0.30); border-color:rgba(212,175,55,0.35); }}
.vadm-kpi.c-gold   .k-ico {{ background:rgba(212,175,55,0.14); }}
.vadm-kpi.c-gold   .k-num {{
    background:linear-gradient(120deg,#F6D365,#D4AF37);
    -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent;
}}

.vadm-sec-title {{
    display:flex; align-items:center; gap:9px;
    color:#7FF7DE; font-size:0.96rem; font-weight:900;
    letter-spacing:0.04em; margin:6px 0 10px;
}}
.vadm-sec-title .cnt {{
    font-size:0.72rem; font-weight:800; color:#38BDF8;
    background:rgba(56,189,248,0.12); border:1px solid rgba(56,189,248,0.3);
    padding:2px 10px; border-radius:999px;
}}

.vadm-emp-row {{
    display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;
    background: rgba(18,24,38,0.42);
    backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(94,234,212,0.10);
    border-radius: 12px; padding: 12px 18px; margin:5px 0;
}}
.vadm-emp-name {{ font-size:0.98rem; font-weight:900; color:#F1F5F9; }}
.vadm-chip {{ font-weight:800; font-size:0.82rem; padding:3px 10px; border-radius:8px; }}
.vadm-chip.on  {{ color:#34D399; background:rgba(52,211,153,0.12); }}
.vadm-chip.off {{ color:#FCA5A5; background:rgba(239,68,68,0.12); }}
.vadm-chip.mut {{ color:#94A3B8; background:rgba(148,163,184,0.10); }}
.vadm-chip.rep {{ color:#38BDF8; background:rgba(56,189,248,0.12); }}
.vadm-chip.gold{{ color:#F6D365; background:rgba(212,175,55,0.12); }}

.vai-panel {{
    background: rgba(18,24,38,0.42);
    backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(139,92,246,0.24);
    border-radius: 18px;
    padding: 18px 20px 16px;
    box-shadow: 0 14px 44px rgba(0,0,0,0.5);
    height: 100%;
}}
.vai-head {{
    display:flex; align-items:center; justify-content:space-between; margin-bottom:12px;
}}
.vai-head .t {{
    display:flex; align-items:center; gap:8px;
    color:#C4B5FD; font-size:0.92rem; font-weight:900; letter-spacing:0.03em;
}}
.vai-head .live {{
    display:inline-flex; align-items:center; gap:6px;
    color:#8B5CF6; font-size:0.68rem; font-weight:900; letter-spacing:0.1em;
    background:rgba(139,92,246,0.12); border:1px solid rgba(139,92,246,0.35);
    padding:3px 10px; border-radius:999px;
}}
.vai-live-dot {{
    width:7px; height:7px; border-radius:50%; background:#8B5CF6;
    box-shadow:0 0 8px rgba(139,92,246,0.9);
    animation: vtmPulse 1.4s ease-in-out infinite;
}}

.vai-view {{
    position:relative; height:216px; overflow:hidden;
    -webkit-mask-image: linear-gradient(180deg, transparent 0, #000 12%, #000 88%, transparent 100%);
            mask-image: linear-gradient(180deg, transparent 0, #000 12%, #000 88%, transparent 100%);
}}
.vai-track {{
    display:flex; flex-direction:column; gap:8px;
    animation: vaiRoll 21s linear infinite;
}}
.vai-view:hover .vai-track {{ animation-play-state: paused; }}
.vai-item {{
    display:flex; align-items:center; gap:12px;
    background: rgba(23,30,48,0.7);
    border: 1px solid rgba(139,92,246,0.14);
    border-radius: 12px; padding: 10px 14px;
    min-height: 64px;
}}
.vai-ava {{
    width:38px; height:38px; border-radius:10px; flex-shrink:0;
    display:flex; align-items:center; justify-content:center; font-size:1.15rem;
    background: linear-gradient(135deg, rgba(139,92,246,0.28), rgba(56,189,248,0.22));
    border:1px solid rgba(139,92,246,0.3);
}}
.vai-info {{ flex:1; min-width:0; }}
.vai-name {{ color:#F1F5F9; font-size:0.9rem; font-weight:800; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.vai-task {{ color:#A9BDD3; font-size:0.76rem; font-weight:600; margin-top:2px;
    white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.vai-state {{
    flex-shrink:0; display:inline-flex; align-items:center; gap:5px;
    color:#34D399; font-size:0.66rem; font-weight:900;
    background:rgba(52,211,153,0.12); border:1px solid rgba(52,211,153,0.3);
    padding:3px 9px; border-radius:999px;
}}
.vai-state-dot {{
    width:6px; height:6px; border-radius:50%; background:#34D399;
    box-shadow:0 0 6px rgba(52,211,153,0.9);
    animation: vtmPulse 1.5s ease-in-out infinite;
}}
@keyframes vaiRoll {{
    0%   {{ transform: translateY(0); }}
    100% {{ transform: translateY(-50%); }}
}}
@media (prefers-reduced-motion: reduce) {{
    .vai-track {{ animation: none !important; }}
}}
.vai-foot {{
    margin-top:12px; padding-top:10px; border-top:1px solid rgba(139,92,246,0.14);
    display:flex; justify-content:space-between; align-items:center;
    color:#94A3B8; font-size:0.74rem; font-weight:700;
}}
.vai-foot .op {{ color:#34D399; font-weight:900; display:inline-flex; align-items:center; gap:6px; }}

@media (max-width: 920px) {{
    .vadm-kpi .k-num {{ font-size:2rem; }}
}}
</style>
""", unsafe_allow_html=True)

    st.markdown(f"""
    <video id="vtm-admin-bg-video" autoplay muted loop playsinline preload="auto" class="vtm-admin-video">
        <source src="{VTM_ADMIN_BG_VIDEO_URL}" type="video/mp4">
    </video>
    <div class="vtm-admin-overlay"></div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
#  ▼▼▼ 디렉터/직원 홈 전용 테마 + 배경 영상 (VTM OS 2.0.8 신규) ▼▼▼
#  · 로그인 후 is_admin=False 이고 page == "home" 일 때만 주입됨
#    → 출퇴근/업무보고/달력/VTM WAY 화면에는 영향 없음
#  · 배경: HTML5 Video (vtm02.mp4) + Dark Overlay (전체화면 fixed cover)
#  · 폴백: html(root) 다크 그라데이션 (영상 로드 실패 시 자동 노출)
#  · 카드: 로그인 박스와 동일 Glassmorphism
#    rgba(18,24,38,0.42) + backdrop-filter: blur(20px)
#  · 표시 전용 스타일이며 DB/세션 로직과 무관
# ═══════════════════════════════════════════════════════════════════
def inject_director_theme():
    st.markdown("""
<style>
html {
    background:
        radial-gradient(1200px 700px at 14% 20%, rgba(45,212,191,0.10) 0%, transparent 60%),
        radial-gradient(1000px 640px at 88% 82%, rgba(139,92,246,0.10) 0%, transparent 60%),
        linear-gradient(180deg, #050B14 0%, #081222 48%, #04090F 100%) !important;
}
body { background: transparent !important; }

.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"]>section,
[data-testid="stMain"],
[data-testid="stMainBlockContainer"],
.main, .main>div {
    background: transparent !important;
}

/* ── 디렉터 홈: 위→아래 자연 스크롤 보장 (내용이 길어도 전체 표시) ── */
html, body,
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"]>section {
    height: auto !important;
    min-height: 100vh !important;
    max-height: none !important;
    overflow-x: hidden !important;
    overflow-y: auto !important;
}
[data-testid="stMain"] {
    height: auto !important;
    min-height: 100vh !important;
    max-height: none !important;
    overflow: visible !important;
    display: block !important;
}

.vtm-dir-video {
    position: fixed;
    top: 0; left: 0;
    width: 100vw; height: 100vh;
    object-fit: cover;
    z-index: -2;
    pointer-events: none;
    opacity: 1;
}
.vtm-dir-overlay {
    position: fixed;
    inset: 0;
    z-index: -1;
    pointer-events: none;
    background:
        radial-gradient(ellipse at 22% 30%, rgba(45,212,191,0.07) 0%, transparent 55%),
        radial-gradient(ellipse at 82% 78%, rgba(139,92,246,0.07) 0%, transparent 55%),
        linear-gradient(180deg, rgba(4,9,18,0.80) 0%, rgba(6,14,26,0.72) 45%, rgba(4,9,15,0.86) 100%);
}

#vtm-stars { opacity: 0.28 !important; }

[data-testid="stMainBlockContainer"] {
    max-width: 1400px !important;
    width: 100% !important;
    margin-left: auto !important;
    margin-right: auto !important;
    padding-top: 12px !important;
    padding-bottom: 16px !important;
}

.stButton>button {
    background: linear-gradient(90deg, #14E0B8 0%, #22C9DD 55%, #0EA5E9 100%) !important;
    color: #04121F !important;
    border: none !important;
    border-radius: 12px !important;
    box-shadow: 0 8px 24px rgba(20,224,184,0.28) !important;
}
.stButton>button:hover {
    background: linear-gradient(90deg, #3BF0CC 0%, #38D6EA 55%, #38BDF8 100%) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 12px 34px rgba(20,224,184,0.44) !important;
    color: #04121F !important;
}
.stButton>button *, .stButton>button p, .stButton>button span {
    color: #04121F !important; font-weight: 900 !important;
}

.vtm-card {
    background: rgba(18,24,38,0.42) !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
    border: 1px solid rgba(94,234,212,0.14) !important;
    border-radius: 16px !important;
    box-shadow: 0 12px 40px rgba(0,0,0,0.45) !important;
}
.vtm-card * { color: #E7EEF7 !important; }
.vtm-card h3 { color: #7FF7DE !important; }
.met-card {
    background: rgba(18,24,38,0.42) !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
    border: 1px solid rgba(94,234,212,0.18) !important;
    border-radius: 16px !important;
}
.topbar {
    background: rgba(18,24,38,0.42) !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
    border-bottom: 2px solid rgba(45,212,191,0.55) !important;
}
.tb-title { color: #7FF7DE !important; }

/* ── 입력창/텍스트영역/셀렉트: 다크 글래스 (출퇴근·업무보고·달력 통일) ── */
.stTextInput>div>div>input,
.stNumberInput>div>div>input,
.stDateInput>div>div>input {
    background: rgba(8,17,31,0.72) !important;
    color: #E7EEF7 !important;
    border: 1px solid rgba(94,234,212,0.22) !important;
    border-radius: 10px !important;
}
.stTextInput>div>div>input::placeholder,
.stNumberInput>div>div>input::placeholder {
    color: #6B7E96 !important; opacity: 1 !important;
}
.stTextArea textarea {
    background: rgba(8,17,31,0.72) !important;
    color: #E7EEF7 !important;
    border: 1px solid rgba(94,234,212,0.22) !important;
    border-radius: 10px !important;
}
.stTextArea textarea::placeholder { color: #6B7E96 !important; opacity: 1 !important; }
.stSelectbox>div>div,
.stMultiSelect>div>div {
    background: rgba(8,17,31,0.72) !important;
    border: 1px solid rgba(94,234,212,0.22) !important;
    border-radius: 10px !important;
}
.stSelectbox *, .stMultiSelect * { color: #E7EEF7 !important; }
.stSelectbox svg, .stMultiSelect svg { fill: #5EEAD4 !important; }

label,.stTextInput label,.stSelectbox label,.stTextArea label,
.stSlider label,.stNumberInput label,.stDateInput label,.stMultiSelect label {
    color: #A9BDD3 !important;
}

/* selectbox/date 팝오버 */
[data-baseweb="popover"] [role="listbox"],
[data-baseweb="popover"] ul {
    background: #0B1526 !important;
    border: 1px solid rgba(94,234,212,0.22) !important;
    border-radius: 12px !important;
}
[data-baseweb="popover"] li,
[data-baseweb="popover"] [role="option"] {
    color: #E2E8F0 !important; background: transparent !important;
}
[data-baseweb="popover"] li:hover,
[data-baseweb="popover"] [role="option"]:hover,
[data-baseweb="popover"] [aria-selected="true"] {
    background: rgba(45,212,191,0.14) !important; color: #7FF7DE !important;
}

/* 데이터프레임(출퇴근 기록 등) 다크 톤 */
[data-testid="stDataFrame"] {
    background: rgba(11,18,32,0.6) !important;
    border: 1px solid rgba(94,234,212,0.14) !important;
    border-radius: 12px !important;
}
[data-testid="stDataFrame"] * { color: #F1F5F9 !important; }

/* 탭(업무보고 오전/오후) 가독성 */
.stTabs [data-baseweb="tab-list"] { border-bottom-color: rgba(94,234,212,0.18) !important; }
.stTabs [data-baseweb="tab"] { color: #A9BDD3 !important; }
.stTabs [aria-selected="true"] { color: #7FF7DE !important; }

@keyframes vdirPulse {
    0%, 100% { opacity: 1;    transform: scale(1); }
    50%      { opacity: 0.45; transform: scale(0.82); }
}

.vdir-hero {
    display:flex; align-items:center; justify-content:space-between;
    flex-wrap:wrap; gap:14px;
    background: rgba(18,24,38,0.42);
    backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(94,234,212,0.16);
    border-radius: 18px;
    padding: 20px 28px;
    margin-bottom: 14px;
    box-shadow: 0 14px 44px rgba(0,0,0,0.45);
    position: relative; z-index: 1;
}
.vdir-hero-left { display:flex; align-items:center; gap:16px; }
.vdir-hero-logo img {
    width: 48px; height: auto; display: block;
    filter: drop-shadow(0 0 14px rgba(20,224,184,0.45));
}
.vdir-hero-title {
    font-size: 1.5rem; font-weight: 900; margin:0; letter-spacing:0.01em;
    color:#F1F5F9;
}
.vdir-hero-title .nm {
    background: linear-gradient(120deg,#7FF7DE 0%,#38BDF8 100%);
    -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent;
}
.vdir-hero-sub { color:#A9BDD3; font-size:0.88rem; font-weight:700; margin:6px 0 0; }
.vdir-hero-time { text-align:right; }
.vdir-hero-time .d { color:#94A3B8; font-size:0.8rem; font-weight:800; }
.vdir-hero-time .t {
    font-size:2rem; font-weight:900; line-height:1.1; letter-spacing:0.02em;
    color:#FFFFFF; text-shadow: 0 0 20px rgba(56,189,248,0.35);
}

.vdir-kpi-grid {
    display:grid;
    grid-template-columns: repeat(auto-fit, minmax(178px, 1fr));
    gap: 12px;
    margin-bottom: 14px;
    position: relative; z-index: 1;
}
.vdir-kpi {
    position:relative; overflow:hidden;
    background: rgba(18,24,38,0.42);
    backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(94,234,212,0.16);
    border-radius: 16px;
    padding: 16px 16px 14px;
    box-shadow: 0 12px 36px rgba(0,0,0,0.42);
    min-height: 118px;
}
.vdir-kpi::before {
    content:""; position:absolute; top:-45%; right:-32%;
    width:160px; height:160px; border-radius:50%;
    background: radial-gradient(circle, var(--glow,rgba(45,212,191,0.28)) 0%, transparent 70%);
    filter: blur(6px);
}
.vdir-kpi .k-ico {
    width:38px; height:38px; border-radius:11px;
    display:flex; align-items:center; justify-content:center; font-size:1.15rem;
    border:1px solid rgba(255,255,255,0.08);
    margin-bottom:9px;
    background: var(--icobg, rgba(45,212,191,0.14));
}
.vdir-kpi .k-lbl { color:#A9BDD3; font-size:0.76rem; font-weight:800; letter-spacing:0.02em; }
.vdir-kpi .k-val {
    font-size:1.55rem; font-weight:900; line-height:1.2; margin:2px 0;
    color:#F1F5F9;
}
.vdir-kpi .k-sub { color:#7E93AB; font-size:0.72rem; font-weight:700; }
.vdir-kpi.c-teal   { --glow:rgba(45,212,191,0.30);  --icobg:rgba(45,212,191,0.14); }
.vdir-kpi.c-teal   .k-val {
    background: linear-gradient(120deg,#7FF7DE 0%,#2DD4BF 100%);
    -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent;
}
.vdir-kpi.c-cyan   { --glow:rgba(56,189,248,0.30);  --icobg:rgba(56,189,248,0.14); }
.vdir-kpi.c-cyan   .k-val {
    background: linear-gradient(120deg,#7DD3FC 0%,#38BDF8 100%);
    -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent;
}
.vdir-kpi.c-violet { --glow:rgba(139,92,246,0.30);  --icobg:rgba(139,92,246,0.16); }
.vdir-kpi.c-violet .k-val {
    background: linear-gradient(120deg,#C4B5FD 0%,#8B5CF6 100%);
    -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent;
}
.vdir-kpi.c-gold   { --glow:rgba(212,175,55,0.26);  --icobg:rgba(212,175,55,0.12);
                     border-color:rgba(212,175,55,0.28); }
.vdir-kpi.c-gold   .k-val {
    background: linear-gradient(120deg,#F6D365 0%,#D4AF37 100%);
    -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent;
}

.vdir-panel {
    background: rgba(18,24,38,0.42);
    backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(94,234,212,0.14);
    border-radius: 18px;
    padding: 18px 20px 16px;
    box-shadow: 0 14px 44px rgba(0,0,0,0.45);
    position: relative; z-index: 1;
    margin-bottom: 12px;
}
.vdir-sec-title {
    display:flex; align-items:center; justify-content:space-between; gap:9px;
    color:#7FF7DE; font-size:0.94rem; font-weight:900;
    letter-spacing:0.04em; margin:0 0 12px;
}
.vdir-sec-title .cnt {
    font-size:0.7rem; font-weight:800; color:#38BDF8;
    background:rgba(56,189,248,0.12); border:1px solid rgba(56,189,248,0.3);
    padding:2px 10px; border-radius:999px;
}

.vdir-tl { position:relative; padding-left: 4px; }
.vdir-tl-item {
    display:flex; gap:14px; position:relative;
    padding: 0 0 18px 0;
}
.vdir-tl-item:last-child { padding-bottom: 4px; }
.vdir-tl-rail {
    display:flex; flex-direction:column; align-items:center; flex-shrink:0;
}
.vdir-tl-dot {
    width:11px; height:11px; border-radius:50%;
    background: var(--dot,#2DD4BF);
    box-shadow: 0 0 10px var(--dot,#2DD4BF);
    margin-top: 4px;
}
.vdir-tl-line {
    width:2px; flex:1; margin-top:4px;
    background: linear-gradient(180deg, var(--dot,#2DD4BF), rgba(94,234,212,0.08));
}
.vdir-tl-item:last-child .vdir-tl-line { display:none; }
.vdir-tl-time { color:#7FF7DE; font-size:0.86rem; font-weight:900; min-width:52px; padding-top:2px; }
.vdir-tl-body .t { color:#F1F5F9; font-size:0.9rem; font-weight:800; }
.vdir-tl-body .d { color:#8CA3BC; font-size:0.76rem; font-weight:600; margin-top:2px; }
.vdir-tl-item.c-teal   { --dot:#2DD4BF; }
.vdir-tl-item.c-cyan   { --dot:#38BDF8; }
.vdir-tl-item.c-violet { --dot:#8B5CF6; }
.vdir-tl-item.c-gold   { --dot:#D4AF37; }
.vdir-tl-item.c-mut    { --dot:#64748B; }

.vdir-todo-item {
    display:flex; align-items:center; justify-content:space-between; gap:10px;
    background: rgba(8,17,31,0.5);
    border: 1px solid rgba(94,234,212,0.10);
    border-radius: 11px;
    padding: 11px 14px;
    margin: 6px 0;
}
.vdir-todo-item .lt { display:flex; align-items:center; gap:10px; }
.vdir-todo-ck {
    width:19px; height:19px; border-radius:5px; flex-shrink:0;
    border: 1.5px solid rgba(56,189,248,0.6);
    background: rgba(56,189,248,0.10);
    display:flex; align-items:center; justify-content:center;
    color:#38BDF8; font-size:0.68rem; font-weight:900;
}
.vdir-todo-txt { color:#E7EEF7; font-size:0.86rem; font-weight:700; }
.vdir-todo-arw { color:#5E7490; font-size:0.9rem; font-weight:900; }

.vdir-sys-row {
    display:flex; align-items:center; justify-content:space-between;
    padding: 9px 2px;
    border-bottom: 1px solid rgba(94,234,212,0.08);
}
.vdir-sys-row:last-child { border-bottom:none; }
.vdir-sys-lbl {
    display:inline-flex; align-items:center; gap:9px;
    color:#CBD5E1; font-size:0.86rem; font-weight:700;
}
.vdir-sys-lbl .ic { font-size:1rem; }
.vdir-sys-val { font-size:0.86rem; font-weight:900; }
.vdir-sys-val.teal  { color:#7FF7DE; }
.vdir-sys-val.cyan  { color:#38BDF8; }
.vdir-sys-val.green { color:#34D399; }

.vdai-panel {
    background: rgba(18,24,38,0.42);
    backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(139,92,246,0.24);
    border-radius: 18px;
    padding: 18px 20px 16px;
    box-shadow: 0 14px 44px rgba(0,0,0,0.5);
    position: relative; z-index: 1;
    margin-bottom: 12px;
}
.vdai-head {
    display:flex; align-items:center; justify-content:space-between; margin-bottom:12px;
}
.vdai-head .t {
    display:flex; align-items:center; gap:8px;
    color:#C4B5FD; font-size:0.92rem; font-weight:900; letter-spacing:0.03em;
}
.vdai-head .live {
    display:inline-flex; align-items:center; gap:6px;
    color:#8B5CF6; font-size:0.68rem; font-weight:900; letter-spacing:0.1em;
    background:rgba(139,92,246,0.12); border:1px solid rgba(139,92,246,0.35);
    padding:3px 10px; border-radius:999px;
}
.vdai-live-dot {
    width:7px; height:7px; border-radius:50%; background:#8B5CF6;
    box-shadow:0 0 8px rgba(139,92,246,0.9);
    animation: vdirPulse 1.4s ease-in-out infinite;
}
.vdai-view {
    position:relative; height:432px; overflow:hidden;
    -webkit-mask-image: linear-gradient(180deg, transparent 0, #000 8%, #000 92%, transparent 100%);
            mask-image: linear-gradient(180deg, transparent 0, #000 8%, #000 92%, transparent 100%);
}
.vdai-track {
    display:flex; flex-direction:column; gap:8px;
    animation: vdaiRoll 21s linear infinite;
}
.vdai-view:hover .vdai-track { animation-play-state: paused; }
.vdai-item {
    display:flex; align-items:center; gap:12px;
    background: rgba(23,30,48,0.7);
    border: 1px solid rgba(139,92,246,0.14);
    border-radius: 12px; padding: 10px 14px;
    min-height: 64px;
}
.vdai-ava {
    width:38px; height:38px; border-radius:10px; flex-shrink:0;
    display:flex; align-items:center; justify-content:center; font-size:1.15rem;
    background: linear-gradient(135deg, rgba(139,92,246,0.28), rgba(56,189,248,0.22));
    border:1px solid rgba(139,92,246,0.3);
}
.vdai-info { flex:1; min-width:0; }
.vdai-name { color:#F1F5F9; font-size:0.9rem; font-weight:800; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.vdai-task { color:#A9BDD3; font-size:0.76rem; font-weight:600; margin-top:2px;
    white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.vdai-state {
    flex-shrink:0; display:inline-flex; align-items:center; gap:5px;
    color:#34D399; font-size:0.66rem; font-weight:900;
    background:rgba(52,211,153,0.12); border:1px solid rgba(52,211,153,0.3);
    padding:3px 9px; border-radius:999px;
}
.vdai-state-dot {
    width:6px; height:6px; border-radius:50%; background:#34D399;
    box-shadow:0 0 6px rgba(52,211,153,0.9);
    animation: vdirPulse 1.5s ease-in-out infinite;
}
@keyframes vdaiRoll {
    0%   { transform: translateY(0); }
    100% { transform: translateY(-50%); }
}
@media (prefers-reduced-motion: reduce) {
    .vdai-track { animation: none !important; }
    .vdai-live-dot, .vdai-state-dot { animation: none !important; }
}
.vdai-foot {
    margin-top:12px; padding-top:10px; border-top:1px solid rgba(139,92,246,0.14);
    display:flex; justify-content:space-between; align-items:center;
    color:#94A3B8; font-size:0.74rem; font-weight:700;
}
.vdai-foot .op { color:#34D399; font-weight:900; display:inline-flex; align-items:center; gap:6px; }
.vdai-foot .op-dot {
    width:8px; height:8px; border-radius:50%; background:#34D399;
    box-shadow:0 0 10px rgba(52,211,153,0.9);
    animation: vdirPulse 1.6s ease-in-out infinite;
}
.vdir-hero-title .hello-text {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
}
@media (max-width: 920px) {
    .vdir-hero { flex-direction: column; align-items: flex-start; }
    .vdir-hero-time { text-align: left; }
    .vdir-hero-title { font-size: 1.25rem; }
    .vdir-kpi-grid { grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); }
    .vdai-view { height: 300px; }
}
</style>
""", unsafe_allow_html=True)

    st.markdown(f"""
    <video id="vtm-dir-bg-video" autoplay muted loop playsinline preload="auto" class="vtm-dir-video">
        <source src="{VTM_DIR_BG_VIDEO_URL}" type="video/mp4">
    </video>
    <div class="vtm-dir-overlay"></div>
    """, unsafe_allow_html=True)


def render_login():
    inject_all()

    st.markdown(f"""
    <video id="vtm-bg-video" autoplay muted loop playsinline preload="auto" class="vtm-video-bg">
        <source src="{VTM_BG_VIDEO_URL}" type="video/mp4">
    </video>
    <div id="vtm-bg-overlay" class="vtm-bgoverlay"></div>
    """, unsafe_allow_html=True)

    left, right = st.columns([1.25, 1], gap="large")

    with left:
        st.markdown(f"""
        <div class="vtm-brand">
          <div class="vtm-brand-logo">
            <img src="{VTM_LOGO_URL}" alt="VTM Logo">
          </div>
          <h1 class="vtm-brand-title">VTM</h1>
          <p class="vtm-brand-sub">OPERATING&nbsp;SYSTEM</p>

          <div class="vtm-hx-badge">HUMAN&nbsp;×&nbsp;AI&nbsp;WORKFORCE&nbsp;OS</div>
          <p class="vtm-hx-line1">Real people and AI employees working as one.</p>
          <p class="vtm-hx-line2">One Team. Two Workforces. Infinite Possibilities.</p>
          <p class="vtm-brand-tag">AI와 사람이 함께 만드는 브랜드 커넥트의 미래</p>

          <div class="vtm-feat-row">
            <div class="vtm-feat">
              <svg viewBox="0 0 24 24" fill="none" stroke="#2DD4BF" stroke-width="1.7"
                   stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 2l8 3.5v5.2c0 5-3.4 9.3-8 10.8-4.6-1.5-8-5.8-8-10.8V5.5L12 2z"/>
                <path d="M9 12l2 2 4-4.5"/>
              </svg>
              <p class="vtm-feat-t">보안 중심</p>
              <p class="vtm-feat-d">안전한 데이터 보호</p>
            </div>
            <div class="vtm-feat">
              <svg viewBox="0 0 24 24" fill="none" stroke="#2DD4BF" stroke-width="1.7"
                   stroke-linecap="round" stroke-linejoin="round">
                <path d="M3 21h18"/>
                <rect x="5" y="12" width="3" height="6" rx="0.5"/>
                <rect x="10.5" y="8" width="3" height="10" rx="0.5"/>
                <rect x="16" y="10" width="3" height="8" rx="0.5"/>
                <path d="M5 8l4-3 4 2 5-4"/>
              </svg>
              <p class="vtm-feat-t">업무 효율화</p>
              <p class="vtm-feat-d">체계적인 업무 관리</p>
            </div>
            <div class="vtm-feat">
              <svg viewBox="0 0 24 24" fill="none" stroke="#2DD4BF" stroke-width="1.7"
                   stroke-linecap="round" stroke-linejoin="round">
                <circle cx="6" cy="6" r="2.5"/>
                <circle cx="18" cy="8" r="2.5"/>
                <circle cx="12" cy="18" r="2.5"/>
                <path d="M8.2 7.2l7.4 0M7.4 8.2l3.4 7.6M16.8 10.2l-3.4 5.6"/>
              </svg>
              <p class="vtm-feat-t">연결과 협업</p>
              <p class="vtm-feat-d">유기적인 팀워크</p>
            </div>
          </div>

          <div class="vtm-wf-panel">
            <div class="vtm-wf-head"><span class="vtm-wf-head-dot"></span>WORKFORCE&nbsp;STATUS</div>
            <div class="vtm-wf-grid">
              <div class="vtm-wf-item">
                <span class="vtm-wf-num">3</span>
                <span class="vtm-wf-lbl">Human Workforce</span>
                <span class="vtm-wf-state on">Online</span>
              </div>
              <div class="vtm-wf-item">
                <span class="vtm-wf-num">7</span>
                <span class="vtm-wf-lbl">AI Workforce</span>
                <span class="vtm-wf-state run">Running</span>
              </div>
              <div class="vtm-wf-item">
                <span class="vtm-wf-num">10</span>
                <span class="vtm-wf-lbl">Total Workforce</span>
                <span class="vtm-wf-state total">Active</span>
              </div>
            </div>
            <div class="vtm-wf-foot">
              Automation Status
              <span class="vtm-op"><span class="vtm-op-dot"></span>Operational</span>
            </div>
          </div>

          <p class="vtm-copy">© 2026 VTM Co., Ltd. All rights reserved.</p>
        </div>
        """, unsafe_allow_html=True)

    with right:
        card = st.container()

        with card:
            st.markdown(f"""
            <div class="vtm-login-card">
              <img src="{VTM_LOGO_URL}" alt="VTM OS">
              <p class="vtm-card-os">VTM&nbsp;OS</p>
              <h2 class="vtm-card-welcome">Welcome Back</h2>
              <p class="vtm-card-sub">브이티엠 운영 시스템에 오신것을 환영합니다.</p>
            </div>
            """, unsafe_allow_html=True)

            emp_df  = get_employees(active_only=True)
            options = ["담당자를 선택하세요"] + [
                f"{r['name']} ({r['role']})" for _, r in emp_df.iterrows()
            ]
            sel = st.selectbox("담당자 선택", options, key="login_sel")

            selected = None
            if sel != "담당자를 선택하세요":
                nm = sel.split(" (")[0]
                m  = emp_df[emp_df["name"] == nm]
                if not m.empty:
                    selected = m.iloc[0]

            pw_input = ""
            if selected is not None:
                if str(selected["password"]).strip():
                    pw_input = st.text_input("비밀번호", type="password",
                        placeholder="비밀번호를 입력하세요", key="login_pw")
                else:
                    st.markdown("""
                    <div class="vtm-nopw">
                      <span>🔓 비밀번호 없이 접속 가능</span>
                    </div>""", unsafe_allow_html=True)

            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            if st.button("시스템 접속  →", key="btn_login", use_container_width=True):
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
            <p class="vtm-ver"><b>VTM OS 2.0.8</b> · 개발자: 박동진 본부장</p>
            """, unsafe_allow_html=True)


def render_sidebar():
    role_txt = "🔴 관리자" if st.session_state.is_admin else "🟢 직원"
    kst_now  = now_kst().strftime("%H:%M")
    kst_date = now_kst().strftime("%m/%d")
 
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:14px;
                background:linear-gradient(90deg,#0B1120,#1E293B);
                border-bottom:2px solid #D4AF37;border-radius:12px 12px 0 0;
                padding:10px 18px;margin-bottom:0;">
      <img src="{VTM_LOGO_URL}" alt="VTM Logo" style="width:44px;height:auto;display:block;filter:drop-shadow(0 0 10px rgba(20,224,184,0.45));">
      <div>
        <div style="color:#D4AF37;font-weight:900;font-size:1.05rem;line-height:1.2;">
            (주) 브이티엠
        </div>
        <div style="color:#64748B;font-size:0.72rem;font-weight:700;">
            VTM 운영 대시보드 v2.0.8
        </div>
      </div>
      <div style="margin-left:auto;text-align:right;">
        <div style="color:#D4AF37;font-size:0.75rem;font-weight:900;">{role_txt} {st.session_state.user_name}</div>
        <div style="color:#64748B;font-size:0.68rem;font-weight:700;">🇰🇷 KST {kst_date} {kst_now}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)
 
    if st.session_state.is_admin:
        menus = [
            ("home",          "🏠 홈",      True),
            ("admin_attend",  "📋 출퇴근",  False),
            ("admin_tasks",   "📊 업무",False),
            ("admin_approve", "✅ 결과",False),
            ("admin_emp",     "👥 관리",False),
            ("admin_excel",   "📥 엑셀",    False),
            ("admin_company_calendar", "📅 일정", False),
            ("admin_logs",    "🔍 로그",    False),
            ("emp_guide",     "📋 VTM WAY", False),
        ]
    else:
        menus = [
            ("home",         "🏠 홈",       True),
            ("emp_attend",   "⏰ 출퇴근",   False),
            ("emp_report",   "📝 업무보고", False),
            ("emp_calendar", "📅 달력",     False),
            ("emp_guide",    "📋 VTM WAY",  False),
        ]
 
    if st.session_state.is_admin:
        cols = st.columns([1, 1, 1, 1, 1, 1, 1, 1, 1.35, 1.35])
    else:
        cols = st.columns([1, 1, 1, 1, 1.35, 1.35])

    for i, (key, label, is_home) in enumerate(menus):
        with cols[i]:
            is_active = (st.session_state.page == key)
            if is_active and is_home:
                st.markdown(
                    f'<div style="background:linear-gradient(135deg,#05F080,#10B981,#059669);'
                    f'border-radius:10px;padding:9px 4px;text-align:center;'
                    f'font-weight:900;font-size:0.8rem;color:#fff;'
                    f'box-shadow:0 0 12px rgba(5,240,128,0.45);margin:2px 0;">'
                    f'{label}</div>', unsafe_allow_html=True)
            elif is_active:
                st.markdown(
                    f'<div style="background:linear-gradient(135deg,#A78BFA,#7C3AED,#5B21B6);'
                    f'border-radius:10px;padding:9px 4px;text-align:center;'
                    f'font-weight:900;font-size:0.8rem;color:#fff;'
                    f'box-shadow:0 0 14px rgba(139,92,246,0.5);margin:2px 0;">'
                    f'{label}</div>', unsafe_allow_html=True)
            else:
                if st.button(label, key=f"nav_{key}", use_container_width=True):
                    st.session_state.page = key; st.rerun()
 
    with cols[-1]:
        if st.button("🚪 로그아웃", key="btn_logout", use_container_width=True):
            wlog("LOGOUT", st.session_state.user_name)
            for k in ["logged_in", "user_id", "user_name", "is_admin"]:
                st.session_state[k] = False if k == "logged_in" else None
            st.session_state.page = "home"; st.rerun()
 
    st.markdown("<hr style='border-color:#1E3A5F;margin:4px 0 10px;'>", unsafe_allow_html=True)
 
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
#  직원/디렉터: 홈 (VTM OS 2.0.8 — 프리미엄 디렉터 대시보드 리디자인)
#  · DB 조회 로직(attendance/reports select)은 기존과 동일 유지
#  · UI만 리디자인: Hero + KPI 6카드 + 오늘 일정 타임라인 +
#    AI Workforce 롤업 패널(표시 전용) + 오늘 할 일 + 시스템 상태
#  · 배경 영상/테마는 메인 라우터에서 inject_director_theme() 로 주입
# ═══════════════════════════════════════════
def page_emp_home():
    uid   = st.session_state.user_id
    uname = st.session_state.user_name
    td    = today_str()
    sb = _sb()
    att_r = sb.table("attendance").select("*").eq("emp_id",uid).eq("work_date",td).limit(1).execute()
    rep_r = sb.table("reports").select("*").eq("emp_id",uid).eq("work_date",td).limit(1).execute()
    att = pd.DataFrame(att_r.data) if att_r.data else pd.DataFrame()
    rep = pd.DataFrame(rep_r.data) if rep_r.data else pd.DataFrame()

    # ── 실제 DB 값 기반 KPI ──
    ci_raw = safe_str(att.iloc[0]["checkin"])  if not att.empty else None
    co_raw = safe_str(att.iloc[0]["checkout"]) if not att.empty else None
    ci  = ci_raw[-8:-3] if ci_raw else "--:--"
    if co_raw:
        co, co_sub = co_raw[-8:-3], "퇴근 완료"
    else:
        co, co_sub = "17:00", "예정 퇴근"
    atp = safe_str(att.iloc[0]["att_type"]) if not att.empty else None
    atp = atp or "미출근"
    ci_sub = atp if not att.empty else "출근 체크 전"

    try:
        prg = int(rep.iloc[0]["pm_progress"]) if not rep.empty and safe_str(str(rep.iloc[0]["pm_progress"])) else 0
    except (ValueError, TypeError):
        prg = 0
    rst = safe_str(rep.iloc[0]["status"]) if not rep.empty else None
    rst = rst or "미제출"
    sub_at  = safe_str(rep.iloc[0]["submitted_at"]) if not rep.empty else None
    rst_sub = f"최종 보고: {sub_at[-8:-3]}" if sub_at else "오늘 업무보고"

    # 오늘 완료: reports 있으면 완료 업무(pm_done) 라인 수, 없으면 0건
    pm_done_txt = safe_str(rep.iloc[0]["pm_done"]) if not rep.empty else None
    if pm_done_txt:
        done_cnt = len([ln for ln in pm_done_txt.splitlines() if ln.strip()])
        done_cnt = max(done_cnt, 1)
    else:
        done_cnt = 0

    kst = now_kst()
    day_kr = ["월","화","수","목","금","토","일"][kst.weekday()]

    # ── Hero ──
    st.markdown(f"""
    <div class="vdir-hero">
      <div class="vdir-hero-left">
        <div class="vdir-hero-logo"><img src="{VTM_LOGO_URL}" alt="VTM Logo"></div>
        <div>
          <h2 class="vdir-hero-title"><span class="hello-text">안녕하세요,</span> <span class="nm">{uname}</span> 👋</h2>
          <p class="vdir-hero-sub">오늘도 AI 직원들과 함께 브랜드를 성장시키는 하루입니다.</p>
        </div>
      </div>
      <div class="vdir-hero-time">
        <div class="d">{kst.strftime('%Y.%m.%d')} ({day_kr})</div>
        <div class="t">{kst.strftime('%H:%M')}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── KPI 6카드 (반응형 CSS Grid — 모바일 자동 세로 스택) ──
    kpis = [
        ("🕘", "출근 시간",   ci,             ci_sub,        "teal"),
        ("🕔", "퇴근 시간",   co,             co_sub,        "cyan"),
        ("📈", "업무 진행률", f"{prg}%",      "오늘 보고 기준", "teal"),
        ("📝", "보고 상태",   rst,            rst_sub,       "violet"),
        ("🤖", "AI 지원",     "7명",          "상시 대기",     "violet"),
        ("✅", "오늘 완료",   f"{done_cnt}건", "완료된 업무",   "gold"),
    ]
    kpi_html = '<div class="vdir-kpi-grid">'
    for ico, lbl, val, sub, cls in kpis:
        kpi_html += (
            '<div class="vdir-kpi c-' + cls + '">'
            '<div class="k-ico">' + ico + '</div>'
            '<div class="k-lbl">' + lbl + '</div>'
            '<div class="k-val">' + str(val) + '</div>'
            '<div class="k-sub">' + sub + '</div>'
            '</div>'
        )
    kpi_html += '</div>'
    st.markdown(kpi_html, unsafe_allow_html=True)

    # ── 관리자 승인/반려/보류 코멘트 배너 (기존 기능 유지) ──
    if not rep.empty:
        s = safe_str(rep.iloc[0]["status"]) or ""
        c = safe_str(rep.iloc[0]["admin_comment"]) or ""
        if   s == "승인": st.success(f"✅ 관리자 승인 완료  |  💬 {c or '승인되었습니다.'}")
        elif s == "반려": st.error(  f"❌ 보고 반려  |  💬 {c or '수정 후 재제출 바랍니다.'}")
        elif s == "보류": st.warning(f"⏸ 보류 처리  |  💬 {c}")

    # ── 좌: 오늘 일정 / 중: AI Workforce 롤업 / 우: 오늘 할 일 + 시스템 상태 ──
    left, mid, right = st.columns([1, 1.35, 1], gap="medium")

    with left:
        att_done_desc = "정상 출근 완료" if not att.empty else "출근 체크를 진행하세요"
        schedule = [
            ("09:30", "출근",                       att_done_desc,                  "teal"),
            ("10:00", "오전 블로그 발행",            "블로그 콘텐츠 발행 및 모니터링", "cyan"),
            ("11:00", "몽해 일별 쇼츠 제작",         "쇼츠 영상 기획 및 제작",        "cyan"),
            ("11:50", "점심시간",                   "휴식 및 재충전",                "mut"),
            ("13:00", "몽해 주별 미드폼 콘텐츠 제작", "주간 미드폼 콘텐츠 기획 및 제작", "violet"),
            ("16:00", "오후 블로그 발행",            "오후 콘텐츠 발행 및 성과 분석",  "gold"),
            ("17:00", "퇴근",                       "업무 종료 및 마무리",           "mut"),
        ]
        tl_html = ""
        for t_, title_, desc_, cls_ in schedule:
            tl_html += (
                '<div class="vdir-tl-item c-' + cls_ + '">'
                '<div class="vdir-tl-rail"><div class="vdir-tl-dot"></div><div class="vdir-tl-line"></div></div>'
                '<div class="vdir-tl-time">' + t_ + '</div>'
                '<div class="vdir-tl-body"><div class="t">' + title_ + '</div><div class="d">' + desc_ + '</div></div>'
                '</div>'
            )
        st.markdown(
            '<div class="vdir-panel">'
            '<div class="vdir-sec-title">🗓 오늘 일정</div>'
            '<div class="vdir-tl">' + tl_html + '</div>'
            '</div>',
            unsafe_allow_html=True)

    with mid:
        # AI Workforce 롤업 — 7명 × 2벌 이어붙여 -50% 지점에서 무한 순환.
        # 순수 CSS 애니메이션(21s linear)으로 한 칸씩 자연스럽게 롤업되며,
        # Streamlit 위젯/세션과 충돌하지 않는 표시 전용 패널이다.
        avatars = ["✍️","✍️","♟️","📈","📣","🧭","🗓️"]
        items_html = ""
        for _bank in range(2):
            for idx, (nm, task) in enumerate(AI_STAFF):
                ava = avatars[idx % len(avatars)]
                items_html += (
                    '<div class="vdai-item">'
                    '<div class="vdai-ava">' + ava + '</div>'
                    '<div class="vdai-info">'
                    '<div class="vdai-name">' + nm + '</div>'
                    '<div class="vdai-task">담당업무: ' + task + '</div>'
                    '</div>'
                    '<div class="vdai-state"><span class="vdai-state-dot"></span>업무 진행 중</div>'
                    '</div>'
                )
        st.markdown(
            '<div class="vdai-panel">'
            '<div class="vdai-head">'
            '<div class="t">🤖 AI WORKFORCE</div>'
            '<div class="live"><span class="vdai-live-dot"></span>7명 상시 대기 중</div>'
            '</div>'
            '<div class="vdai-view"><div class="vdai-track">' + items_html + '</div></div>'
            '<div class="vdai-foot">AI 자동화 상태'
            '<span class="op"><span class="op-dot"></span>Running · 7 Agents</span>'
            '</div>'
            '</div>',
            unsafe_allow_html=True)

    with right:
        todos = [
            "오전 블로그 발행 확인",
            "몽해 일별 쇼츠 제작 확인",
            "몽해 주별 미드폼 제작 확인",
            "오후 블로그 발행 확인",
            "AI 결과물 검수",
            "업무보고 작성",
        ]
        todo_html = ""
        for t_ in todos:
            todo_html += (
                '<div class="vdir-todo-item">'
                '<div class="lt"><div class="vdir-todo-ck">✓</div>'
                '<div class="vdir-todo-txt">' + t_ + '</div></div>'
                '<div class="vdir-todo-arw">›</div>'
                '</div>'
            )
        st.markdown(
            '<div class="vdir-panel">'
            '<div class="vdir-sec-title">✅ 오늘 할 일 <span class="cnt">' + str(len(todos)) + '건</span></div>'
            + todo_html +
            '</div>',
            unsafe_allow_html=True)

        st.markdown("""
        <div class="vdir-panel">
          <div class="vdir-sec-title">🖥 시스템 상태</div>
          <div class="vdir-sys-row">
            <span class="vdir-sys-lbl"><span class="ic">🧑‍💼</span>Human Online</span>
            <span class="vdir-sys-val teal">2명</span>
          </div>
          <div class="vdir-sys-row">
            <span class="vdir-sys-lbl"><span class="ic">🤖</span>AI Online</span>
            <span class="vdir-sys-val cyan">7명</span>
          </div>
          <div class="vdir-sys-row">
            <span class="vdir-sys-lbl"><span class="ic">📡</span>Automation</span>
            <span class="vdir-sys-val green">Running</span>
          </div>
          <div class="vdir-sys-row">
            <span class="vdir-sys-lbl"><span class="ic">🗄</span>Supabase</span>
            <span class="vdir-sys-val green">Connected</span>
          </div>
        </div>
        """, unsafe_allow_html=True)
 
# ═══════════════════════════════════════════
#  직원: 출퇴근
# ═══════════════════════════════════════════
ATT_TYPES = ["정상출근","오전 반차","오후 반차","조퇴","연차","병가","공가"]
 
def page_emp_attend():
    topbar("⏰ 출퇴근")
    uid = st.session_state.user_id; uname = st.session_state.user_name; td = today_str()
    sb = _sb()
    att_r = sb.table("attendance").select("*").eq("emp_id",uid).eq("work_date",td).limit(1).execute()
    att = pd.DataFrame(att_r.data) if att_r.data else pd.DataFrame()
 
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
            _sb().table("attendance").insert({
                "emp_id":uid,"emp_name":uname,"work_date":td,
                "checkin":now_str(),"att_type":sel_type,"created_at":now_str()
            }).execute()
            wlog("CHECKIN", uname, "", sel_type)
            st.success(f"✅ 출근 완료! ({sel_type} {now_kst().strftime('%H:%M')} KST)")
            st.rerun()
    else:
        st.success(f"✅ 출근 완료 — {ci_t} ({atp})")
                    if st.button("🏠 퇴근 체크아웃", key="btn_co", use_container_width=True):

                now_dt = now_kst()
                weekday = now_dt.weekday()

                if weekday in [0, 1, 2, 3]:
                    cutoff = now_dt.replace(hour=17, minute=0, second=0, microsecond=0)
                    if now_dt < cutoff:
                        st.warning("⏰ 17:00 이후 체크아웃 가능합니다.")
                        st.stop()

                elif weekday == 4:
                    cutoff = now_dt.replace(hour=16, minute=30, second=0, microsecond=0)
                    if now_dt < cutoff:
                        st.warning("⏰ 16:30 이후 체크아웃 가능합니다.")
                        st.stop()

                _sb().table("attendance").update({
                    "checkout": now_str()
                }).eq("emp_id", uid).eq("work_date", td).execute()

                wlog("CHECKOUT", uname)
                st.success(f"🏠 퇴근 완료! ({now_dt.strftime('%H:%M')} KST)")
                st.rerun()
        else:
            st.success(f"🏠 퇴근 완료 — {co_t}")
 
    st.markdown("---")
    st.markdown("<div class='vtm-card'><h3>📋 최근 출퇴근 기록</h3></div>", unsafe_allow_html=True)
    hist_r = _sb().table("attendance").select("work_date,att_type,checkin,checkout").eq("emp_id",uid).order("work_date",desc=True).limit(10).execute()
    hist = pd.DataFrame(hist_r.data) if hist_r.data else pd.DataFrame()
    if not hist.empty:
        hist.columns = ["날짜","유형","출근","퇴근"]
        st.dataframe(hist, use_container_width=True, hide_index=True)
 
# ═══════════════════════════════════════════
#  직원: 업무 보고
# ═══════════════════════════════════════════
def page_emp_report():
    topbar("📝 업무 보고")
    uid = st.session_state.user_id; uname = st.session_state.user_name; td = today_str()
    sb = _sb()
    ex_r = sb.table("reports").select("*").eq("emp_id",uid).eq("work_date",td).limit(1).execute()
    exist = pd.DataFrame(ex_r.data) if ex_r.data else pd.DataFrame()
 
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
            sb = _sb()
            if exist.empty:
                sb.table("reports").insert({
                    "emp_id":uid,"emp_name":uname,"work_date":td,
                    "am_tasks":am_tasks,"am_priority":am_priority,"am_notes":am_notes,
                    "status":"대기중","submitted_at":now_str()
                }).execute()
            else:
                sb.table("reports").update({
                    "am_tasks":am_tasks,"am_priority":am_priority,
                    "am_notes":am_notes,"submitted_at":now_str()
                }).eq("emp_id",uid).eq("work_date",td).execute()
            wlog("AM_PLAN", uname, td)
            st.success("✅ 오전 계획 저장 완료!"); st.rerun()
 
    with tab2:
        st.markdown("<div class='vtm-card'><h3>🌇 퇴근 결과 보고</h3></div>", unsafe_allow_html=True)
        pm_done = st.text_area("✅ 완료한 업무",
            value=safe_str(exist.iloc[0]["pm_done"]) or "" if not exist.empty else "",
            height=100, placeholder="오늘 완료한 업무를 상세히 입력하세요...")
        pm_progress = st.slider("📊 전체 진행률 (%)", 0, 100,
            value=int(exist.iloc[0]["pm_progress"]) if not exist.empty else 0, step=5)
        pm_tomorrow = st.text_area("📅 내일 예정",
            value=safe_str(exist.iloc[0]["pm_tomorrow"]) or "" if not exist.empty else "",
            height=75, placeholder="내일 진행할 업무를 입력하세요...")
        pm_remarks = st.text_area("💬 특이사항",
            value=safe_str(exist.iloc[0]["pm_remarks"]) or "" if not exist.empty else "",
            height=75, placeholder="이슈, 공유사항 등을 입력하세요...")
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
            sb = _sb()
            if exist.empty:
                sb.table("reports").insert({
                    "emp_id":uid,"emp_name":uname,"work_date":td,
                    "pm_done":pm_done,"pm_progress":pm_progress,
                    "pm_tomorrow":pm_tomorrow,"pm_remarks":pm_remarks,
                    "drive_link":drive_link,"result_link":result_link,
                    "status":"대기중","submitted_at":now_str()
                }).execute()
            else:
                sb.table("reports").update({
                    "pm_done":pm_done,"pm_progress":pm_progress,
                    "pm_tomorrow":pm_tomorrow,"pm_remarks":pm_remarks,
                    "drive_link":drive_link,"result_link":result_link,
                    "status":"대기중","submitted_at":now_str()
                }).eq("emp_id",uid).eq("work_date",td).execute()
            wlog("REPORT", uname, td)
            st.success("✅ 업무보고가 완료되었습니다!")
            st.balloons(); st.rerun()
 
# ═══════════════════════════════════════════
#  직원: 달력
# ═══════════════════════════════════════════
def render_day_detail(uid, d_str):
    """선택한 날짜 상세 카드 — 출퇴근 + 업무보고 + 승인내역"""
    sb = _sb()
    att_r = sb.table("attendance").select("*").eq("emp_id",uid).eq("work_date",d_str).limit(1).execute()
    rep_r = sb.table("reports").select("*").eq("emp_id",uid).eq("work_date",d_str).limit(1).execute()
    att = pd.DataFrame(att_r.data) if att_r.data else pd.DataFrame()
    rep = pd.DataFrame(rep_r.data) if rep_r.data else pd.DataFrame()

    try:
        dt_obj = datetime.strptime(d_str, "%Y-%m-%d")
        day_kr = ["월","화","수","목","금","토","일"][dt_obj.weekday()]
        d_label = f"{dt_obj.year}년 {dt_obj.month}월 {dt_obj.day}일 ({day_kr})"
    except Exception:
        d_label = d_str

    st.markdown(
        f'<div style="background:linear-gradient(90deg,#1E293B,#0F172A);'
        f'border:2px solid #2DD4BF;border-radius:14px;padding:12px 20px;margin:6px 0 2px;">'
        f'<span style="color:#2DD4BF;font-size:1rem;font-weight:900;">'
        f'📅 {d_label} — 상세 보기 &nbsp;<span style="font-size:0.75rem;color:#94A3B8;">'
        f'(같은 날짜 버튼을 다시 누르면 닫힙니다)</span></span></div>',
        unsafe_allow_html=True)

    if not att.empty:
        a = att.iloc[0]
        ci_raw = safe_str(a["checkin"])
        co_raw = safe_str(a["checkout"])
        ci_t = ci_raw[-8:-3] if ci_raw else "--:--"
        co_t = co_raw[-8:-3] if co_raw else "미퇴근"
        atp  = safe_str(a["att_type"]) or "정상출근"
        ac1, ac2 = st.columns(2)
        with ac1:
            st.markdown(
                f'<div class="vtm-card" style="text-align:center;padding:10px;">'
                f'<h3 style="font-size:0.82rem;margin:0 0 4px;">🟢 출근</h3>'
                f'<p style="font-size:1.5rem;font-weight:900;color:#10B981;margin:2px 0;">{ci_t}</p>'
                f'<p style="font-size:0.78rem;color:#64748B;margin:0;">{atp}</p></div>',
                unsafe_allow_html=True)
        with ac2:
            st.markdown(
                f'<div class="vtm-card" style="text-align:center;padding:10px;">'
                f'<h3 style="font-size:0.82rem;margin:0 0 4px;">🔴 퇴근</h3>'
                f'<p style="font-size:1.5rem;font-weight:900;color:#EF4444;margin:2px 0;">{co_t}</p>'
                f'<p style="font-size:0.78rem;color:#64748B;margin:0;">&nbsp;</p></div>',
                unsafe_allow_html=True)
    else:
        st.markdown(
            '<div style="background:rgba(239,68,68,0.1);border:1px solid #EF4444;'
            'border-radius:10px;padding:10px;margin:4px 0;text-align:center;">'
            '<span style="color:#EF4444;font-weight:900;">❗ 출근 기록 없음</span></div>',
            unsafe_allow_html=True)

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    if not rep.empty:
        r = rep.iloc[0]
        status  = safe_str(r["status"]) or "대기중"
        sc      = {"승인":"#10B981","대기중":"#F59E0B","반려":"#EF4444","보류":"#8B5CF6"}.get(status,"#6B7280")
        s_emoji = {"승인":"✅","대기중":"⏳","반려":"❌","보류":"⏸"}.get(status,"📋")
        prg     = int(r["pm_progress"]) if safe_str(str(r["pm_progress"])) else 0
        bar_c   = "#10B981" if prg >= 80 else ("#F59E0B" if prg >= 40 else "#EF4444")

        am_tasks = safe_str(r["am_tasks"])    or "—"
        am_pri   = safe_str(r["am_priority"]) or "—"
        am_notes = safe_str(r["am_notes"])    or "—"
        pm_done  = safe_str(r["pm_done"])     or "—"
        pm_tom   = safe_str(r["pm_tomorrow"]) or "—"
        pm_rem   = safe_str(r["pm_remarks"])  or "—"
        cmt      = safe_str(r["admin_comment"]) or ""
        sub_at   = safe_str(r["submitted_at"])  or "—"
        appr_at  = safe_str(r["approved_at"])   or "—"
        dl_val   = safe_str(r["drive_link"])
        rl_val   = safe_str(r["result_link"])

        st.markdown(
            f'<div class="vtm-card" style="padding:10px 16px;margin:4px 0 2px;">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;">'
            f'<span style="font-size:0.96rem;font-weight:900;">📝 업무 보고서</span>'
            f'<span style="background:{sc};color:#fff;padding:3px 14px;border-radius:20px;'
            f'font-weight:900;font-size:0.8rem;">{s_emoji} {status}</span>'
            f'</div></div>',
            unsafe_allow_html=True)

        st.markdown(
            f'<div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:10px;'
            f'padding:10px 16px;margin:3px 0;">'
            f'<p style="font-size:0.7rem;color:#64748B;font-weight:700;margin:0 0 4px;">🌅 오전 업무 계획</p>'
            f'<p style="font-size:0.87rem;font-weight:700;color:#1E293B;margin:0 0 3px;'
            f'white-space:pre-wrap;">{am_tasks}</p>'
            f'<p style="font-size:0.76rem;color:#475569;margin:0;">'
            f'우선순위: {am_pri}&nbsp;&nbsp;|&nbsp;&nbsp;특이사항: {am_notes}</p></div>',
            unsafe_allow_html=True)

        st.markdown(
            f'<div style="background:#F0FDF4;border:1px solid #BBF7D0;border-radius:10px;'
            f'padding:10px 16px;margin:3px 0;">'
            f'<p style="font-size:0.7rem;color:#64748B;font-weight:700;margin:0 0 4px;">🌇 퇴근 결과 보고</p>'
            f'<p style="font-size:0.87rem;font-weight:700;color:#1E293B;margin:0 0 5px;'
            f'white-space:pre-wrap;">{pm_done}</p>'
            f'<div style="background:#E2E8F0;border-radius:5px;height:7px;margin:3px 0 4px;">'
            f'<div style="background:{bar_c};width:{prg}%;height:7px;border-radius:5px;"></div></div>'
            f'<p style="font-size:0.74rem;color:#475569;margin:0;">'
            f'진행률 {prg}%&nbsp;&nbsp;|&nbsp;&nbsp;내일예정: {pm_tom}</p>'
            + (f'<p style="font-size:0.76rem;color:#475569;margin:3px 0 0;">💬 특이사항: {pm_rem}</p>'
               if pm_rem and pm_rem != "—" else "")
            + '</div>',
            unsafe_allow_html=True)

        dl_a = (f'<a href="{dl_val}" target="_blank" style="color:#3B82F6;font-weight:700;">🔗 열기</a>'
                if dl_val else '없음')
        rl_a = (f'<a href="{rl_val}" target="_blank" style="color:#3B82F6;font-weight:700;">🔗 열기</a>'
                if rl_val else '없음')
        st.markdown(
            f'<div style="background:#F8F9FA;border:1px solid #E2E8F0;border-radius:8px;'
            f'padding:7px 14px;margin:3px 0;font-size:0.77rem;color:#475569;">'
            f'📁 Drive: {dl_a}&nbsp;&nbsp;&nbsp;🔗 결과물: {rl_a}</div>',
            unsafe_allow_html=True)

        if cmt:
            st.markdown(
                f'<div style="background:linear-gradient(135deg,#ECFEFF,#CFFAFE);'
                f'border:2px solid #2DD4BF;border-radius:10px;padding:10px 16px;margin:4px 0;">'
                f'<p style="font-size:0.72rem;color:#0E7490;font-weight:900;margin:0 0 4px;">'
                f'💬 관리자 코멘트</p>'
                f'<p style="font-size:0.9rem;font-weight:700;color:#1A1A1A;margin:0;'
                f'line-height:1.5;">{cmt}</p></div>',
                unsafe_allow_html=True)

        sub_disp  = sub_at[-17:-3]  if len(sub_at)  > 13 else sub_at
        appr_disp = appr_at[-17:-3] if len(appr_at) > 13 else appr_at
        tail = f'제출: {sub_disp}'
        if appr_at and appr_at != "—":
            tail += f'&nbsp;&nbsp;·&nbsp;&nbsp;승인: {appr_disp}'
        st.markdown(
            f'<div style="font-size:0.68rem;color:#94A3B8;text-align:right;margin:4px 0 6px;">'
            f'{tail}</div>',
            unsafe_allow_html=True)
    else:
        st.markdown(
            '<div style="background:rgba(100,116,139,0.12);border:1px solid #334155;'
            'border-radius:12px;padding:18px;text-align:center;margin:4px 0;">'
            '<p style="color:#64748B;font-weight:700;font-size:0.9rem;margin:0;">'
            '📭 이 날 업무 보고 내역이 없습니다.</p></div>',
            unsafe_allow_html=True)

    st.markdown("<hr style='border-color:#1E3A5F;margin:12px 0 4px;'>", unsafe_allow_html=True)
    st.markdown("### 🏖 휴가 · 반차 신청")

    leave_r = (
        _sb()
        .table("leave_requests")
        .select("*")
        .eq("emp_id", uid)
        .eq("leave_date", d_str)
        .execute()
    )

    leave_df = pd.DataFrame(leave_r.data) if leave_r.data else pd.DataFrame()

    if leave_df.empty:

        with st.form(f"leave_apply_{d_str}"):

            leave_type = st.selectbox(
                "신청 종류",
                [
                    "월차",
                    "오전반차",
                    "오후반차",
                    "여름휴가"
                ]
            )

            reason = st.text_area(
                "사유",
                placeholder="간단한 사유를 입력하세요."
            )

            if st.form_submit_button("📨 신청하기"):

                _sb().table("leave_requests").insert({
                    "emp_id": uid,
                    "emp_name": st.session_state.user_name,
                    "leave_date": d_str,
                    "leave_type": leave_type,
                    "reason": reason,
                    "status": "대기중"
                }).execute()

                st.success("신청되었습니다.")
                st.rerun()

    else:

        r = leave_df.iloc[0]

        status = safe_str(r["status"])

        color = {
            "대기중":"orange",
            "승인":"green",
            "반려":"red"
        }.get(status,"gray")

        st.markdown(
            f"""
<div style="
padding:14px;
border-radius:10px;
background:#F8FAFC;
border-left:6px solid {color};
margin-top:10px;
">
<b>신청 종류</b> : {r['leave_type']}<br>
<b>상태</b> : {status}<br>
<b>사유</b> : {safe_str(r['reason'])}
</div>
""",
            unsafe_allow_html=True
        )

def page_emp_calendar():
    topbar("📅 업무 달력")
    uid   = st.session_state.user_id
    today = now_kst().date()

    if "cal_selected" not in st.session_state:
        st.session_state.cal_selected = None

    c1, c2, _ = st.columns([1, 1, 2])
    with c1: yr = st.number_input("연도", value=today.year, min_value=2024, max_value=2030, key="cy")
    with c2: mo = st.number_input("월",   value=today.month, min_value=1, max_value=12, key="cm")
    yr = int(yr); mo = int(mo)

    sb = _sb()
    from_date = f"{yr}-{mo:02d}-01"
    last_day = calendar.monthrange(yr, mo)[1]
    to_date = f"{yr}-{mo:02d}-{last_day:02d}"

    att_dr = sb.table("attendance").select("work_date,att_type").eq("emp_id",uid).gte("work_date",from_date).lte("work_date",to_date).execute()
    rep_dr = sb.table("reports").select("work_date,status,pm_progress").eq("emp_id",uid).gte("work_date",from_date).lte("work_date",to_date).execute()
    ev_dr = sb.table("company_events").select("*").eq("is_public",True).gte("event_date",from_date).lte("event_date",to_date).execute()
    lv_dr = sb.table("leave_requests").select("*").gte("leave_date",from_date).lte("leave_date",to_date).execute()

    att_df = pd.DataFrame(att_dr.data) if att_dr.data else pd.DataFrame()
    rep_df = pd.DataFrame(rep_dr.data) if rep_dr.data else pd.DataFrame()
    ev_df = pd.DataFrame(ev_dr.data) if ev_dr.data else pd.DataFrame()
    lv_df = pd.DataFrame(lv_dr.data) if lv_dr.data else pd.DataFrame()

    if not lv_df.empty:
        lv_df = lv_df[(lv_df["status"] == "승인") | (lv_df["emp_id"] == uid)]

    att_map = {r["work_date"]: r for _, r in att_df.iterrows()} if not att_df.empty else {}
    rep_map = {r["work_date"]: r for _, r in rep_df.iterrows()} if not rep_df.empty else {}

    event_map = {}
    if not ev_df.empty:
        for _, r in ev_df.iterrows():
            event_map.setdefault(r["event_date"], []).append(r)

    leave_map = {}
    if not lv_df.empty:
        for _, r in lv_df.iterrows():
            leave_map.setdefault(r["leave_date"], []).append(r)
    cal_weeks = calendar.monthcalendar(yr, mo)
    sel = st.session_state.cal_selected

    COLG = '<colgroup><col style="width:16.8%"><col style="width:16.8%"><col style="width:16.8%"><col style="width:16.8%"><col style="width:16.8%"><col style="width:8%"><col style="width:8%"></colgroup>'

    st.markdown("""<style>
table.vtm-cal {
    width:100%; border-collapse:separate; border-spacing:3px;
    table-layout:fixed; margin:0 !important;
}
table.vtm-cal th {
    padding:8px 4px; text-align:center; font-weight:900;
    font-size:0.86rem; border-radius:7px;
}
table.vtm-cal th.hwd  { background:#1E293B; color:#2DD4BF; }
table.vtm-cal th.hsat { background:#1a2d44; color:#93C5FD; }
table.vtm-cal th.hsun { background:#2a1520; color:#FCA5A5; }
table.vtm-cal td {
    border-radius:8px 8px 0 0; vertical-align:top;
    padding:7px 7px 5px; height:82px;
    border:1.5px solid transparent; border-bottom:none !important;
    position:relative;
}
table.vtm-cal td.wd    { background:#FFFFFF; border-color:#CBD5E1; }
table.vtm-cal td.sat   { background:#EFF6FF; border-color:#BFDBFE; }
table.vtm-cal td.sun   { background:#FFF1F2; border-color:#FECDD3; }
table.vtm-cal td.today { background:#ECFEFF !important; border:2px solid #2DD4BF !important; border-bottom:none !important; }
table.vtm-cal td.sel   { background:#EFF6FF !important; border:2px solid #3B82F6 !important; border-bottom:none !important; }
table.vtm-cal td.empty { background:transparent !important; border:none !important; }
table.vtm-cal .daynum  { font-size:1rem; font-weight:900; display:block; margin-bottom:3px; line-height:1; }
table.vtm-cal td.wd    .daynum { color:#1E293B; }
table.vtm-cal td.sat   .daynum { color:#1D4ED8; }
table.vtm-cal td.sun   .daynum { color:#BE123C; }
table.vtm-cal td.today .daynum { color:#0E7490; }
table.vtm-cal td.today .daynum::after { content:" ★"; font-size:0.6rem; }
table.vtm-cal td.sel   .daynum { color:#1D4ED8; }
table.vtm-cal .badge {
    display:inline-block; border-radius:3px;
    padding:1px 5px; font-size:0.58rem; font-weight:700;
    margin:1px 0; line-height:1.5; white-space:nowrap;
}
table.vtm-cal .b-att  { background:#D1FAE5; color:#065f46; }
table.vtm-cal .b-ok   { background:#DBEAFE; color:#1e40af; }
table.vtm-cal .b-pend { background:#CFFAFE; color:#155E75; }
table.vtm-cal .b-rjct { background:#FEE2E2; color:#991b1b; }
table.vtm-cal .b-hold { background:#EDE9FE; color:#4C1D95; }
table.vtm-cal .b-none { background:#F1F5F9; color:#94A3B8; }
table.vtm-cal .stamp {
    position:absolute; top:5px; right:5px; width:26px; height:26px;
    border-radius:50%; border:2.5px solid #DC2626;
    display:flex; align-items:center; justify-content:center;
    font-size:0.48rem; font-weight:900; color:#DC2626;
    background:rgba(220,38,38,0.08); transform:rotate(-15deg);
    line-height:1.1; text-align:center;
}

div:has(> .cmark) + div .stButton > button {
    background: #334155 !important;
    color: #CBD5E1 !important;
    height: 28px !important;
    min-height: 28px !important;
    border-radius: 0 0 8px 8px !important;
    font-size: 0.62rem !important;
    font-weight: 700 !important;
    padding: 5px 2px !important;
    transform: none !important;
    box-shadow: none !important;
    border: none !important;
    letter-spacing: 0.02em !important;
    width: 100% !important;
}
div:has(> .cmark) + div .stButton > button:hover {
    background: #1E40AF !important;
    color: #BFDBFE !important;
    transform: none !important;
    box-shadow: none !important;
}
div:has(> .cmark) + div [data-testid="stHorizontalBlock"] {
    gap: 3px !important;
    margin-top: -1px !important;
}
div:has(> .cmark) + div [data-testid="stColumn"] {
    padding: 0 !important;
    min-width: 0 !important;
}
</style>""", unsafe_allow_html=True)

    st.markdown(
        f'<table class="vtm-cal">{COLG}'
        '<thead><tr>'
        '<th class="hwd">월</th><th class="hwd">화</th>'
        '<th class="hwd">수</th><th class="hwd">목</th>'
        '<th class="hwd">금</th>'
        '<th class="hsat">토</th><th class="hsun">일</th>'
        '</tr></thead></table>',
        unsafe_allow_html=True)

    for wi, week in enumerate(cal_weeks):
        cells = f'<table class="vtm-cal">{COLG}<tbody><tr>'
        for i, day in enumerate(week):
            is_sat=(i==5); is_sun=(i==6); is_wk=is_sat or is_sun
            if day == 0:
                cells += '<td class="empty"></td>'; continue
            d = f"{yr}-{mo:02d}-{day:02d}"
            is_td=(d==today_str()); is_sel=(d==sel)
            has_att=d in att_map; has_rep=d in rep_map
            rep_st  = rep_map[d]["status"]      if has_rep else None
            rep_prg = rep_map[d]["pm_progress"] if has_rep else 0
            base = "sun" if is_sun else ("sat" if is_sat else "wd")
            cls  = base + (" sel" if is_sel else (" today" if is_td else ""))
            badges = ""

            for ev in event_map.get(d, [])[:2]:
                badges += f'<span class="badge b-ok">📌 {safe_str(ev.get("event_type"))}</span><br>'

            for lv in leave_map.get(d, [])[:2]:
                lv_status = safe_str(lv.get("status")) or "대기중"
                lv_emp = safe_str(lv.get("emp_name")) or "-"
                lv_type = safe_str(lv.get("leave_type")) or "-"
                if lv_status == "승인":
                    badges += f'<span class="badge b-att">🏖 {lv_emp} {lv_type}</span><br>'
                else:
                    badges += f'<span class="badge b-pend">⏳ {lv_emp} {lv_type}</span><br>'

            if not is_wk:
                if has_att:
                    badges += f'<span class="badge b-att">✅ {(att_map[d]["att_type"] or "출근")[:4]}</span><br>'
                else:
                    badges += '<span class="badge b-none">미출근</span><br>'

                if has_rep:
                    if rep_st=="승인":   badges += f'<span class="badge b-ok">📋 {rep_prg}%</span>'
                    elif rep_st=="반려": badges += '<span class="badge b-rjct">❌ 반려</span>'
                    elif rep_st=="보류": badges += '<span class="badge b-hold">⏸ 보류</span>'
                    else:               badges += f'<span class="badge b-pend">⏳ {rep_st}</span>'
                else:
                    badges += '<span class="badge b-none">보고없음</span>'
            stamp = '<div class="stamp">승<br>인</div>' if (has_rep and rep_st=="승인" and not is_wk) else ""
            cells += f'<td class="{cls}">{stamp}<span class="daynum">{day}</span>{badges}</td>'
        cells += '</tr></tbody></table>'
        st.markdown(cells, unsafe_allow_html=True)

        st.markdown('<div class="cmark"></div>', unsafe_allow_html=True)

        cols = st.columns([1, 1, 1, 1, 1, 0.48, 0.48])
        for i, day in enumerate(week):
            with cols[i]:
                if day == 0 or i >= 5:
                    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                else:
                    d = f"{yr}-{mo:02d}-{day:02d}"
                    is_sel = (d == sel)
                    lbl = "▲ 닫기" if is_sel else "상세내역 확인"
                    if st.button(lbl, key=f"cbtn_{d}", use_container_width=True):
                        st.session_state.cal_selected = None if is_sel else d
                        st.rerun()

        week_dates = [f"{yr}-{mo:02d}-{day:02d}" for i,day in enumerate(week) if day!=0 and i<5]
        if sel in week_dates:
            render_day_detail(uid, sel)


# ═══════════════════════════════════════════
#  직원: VTM 사규 / VTM WAY
# ═══════════════════════════════════════════
def page_emp_guide():
    topbar("📋 VTM WAY")
    st.markdown("""
<style>
.vtm-guide-wrap {
    max-width: 860px; margin: 0 auto; padding: 0 4px;
    position: relative; z-index: 1;
}
.vtm-guide-hero {
    background: linear-gradient(135deg, #0F172A 0%, #1E293B 60%, #0F172A 100%);
    border: 1px solid rgba(45,212,191,0.45);
    border-radius: 18px;
    padding: 36px 40px 28px;
    text-align: center;
    margin-bottom: 20px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.4);
}
.vtm-guide-hero .en-title {
    font-size: 0.82rem; font-weight: 900; letter-spacing: 0.22em;
    color: #2DD4BF; margin-bottom: 8px;
}
.vtm-guide-hero .ko-title {
    font-size: 1.55rem; font-weight: 900; color: #F1F5F9;
    margin-bottom: 10px; letter-spacing: 0.04em;
}
.vtm-guide-hero .tagline {
    font-size: 0.95rem; color: #94A3B8; font-weight: 700;
    line-height: 1.6;
}
.vtm-guide-hero .gold-line {
    width: 60px; height: 2px;
    background: linear-gradient(90deg, transparent, #2DD4BF, transparent);
    margin: 14px auto;
}
.vtm-section {
    background: linear-gradient(135deg, #1E293B 0%, #162032 100%);
    border: 1px solid #2D3F55;
    border-radius: 14px;
    padding: 24px 28px;
    margin-bottom: 14px;
    box-shadow: 0 4px 14px rgba(0,0,0,0.25);
}
.vtm-section-title {
    font-size: 0.72rem; font-weight: 900; letter-spacing: 0.18em;
    color: #2DD4BF; text-transform: uppercase;
    margin-bottom: 14px; display: flex; align-items: center; gap: 8px;
}
.vtm-section-title::after {
    content: ""; flex: 1; height: 1px;
    background: linear-gradient(90deg, rgba(45,212,191,0.4), transparent);
}
.vtm-value-item {
    display: flex; align-items: flex-start; gap: 12px;
    padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.04);
}
.vtm-value-item:last-child { border-bottom: none; }
.vtm-value-num {
    min-width: 28px; height: 28px; border-radius: 50%;
    background: linear-gradient(135deg, #2DD4BF, #0EA5E9);
    display: flex; align-items: center; justify-content: center;
    font-size: 0.72rem; font-weight: 900; color: #000;
    flex-shrink: 0; margin-top: 1px;
}
.vtm-value-text { color: #E2E8F0; font-size: 0.9rem; font-weight: 700; line-height: 1.5; }
.vtm-rule-grid {
    display: grid; grid-template-columns: 1fr 1fr;
    gap: 10px; margin-top: 2px;
}
.vtm-rule-card {
    background: rgba(15,23,42,0.6);
    border: 1px solid rgba(45,212,191,0.2);
    border-radius: 10px; padding: 14px 16px;
}
.vtm-rule-card .rc-label {
    font-size: 0.68rem; font-weight: 900; color: #2DD4BF;
    letter-spacing: 0.1em; margin-bottom: 6px;
}
.vtm-rule-card .rc-val {
    font-size: 0.88rem; font-weight: 700; color: #F1F5F9;
}
.vtm-rule-card .rc-sub {
    font-size: 0.76rem; color: #94A3B8; font-weight: 600; margin-top: 2px;
}
.vtm-badge-row {
    display: flex; flex-wrap: wrap; gap: 8px; margin-top: 4px;
}
.vtm-badge {
    background: rgba(45,212,191,0.12);
    border: 1px solid rgba(45,212,191,0.35);
    border-radius: 20px; padding: 5px 14px;
    font-size: 0.78rem; font-weight: 700; color: #2DD4BF;
}
.vtm-bullet { list-style: none; padding: 0; margin: 0; }
.vtm-bullet li {
    padding: 5px 0 5px 20px; position: relative;
    color: #E2E8F0; font-size: 0.88rem; font-weight: 600;
    border-bottom: 1px solid rgba(255,255,255,0.04);
}
.vtm-bullet li:last-child { border-bottom: none; }
.vtm-bullet li::before {
    content: "▸"; position: absolute; left: 0;
    color: #2DD4BF; font-size: 0.72rem; top: 7px;
}
.vtm-highlight {
    background: linear-gradient(135deg, rgba(45,212,191,0.08), rgba(45,212,191,0.04));
    border-left: 3px solid #2DD4BF;
    border-radius: 0 8px 8px 0;
    padding: 12px 16px;
    margin: 8px 0;
    color: #E2E8F0; font-size: 0.88rem; font-weight: 700; line-height: 1.6;
}
.vtm-promise {
    background: linear-gradient(135deg, #0F172A, #1a2540);
    border: 1.5px solid rgba(45,212,191,0.5);
    border-radius: 14px; padding: 22px 26px;
    text-align: center; margin-top: 6px;
}
.vtm-promise p { color: #CBD5E1; font-size: 0.9rem; font-weight: 700;
    line-height: 1.8; margin: 0; }
.vtm-promise .gold { color: #2DD4BF; font-weight: 900; }
</style>

<div class="vtm-guide-wrap">

  <div class="vtm-guide-hero">
    <div class="en-title">VTM OS 1.0 &nbsp;·&nbsp; COMPANY GUIDE</div>
    <div class="ko-title">VTM WAY</div>
    <div class="gold-line"></div>
    <div class="tagline">WE GROW TOGETHER, WE GO FURTHER<br>
      <span style="font-size:0.85rem;color:#64748B;">우리는 함께 성장하는 사람들이 더 큰 가치를 만들어가는 문화를 추구합니다.</span>
    </div>
  </div>

  <div class="vtm-section">
    <div class="vtm-section-title">🏆 &nbsp;핵심 가치</div>
    <div class="vtm-value-item"><div class="vtm-value-num">1</div><div class="vtm-value-text">성장하는 과정을 중요하게 생각합니다.</div></div>
    <div class="vtm-value-item"><div class="vtm-value-num">2</div><div class="vtm-value-text">혼자 일하지 않습니다.</div></div>
    <div class="vtm-value-item"><div class="vtm-value-num">3</div><div class="vtm-value-text">책임감을 행동으로 보여줍니다.</div></div>
    <div class="vtm-value-item"><div class="vtm-value-num">4</div><div class="vtm-value-text">긍정적인 조직 문화를 만듭니다.</div></div>
    <div class="vtm-value-item"><div class="vtm-value-num">5</div><div class="vtm-value-text">변화와 도전을 두려워하지 않습니다.</div></div>
    <div class="vtm-value-item"><div class="vtm-value-num">6</div><div class="vtm-value-text">회사의 성장을 함께 만들어 갑니다.</div></div>
  </div>

  <div class="vtm-section">
    <div class="vtm-section-title">⏰ &nbsp;근태 규정</div>
    <div class="vtm-rule-grid">
      <div class="vtm-rule-card">
        <div class="rc-label">출근</div>
        <div class="rc-val">오전 9:30 이전</div>
        <div class="rc-sub">출근 후 VTM OS 전산 체크</div>
      </div>
      <div class="vtm-rule-card">
        <div class="rc-label">퇴근</div>
        <div class="rc-val">17:00</div>
        <div class="rc-sub">불필요한 야근·연장 지양</div>
      </div>
      <div class="vtm-rule-card">
        <div class="rc-label">오전 근무</div>
        <div class="rc-val">10:00 ~ 11:50</div>
      </div>
      <div class="vtm-rule-card">
        <div class="rc-label">점심시간</div>
        <div class="rc-val">11:50 ~ 13:00</div>
      </div>
      <div class="vtm-rule-card">
        <div class="rc-label">오후 근무</div>
        <div class="rc-val">13:00 ~ 17:00</div>
      </div>
      <div class="vtm-rule-card">
        <div class="rc-label">휴무</div>
        <div class="rc-val">토 · 일 · 공휴일</div>
        <div class="rc-sub">국공휴일 및 법정공휴일</div>
      </div>
    </div>
    <div class="vtm-highlight" style="margin-top:12px;">
      ⚠️ 개인 사정으로 지각 시 <strong>사전 공유 원칙</strong>
    </div>
  </div>

  <div class="vtm-section">
    <div class="vtm-section-title">🌴 &nbsp;휴가 규정</div>
    <div class="vtm-rule-grid">
      <div class="vtm-rule-card">
        <div class="rc-label">월차</div>
        <div class="rc-val">월 1회</div>
        <div class="rc-sub">전월 만근 시 제공</div>
      </div>
      <div class="vtm-rule-card">
        <div class="rc-label">오전 반차</div>
        <div class="rc-val">오후 2시 출근</div>
      </div>
      <div class="vtm-rule-card">
        <div class="rc-label">오후 반차</div>
        <div class="rc-val">오후 2시 퇴근</div>
      </div>
      <div class="vtm-rule-card">
        <div class="rc-label">긴급 상황</div>
        <div class="rc-val">즉시 본부장 연락</div>
        <div class="rc-sub">갑작스러운 개인 일정 발생 시</div>
      </div>
    </div>
  </div>

  <div class="vtm-section">
    <div class="vtm-section-title">🏢 &nbsp;사무실 운영 규정</div>
    <div class="vtm-rule-grid">
      <div class="vtm-rule-card">
        <div class="rc-label">화요일</div>
        <div class="rc-val">분리수거</div>
        <div class="rc-sub">퇴근 전 전 직원 진행</div>
      </div>
      <div class="vtm-rule-card">
        <div class="rc-label">금요일</div>
        <div class="rc-val">16:30 청소</div>
        <div class="rc-sub">청소 완료 후 퇴근</div>
      </div>
    </div>
  </div>

  <div class="vtm-section">
    <div class="vtm-section-title">📌 &nbsp;업무 운영 원칙</div>
    <ul class="vtm-bullet">
      <li><strong>결과 중심 문화</strong> — 결과를 만들기 위한 노력과 과정의 공유 모두 중요합니다.</li>
      <li><strong>모든 업무 흐름</strong>은 VTM OS를 통해 관리하며, 현황이 항상 확인 가능해야 합니다.</li>
      <li><strong>결과물 관리</strong> — 모든 결과물은 공용 Google Drive에 업로드합니다. 개인 PC 보관만으로 업무를 종료할 수 없습니다.</li>
    </ul>
  </div>

<div class='vtm-section'>
    <div class='vtm-section-title'>🤖 &nbsp;AI 프로그램 사용 규정</div>

<div style='color:#94A3B8;font-size:0.78rem;font-weight:700;margin-bottom:10px;'>
브이티엠에서 사용할 수 있는 AI 생성 플랫폼
</div>

<div style='color:#CBD5E1;font-size:0.82rem;font-weight:800;margin:10px 0 8px;'>
자유롭게 활용 가능한 프로그램
</div>

<div class='vtm-badge-row'>
<a class='vtm-badge' href='https://chatgpt.com/' target='_blank'>ChatGPT</a>
<a class='vtm-badge' href='https://gemini.google.com/' target='_blank'>Gemini</a>
<a class='vtm-badge' href='https://claude.ai/' target='_blank'>Claude</a>
<a class='vtm-badge' href='https://www.genspark.ai/' target='_blank'>Genspark</a>
</div>

<div class='vtm-highlight' style='margin-top:14px;'>
🎵 <strong>음악 관련 AI</strong>
<span style='color:#2DD4BF;font-weight:900;'>[텔레그램 사용공유]</span><br>
<a href='https://suno.com/' target='_blank' style='color:#7FF7DE;font-weight:800;'>수노</a>
&nbsp;·&nbsp;
<a href='https://www.munute.com/' target='_blank' style='color:#7FF7DE;font-weight:800;'>마스터링</a>
</div>

<div class='vtm-highlight' style='margin-top:12px;'>
🎬 <strong>영상 관련 AI</strong>
<span style='color:#2DD4BF;font-weight:900;'>[텔레그램 사용공유]</span><br>
<a href='https://labs.google/fx/tools/flow' target='_blank' style='color:#7FF7DE;font-weight:800;'>플로우</a>
&nbsp;·&nbsp;
<a href='https://openart.ai/' target='_blank' style='color:#7FF7DE;font-weight:800;'>오픈아트</a>
&nbsp;·&nbsp;
<a href='https://higgsfield.ai/' target='_blank' style='color:#7FF7DE;font-weight:800;'>힉스필드</a>
&nbsp;·&nbsp;
<a href='https://www.topview.ai/' target='_blank' style='color:#7FF7DE;font-weight:800;'>탑뷰</a>
&nbsp;·&nbsp;
<a href='https://www.seaart.ai/' target='_blank' style='color:#7FF7DE;font-weight:800;'>씨아트</a>
&nbsp;·&nbsp;
<a href='https://www.domoai.app/ko' target='_blank' style='color:#7FF7DE;font-weight:800;'>도모AI</a>
</div>

<div class='vtm-highlight' style='margin-top:12px;'>
🖼 <strong>이미지 관련 AI</strong>
<span style='color:#2DD4BF;font-weight:900;'>[텔레그램 사용공유]</span><br>
<a href='https://www.midjourney.com/' target='_blank' style='color:#7FF7DE;font-weight:800;'>미드저니</a>
&nbsp;·&nbsp;
<a href='https://nijijourney.com/ko/' target='_blank' style='color:#7FF7DE;font-weight:800;'>니지저니</a>
&nbsp;·&nbsp;
<a href='https://www.dzine.ai/' target='_blank' style='color:#7FF7DE;font-weight:800;'>디자인AI</a>
&nbsp;·&nbsp;
<a href='https://www.canva.com/' target='_blank' style='color:#7FF7DE;font-weight:800;'>캔바</a>
</div>

<div class='vtm-highlight' style='margin-top:12px;'>
🎤 <strong>음성 관련 AI</strong>
<span style='color:#2DD4BF;font-weight:900;'>[텔레그램 사용공유]</span><br>
<a href='https://app.typecast.ai/' target='_blank' style='color:#7FF7DE;font-weight:800;'>타입캐스트</a>
&nbsp;·&nbsp;
<a href='https://elevenlabs.io/' target='_blank' style='color:#7FF7DE;font-weight:800;'>일레븐랩스</a>
</div>

<div class='vtm-highlight' style='margin-top:14px;'>
📢 <strong>텔레그램 공유 의무</strong><br>
<span style='font-size:0.84rem;color:#CBD5E1;'>
자유 활용 프로그램 외 음악·영상·이미지·음성 관련 AI는 사용 시작 및 종료 시 텔레그램 업무방에 공유합니다.<br>
점심시간 전 반드시 사용 중인 프로그램 종료 공유 후 식사합니다.
</span>
</div>
</div>

  <div class="vtm-section">
    <div class="vtm-section-title">💬 &nbsp;커뮤니케이션 규정</div>
    <ul class="vtm-bullet">
      <li>현재 진행 상황은 항상 확인 가능해야 합니다.</li>
      <li>업무 중 어려움이 있으면 혼자 해결하려 하지 않고 적극적으로 공유합니다.</li>
      <li>새로운 서비스·프로젝트·사업 아이디어는 반드시 <strong>본부장과 사전 소통</strong> 후 진행합니다.</li>
    </ul>
    <div style="color:#94A3B8;font-size:0.8rem;font-weight:700;margin:12px 0 6px;">즉시 본부장 보고 필요 상황</div>
    <div class="vtm-badge-row">
      <span class="vtm-badge" style="border-color:rgba(239,68,68,0.4);color:#FCA5A5;">일정 지연</span>
      <span class="vtm-badge" style="border-color:rgba(239,68,68,0.4);color:#FCA5A5;">문제 발생</span>
      <span class="vtm-badge" style="border-color:rgba(239,68,68,0.4);color:#FCA5A5;">고객 이슈</span>
      <span class="vtm-badge" style="border-color:rgba(239,68,68,0.4);color:#FCA5A5;">프로젝트 변경</span>
      <span class="vtm-badge" style="border-color:rgba(239,68,68,0.4);color:#FCA5A5;">긴급 상황</span>
    </div>
  </div>

  <div class="vtm-section">
    <div class="vtm-section-title">⭐ &nbsp;VTM 인재상</div>
    <div style="color:#94A3B8;font-size:0.82rem;font-weight:700;margin-bottom:10px;">우리는 이런 사람과 함께하고 싶습니다.</div>
    <div class="vtm-badge-row">
      <span class="vtm-badge">책임감 있는 사람</span>
      <span class="vtm-badge">실행하는 사람</span>
      <span class="vtm-badge">협업하는 사람</span>
      <span class="vtm-badge">성장하려는 사람</span>
      <span class="vtm-badge">긍정적인 에너지</span>
    </div>
  </div>

  <div class="vtm-promise">
    <p>
      능력은 함께 키울 수 있지만<br>
      <span class="gold">태도와 책임감은 스스로 선택해야 합니다.</span><br><br>
      우리는 완벽한 사람보다<br>
      <span class="gold">함께 성장할 수 있는 사람</span>과 오래 가고 싶습니다.
    </p>
  </div>

</div>
""", unsafe_allow_html=True)


def page_admin_home():
    topbar("🔴 관리자 대시보드")
    td = today_str(); sb = _sb()

    human_total = (sb.table("employees").select("*",count="exact").eq("active",1).eq("is_admin",0).execute().count) or 0
    t_att = (sb.table("attendance").select("*",count="exact").eq("work_date",td).execute().count) or 0
    pend  = (sb.table("reports").select("*",count="exact").eq("status","대기중").execute().count) or 0
    appr  = (sb.table("reports").select("*",count="exact").eq("status","승인").eq("work_date",td).execute().count) or 0

    emp_r   = sb.table("employees").select("id,name,role").eq("active",1).eq("is_admin",0).execute()
    att_r   = sb.table("attendance").select("emp_id,att_type,checkin,checkout").eq("work_date",td).execute()
    rep_r   = sb.table("reports").select("emp_id,status,pm_progress").eq("work_date",td).execute()
    emp_df  = pd.DataFrame(emp_r.data)  if emp_r.data  else pd.DataFrame()
    att_td  = pd.DataFrame(att_r.data)  if att_r.data  else pd.DataFrame()
    rep_td  = pd.DataFrame(rep_r.data)  if rep_r.data  else pd.DataFrame()

    ai_total       = len(AI_STAFF)                # 7
    human_online   = int(t_att)                  # 오늘 출근한 휴먼 직원
    total_workforce = human_total + ai_total     # 전체 Workforce

    kst = now_kst()
    day_kr = ["월","화","수","목","금","토","일"][kst.weekday()]
    st.markdown(f"""
    <div class="vadm-hero">
      <div class="vadm-hero-left">
       <div class="vadm-hero-logo"><img src="{VTM_LOGO_URL}" alt="VTM Logo"></div>
        <div>
          <h2 class="vadm-hero-title">관리자 대시보드</h2>
          <p class="vadm-hero-sub">🇰🇷 KST {kst.strftime('%Y년 %m월 %d일')} ({day_kr}) {kst.strftime('%H:%M')} &nbsp;·&nbsp; 👤 {st.session_state.user_name}</p>
        </div>
      </div>
      <div class="vadm-hero-badge"><span class="vadm-hero-dot"></span>SYSTEM OPERATIONAL · 정상 운영 중</div>
    </div>
    """, unsafe_allow_html=True)

    k1, k2, k3, k4 = st.columns(4)
    kpi_data = [
        (k1, "c-teal",   f"{human_online}", "명", "오늘 출근 (휴먼 직원)", "HUMAN ONLINE", "🧑‍💼"),
        (k2, "c-violet", f"{ai_total}",     "명", "오늘 출근 (AI 직원)",   "AI ONLINE",     "🤖"),
        (k3, "c-cyan",   f"{ai_total}",     "명", "AI 직원 상시 대기",     "AI STANDBY",    "🛰️"),
        (k4, "c-gold",   f"{appr}",         "건", "오늘 승인",             "TODAY'S APPROVALS", "🗂️"),
    ]
    for col, cls, num, unit, lbl, en, ico in kpi_data:
        col.markdown(f"""
        <div class="vadm-kpi {cls}">
          <div class="k-top">
            <div>
              <span class="k-num">{num}</span><span class="k-unit">{unit}</span>
              <div class="k-lbl">{lbl}</div>
              <div class="k-en">{en}</div>
            </div>
            <div class="k-ico">{ico}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="display:flex;gap:10px;flex-wrap:wrap;margin:14px 0 6px;">
      <div class="vadm-chip on"   style="padding:7px 16px;border:1px solid rgba(52,211,153,0.35);">🧑‍💼 휴먼 직원 {human_total}명</div>
      <div class="vadm-chip"      style="padding:7px 16px;color:#C4B5FD;background:rgba(139,92,246,0.12);border:1px solid rgba(139,92,246,0.35);">🤖 AI 직원 {ai_total}명</div>
      <div class="vadm-chip gold" style="padding:7px 16px;border:1px solid rgba(212,175,55,0.35);">👥 전체 Workforce {total_workforce}명</div>
      <div class="vadm-chip rep"  style="padding:7px 16px;border:1px solid rgba(56,189,248,0.35);">⏳ 승인 대기 {pend}건</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    left, right = st.columns([1.35, 1], gap="large")

    with left:
        st.markdown(
            f'<div class="vadm-sec-title">🧑‍💼 휴먼 직원 현황 '
            f'<span class="cnt">전체 {human_total}명</span></div>',
            unsafe_allow_html=True)

        att_map = {}
        if not att_td.empty:
            for _, row in att_td.iterrows():
                att_map[row["emp_id"]] = row
        rep_map = {}
        if not rep_td.empty:
            for _, row in rep_td.iterrows():
                rep_map[row["emp_id"]] = row

        if emp_df.empty:
            st.markdown('<div class="vtm-card"><p>재직 중인 휴먼 직원이 없습니다.</p></div>', unsafe_allow_html=True)
        else:
            for _, emp in emp_df.iterrows():
                eid = emp["id"]; ename = emp["name"]; erole = safe_str(emp.get("role")) or ""
                a = att_map.get(eid)
                r = rep_map.get(eid)

                if a is not None:
                    ci_raw = safe_str(a["checkin"])
                    co_raw = safe_str(a["checkout"])
                    ci  = ci_raw[-8:-3] if ci_raw else "--:--"
                    co  = co_raw[-8:-3] if co_raw else "퇴근전"
                    atp = safe_str(a["att_type"]) or "정상출근"
                else:
                    ci = "--:--"; co = "퇴근전"; atp = "미출근"

                if r is not None:
                    rs = safe_str(r["status"]) or "미제출"
                    try:
                        prg = int(r["pm_progress"]) if safe_str(str(r["pm_progress"])) else 0
                    except (ValueError, TypeError):
                        prg = 0
                else:
                    rs = "미제출"; prg = 0

                ci_cls = "on" if a is not None else "off"
                rep_cls = {"승인":"on","대기중":"gold","반려":"off","보류":"mut"}.get(rs, "mut")
                rep_txt = "미제출(출근전)" if rs == "미제출" else "보고:" + rs

                st.markdown(f"""
                <div class="vadm-emp-row">
                  <div style="display:flex;flex-direction:column;">
                    <span class="vadm-emp-name">{ename}</span>
                    <span style="color:#7E93AB;font-size:0.74rem;font-weight:700;">{erole}</span>
                  </div>
                  <div style="display:flex;gap:7px;flex-wrap:wrap;">
                    <span class="vadm-chip {ci_cls}">✅ {ci}</span>
                    <span class="vadm-chip mut">🏠 {co}</span>
                    <span class="vadm-chip mut">📋 {atp}</span>
                    <span class="vadm-chip {rep_cls}">{rep_txt}</span>
                    <span class="vadm-chip rep">📊 {prg}%</span>
                  </div>
                </div>
                """, unsafe_allow_html=True)

    with right:
        st.markdown(
            f'<div class="vadm-sec-title">🤖 AI 직원 실시간 업무 '
            f'<span class="cnt">{ai_total}명 가동</span></div>',
            unsafe_allow_html=True)

        avatars = ["✍️","✍️","♟️","📈","📣","🧭","🗓️"]
        items_html = ""
        for _bank in range(2):
            for idx, (nm, task) in enumerate(AI_STAFF):
                ava = avatars[idx % len(avatars)]
                items_html += f"""
                <div class="vai-item">
                  <div class="vai-ava">{ava}</div>
                  <div class="vai-info">
                    <div class="vai-name">{nm}</div>
                    <div class="vai-task">{task}</div>
                  </div>
                  <div class="vai-state"><span class="vai-state-dot"></span>업무중</div>
                </div>"""

        st.markdown(f"""
        <div class="vai-panel">
      <div class="vai-head">
        <div class="t">🤖 AI WORKFORCE</div>
        <div class="live"><span class="vai-live-dot"></span>LIVE</div>
      </div>
      <div class="vai-view">
        <div class="vai-track">{items_html}</div>
      </div>
      <div class="vai-foot">
        AI 자동화 상태
        <span class="op"><span class="vadm-hero-dot"></span>Running · {len(AI_STAFF)} Agents</span>
      </div>
    </div>
    """, unsafe_allow_html=True)
 
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
    sb = _sb()
    q2 = sb.table("attendance").select("emp_name,att_type,checkin,checkout,work_date").eq("work_date",str(sel_date))
    if sel_emp != "전체": q2 = q2.eq("emp_name",sel_emp)
    att_r2 = q2.order("checkin").execute()
    att = pd.DataFrame(att_r2.data) if att_r2.data else pd.DataFrame()
    if att.empty:
        st.info(f"📭 {sel_date} 출퇴근 기록 없음")
    else:
        att.columns = ["직원명","유형","출근","퇴근","날짜"]

        st.markdown("""
<style>
[data-testid="stElementToolbar"] {
    background: rgba(8,17,31,0.88) !important;
    border: 1px solid rgba(94,234,212,0.25) !important;
    border-radius: 10px !important;
    padding: 4px !important;
}

[data-testid="stElementToolbar"] button,
[data-testid="stElementToolbar"] svg {
    color: #7FF7DE !important;
    fill: #7FF7DE !important;
    stroke: #7FF7DE !important;
}

[data-testid="stElementToolbar"] button:hover {
    background: rgba(45,212,191,0.16) !important;
}
</style>
""", unsafe_allow_html=True)
        st.dataframe(att, use_container_width=True, hide_index=True)
    if sel_emp == "전체":
        all_emp = get_employees()
        checked = set(att["직원명"].tolist()) if not att.empty else set()
        absent  = all_emp[(~all_emp["name"].isin(checked)) & (all_emp["is_admin"] == 0)]
        if not absent.empty:
            st.markdown("---")
            for _, row in absent.iterrows():
                st.markdown(f"""<div style="background:rgba(239,68,68,0.12);border:1px solid rgba(239,68,68,0.5);
                    border-radius:10px;padding:10px;margin:3px 0;backdrop-filter:blur(10px);">
                  <span style="color:#FCA5A5;font-weight:900;">
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
    sb = _sb()
    rq = sb.table("reports").select("*").eq("work_date",str(sel_date))
    if sel_emp != "전체": rq = rq.eq("emp_name",sel_emp)
    reps_r = rq.execute()
    reps = pd.DataFrame(reps_r.data) if reps_r.data else pd.DataFrame()
    if reps.empty:
        st.info("📭 해당 조건 업무 보고 없음")
        return
 
    def do_approve_task(rid, status, emp, comment):
        _sb().table("reports").update({
            "status":status,"admin_comment":comment,"approved_at":now_str()
        }).eq("id",rid).execute()
        wlog(f"APPROVE_{status}", st.session_state.user_name, emp, comment)
        st.rerun()
 
    for _, r in reps.iterrows():
        rid    = int(r["id"])
        status = safe_str(r["status"]) or "대기중"
        sc     = {"승인":"#10B981","대기중":"#F59E0B","반려":"#EF4444"}.get(status, "#6B7280")
 
        dl_val = safe_str(r["drive_link"])
        rl_val = safe_str(r["result_link"])
        dl_html = f'<a href="{dl_val}" target="_blank" style="color:#38BDF8;font-weight:700;">링크열기</a>' if dl_val else "없음"
        rl_html = f'<a href="{rl_val}" target="_blank" style="color:#38BDF8;font-weight:700;">링크열기</a>' if rl_val else "없음"
 
        am_tasks_txt  = safe_str(r["am_tasks"])  or "미입력"
        pm_done_txt   = safe_str(r["pm_done"])   or "미입력"
        cmt_val       = safe_str(r["admin_comment"]) or ""
        prg_val       = r["pm_progress"] if safe_str(str(r["pm_progress"])) else 0
 
        card_parts = [
            f'<div class="vtm-card">',
            f'  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">',
            f'    <h3 style="margin:0;">{r["emp_name"]} — {r["work_date"]}</h3>',
            f'    <span style="background:{sc};color:#fff;padding:3px 14px;border-radius:12px;font-weight:900;font-size:0.8rem;">{status}</span>',
            f'  </div>',
            f'  <p><b>🌅 오전 계획:</b> {am_tasks_txt}</p>',
            f'  <p><b>🌇 완료 업무:</b> {pm_done_txt}</p>',
            f'  <p><b>📊 진행률:</b> {prg_val}%</p>',
            f'  <p><b>📁 Drive:</b> {dl_html} &nbsp;&nbsp; <b>🔗 결과물:</b> {rl_html}</p>',
        ]
        if cmt_val:
            card_parts.append(f'  <p style="background:rgba(45,212,191,0.15);border-left:3px solid #2DD4BF;padding:6px 10px;border-radius:4px;"><b>💬 코멘트:</b> {cmt_val}</p>')
        card_parts.append('</div>')
        st.markdown("\n".join(card_parts), unsafe_allow_html=True)
 
        cmt_input = st.text_input(
            "💬 코멘트 입력 (선택사항)",
            key=f"tcmt_{rid}",
            placeholder="승인 메시지 또는 반려 사유를 입력하세요..."
        )
        ba, bb, bc = st.columns(3)
        with ba:
            if st.button("✅ 승인", key=f"tap_{rid}", use_container_width=True):
                do_approve_task(rid, "승인", r["emp_name"], cmt_input or "승인되었습니다.")
        with bb:
            if st.button("❌ 반려", key=f"trj_{rid}", use_container_width=True):
                do_approve_task(rid, "반려", r["emp_name"], cmt_input or "반려 사유를 입력해 주세요.")
        with bc:
            if st.button("⏸ 보류", key=f"thl_{rid}", use_container_width=True):
                do_approve_task(rid, "보류", r["emp_name"], cmt_input or "보류 처리되었습니다.")
 
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
 
# ═══════════════════════════════════════════
#  관리자: 결과 승인
# ═══════════════════════════════════════════
def page_admin_approve():
    topbar("✅ 결과 승인")
    c1, c2, c3 = st.columns(3)

    with c1:
        sel_date = st.date_input("날짜", value=now_kst().date(), key="approve_date")

    with c2:
        emp_df = get_employees()
        names = ["전체"] + list(emp_df["name"])
        sel_emp = st.selectbox("직원", names, key="approve_emp")

    with c3:
        sel_status = st.selectbox("상태", ["대기중", "승인", "반려", "보류", "전체"], key="approve_status")

    rq = _sb().table("reports").select("*").eq("work_date", str(sel_date))

    if sel_emp != "전체":
        rq = rq.eq("emp_name", sel_emp)

    if sel_status != "전체":
        rq = rq.eq("status", sel_status)

    pend_r = rq.order("submitted_at", desc=True).execute()
    pend = pd.DataFrame(pend_r.data) if pend_r.data else pd.DataFrame()

    if pend.empty:
        st.info("📭 선택한 조건의 업무보고가 없습니다.")
        return

    st.markdown(
        f"<div class='vtm-card'><h3>📋 조회 결과 {len(pend)}건</h3></div>",
        unsafe_allow_html=True
    )
 
    def do_approve(rid, status, emp, comment):
        _sb().table("reports").update({
            "status":status,"admin_comment":comment,"approved_at":now_str()
        }).eq("id",rid).execute()
        wlog(f"APPROVE_{status}", st.session_state.user_name, emp, comment)
        st.rerun()
 
    for _, r in pend.iterrows():
        with st.expander(f"📝 {r['emp_name']}  ·  {r['work_date']}  ·  진행률 {r['pm_progress']}%"):
            am  = safe_str(r['am_tasks'])    or '없음'
            pm  = safe_str(r['pm_done'])     or '없음'
            tom = safe_str(r['pm_tomorrow']) or '없음'
            rem = safe_str(r['pm_remarks'])  or '없음'
            st.markdown(f"""
<div style="color:#F1F5F9;font-size:0.9rem;line-height:1.8;">
  <p><span style="color:#7FF7DE;font-weight:900;">🌅 오전 계획:</span>&nbsp; {am}</p>
  <p><span style="color:#7FF7DE;font-weight:900;">🌇 완료 업무:</span>&nbsp; {pm}</p>
  <p><span style="color:#7FF7DE;font-weight:900;">📅 내일 예정:</span>&nbsp; {tom}</p>
  <p><span style="color:#7FF7DE;font-weight:900;">💬 특이사항:</span>&nbsp; {rem}</p>
</div>
""", unsafe_allow_html=True)
            dl_val = safe_str(r.get("drive_link"))
            rl_val = safe_str(r.get("result_link"))
            if dl_val:
                st.markdown(f'<p style="color:#60A5FA;font-weight:700;">📁 <a href="{dl_val}" target="_blank" style="color:#60A5FA;">Google Drive 링크 열기</a></p>', unsafe_allow_html=True)
            if rl_val:
                st.markdown(f'<p style="color:#60A5FA;font-weight:700;">🔗 <a href="{rl_val}" target="_blank" style="color:#60A5FA;">결과물 링크 열기</a></p>', unsafe_allow_html=True)

            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
            cmt = st.text_input("💬 코멘트", key=f"cmt_{r['id']}", placeholder="승인/반려 사유를 입력하세요...")
            ca, cb, cc = st.columns(3)
            with ca:
                if st.button("✅ 승인", key=f"ap_{r['id']}", use_container_width=True):
                    do_approve(r['id'], "승인", r['emp_name'], cmt or "승인되었습니다.")
            with cb:
                if st.button("❌ 반려", key=f"rj_{r['id']}", use_container_width=True):
                    do_approve(r['id'], "반려", r['emp_name'], cmt or "반려 사유를 입력해 주세요.")
            with cc:
                if st.button("⏸ 보류", key=f"hl_{r['id']}", use_container_width=True):
                    do_approve(r['id'], "보류", r['emp_name'], cmt or "보류 처리되었습니다.")
 
# ═══════════════════════════════════════════
#  관리자: 직원 관리
# ═══════════════════════════════════════════
def page_admin_emp():
    topbar("👥 직원 관리")
    emp_df = get_employees(active_only=True)
    st.markdown("<div class='vtm-card'><h3>👥 전체 직원 목록</h3></div>", unsafe_allow_html=True)
    for _, emp in emp_df.iterrows():
        ac  = "#34D399" if emp["active"] else "#FCA5A5"
        at  = "재직 중" if emp["active"] else "퇴직"
        adm = "🔴 관리자" if emp["is_admin"] else "🟢 직원"
        ci, cb = st.columns([5, 1])
        with ci:
            st.markdown(f"""<div class="vtm-card" style="padding:9px 15px;margin:2px 0;">
              <span style="font-weight:900;">{emp['name']}</span>
              &nbsp;<span style="color:#94A3B8;font-weight:700;">{emp['role']}</span>
              &nbsp;<span style="color:{ac};font-weight:700;">{at}</span>
              &nbsp;<span style="font-weight:700;">{adm}</span>
            </div>""", unsafe_allow_html=True)
        with cb:
            if emp["active"] and not emp["is_admin"]:
                if st.button("🗑 퇴직", key=f"del_{emp['id']}", use_container_width=True):
                    _sb().table("employees").update({"active":0}).eq("id",emp["id"]).execute()
                    wlog("EMP_DEL", st.session_state.user_name, emp["name"])
                    st.success(f"'{emp['name']}' 퇴직 처리"); st.rerun()
            elif not emp["active"]:
                if st.button("♻ 복직", key=f"act_{emp['id']}", use_container_width=True):
                    _sb().table("employees").update({"active":1}).eq("id",emp["id"]).execute()
                    wlog("EMP_ACT", st.session_state.user_name, emp["name"])
                    st.success(f"'{emp['name']}' 복직 완료"); st.rerun()
                        # ── AI 직원 롤업 목록 ──
    st.markdown("<div class='vtm-card'><h3>🤖 AI 직원 실시간 업무</h3></div>", unsafe_allow_html=True)

    avatars = ["✍️","✍️","♟️","📈","📣","🧭","🗓️"]
    items_html = ""

    for _bank in range(2):
        for idx, (nm, task) in enumerate(AI_STAFF):
            ava = avatars[idx % len(avatars)]
            items_html += f'<div class="vai-item"><div class="vai-ava">{ava}</div><div class="vai-info"><div class="vai-name">{nm}</div><div class="vai-task">담당업무: {task}</div></div><div class="vai-state"><span class="vai-state-dot"></span>업무중</div></div>'

    st.markdown(f'''<div class="vai-panel">
      <div class="vai-head">
        <div class="t">🤖 AI WORKFORCE</div>
        <div class="live"><span class="vai-live-dot"></span>LIVE</div>
      </div>
      <div class="vai-view">
        <div class="vai-track">{items_html}</div>
      </div>
      <div class="vai-foot">
        AI 자동화 상태
        <span class="op"><span class="vadm-hero-dot"></span>Running · {len(AI_STAFF)} Agents</span>
      </div>
    </div>''', unsafe_allow_html=True)

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
                    _sb().table("employees").insert({
                        "id":new_id,"name":new_name.strip(),"role":new_role.strip(),
                        "is_admin":1 if new_admin else 0,"password":new_pw,
                        "active":1,"created_at":now_str()
                    }).execute()
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
            st.markdown(f"<span style='color:#7FF7DE;font-weight:700;font-size:0.84rem;'>"
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
        sb = _sb(); sheets = {}
        if "출퇴근 기록" in rec_types:
            aq = (sb.table("attendance")
                  .select("emp_name,work_date,att_type,checkin,checkout")
                  .gte("work_date",d_from).lte("work_date",d_to))
            if sel_emp != "전체 인원": aq = aq.eq("emp_name",sel_emp)
            ar = aq.order("work_date").order("emp_name").execute()
            if ar.data:
                df = pd.DataFrame(ar.data)
                df.columns = ["직원명","날짜","유형","출근","퇴근"]
                sheets["출퇴근 기록"] = df
        if "업무 보고" in rec_types:
            rq2 = (sb.table("reports")
                   .select("emp_name,work_date,am_tasks,am_priority,pm_done,pm_progress,"
                           "pm_tomorrow,pm_remarks,drive_link,result_link,status,admin_comment,submitted_at")
                   .gte("work_date",d_from).lte("work_date",d_to))
            if sel_emp != "전체 인원": rq2 = rq2.eq("emp_name",sel_emp)
            rr2 = rq2.order("work_date").order("emp_name").execute()
            if rr2.data:
                df = pd.DataFrame(rr2.data)
                df.columns = ["직원명","날짜","오전계획","우선순위","완료업무",
                              "진행률","내일예정","특이사항","Drive","결과링크","상태","코멘트","제출시간"]
                sheets["업무 보고"] = df
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
#  관리자: 회사 일정
# ═══════════════════════════════════════════
def page_admin_company_calendar():
    topbar("📅 회사 일정")

    sb = _sb()
    today = now_kst().date()

    if "admin_cal_selected" not in st.session_state:
        st.session_state.admin_cal_selected = None

    c1, c2, _ = st.columns([1, 1, 2])
    with c1:
        yr = st.number_input("연도", value=today.year, min_value=2024, max_value=2030, key="admin_cy")
    with c2:
        mo = st.number_input("월", value=today.month, min_value=1, max_value=12, key="admin_cm")

    yr = int(yr)
    mo = int(mo)

    from_date = f"{yr}-{mo:02d}-01"
    last_day = calendar.monthrange(yr, mo)[1]
    to_date = f"{yr}-{mo:02d}-{last_day:02d}"

    ev_r = (
        sb.table("company_events")
        .select("*")
        .gte("event_date", from_date)
        .lte("event_date", to_date)
        .order("event_date")
        .execute()
    )

    lv_r = (
        sb.table("leave_requests")
        .select("*")
        .gte("leave_date", from_date)
        .lte("leave_date", to_date)
        .order("leave_date")
        .execute()
    )

    ev_df = pd.DataFrame(ev_r.data) if ev_r.data else pd.DataFrame()
    lv_df = pd.DataFrame(lv_r.data) if lv_r.data else pd.DataFrame()

    event_map = {}
    if not ev_df.empty:
        for _, r in ev_df.iterrows():
            d = safe_str(r.get("event_date"))
            event_map.setdefault(d, []).append(r)

    leave_map = {}
    if not lv_df.empty:
        for _, r in lv_df.iterrows():
            d = safe_str(r.get("leave_date"))
            leave_map.setdefault(d, []).append(r)

    cal_weeks = calendar.monthcalendar(yr, mo)
    sel = st.session_state.admin_cal_selected

    COLG = '<colgroup><col style="width:16.8%"><col style="width:16.8%"><col style="width:16.8%"><col style="width:16.8%"><col style="width:16.8%"><col style="width:8%"><col style="width:8%"></colgroup>'

    st.markdown("""
<style>
table.vtm-cal {
    width:100%; border-collapse:separate; border-spacing:3px;
    table-layout:fixed; margin:0 !important;
}
table.vtm-cal th {
    padding:8px 4px; text-align:center; font-weight:900;
    font-size:0.86rem; border-radius:7px;
}
table.vtm-cal th.hwd  { background:#1E293B; color:#2DD4BF; }
table.vtm-cal th.hsat { background:#1a2d44; color:#93C5FD; }
table.vtm-cal th.hsun { background:#2a1520; color:#FCA5A5; }
table.vtm-cal td {
    border-radius:8px 8px 0 0; vertical-align:top;
    padding:7px 7px 5px; height:96px;
    border:1.5px solid transparent; border-bottom:none !important;
    position:relative;
}
table.vtm-cal td.wd    { background:#FFFFFF; border-color:#CBD5E1; }
table.vtm-cal td.sat   { background:#EFF6FF; border-color:#BFDBFE; }
table.vtm-cal td.sun   { background:#FFF1F2; border-color:#FECDD3; }
table.vtm-cal td.today { background:#ECFEFF !important; border:2px solid #2DD4BF !important; border-bottom:none !important; }
table.vtm-cal td.sel   { background:#EFF6FF !important; border:2px solid #3B82F6 !important; border-bottom:none !important; }
table.vtm-cal td.empty { background:transparent !important; border:none !important; }
table.vtm-cal .daynum  { font-size:1rem; font-weight:900; display:block; margin-bottom:4px; line-height:1; }
table.vtm-cal td.wd .daynum { color:#1E293B; }
table.vtm-cal td.sat .daynum { color:#1D4ED8; }
table.vtm-cal td.sun .daynum { color:#BE123C; }
table.vtm-cal .badge {
    display:inline-block; border-radius:4px;
    padding:1px 5px; font-size:0.56rem; font-weight:800;
    margin:1px 0; line-height:1.5; white-space:nowrap;
}
table.vtm-cal .b-event { background:#DBEAFE; color:#1E40AF; }
table.vtm-cal .b-ok { background:#D1FAE5; color:#065F46; }
table.vtm-cal .b-pend { background:#FEF3C7; color:#92400E; }
table.vtm-cal .b-rej { background:#FEE2E2; color:#991B1B; }

div:has(> .admin-cmark) + div .stButton > button {
    background:#334155 !important;
    color:#CBD5E1 !important;
    height:28px !important;
    min-height:28px !important;
    border-radius:0 0 8px 8px !important;
    font-size:0.62rem !important;
    font-weight:700 !important;
    padding:5px 2px !important;
    box-shadow:none !important;
    border:none !important;
    width:100% !important;
}
div:has(> .admin-cmark) + div .stButton > button:hover {
    background:#1E40AF !important;
    color:#BFDBFE !important;
}
div:has(> .admin-cmark) + div [data-testid="stHorizontalBlock"] {
    gap:3px !important;
    margin-top:-1px !important;
}
div:has(> .admin-cmark) + div [data-testid="stColumn"] {
    padding:0 !important;
    min-width:0 !important;
}
</style>
""", unsafe_allow_html=True)

    st.markdown(
        f'<table class="vtm-cal">{COLG}'
        '<thead><tr>'
        '<th class="hwd">월</th><th class="hwd">화</th><th class="hwd">수</th>'
        '<th class="hwd">목</th><th class="hwd">금</th>'
        '<th class="hsat">토</th><th class="hsun">일</th>'
        '</tr></thead></table>',
        unsafe_allow_html=True
    )

    for week in cal_weeks:
        cells = f'<table class="vtm-cal">{COLG}<tbody><tr>'

        for i, day in enumerate(week):
            is_sat = i == 5
            is_sun = i == 6

            if day == 0:
                cells += '<td class="empty"></td>'
                continue

            d = f"{yr}-{mo:02d}-{day:02d}"
            base = "sun" if is_sun else ("sat" if is_sat else "wd")
            cls = base + (" sel" if d == sel else (" today" if d == today_str() else ""))

            badges = ""

            for ev in event_map.get(d, [])[:2]:
                badges += f'<span class="badge b-event">📌 {safe_str(ev.get("event_type"))}</span><br>'

            for lv in leave_map.get(d, [])[:3]:
                status = safe_str(lv.get("status")) or "대기중"
                emp = safe_str(lv.get("emp_name")) or "-"
                ltype = safe_str(lv.get("leave_type")) or "-"

                if status == "승인":
                    badges += f'<span class="badge b-ok">🏖 {emp} {ltype}</span><br>'
                elif status == "반려":
                    badges += f'<span class="badge b-rej">❌ {emp}</span><br>'
                else:
                    badges += f'<span class="badge b-pend">⏳ {emp} {ltype}</span><br>'

            cells += f'<td class="{cls}"><span class="daynum">{day}</span>{badges}</td>'

        cells += '</tr></tbody></table>'
        st.markdown(cells, unsafe_allow_html=True)

        st.markdown('<div class="admin-cmark"></div>', unsafe_allow_html=True)

        cols = st.columns([1, 1, 1, 1, 1, 0.48, 0.48])
        for i, day in enumerate(week):
            with cols[i]:
                if day == 0 or i >= 5:
                    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                else:
                    d = f"{yr}-{mo:02d}-{day:02d}"
                    is_sel = d == sel
                    lbl = "▲ 닫기" if is_sel else "상세내역 확인"
                    if st.button(lbl, key=f"admin_cbtn_{d}", use_container_width=True):
                        st.session_state.admin_cal_selected = None if is_sel else d
                        st.rerun()

        week_dates = [f"{yr}-{mo:02d}-{day:02d}" for i, day in enumerate(week) if day != 0 and i < 5]

        if sel in week_dates:
            st.markdown(f"<div class='vtm-card'><h3>📅 {sel} 상세내역</h3></div>", unsafe_allow_html=True)

            st.markdown("<div class='vtm-card'><h3>📌 회사 일정 등록</h3></div>", unsafe_allow_html=True)

            with st.form(f"form_company_event_{sel}", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    event_type = st.selectbox(
                        "일정 유형",
                        ["회의", "미팅", "출장", "회식", "회사행사", "교육", "생일", "공휴일", "기타"],
                        key=f"ce_type_{sel}"
                    )
                    end_date = st.date_input("종료일", value=datetime.strptime(sel, "%Y-%m-%d").date(), key=f"ce_end_{sel}")
                with c2:
                    title = st.text_input("일정 제목", placeholder="예) 전체 회의 / 김다현 생일 / 거래처 미팅", key=f"ce_title_{sel}")
                    description = st.text_area("상세 내용", height=90, placeholder="일정 설명을 입력하세요.", key=f"ce_desc_{sel}")

                submitted = st.form_submit_button("✅ 회사 일정 등록", use_container_width=True)

                if submitted:
                    if not title.strip():
                        st.error("일정 제목을 입력하세요.")
                    else:
                        sb.table("company_events").insert({
                            "event_date": sel,
                            "end_date": str(end_date) if end_date else sel,
                            "event_type": event_type,
                            "title": title.strip(),
                            "description": description.strip(),
                            "created_by_id": st.session_state.user_id,
                            "created_by_name": st.session_state.user_name,
                            "is_public": True,
                            "created_at": now_str(),
                            "updated_at": now_str()
                        }).execute()
                        wlog("COMPANY_EVENT_ADD", st.session_state.user_name, title.strip(), event_type)
                        st.success("✅ 회사 일정이 등록되었습니다.")
                        st.rerun()

            day_events = event_map.get(sel, [])
            day_leaves = leave_map.get(sel, [])

            if not day_events and not day_leaves:
                st.info("📭 이 날짜에는 등록된 회사 일정이나 휴가 신청이 없습니다.")

            for ev in day_events:
                ev_id = int(ev.get("id"))
                st.markdown(f"""
                <div class="vtm-card">
                    <h3>📌 {safe_str(ev.get("event_type"))} · {safe_str(ev.get("title"))}</h3>
                    <p>{safe_str(ev.get("description")) or ""}</p>
                    <p style="color:#94A3B8;font-size:0.8rem;">
                        등록자: {safe_str(ev.get("created_by_name")) or "-"}
                    </p>
                </div>
                """, unsafe_allow_html=True)

                if st.button("🗑 회사 일정 삭제", key=f"delete_event_{ev_id}", use_container_width=True):
                    sb.table("company_events").delete().eq("id", ev_id).execute()
                    wlog("COMPANY_EVENT_DELETE", st.session_state.user_name, safe_str(ev.get("title")), safe_str(ev.get("event_type")))
                    st.warning("🗑 회사 일정이 삭제되었습니다.")
                    st.rerun()

            for lv in day_leaves:
                lv_id = int(lv.get("id"))
                status = safe_str(lv.get("status")) or "대기중"
                emp_name = safe_str(lv.get("emp_name")) or "-"
                leave_type = safe_str(lv.get("leave_type")) or "-"
                reason = safe_str(lv.get("reason")) or "사유 없음"

                st.markdown(f"""
                <div class="vtm-card">
                    <h3>🏖 {emp_name} · {leave_type}</h3>
                    <p><b>상태:</b> {status}</p>
                    <p><b>사유:</b> {reason}</p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"🗑 {leave_type} 신청 삭제", key=f"delete_leave_{lv_id}", use_container_width=True):
                    sb.table("leave_requests").delete().eq("id", lv_id).execute()
                    wlog("LEAVE_DELETE", st.session_state.user_name, emp_name, f"{sel} {leave_type}")
                    st.warning("🗑 휴가/반차 신청이 삭제되었습니다.")
                    st.rerun()
                    
                if status == "대기중":
                    comment = st.text_input("관리자 코멘트", key=f"leave_comment_{lv_id}", placeholder="승인 또는 반려 사유")

                    ca, cb = st.columns(2)
                    with ca:
                        if st.button("✅ 휴가 승인", key=f"leave_ok_{lv_id}", use_container_width=True):
                            sb.table("leave_requests").update({
                                "status": "승인",
                                "admin_comment": comment or "승인되었습니다.",
                                "approved_at": now_str(),
                                "approved_by_id": st.session_state.user_id,
                                "approved_by_name": st.session_state.user_name
                            }).eq("id", lv_id).execute()
                            wlog("LEAVE_APPROVE", st.session_state.user_name, emp_name, f"{sel} {leave_type}")
                            st.success("✅ 승인 완료")
                            st.rerun()

                    with cb:
                        if st.button("❌ 휴가 반려", key=f"leave_no_{lv_id}", use_container_width=True):
                            sb.table("leave_requests").update({
                                "status": "반려",
                                "admin_comment": comment or "반려되었습니다.",
                                "approved_at": now_str(),
                                "approved_by_id": st.session_state.user_id,
                                "approved_by_name": st.session_state.user_name
                            }).eq("id", lv_id).execute()
                            wlog("LEAVE_REJECT", st.session_state.user_name, emp_name, f"{sel} {leave_type}")
                            st.warning("❌ 반려 처리 완료")
                            st.rerun()
# ═══════════════════════════════════════════
#  관리자: 로그
# ═══════════════════════════════════════════            
def page_admin_logs():
    topbar("🔍 시스템 로그")
    log_r = _sb().table("logs").select("created_at,action,actor,target,detail").order("created_at",desc=True).limit(300).execute()
    logs = pd.DataFrame(log_r.data) if log_r.data else pd.DataFrame()
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
    # ── 관리자(본부장) 로그인 시: 프리미엄 테마 + 배경 영상(vtm01.mp4) 주입 ──
    #    비관리자(디렉터/직원): 모든 페이지에 디렉터 테마 + 배경 영상(vtm02.mp4) 주입
    #    → 홈/출퇴근/업무보고/달력/VTM WAY 전 페이지에 동일한 프리미엄 룩 적용
    if st.session_state.is_admin:
        inject_admin_theme()
    else:
        inject_director_theme()

    render_sidebar()
 
    if st.session_state.is_admin:
        pages = {
            "home":          page_admin_home,
            "admin_attend":  page_admin_attend,
            "admin_tasks":   page_admin_tasks,
            "admin_approve": page_admin_approve,
            "admin_emp":     page_admin_emp,
            "admin_excel":   page_admin_excel,
            "admin_company_calendar": page_admin_company_calendar,
            "admin_logs":    page_admin_logs,
            "emp_guide":     page_emp_guide,
        }
    else:
        pages = {
            "home":         page_emp_home,
            "emp_attend":   page_emp_attend,
            "emp_report":   page_emp_report,
            "emp_calendar": page_emp_calendar,
            "emp_guide":    page_emp_guide,
        }
 
    pages.get(st.session_state.page, list(pages.values())[0])()
 
    st.markdown("""
    <div style="text-align:center;padding:20px;color:#475569;
                font-size:0.74rem;font-weight:700;position:relative;z-index:1;">
        © 2026 (주) 브이티엠 운영 대시보드 v2.0.8
        &nbsp;|&nbsp; 개발자: 박동진 본부장
    </div>""", unsafe_allow_html=True)
