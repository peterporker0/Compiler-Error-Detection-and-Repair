import re
DECL=re.compile(r"\b(?:int|char|float|double|long|short|unsigned|signed|_Bool)\s+([A-Za-z_]\w*)\s*(?:=\s*([^;,]+))?\s*;")
ASSIGN=re.compile(r"^\s*([A-Za-z_]\w*)\s*=\s*([^;]+)\s*;\s*$")
def analyze_semantics(source):
 lines=[]
 for x in source.splitlines():
  x=re.sub(r"//.*","",x); x=re.sub(r'"(?:\\.|[^"\\])*"','""',x); lines.append(x)
 declared=set(); issues=[]
 for n,line in enumerate(lines,1):
  for m in DECL.finditer(line):
   name,init=m.group(1),m.group(2); declared.add(name)
   if init and '""' in init: issues.append({"line":n,"column":0,"message":f"Possible incompatible string initializer for '{name}'.","category":"Semantic","level":"warning"})
 for n,line in enumerate(lines,1):
  s=line.strip()
  if not s or s.startswith("#") or re.match(r"^(int|char|float|double|long|short|unsigned|signed|_Bool)\b",s): continue
  m=ASSIGN.match(line)
  if m and m.group(1) not in declared: issues.append({"line":n,"column":0,"message":f"Variable '{m.group(1)}' may be used before declaration.","category":"Semantic","level":"warning"})
 return issues
