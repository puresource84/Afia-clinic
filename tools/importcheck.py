import os,re,glob,sys
R=sys.argv[1] if len(sys.argv)>1 else '/home/claude/afia-src/modules'
mods={d for d in os.listdir(R) if os.path.isfile(os.path.join(R,d,'__manifest__.py'))}
def names_in(p):
    if not os.path.exists(p): return None
    s=open(p,encoding='utf-8',errors='ignore').read()
    n=set(re.findall(r'^\s*(?:class|def)\s+([A-Za-z_]\w*)',s,re.M))
    n|=set(re.findall(r'^([A-Z_][A-Z0-9_]*)\s*=',s,re.M))
    n|=set(re.findall(r'^([a-z_]\w*)\s*=',s,re.M))
    for imp in re.findall(r'import\s+([A-Za-z_][\w, ]*)',s): n|={x.strip() for x in imp.split(',')}
    return n
bad=[]
PAT=re.compile(r'from\s+(odoo\.addons\.([a-z0-9_]+)\.([a-z0-9_.]+)|\.([a-z0-9_]+))\s+import\s+\(?\s*([^)\n]+)')
for m in sorted(mods):
    for f in glob.glob(os.path.join(R,m,'**','*.py'),recursive=True):
        if '__pycache__' in f: continue
        s=open(f,encoding='utf-8',errors='ignore').read()
        for full,amod,apath,rel,imported in PAT.findall(s):
            if amod and amod not in mods: continue
            target=os.path.join(R,amod,*apath.split('.')) if amod else os.path.join(os.path.dirname(f),rel)
            tf=target+'.py'
            if not os.path.exists(tf):
                if os.path.isdir(target): continue
                bad.append((os.path.relpath(f,R),full,'FILE MISSING')); continue
            have=names_in(tf)
            for nm in [x.strip().split(' as ')[0] for x in imported.split(',') if x.strip()]:
                if not re.match(r'^[A-Za-z_]\w*$',nm): continue
                if have is not None and nm not in have:
                    where=[os.path.relpath(p,R) for p in glob.glob(os.path.join(R,amod or m,'**','*.py'),recursive=True)
                           if '__pycache__' not in p and (names_in(p) or set()) and nm in (names_in(p) or set())]
                    bad.append((os.path.relpath(f,R),f"{full} import {nm}",f"NOT FOUND in that file; defined in {where}"))
for b in bad: print(f"[BROKEN IMPORT] {b[0]}\n     {b[1]}\n     {b[2]}")
print("TOTAL:",len(bad) if bad else "0 - all intra-addon imports resolve")
