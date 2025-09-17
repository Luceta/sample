
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# ---------- SaaS-like theming ----------
st.set_page_config(page_title="ActionNote — AI 협업 노트", page_icon="📌", layout="wide")

CSS = """
<style>
:root {
  --bg:#0b1220;
  --card:#11192a;
  --text:#e8eef6;
  --accent:#7aa2ff;
  --accent-2:#00d4ff;
}
main, .stApp { background: linear-gradient(180deg, var(--bg) 0%, #0f172a 100%); color: var(--text); }
[data-testid="stSidebar"] { background: linear-gradient(180deg, #0d1426, #0b1220); border-right: 1px solid #1f2a44; }
.grad { background: linear-gradient(90deg, var(--accent), var(--accent-2)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.card { background: var(--card); border: 1px solid #1f2a44; border-radius: 16px; padding: 18px 20px; box-shadow: 0 8px 24px rgba(0,0,0,0.25); }
.stButton>button { background: linear-gradient(90deg, var(--accent), var(--accent-2)); border:0; color:#0b1220; font-weight:700; border-radius:12px; padding:.6rem 1rem; }
.stTextArea textarea, .stTextInput input { background:#0d1528; color:var(--text); border:1px solid #20304c; border-radius:12px; }
.dataframe th, .dataframe td { color:#dbe7f3 !important; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("### 📌 ActionNote")
    st.caption("회의 → 요약/결정/액션 → 메일/캘린더")
    st.divider()
    st.markdown("**입력 소스**")
    input_mode = st.radio("", ["텍스트 붙여넣기", "파일 업로드(.txt/.md/.docx/.pdf)", "노트 사진(OCR) — 데모용 텍스트"], label_visibility="collapsed")
    st.divider()
    st.caption("⚡ 데모 가이드")
    st.markdown("- 입력 선택 → 텍스트/파일 업로드\n- 결과 탭에서 요약/결정/액션/메일 확인\n- 아래에서 .ics(일정) 내려받기")

st.markdown("<h1 class='grad'>ActionNote — AI 협업 노트 (SaaS Prototype)</h1>", unsafe_allow_html=True)
st.markdown("<div class='card'>회의 메모/자료를 입력하면, 요약·결정·액션 테이블과 메일 초안을 생성하고, 추천 시간대 선택으로 일정(.ics)까지 만듭니다.</div>", unsafe_allow_html=True)
st.write("")

colL, colR = st.columns([1.2, 1])

with colL:
    st.subheader("① 입력")
    if input_mode == "텍스트 붙여넣기":
        raw_text = st.text_area("회의 메모/대화 내용을 붙여넣어 주세요", height=220, placeholder="안건/논의/결정 중심으로 자유롭게 입력")
    elif input_mode == "파일 업로드(.txt/.md/.docx/.pdf)":
        up = st.file_uploader("회의 자료 업로드", type=["txt","md","docx","pdf"])
        raw_text = ""
        if up is not None:
            raw_text = up.read().decode("utf-8","ignore")
            st.success(f"업로드 완료: {up.name}")
    else:
        raw_text = st.text_area("노트 사진(OCR) 데모 — 텍스트 입력", height=200, value="안건: 신규 기능 A 논의\n- 발언자A: 와이어프레임 필요\n- 발언자B: 경쟁사 B 리서치\n결정: 다음 주까지 WF 시안, 리서치 1건\n마감: WF(2주), 리서치(1주)")

    st.subheader("② 파라미터")
    with st.expander("액션 아이템 기본값"):
        default_durations = {"가벼움(30분)":30,"표준(60분)":60,"심화(90분)":90}
        dur_choice = st.selectbox("예상 소요", list(default_durations.keys()))
        deadline_days = st.slider("기본 마감일(오늘 기준, 일)", 1, 21, 7)

    go = st.button("🚀 문서 생성")

with colR:
    st.subheader("③ 결과")
    tab1, tab2, tab3, tab4 = st.tabs(["요약", "결정", "액션 테이블", "메일 미리보기"])

    if 'summary' not in st.session_state:
        st.session_state.summary = ""
        st.session_state.decisions = "- (생성 후 표시)"
        st.session_state.df = pd.DataFrame(columns=["업무","담당","기한","우선순위"])
        st.session_state.mail = ""

    with tab1:
        st.markdown(st.session_state.summary or "_생성 버튼을 눌러주세요_")
    with tab2:
        st.markdown(st.session_state.decisions or "_생성 버튼을 눌러주세요_")
    with tab3:
        st.dataframe(st.session_state.df, use_container_width=True, height=220)
    with tab4:
        st.code(st.session_state.mail or "메일 미리보기는 생성 이후 표시됩니다.", language="markdown")

st.divider()

st.subheader("④ 일정(.ics) 내려받기 — 데모")
date = st.date_input("시작 날짜", datetime.today())
slot_choice = st.selectbox("추천 슬롯(데모)", ["09:00-09:30","10:00-11:00","14:00-15:00"])
download_ics = st.button("📅 .ics 생성")

# ---------- Generation logic (demo stubs) ----------
def generate_docs(text:str, dur_min:int, deadline_days:int):
    if not text.strip():
        return ("### 회의 요약\n- (입력 없음)\n",
                "- (입력 없음)\n",
                pd.DataFrame(columns=["업무","담당","기한","우선순위"]),
                "# 메일 초안\n\n(입력 없음)")

    summary = "### 회의 요약\n- 신규 기능 A 와이어프레임 필요\n- 경쟁사 B 리서치 진행\n- 다음 주 중 1차 검토 미팅\n"
    decisions = "### 결정 사항\n- WF 시안 1주 내 공유\n- 경쟁사 리서치 1건 수집\n- 다음 회의 전 개발 기술 검토\n"
    ddl1 = (datetime.today() + timedelta(days=deadline_days)).strftime("%Y-%m-%d")
    ddl2 = (datetime.today() + timedelta(days=max(1,deadline_days-3))).strftime("%Y-%m-%d")
    df = pd.DataFrame([
        ["와이어프레임 제작", "디자이너 김OO", ddl1, "높음"],
        ["경쟁사 리서치", "PM 이OO", ddl2, "중간"],
        ["기술 검토 미팅 준비", "개발팀", ddl1, "중간"],
    ], columns=["업무","담당","기한","우선순위"])

    mail = f"""# [회의 요약] 신규 기능 A / 주간 정기

안녕하세요 팀,
아래는 오늘 회의 요약과 실행 항목입니다.

## 요약
- 신규 기능 A 와이어프레임 필요
- 경쟁사 B 리서치 진행
- 다음 주 중 1차 검토 미팅

## 결정 사항
- WF 시안 1주 내 공유
- 경쟁사 리서치 1건 수집
- 다음 회의 전 개발 기술 검토

## 실행 항목
| 업무 | 담당 | 기한 | 우선순위 |
|---|---|---|---|
| 와이어프레임 제작 | 디자이너 김OO | {ddl1} | 높음 |
| 경쟁사 리서치 | PM 이OO | {ddl2} | 중간 |
| 기술 검토 미팅 준비 | 개발팀 | {ddl1} | 중간 |

감사합니다.
"""
    return summary, decisions, df, mail

if go:
    s, d, df, mail = generate_docs(raw_text, default_durations[dur_choice], deadline_days)
    st.session_state.summary = s
    st.session_state.decisions = d
    st.session_state.df = df
    st.session_state.mail = mail
    st.success("문서 생성 완료! 우측 탭에서 확인하세요.")

# ---------- ICS creation (demo) ----------
def make_ics(date_str:str, timestr:str, title="ActionNote Action"):
    start, end = timestr.split("-")
    dt = datetime.strptime(f"{date_str} {start}", "%Y-%m-%d %H:%M")
    dt_end = datetime.strptime(f"{date_str} {end}", "%Y-%m-%d %H:%M")
    ics = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//ActionNote//SaaS Prototype//EN
BEGIN:VEVENT
UID:{datetime.utcnow().timestamp()}@actionnote
DTSTAMP:{datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")}
DTSTART:{dt.strftime("%Y%m%dT%H%M%S")}
DTEND:{dt_end.strftime("%Y%m%dT%H%M%S")}
SUMMARY:{title}
DESCRIPTION:자동 생성된 액션 일정
END:VEVENT
END:VCALENDAR"""
    return ics

if download_ics:
    ics_text = make_ics(date.strftime("%Y-%m-%d"), slot_choice, "액션 수행 시간")
    st.download_button("📥 .ics 파일 다운로드", data=ics_text, file_name="actionnote_action.ics", mime="text/calendar")
