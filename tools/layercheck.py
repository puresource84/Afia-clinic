import ast,os,re,sys,glob
from collections import defaultdict
R=sys.argv[1] if len(sys.argv)>1 else '/home/claude/afia-src/modules'
mods=[d for d in sorted(os.listdir(R)) if os.path.isfile(os.path.join(R,d,'__manifest__.py'))]
man={m:ast.literal_eval(open(os.path.join(R,m,'__manifest__.py'),encoding='utf-8').read()) for m in mods}
LOCAL=set(mods)
# closure
def closure(m,seen=None):
    seen=seen or set()
    for d in man[m].get('depends',[]) or []:
        if d in LOCAL and d not in seen:
            seen.add(d); closure(d,seen)
    return seen
CL={m:closure(m) for m in mods}
# model -> defining modules ; method -> defining modules
model_def=defaultdict(set); meth_def=defaultdict(set)
for m in mods:
    for f in glob.glob(os.path.join(R,m,'**','*.py'),recursive=True):
        if '__pycache__' in f: continue
        s=open(f,encoding='utf-8',errors='ignore').read()
        for n in re.findall(r"_name\s*=\s*['\"]([a-z0-9._]+)['\"]",s): model_def[n].add(m)
        for n in re.findall(r"^\s*def\s+([a-zA-Z_][\w]*)",s,re.M): meth_def[n].add(m)
problems=[]
for m in mods:
    avail=CL[m]|{m}
    for f in glob.glob(os.path.join(R,m,'**','*.py'),recursive=True)+glob.glob(os.path.join(R,m,'**','*.xml'),recursive=True):
        if '__pycache__' in f: continue
        rel=os.path.relpath(f,R); s=open(f,encoding='utf-8',errors='ignore').read()
        s_nc=re.sub(r'<!--.*?-->','',s,flags=re.S)
        # models used
        used=set(re.findall(r"env\[['\"]([a-z0-9._]+)['\"]\]",s_nc))
        used|=set(re.findall(r"comodel_name\s*=\s*['\"]([a-z0-9._]+)['\"]",s_nc))
        used|=set(re.findall(r'<field name="model(?:_id)?">([a-z0-9._]+)</field>',s_nc))
        used|=set(re.findall(r'<field name="res_model">([a-z0-9._]+)</field>',s_nc))
        for mo in sorted(used):
            owners=model_def.get(mo)
            if owners and not (owners & avail):
                problems.append((m,rel,'MODEL',mo,sorted(owners)))
        # object-button methods used in xml
        if f.endswith('.xml'):
            for meth in sorted(set(re.findall(r'<button[^>]*name="([a-z_][\w]*)"[^>]*type="object"',s_nc))
                               |set(re.findall(r'type="object"[^>]*name="([a-z_][\w]*)"',s_nc))):
                owners=meth_def.get(meth)
                if owners and not (owners & avail):
                    problems.append((m,rel,'METHOD',meth,sorted(owners)))
if not problems: print("LAYERING OK - no module references a model or method defined outside its dependency closure")
for p in problems: print(f"[{p[2]}] {p[0]}  {p[1]}\n        uses '{p[3]}' which is defined in {p[4]} (not in its depends closure)")
print(f"\nTOTAL: {len(problems)}")
