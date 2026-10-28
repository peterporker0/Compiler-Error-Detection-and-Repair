import requests
TEMPLATES={
"insert_semicolon":"A statement may be missing a semicolon. Check the statement immediately before the reported location.",
"insert_parenthesis":"A closing parenthesis may be missing. Match each opening parenthesis with a closing one.",
"declare_variable":"This name may be undeclared or misspelled. Declare it with the intended type before use.",
"review_type":"Check whether the assigned expression has a compatible type.",
"remove_invalid_character":"Remove or replace the character that is not valid in this context.",
"review_manually":"Review the nearby source and compiler diagnostic; no automatic patch is available."}
def explain(message,repair,context,use_ollama=False,model="llama3.2",code=""):
 if use_ollama:
  try:
   r=requests.post("http://localhost:11434/api/generate",json={"model":model,"prompt":f"Explain this C compiler diagnostic briefly. Do not claim fixes are validated. Diagnostic: {message}\nContext:\n{context}\nCode:\n{code}","stream":False},timeout=40)
   r.raise_for_status(); answer=r.json().get("response","").strip()
   if answer: return answer,"Local Ollama"
  except Exception: pass
 return TEMPLATES.get(repair,"Review the compiler diagnostic and nearby code. Treat any fix as a hypothesis."),"Local template"
