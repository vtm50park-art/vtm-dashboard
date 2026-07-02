# ═══════════════════════════════════════════════════════════════════
#  VTM OS 로그인 — 배경 영상 버전 패치 (v2.0.2-video)
#
#  [v2.0.1-stable 대비 변경점]
#   · 배경: HTML5 <video> (Supabase Storage MP4) 방식으로 적용
#     - autoplay / muted / loop / playsinline / preload="auto"
#     - position:fixed + object-fit:cover 로 전체 화면 커버
#     - pointer-events:none (클릭 불가) / z-index:-2
#     - 영상 위 Dark Overlay(linear-gradient, 평균 ≈ rgba(0,0,0,.55))로
#       로그인 카드 가독성 확보 / z-index:-1
#     - 영상 로드 실패 시 폴백: html/body의 다크 그라데이션이 그대로 노출
#   · Vimeo iframe 은 사용하지 않음 (완전 제거 상태 유지)
#   · :has() 미사용, 카드는 클래스 기반 wrapper 유지 (v2.0.1과 동일)
#
#  [불변 영역]
#   · 로그인 로직 / Supabase / Employee Query / Password 검증 /
#     session_state / st.rerun → 원본과 100% 동일
#
#  아래 3개 블록을 vtm_dashboard.py 의 같은 이름 함수와 통째로 교체하세요.
# ═══════════════════════════════════════════════════════════════════

VTM_LOGO_URL     = "https://i.postimg.cc/TwMLPgWj/beu-itiem-logo.png"
VTM_BG_VIDEO_URL = "https://pwaqbxfaokaliclhmixo.supabase.co/storage/v1/object/public/assets/vtm.mp4"


# ───────────────────────────────────────────────────────────────────
# 1) init_data()  ─ 교체 블록 (이전 패치와 동일: emp_seo 생성 제거)
# ───────────────────────────────────────────────────────────────────
def init_data():
    """앱 세션 시작 시 기본 직원 데이터 확인 및 초기화 (세션당 1회 실행)"""
    # 이미 이번 세션에서 초기화됐으면 스킵
    if st.session_state.get("_db_init_done"):
        return

    try:
        sb = _sb()

        # ── Supabase 연결 확인 ──
        test = sb.table("employees").select("id").limit(1).execute()

        # ── 기본 직원 없으면 삽입 (※ 서아영/emp_seo 는 신규 세팅에서 제외) ──
        check = sb.table("employees").select("id").eq("id","admin_park").execute()
        if not check.data:
            _now = now_str()
            sb.table("employees").insert([
                {"id":"admin_park","name":"박동진 본부장","role":"본부장",
                 "is_admin":1,"password":"5638","active":1,"created_at":_now},
                {"id":"emp_ahn","name":"안효민 디렉터","role":"디렉터",
                 "is_admin":0,"password":"","active":1,"created_at":_now},
            ]).execute()

        # ── 김소원 퇴사 처리 (행이 없어도 오류 없음) ──
        try:
            sb.table("employees").update({"active":0}).eq("id","emp_kim").execute()
        except Exception:
            pass

        # ── 서아영 퇴사 처리: 기존 DB에 emp_seo가 이미 있는 경우 비활성화 ──
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


# ───────────────────────────────────────────────────────────────────
# 2) inject_all()  ─ 교체 블록
#    전역 CSS/별 캔버스: 원본 그대로.
#    로그인 전용 CSS: Vimeo·:has() 제거, 그라데이션 배경,
#    클래스 기반 카드(.st-key-vtm_login_card), Workforce 패널 스타일 추가.
# ───────────────────────────────────────────────────────────────────
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

/* ─── 입력 필드: 아이보리 그라데이션 + 검정 글자 ─── */
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
 
/* ── expander 내부 텍스트 가독성 ── */
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

/* ── 달력 투명 클릭 버튼 CSS는 page_emp_calendar() 안에서 별도 주입 ── */

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

    # ═══════════════════════════════════════════════════════════
    # ▼▼▼ [로그인 전용 CSS — 배경 영상 버전] ▼▼▼
    #  · 배경: HTML5 Video (.vtm-video-bg) + Dark Overlay (.vtm-bgoverlay)
    #  · 폴백: html/body 다크 그라데이션 (영상 로드 실패 시 자동 노출)
    #  · Vimeo iframe 미사용 / :has() 미사용
    #  · 카드는 .st-key-vtm_login_card (클래스 기반 wrapper)
    #  · 로그인 전(logged_in=False)에만 주입 → 로그인 후 영향 없음
    # ═══════════════════════════════════════════════════════════
    if not st.session_state.get("logged_in", False):
        st.markdown("""
<style>
/* ── 폴백 배경: 영상 로드 전/실패 시 노출되는 다크 그라데이션 ──
     (root 배경은 z-index:-2 영상보다 항상 뒤에 그려짐)            */
html, body {
    background:
        radial-gradient(1100px 640px at 16% 26%, rgba(20,224,184,0.12) 0%, transparent 60%),
        radial-gradient(920px 560px at 86% 78%, rgba(14,165,233,0.11) 0%, transparent 60%),
        linear-gradient(180deg, #050B14 0%, #081222 48%, #04090F 100%) !important;
}
/* ── 영상이 비치도록 Streamlit 컨테이너 전부 투명화 ── */
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"]>section,
[data-testid="stMain"],
[data-testid="stMainBlockContainer"],
.main, .main>div {
    background: transparent !important;
}

/* ── HTML5 배경 영상 (Supabase Storage MP4) ── */
.vtm-video-bg {
    position: fixed;
    top: 0; left: 0;
    width: 100%;
    height: 100%;
    object-fit: cover;
    z-index: -2;
    pointer-events: none;
}
/* ── Dark Overlay: 로그인 카드 가독성 확보 (평균 ≈ rgba(0,0,0,.55)) ── */
.vtm-bgoverlay {
    position: fixed;
    inset: 0;
    z-index: -1;
    pointer-events: none;
    background:
        radial-gradient(ellipse at 26% 38%, rgba(20,224,184,0.08) 0%, transparent 55%),
        linear-gradient(180deg, rgba(0,0,0,0.62) 0%, rgba(0,0,0,0.48) 45%, rgba(0,0,0,0.72) 100%);
}

[data-testid="stMainBlockContainer"] {
    max-width: 1180px !important;
    padding-top: 5vh !important;
    padding-bottom: 4vh !important;
}

/* ── 좌(브랜드) / 우(카드) 세로 중앙 정렬 ── */
[data-testid="stHorizontalBlock"] { align-items: center !important; }

/* ── 좌측 브랜드 영역 ── */
.vtm-brand { padding: 6px 26px 6px 4px; }
.vtm-brand-logo img {
    width: 150px; max-width: 42vw; height: auto; display: block;
    filter: drop-shadow(0 0 26px rgba(20,224,184,0.35));
    margin-bottom: 18px;
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
    letter-spacing: 0.42em; margin: 7px 0 0 2px;
}

/* ── Human × AI Workforce 카피 ── */
.vtm-hx-badge {
    display: inline-block; margin: 20px 0 0;
    padding: 6px 14px; border-radius: 999px;
    background: rgba(45,212,191,0.10);
    border: 1px solid rgba(45,212,191,0.42);
    color: #7FF7DE; font-size: 0.82rem; font-weight: 900;
    letter-spacing: 0.14em;
}
.vtm-hx-line1 {
    color: #DCE8F5; font-size: 1.02rem; font-weight: 700;
    margin: 14px 0 0; letter-spacing: 0.01em;
}
.vtm-hx-line2 {
    font-size: 0.92rem; font-weight: 800; margin: 5px 0 0;
    background: linear-gradient(90deg, #7FF7DE 0%, #38BDF8 100%);
    -webkit-background-clip: text; background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: 0.04em;
}
.vtm-brand-tag {
    color: #7E93AB; font-size: 0.84rem; font-weight: 500;
    margin: 10px 0 0; letter-spacing: 0.02em;
}

/* ── 아이콘 3종 ── */
.vtm-feat-row { display: flex; gap: 30px; margin-top: 28px; flex-wrap: wrap; }
.vtm-feat { text-align: center; min-width: 86px; }
.vtm-feat svg { width: 28px; height: 28px; margin-bottom: 7px; }
.vtm-feat-t { color: #F1F5F9; font-size: 0.84rem; font-weight: 800; margin: 0; }
.vtm-feat-d { color: #7E93AB; font-size: 0.74rem; font-weight: 500; margin: 3px 0 0; }

/* ── Workforce Status 패널 (기능 없는 상태 표시 카드) ── */
.vtm-wf-panel {
    margin-top: 26px; max-width: 480px;
    background: linear-gradient(160deg, rgba(13,26,44,0.62) 0%, rgba(7,14,26,0.78) 100%);
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

/* ── 로그인 카드: 클래스 기반 wrapper (st.container(key=...)) ── */
.st-key-vtm_login_card {
    background: linear-gradient(165deg, rgba(14,26,44,0.78) 0%, rgba(7,14,26,0.90) 100%);
    border: 1px solid rgba(94,234,212,0.16);
    border-radius: 24px;
    padding: 34px 30px 24px;
    box-shadow: 0 34px 90px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,255,255,0.06);
}
.vtm-card-head { text-align: center; margin-bottom: 16px; }
.vtm-card-head img {
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

/* ── 로그인 모드: 입력 필드 → 다크 글래스 ── */
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

/* ── selectbox 드롭다운 팝오버 ── */
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

/* ── 로그인 버튼 → 틸 그라데이션 ── */
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

/* ── 별 캔버스: 은은하게 ── */
#vtm-stars { opacity: 0.35 !important; }

/* ── 모바일: 첫 번째 컬럼(브랜드) 숨김 → 카드 중심 단일 컬럼 ── */
/*    위치 선택자(first/last-child)만 사용 — 로그인 화면의 유일한 컬럼 블록 ── */
@media (max-width: 920px) {
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child,
    [data-testid="stHorizontalBlock"] > div[data-testid="column"]:first-child {
        display: none !important;
    }
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child,
    [data-testid="stHorizontalBlock"] > div[data-testid="column"]:last-child {
        width: 100% !important; flex: 1 1 100% !important;
    }
    .st-key-vtm_login_card { padding: 26px 20px 20px; border-radius: 20px; }
    [data-testid="stMainBlockContainer"] {
        padding-top: 6vh !important;
        max-width: 460px !important;
    }
    .vtm-card-welcome { font-size: 1.48rem; }
}
</style>
""", unsafe_allow_html=True)


# ───────────────────────────────────────────────────────────────────
# 3) render_login()  ─ 교체 블록
#    · 배경: HTML5 <video> (Supabase Storage MP4) + Dark Overlay
#    · 카드: st.container(key="vtm_login_card") → 클래스 기반 스타일
#    · 로그인 로직: 원본과 100% 동일
# ───────────────────────────────────────────────────────────────────
def render_login():
    inject_all()

    # ── HTML5 배경 영상 + Dark Overlay ──
    #    autoplay / muted / loop / playsinline: 모바일 포함 자동재생 정책 대응
    #    pointer-events:none (CSS): 영상 클릭 불가
    st.markdown(f"""
    <video autoplay muted loop playsinline preload="auto" class="vtm-video-bg">
        <source src="{VTM_BG_VIDEO_URL}" type="video/mp4">
    </video>
    <div class="vtm-bgoverlay"></div>
    """, unsafe_allow_html=True)

    # ── PC: 좌측 브랜드 + 우측 로그인 카드 / 모바일: 카드 단일 컬럼 ──
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
        # 클래스 기반 카드 wrapper: .st-key-vtm_login_card 로 스타일링
        # (Streamlit ≥1.39. 구버전이면 스타일 없이도 정상 동작하도록 폴백)
        try:
            card = st.container(key="vtm_login_card")
        except TypeError:
            card = st.container()

        with card:
            st.markdown(f"""
            <div class="vtm-card-head">
              <img src="{VTM_LOGO_URL}" alt="VTM OS">
              <p class="vtm-card-os">VTM&nbsp;OS</p>
              <h2 class="vtm-card-welcome">Welcome Back</h2>
              <p class="vtm-card-sub">브이티엠 운영 시스템에 오신것을 환영합니다.</p>
            </div>
            """, unsafe_allow_html=True)

            # ── 이하 로그인 로직: 원본과 동일 (절대 변경 금지 영역) ──
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
            <p class="vtm-ver"><b>VTM OS 2.0.2</b> · 개발자: 박동진 본부장</p>
            """, unsafe_allow_html=True)
