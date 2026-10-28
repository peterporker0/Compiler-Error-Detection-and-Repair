import json, sqlite3
from datetime import datetime
from pathlib import Path
from html import escape
import pandas as pd
import streamlit as st
from pipeline import analyze_code
from repair_model import train_models

ROOT = Path(__file__).resolve().parent
DB = ROOT / "codelens_history.sqlite3"
st.set_page_config(page_title="CodeLens AI — Compiler Studio", page_icon="🧬", layout="wide")

st.markdown(r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;600;700;800&display=swap');
:root{--mint:#5eead4;--blue:#7c9cff;--violet:#c4a5fd}
html,body,[class*="css"]{font-family:Manrope,sans-serif}
.stApp{background:radial-gradient(ellipse at 80% 0%,rgba(86,73,190,.18),transparent 38%),radial-gradient(ellipse at 0% 34%,rgba(29,181,173,.09),transparent 35%),#080d18;color:#edf4ff}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0d1524,#090f1a);border-right:1px solid rgba(155,177,211,.16)}
.block-container{max-width:1500px;padding-top:1.4rem}
.hero{position:relative;overflow:hidden;padding:30px;border:1px solid rgba(142,165,211,.2);border-radius:24px;background:linear-gradient(118deg,#182840ee,#141830e8 58%,#221a43e0);animation:rise .6s ease both}
.hero:after{content:"";position:absolute;right:-90px;top:-190px;width:350px;height:350px;border-radius:50%;background:radial-gradient(circle,rgba(94,234,212,.22),transparent 68%);animation:orb 8s ease-in-out infinite}
.eyebrow{display:inline-flex;gap:8px;align-items:center;color:#9cefe4;border:1px solid #5eead433;background:#5eead411;padding:7px 11px;border-radius:99px;font-size:10px;font-weight:800;letter-spacing:1.3px;text-transform:uppercase;position:relative;z-index:1}
.dot{width:6px;height:6px;background:var(--mint);border-radius:50%;animation:pulse 1.7s infinite}
.hero h1{position:relative;z-index:1;font-size:clamp(32px,4vw,48px);letter-spacing:-2px;line-height:1.12;margin:18px 0 10px;color:#f4f7ff}
.gradient{background:linear-gradient(90deg,var(--mint),#8cb5ff 50%,var(--violet));-webkit-background-clip:text;background-clip:text;color:transparent}
.hero p{position:relative;z-index:1;color:#a6b5cb;font-size:13px;line-height:1.8;max-width:800px}
.chips{position:relative;z-index:1;display:flex;flex-wrap:wrap;gap:8px;margin-top:16px}.chip{border:1px solid #a0b4da2b;background:#090e194d;color:#c6d2e7;border-radius:8px;padding:7px 10px;font-size:10px;font-weight:700}
.section{font-size:17px;font-weight:800;margin:27px 0 12px;letter-spacing:-.4px}.section small{font-size:10px;letter-spacing:1.4px;color:#8194b5;margin-left:8px}
.metric{border:1px solid #9bb1d326;border-radius:15px;padding:15px;background:linear-gradient(145deg,#131e30,#0d1421);min-height:94px;animation:rise .45s ease both}.metric-label{color:#8194b2;font-size:10px;font-weight:800;letter-spacing:1.2px;text-transform:uppercase}.metric-value{font-size:25px;font-weight:800;margin-top:8px;color:#f4f7ff}.metric-note{color:#8194b2;font-size:10px;margin-top:3px}
.stTextArea textarea{background:#080e19!important;color:#d9e7ff!important;border:1px solid #7d99c73d!important;border-radius:13px!important;font-family:'DM Mono',monospace!important;font-size:13px!important;line-height:1.7!important}
.stButton>button,.stDownloadButton>button{border-radius:10px;border:1px solid #5eead440;background:linear-gradient(100deg,#5eead4,#7c9cff);color:#07121d;font-weight:800;transition:transform .18s,filter .18s}.stButton>button:hover,.stDownloadButton>button:hover{transform:translateY(-2px);filter:brightness(1.07);color:#07121d}
.stTabs [data-baseweb="tab"]{color:#90a2bd;font-weight:700}.stTabs [aria-selected="true"]{color:var(--mint)!important;border-bottom:2px solid var(--mint)!important}
@keyframes rise{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}@keyframes pulse{0%{box-shadow:0 0 0 0 #5eead488}70%{box-shadow:0 0 0 7px #5eead400}100%{box-shadow:0 0 0 0 #5eead400}}@keyframes orb{50%{transform:translate(-20px,18px)}}
@media(prefers-reduced-motion:reduce){*,*:before,*:after{animation-duration:.01ms!important;transition-duration:.01ms!important}}
</style>
""", unsafe_allow_html=True)

theme = st.sidebar.selectbox("Appearance", ["Dark", "Light"], index=0)
if theme == "Light":
    st.markdown("""<style>
    .stApp{background:#f3f6fb!important;color:#172033!important}
    [data-testid="stSidebar"]{background:#fff!important;border-right:1px solid #d9e2ef!important}
    .hero{background:linear-gradient(120deg,#fff,#eef2ff)!important;border-color:#d9e2ef!important}
    .hero h1,.section{color:#172033!important}.hero p{color:#53627a!important}
    .metric{background:#fff!important;border-color:#d9e2ef!important}.metric-value{color:#172033!important}
    .metric-label,.metric-note{color:#667895!important}.stTextArea textarea{background:#fff!important;color:#172033!important;border-color:#cbd7e7!important}
    </style>""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## ◈ CodeLens **AI**")
    st.caption("COMPILER STUDIO · LOCAL-FIRST")
    st.markdown("---")
    use_ollama = st.toggle("Use local Ollama", value=False)
    ollama_model = st.text_input("Ollama model", "llama3.2", disabled=not use_ollama)
    if st.button("↻ Retrain ML models", use_container_width=True):
        try:
            info = train_models()
            st.success(f"Trained on {info['rows']} examples.")
        except Exception as exc:
            st.error(str(exc))
    st.caption("Analysis pipeline")
    st.markdown("01 · Language checker\n\n02 · Lexer (C/C++)\n\n03 · Semantic heuristics (C/C++)\n\n04 · ML prediction\n\n05 · Repair validation")

st.markdown("""<div class="hero"><div class="eyebrow"><span class="dot"></span> Intelligent code diagnostics</div>
<h1>Write code.<br><span class="gradient">Understand the error.</span></h1>
<p>A local-first compiler workspace with multi-language syntax checks, ML-assisted error prediction, repair validation and a refined animated workspace.</p>
<div class="chips"><span class="chip">Python + C</span><span class="chip">ML predictions</span><span class="chip">Language-aware checks</span><span class="chip">Optional local LLM</span><span class="chip">Dark / Light theme</span></div></div>""", unsafe_allow_html=True)

st.markdown('<div class="section">Code workspace <small>/ 01 · INPUT</small></div>', unsafe_allow_html=True)
languages = ["C","C++","Python","Java","JavaScript","TypeScript","Go","Rust","C#","PHP","Ruby","JSON"]
language = st.selectbox("Programming language", languages, index=0)
samples = {
"C": '#include <stdio.h>\n\nint main(void) {\n    int value = 10\n    printf("%d\\n", value);\n    return 0;\n}\n',
"C++": '#include <iostream>\nint main() { std::cout << "Hello\\n"; return 0; }\n',
"Python": 'def greet(name):\n    print("Hello", name)\n\ngreet("world")\n',
"Java": 'public class Main {\n    public static void main(String[] args) {\n        System.out.println("Hello");\n    }\n}\n',
"JavaScript": 'function greet(name) {\n  console.log("Hello", name);\n}\ngreet("world");\n',
"TypeScript": 'const greet = (name: string): void => {\n  console.log(`Hello ${name}`);\n};\ngreet("world");\n',
"Go": 'package main\nimport "fmt"\nfunc main() { fmt.Println("Hello") }\n',
"Rust": 'fn main() {\n    println!("Hello");\n}\n',
"C#": 'using System;\nclass Program { static void Main() { Console.WriteLine("Hello"); } }\n',
"PHP": '<?php\necho "Hello";\n',
"Ruby": 'puts "Hello"\n',
"JSON": '{"name": "CodeLens", "active": true}\n',
}
left, right = st.columns([3.3,1.05], gap="large")
with right:
    st.markdown('<div class="section">Quick start <small>/ EXAMPLES</small></div>', unsafe_allow_html=True)
    st.caption("Choose a language and load its sample.")
    if st.button("Load valid sample", use_container_width=True):
        st.session_state["source_code"] = samples[language]
        st.session_state.pop("result", None)
        st.rerun()
    if st.button("Load syntax-error sample", use_container_width=True):
        error_samples = {
            "C": '#include <stdio.h>\nint main(void) {\n int x = 10\n printf("%d", x);\n return 0;\n}\n',
            "Python": 'def greet(name)\n    print("Hello", name)\n',
            "JavaScript": 'function greet( {\n console.log("Hello");\n',
            "JSON": '{"name": "CodeLens",}\n'
        }
        st.session_state["source_code"] = error_samples.get(language, samples[language])
        st.session_state.pop("result", None)
        st.rerun()
    st.markdown("---")
    st.caption("Language checks depend on installed toolchains. Python and JSON checks are built in.")
with left:
    source = st.text_area("Source code", value=st.session_state.get("source_code", samples[language]), key="source_code", height=320, label_visibility="collapsed")
    a, b, _ = st.columns([1.2,1,3])
    with a: analyze_clicked = st.button("✦ Analyze code", type="primary", use_container_width=True)
    with b:
        if st.button("Clear results", use_container_width=True):
            st.session_state.pop("result",None); st.rerun()

def connect_db():
    con = sqlite3.connect(DB)
    con.execute("CREATE TABLE IF NOT EXISTS analyses(id INTEGER PRIMARY KEY, created_at TEXT, language TEXT, source TEXT, issue_count INTEGER, result_json TEXT)")
    con.commit()
    return con

if analyze_clicked:
    if not source.strip():
        st.warning("Paste source code first.")
    else:
        with st.spinner(f"Checking {language} syntax and analyzing diagnostics..."):
            try:
                result = analyze_code(source, use_ollama, ollama_model, language=language)
                st.session_state["result"] = result
                st.session_state["analyzed_source"] = source
                con = connect_db()
                con.execute("INSERT INTO analyses(created_at,language,source,issue_count,result_json) VALUES(?,?,?,?,?)",
                            (datetime.now().isoformat(timespec="seconds"), language, source, len(result["issues"]), json.dumps(result, default=str)))
                con.commit(); con.close()
            except Exception as exc:
                st.error(f"Analysis failed: {exc}")

result = st.session_state.get("result")
if result:
    st.markdown('<div class="section">Analysis overview <small>/ 02 · RESULTS</small></div>', unsafe_allow_html=True)
    syntax = result["syntax"]
    metrics = st.columns(4)
    values = [("Tokens",len(result["tokens"]),"Lexical scan"),("Issues",len(result["issues"]),"Detected findings"),("Checker","READY" if syntax["available"] else "MISSING",language+" toolchain"),("Syntax","PASS" if syntax["available"] and syntax["ok"] else ("ISSUES" if syntax["available"] else "N/A"),"Syntax validation")]
    for col,(label,value,note) in zip(metrics,values):
        col.markdown(f'<div class="metric"><div class="metric-label">{escape(label)}</div><div class="metric-value">{escape(str(value))}</div><div class="metric-note">{escape(note)}</div></div>',unsafe_allow_html=True)
    st.markdown('<div class="section">Diagnostic console <small>/ 03 · FINDINGS</small></div>', unsafe_allow_html=True)
    st.code(syntax.get("raw_output","No output."), language="text")
    tabs = st.tabs(["✦ Explanations","⌘ Tokens","⤴ Repair workspace","◫ ML evaluation","◷ History"])
    with tabs[0]:
        if not result["predictions"]: st.success("No issues were reported by the available checks.")
        for i,item in enumerate(result["predictions"],1):
            d,p = item["diagnostic"],item["prediction"]
            with st.expander(f"Issue {i:02d} · Line {d.get('line','?')} · {d.get('message','Diagnostic')}", expanded=i==1):
                st.markdown(f"**Predicted category:** `{p['error_type']}` · confidence {p['error_confidence']:.0%}")
                st.markdown(f"**Repair class:** `{p['repair_type']}` · confidence {p['repair_confidence']:.0%}")
                st.write(item["explanation"])
                st.caption(f"Explanation source: {item['provider']}. Predictions are suggestions, not guarantees.")
                st.code(item["context"],language="text")
    with tabs[1]:
        st.dataframe(pd.DataFrame(result["tokens"]),use_container_width=True,hide_index=True) if result["tokens"] else st.info("Token details are currently enabled for C and C++.")
    with tabs[2]:
        candidates = result.get("candidates",[])
        if not candidates: st.info("Automatic patch candidates are currently limited to conservative C cases. Other languages still receive syntax checks and available ML explanations.")
        else:
            cand = st.selectbox("Repair candidate",[x["name"] for x in candidates])
            item = next(x for x in candidates if x["name"]==cand)
            st.write(item["note"])
            if item["validation"]["available"] and item["validation"]["ok"]: st.success("Candidate passed syntax validation. This does not prove logical correctness.")
            else: st.warning("Candidate requires review or could not pass validation.")
            st.code(item["diff"] or "No diff",language="diff")
            st.code(item["code"],language="c")
            ext = {"C":".c","C++":".cpp","Python":".py","Java":".java","JavaScript":".js","TypeScript":".ts","Go":".go","Rust":".rs","C#":".cs","PHP":".php","Ruby":".rb","JSON":".json"}.get(language,".txt")
            st.download_button("Download candidate",item["code"],file_name="codelens_candidate"+ext)
    with tabs[3]:
        st.caption("Starter dataset is small; metrics are exploratory and not evidence of production performance.")
        if st.button("Run held-out ML evaluation"):
            st.session_state["evaluation"] = evaluate_models()
        ev = st.session_state.get("evaluation")
        if ev:
            st.warning(ev["warning"])
            if ev.get("evaluated"):
                cols = st.columns(4)
                for col,label,key in zip(cols,["Accuracy","Precision","Recall","F1"],["accuracy","precision_weighted","recall_weighted","f1_weighted"]):
                    col.metric(label,f"{ev[key]:.1%}")
                st.dataframe(pd.DataFrame(ev["confusion_matrix"],index=ev["labels"],columns=ev["labels"]),use_container_width=True)
            else: st.error(ev.get("error","Evaluation unavailable"))
    with tabs[4]:
        con=connect_db()
        rows=con.execute("SELECT id,created_at,language,issue_count FROM analyses ORDER BY id DESC LIMIT 30").fetchall()
        con.close()
        st.dataframe(pd.DataFrame(rows,columns=["ID","Created at","Language","Issues"]),use_container_width=True,hide_index=True) if rows else st.info("No saved analyses yet.")
    payload={"application":"CodeLens AI — Compiler Studio","language":language,"generated_at":datetime.now().isoformat(),"source":st.session_state.get("analyzed_source",""),"syntax":syntax,"issues":result["issues"],"predictions":result["predictions"],"repair_candidates": result.get("candidates", [])}
    st.markdown('<div class="section">Export analysis <small>/ 04 · REPORT</small></div>',unsafe_allow_html=True)
    x,y,z=st.columns(3)
    with x: st.download_button("Download JSON",json.dumps(payload,indent=2,default=str),file_name="codelens_analysis.json",mime="application/json",use_container_width=True)
    with y: st.download_button("Download text report",f"CodeLens AI Analysis\nLanguage: {language}\nIssues: {len(result['issues'])}\n\n{syntax.get('raw_output','')}",file_name="codelens_analysis.txt",mime="text/plain",use_container_width=True)
    with z:
        html=f"<!doctype html><html><meta charset='utf-8'><title>CodeLens report</title><body><h1>CodeLens AI Analysis</h1><h2>{escape(language)}</h2><pre>{escape(json.dumps(payload,indent=2,default=str))}</pre></body></html>"
        st.download_button("Download HTML",html,file_name="codelens_analysis.html",mime="text/html",use_container_width=True)
st.caption("CodeLens AI · Local-first educational prototype · Review all repair suggestions before use.")
