# يبني ملفات الكتب (muwatta / abudawud / tirmidhi) بصيغة موحدة تفصل: الحديث | تعليق الإمام | الأحكام
# المصادر: AhmedBaset/hadith-json (النص) + fawazahmed0/hadith-api (الأحكام) — كلاهما من sunnah.com
import json, re, sys, os
SRC = sys.argv[1] if len(sys.argv) > 1 else '/tmp/mw'
OUT = sys.argv[2] if len(sys.argv) > 2 else '.'
DIAC = '[\u064B-\u0652\u0670]*'
def marker(words):
    return re.compile('(?:^|\\s)(?:و)?' + '\\s+'.join(''.join(re.escape(ch)+DIAC for ch in w) for w in words.split()))
norm = lambda s: re.sub(r'[\u200f\u200e\s\.\u2026\u064b-\u0652\u0670\u0640"«»]+', '', s)

def clean(s):
    s = s.replace('\u200f', '').replace('\u200e', '')
    s = re.sub(r'\s+', ' ', s).strip()
    out = []; o = True
    for ch in s:
        if ch == '"': out.append('«' if o else '»'); o = not o
        else: out.append(ch)
    s = ''.join(out)
    s = re.sub(r'«\s+', '«', s); s = re.sub(r'\s+»', '»', s)
    return re.sub(r'\s+([\.،؛:؟])', r'\1', s)

BASE = {'Sahih':'صحيح','Hasan':'حسن','Daif':'ضعيف','Shadh':'شاذ','Munkar':'منكر','Mawdu':'موضوع','Mursal':'مرسل','Batil':'باطل','Maqtu':'مقطوع','Muquf':'موقوف','Mauquf':'موقوف'}
def grade_ar(g):
    if not g: return ''
    t = g.replace('Very Daif', 'VeryDaif').split()
    isn = any(x in ('Isnaad', 'Sanad') for x in t)
    base = []; extra = []
    for x in t:
        if x == 'VeryDaif': base.append('ضعيف جدًا')
        elif x in ('Sahih', 'Hasan', 'Daif', 'Shadh', 'Munkar', 'Mawdu', 'Mursal', 'Batil'): base.append(BASE[x])
        elif x in ('Maqtu', 'Muquf', 'Mauquf'): extra.append(BASE[x])
        elif x == 'Lighairihi': extra.append('لغيره')
        elif x == 'Mutawatir': extra.append('متواتر')
        elif x == 'Matn': extra.append('المتن')
    s = ' '.join(base)
    if isn and s: s = 'إسناده ' + s
    if extra: s = (s + ' ' + ' '.join(extra)).strip()
    return s

CFG = {
 'muwatta':  dict(src='malik.json',    fz=None,            m2=None,           title='موطأ الإمام مالك', riwaya='رواية يحيى بن يحيى الليثي — ترقيم محمد فؤاد عبد الباقي', g2=None),
 'abudawud': dict(src='abudawud.json', fz='f_abd.json',    m2='قال أبو داود', title='سنن أبي داود',     riwaya='سنن أبي داود السجستاني — ترقيم محمد فؤاد عبد الباقي', g2='Shuaib Al Arnaut'),
 'tirmidhi': dict(src='tirmidhi.json', fz='f_tir.json',    m2='قال أبو عيسى', title='جامع الترمذي',     riwaya='جامع الترمذي — ترقيم أحمد شاكر / فؤاد عبد الباقي', g2='Bashar Awad Maarouf'),
}
for key, c in CFG.items():
    m = json.load(open(f'{SRC}/{c["src"]}'))
    grades = {}
    if c['fz']:
        f = json.load(open(f'{SRC}/{c["fz"]}'))
        for h in f['hadiths']:
            if h['text'].strip():
                d = {g['name']: g['grade'] for g in h['grades']}
                grades[norm(h['text'])] = (grade_ar(d.get('Al-Albani')), grade_ar(d.get(c['g2'])))
    rx = marker(c['m2']) if c['m2'] else None
    rows = []; withc = withg = 0
    for h in m['hadiths']:
        full = clean(h['arabic']); com = ''
        if rx and full:
            mt = rx.search(full)
            if mt and full[:mt.start()].strip():
                com = full[mt.start():].strip(); full = full[:mt.start()].strip()
        ga, gb = grades.get(norm(h['arabic']), ('', ''))
        row = [h['idInBook'], h['chapterId'], full, com, ga, gb]
        if not full: row.append(re.sub(r'\s+', ' ', h['english']['text']).strip())
        while len(row) > 3 and row[-1] == '': row.pop()
        withc += bool(com); withg += bool(ga)
        rows.append(row)
    out = dict(title=c['title'], riwaya=c['riwaya'], chapters=[[x['id'], clean(x['arabic'])] for x in m['chapters']], hadiths=rows)
    json.dump(out, open(f'{OUT}/{key}.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print(key, len(rows), 'with-comment', withc, 'with-albani', withg, os.path.getsize(f'{OUT}/{key}.json'))
