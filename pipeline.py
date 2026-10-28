from lexer import tokenize
from syntax_checker import check_syntax
from semantic_checker import analyze_semantics
from repair_model import predict
from ai_explainer import explain
def ctx(source,line,radius=1):
 lines=source.splitlines(); start=max(0,line-1-radius); end=min(len(lines),line+radius)
 return "\n".join(f"{i+1}: {lines[i]}" for i in range(start,end))
def propose(source,diagnostics):
 lines=source.splitlines()
 for d in diagnostics:
  msg=d.get("message","").lower(); n=max(1,min(int(d.get("line",1) or 1),len(lines) or 1))
  if "expected" in msg and "before" in msg and (";" in msg or "semicolon" in msg) and n>1:
   i=n-2; s=lines[i].rstrip()
   if s and not s.endswith((";","{","}",":",",")) and not s.lstrip().startswith("#"):
    lines[i]=s+";"; return "\n".join(lines)+("\n" if source.endswith("\n") else ""),f"Inserted semicolon at line {i+1}."
 return None,"No conservative automatic repair matched."
def analyze_code(source, use_ollama=False, model="llama3.2", language="C"):
 tokens,lex=tokenize(source); syn=check_syntax(source); sem=analyze_semantics(source)
 issues=[dict(x,level="error") for x in lex]+[x for x in syn["diagnostics"] if x.get("level") in ("error","fatal error")]+sem
 preds=[]
 for d in issues:
  c=ctx(source,int(d.get("line",1) or 1)); p=predict(d.get("message",""),c)
  e,provider=explain(d.get("message",""),p["repair_type"],c,use_ollama,model,source)
  preds.append({"diagnostic":d,"context":c,"prediction":p,"explanation":e,"provider":provider})
 candidate,note=propose(source,syn["diagnostics"]); validation=check_syntax(candidate) if candidate is not None else None
 return {"tokens":tokens,"lexical":lex,"syntax":syn,"semantic":sem,"issues":issues,"predictions":preds,"candidate":candidate,"repair_note":note,"validation":validation}
