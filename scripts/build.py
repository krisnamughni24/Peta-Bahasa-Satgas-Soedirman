"""Build index.html from the language recap workbook.

Usage: python scripts/build.py <rekap.xlsx> <all_kabkota_ind.geojson> [form_responses.csv ...]

Each optional CSV is a Google Form export ("Form PRELIMINARY MAPPING KEMAMPUAN BAHASA DAERAH")
whose rows are appended to the workbook's Detail Bahasa rows.
Requires: pandas, openpyxl, shapely.
"""
import json,collections,re
import pandas as pd
from shapely.geometry import shape
import sys,os,base64
F=sys.argv[1] if len(sys.argv)>1 else 'rekap.xlsx'
GEO=sys.argv[2] if len(sys.argv)>2 else 'all_kabkota_ind.geojson'
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
g=json.load(open(GEO))
J=[f for f in g['features'] if f['properties']['province_id'] in ('31','32','33','34','35','36')]
PROV={'JAWA TIMUR':'Jawa Timur','JAWA TENGAH':'Jawa Tengah','JAWA BARAT':'Jawa Barat','BANTEN':'Banten','DKI JAKARTA':'DKI Jakarta','DAERAH ISTIMEWA YOGYAKARTA':'DI Yogyakarta'}
def norm(k): return k.strip().replace('Kota Administrasi ','Kota ').replace('Gunungkidul','Gunung Kidul').upper()
def L(b): return {'Bahasa Jawa':'Jawa','Jawa (krama inggil)':'Jawa','Jakarta':'Betawi','Melayu Bangka':'Melayu'}.get(b.strip(),b.strip())
def lv(s):
    if pd.isna(s): return 'k'
    t=str(s).lower().strip()
    if t.startswith('dasar'): return 'd'
    if t.startswith('menengah'): return 'm'
    if re.search(r'fasih|fluent|native|mahir|advance|expert|\bpro\b|sepik|ngoko; krama',t): return 'f'
    if re.search(r'aktif|menengah|cukup|intermediate',t): return 'm'
    if re.search(r'dasar|pasif|pemula|amatir',t): return 'd'
    return 'k'
def group(lang,basis):
    b=basis.lower()
    if lang=='Jawa':
        for k,v in [('gabungan','Mataraman'),('mataraman','Mataraman'),('arek','Arekan / Jawa Timuran'),('ngapak','Ngapak / Banyumasan'),('pesisir','Pesisiran / Semarangan'),('pekalongan','Pekalongan'),('kedu','Kedu'),('samin','Samin / Blora'),('umum','Jawa umum')]:
            if k in b: return v
    if lang=='Sunda':
        if 'bogor' in b: return 'Sunda Bogor'
        if 'wetan' in b: return 'Sunda Wetan'
        return 'Sunda Priangan'
    return lang
d=pd.read_excel(F,'Detail Bahasa',dtype={'No. Helm':str})
# Form option -> (language, dialect key in Referensi Wilayah Bahasa)
FORM_DIALECT={
    'jawa mataraman':('Jawa','Mataraman'),'jawa arekan':('Jawa','Arekan'),'jawa pesisiran':('Jawa','Pesisir'),
    'jawa banyumasan':('Jawa','Ngapak'),'jawa cirebonan':('Cirebon',''),'sunda priangan':('Sunda','Priangan'),
    'sunda cirebon':('Sunda',''),'sunda banten':('Sunda',''),'betawi':('Betawi',''),'osing banyuwangi':('Osing','Osing (Banyuwangi)')}
FORM_LEVEL={'fasih':'Fasih','aktif':'Menengah','dasar':'Dasar','pasif':'Dasar'}  # passive understanding counts as Dasar
def load_form(path):
    """Turn one form export into Detail Bahasa-like rows (one per language/dialect)."""
    c=pd.read_csv(path,dtype=str)
    rows=[]
    for _,x in c.iterrows():
        helm=str(x.iloc[1]).strip().zfill(3)
        lvl=FORM_LEVEL.get(str(x.iloc[10]).split(':')[0].strip().lower())
        if not lvl: continue  # "Tidak bisa sama sekali": Indonesian only
        chosen={'Jawa' if 'jawa'==t.strip().lower() else 'Sunda' if t.strip().lower()=='sunda' else 'Osing' if t.strip().lower().startswith('osing') else None for t in str(x.iloc[8]).split(';')}-{None}
        got=set()
        for t in str(x.iloc[9]).split(';'):
            t=t.strip().lower()
            for key,(lang,dia) in FORM_DIALECT.items():
                if t.startswith(key):
                    rows.append({'No. Helm':helm,'Bahasa':lang,'Dialek/Subbahasa':dia or None,'Tingkat Kemahiran':lvl})
                    got.add('Jawa' if lang=='Cirebon' else lang)
        for lang in chosen-got:  # language ticked without a dialect -> general entry
            rows.append({'No. Helm':helm,'Bahasa':lang,'Dialek/Subbahasa':None,'Tingkat Kemahiran':lvl})
    return pd.DataFrame(rows),set(c.iloc[:,1].str.strip().str.zfill(3))
FORM_HELMS=set()
for fp in sys.argv[3:]:
    fr,hs=load_form(fp); FORM_HELMS|=hs
    d=pd.concat([d,fr],ignore_index=True)
w=pd.read_excel(F,'Referensi Wilayah Bahasa'); w.columns=['b','dia','prov','kab','basis']
REF={(r.b,'' if pd.isna(r.dia) else r.dia):('' if pd.isna(r.kab) else r.kab, '' if pd.isna(r.basis) else r.basis) for r in w.itertuples()}
def ref(lang,dia):
    for key in [(lang,dia),(lang,'')]:
        if key in REF: return REF[key]
    t=dia.lower()
    if L(lang)=='Jawa':
        if re.search(r'surabaya|timuran',t): return REF[('Jawa','Suroboyoan')]
        if re.search(r'mata?ra?man|matraman|solo|jogja|yogya',t): return REF[('Jawa','Mataraman')]
        return REF[('Jawa','')]
    return ('','')
SPLIT={('Jawa; Sunda','Jawa Mataraman; Sunda Priangan'):{'Jawa':'Mataraman','Sunda':'Priangan'},('Jawa; Sunda','Mataraman; Loma/Lemes'):{'Jawa':'Mataraman','Sunda':''}}
geo={norm(f['properties']['alt_name']):f for f in J}
rank={'f':3,'m':2,'d':1,'k':0}
LA=collections.defaultdict(lambda: collections.defaultdict(dict))  # kab->lang->helm->lev
GA=collections.defaultdict(lambda: collections.defaultdict(dict))  # kab->group->helm->lev
off=collections.defaultdict(set); gl={}
def put(D,k,key,h,lev):
    c=D[k][key].get(h)
    if c is None or rank[lev]>rank[c]: D[k][key][h]=lev
for _,r in d.iterrows():
    raw=[x.strip() for x in str(r['Bahasa']).split(';')]
    dia='' if pd.isna(r['Dialek/Subbahasa']) else r['Dialek/Subbahasa']
    lev=lv(r['Tingkat Kemahiran']); h=r['No. Helm']
    for rl in raw:
        lang=L(rl)
        if lang=='Indonesia': continue
        dd=SPLIT[(r['Bahasa'],dia)][rl] if (r['Bahasa'],dia) in SPLIT else (dia if len(raw)==1 else '')
        kabs,basis=ref(rl,dd)
        if not kabs: kabs,basis=ref(lang,dd)
        if (r['Bahasa'],dia) in SPLIT and rl=='Sunda': kabs,basis=REF[('Sunda','')]
        jk=[norm(k) for k in kabs.split(';') if k.strip() and norm(k) in geo]
        if not jk: off[lang].add(h); continue
        gp=group(lang,basis); gl[gp]=lang
        for k in jk: put(LA,k,lang,h,lev); put(GA,k,gp,h,lev)
def pack(D):
    o={}
    for key,hs in D.items():
        c=collections.Counter(hs.values()); o[key]=[len(hs),c['f'],c['m'],c['d'],c['k']]
    return o
out=[]
for k,f in geo.items():
    geom=shape(f['geometry']).simplify(0.006,preserve_topology=True)
    polys=[geom] if geom.geom_type=='Polygon' else list(geom.geoms)
    P=[]
    for p in polys:
        if p.area<2e-4 and len(polys)>1: continue
        P.append([[[round(x,3),round(y,3)] for x,y in p.exterior.coords]]+[[[round(x,3),round(y,3)] for x,y in i.coords] for i in p.interiors])
    best={}
    for lang,hs in LA[k].items():
        for h,l in hs.items():
            if h not in best or rank[l]>rank[best[h]]: best[h]=l
    out.append({'n':f['properties']['alt_name'].title().replace('Kabupaten ','Kab. '),'p':PROV[f['properties']['prov_name']],
      't':len(best),'f':sum(1 for v in best.values() if v=='f'),'l':pack(LA[k]),'d':pack(GA[k]),'g':P})
data={'regions':out,'off':{l:len(h) for l,h in off.items()},'gl':gl}
json.dump(data,open(os.path.join(ROOT,'src','data.json'),'w'),separators=(',',':'))
m=pd.read_excel(F,'Master Anggota')
reg=set()
for _,r in d.iterrows():
    ls=[L(x) for x in str(r['Bahasa']).split(';')]
    if any(l not in ('Indonesia','Arab','Mandarin','Hokkien') for l in ls): reg.add(r['No. Helm'])
k={'serdik':len(set(m['No. Helm'].astype(str).str.zfill(3))|FORM_HELMS),'reg':len(reg)}
tpl=open(os.path.join(ROOT,'src','template.html')).read()
logo='data:image/png;base64,'+base64.b64encode(open(os.path.join(ROOT,'assets','logo-p3mdi.png'),'rb').read()).decode()
data['k']=k
open(os.path.join(ROOT,'index.html'),'w').write(tpl.replace('__DATA__',json.dumps(data,separators=(',',':'))).replace('__LOGO__',logo))
print('built index.html',k)
print(gl); print({l:len(h) for l,h in off.items()})
