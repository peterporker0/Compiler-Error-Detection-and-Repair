import re, shutil, subprocess, tempfile
from pathlib import Path
DIAG=re.compile(r"(?P<file>[^:\n]+):(?P<line>\d+):(?:(?P<col>\d+):)?\s*(?P<level>fatal error|error|warning|note):\s*(?P<msg>.*)")
def check_syntax(source,timeout=8):
 gcc=shutil.which("gcc")
 if not gcc: return {"available":False,"ok":False,"diagnostics":[],"raw_output":"GCC not found on PATH."}
 with tempfile.TemporaryDirectory(prefix="a25_") as tmp:
  f=Path(tmp)/"input.c"; f.write_text(source,encoding="utf-8")
  try:
   p=subprocess.run([gcc,"-std=c11","-Wall","-Wextra","-fsyntax-only",str(f)],capture_output=True,text=True,timeout=timeout,cwd=tmp,shell=False)
   raw=(p.stderr or "")+(p.stdout or ""); ds=[]
   for line in raw.splitlines():
    m=DIAG.search(line)
    if m: ds.append({"line":int(m.group("line")),"column":int(m.group("col") or 0),"level":m.group("level"),"message":m.group("msg").strip(),"category":"Syntax" if "error" in m.group("level") else "Compiler warning"})
   return {"available":True,"ok":p.returncode==0,"diagnostics":ds,"raw_output":raw.strip() or "No compiler diagnostics."}
  except subprocess.TimeoutExpired: return {"available":True,"ok":False,"diagnostics":[],"raw_output":"GCC syntax check timed out."}
