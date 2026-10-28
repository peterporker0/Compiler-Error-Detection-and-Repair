import re, bisect
TOKEN_RE = re.compile(
 r"(?P<COMMENT>//[^\n]*|/\*[\s\S]*?\*/)|"
 r"(?P<STRING>\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*')|"
 r"(?P<PREPROCESSOR>^\s*#.*)|"
 r"(?P<NUMBER>\b(?:0[xX][0-9A-Fa-f]+|\d+(?:\.\d+)?)\b)|"
 r"(?P<IDENTIFIER>[A-Za-z_]\w*)|"
 r"(?P<OPERATOR>==|!=|<=|>=|\+\+|--|&&|\|\||->|[+\-*/%=<>!&|^~?:])|"
 r"(?P<DELIMITER>[(){}\[\],;.#])|(?P<WHITESPACE>\s+)|(?P<UNKNOWN>.)", re.MULTILINE)
KEYWORDS=set("auto break case char const continue default do double else enum extern float for goto if int long register return short signed sizeof static struct switch typedef union unsigned void volatile while _Bool".split())
def tokenize(source):
 tokens=[]; issues=[]; starts=[0]+[m.end() for m in re.finditer("\n",source)]
 for m in TOKEN_RE.finditer(source):
  kind, lexeme=m.lastgroup,m.group()
  if kind in {"COMMENT","PREPROCESSOR","WHITESPACE"}: continue
  ix=bisect.bisect_right(starts,m.start())-1
  line,col=ix+1,m.start()-starts[ix]+1
  if kind=="IDENTIFIER" and lexeme in KEYWORDS: kind="KEYWORD"
  if kind=="UNKNOWN": issues.append({"line":line,"column":col,"message":f"Unrecognized character: {lexeme!r}","category":"Lexical"})
  tokens.append({"type":kind,"lexeme":lexeme,"line":line,"column":col})
 return tokens,issues
