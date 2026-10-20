# -*- coding: utf-8 -*-
# يصلح ملفات muwatta / abudawud / tirmidhi (الناتجة من build_books.py) ويفصل الإسناد عن المتن.
# الاستخدام:  python3 fix_books.py <مجلد الملفات الأصلية> <مجلد الإخراج>
# صيغة الصف الجديدة (٨ خانات ثابتة):
#   [رقم, معرّف الكتاب, المتن, تعليق الإمام, حكم الألباني, حكم ثانٍ, إنجليزي (لو العربي غير متوفر), الإسناد]
# الإصلاحات هنا آلية وآمنة فقط (أخطاء كتابية لا يختلف عليها)، وكل ما فيه احتمال خلاف
# يُترك كما هو ويُكتب في review.json لمراجعته يدويًا.
import json, re, sys, os
from isnad import split_isnad, nz

SRC = sys.argv[1] if len(sys.argv) > 1 else '.'
OUT = sys.argv[2] if len(sys.argv) > 2 else './out'
os.makedirs(OUT, exist_ok=True)

HAR = '\u064B\u064C\u064D\u064E\u064F\u0650\u0651\u0652'
DIAC = '[\u064B-\u0652\u0670]*'

def marker(words):
    return re.compile('(?:^|\\s)(?:و' + DIAC + ')?' + '\\s+'.join(''.join(re.escape(ch) + DIAC for ch in w) for w in words.split()))

BAB = marker('في الباب عن')

def collapse_marks(t):
    """حركة مكررة حرفيًا (َََ → َ). لا يمس اختلاف الحركات (يُسجَّل للمراجعة)."""
    return re.sub('([' + HAR + '\u0670])\\1+', r'\1', t)

def fix_text(t, key, stats):
    o = t
    t = collapse_marks(t)
    # رقم هامش عالق بعد نهاية الجملة (أبو داود)
    t = re.sub(r'([\.»])\d+$', r'\1', t)
    # أرقام هوامش بين أقواس داخل النص (الموطأ)
    t = re.sub(r'\s*\(\d{1,2}\)(?=\s)', '', t)
    # قوس آية مكسور: [الواقعة: [79 ← [الواقعة: 79]
    t = re.sub(r'\[([^\[\]:]+):\s*\[(\d+)(?!\])', r'[\1: \2]', t)
    return t

def strip_stray_open_quote(t):
    if t.count('«') > t.count('»'):
        n = re.sub(r'\s*«\s*(\.?)\s*$', r'\1', t)
        if n != t:
            return n, True
    return t, False

review = {k: {} for k in ('muwatta', 'abudawud', 'tirmidhi')}
def flag(book, kind, i):
    review[book].setdefault(kind, []).append(i)

report = {}
for key in ('muwatta', 'abudawud', 'tirmidhi'):
    d = json.load(open(f'{SRC}/{key}.json', encoding='utf-8'))
    rows = []
    st = dict(marks=0, stray_quote=0, babs_moved=0, isnad=0, no_isnad=0, footnote=0)
    for r in d['hadiths']:
        r = list(r) + [''] * (7 - len(r))
        i, ch, full, com, ga, gb, en = r[:7]
        o_full, o_com = full, com
        full = fix_text(full, key, st); com = fix_text(com, key, st)
        if full != o_full or com != o_com:
            if collapse_marks(o_full + o_com) != (o_full + o_com): st['marks'] += 1
            else: st['footnote'] += 1
        full, sq = strip_stray_open_quote(full)
        st['stray_quote'] += sq
        # الترمذي: "وفي الباب عن ..." كلام الإمام وليس من الحديث
        if key == 'tirmidhi' and full:
            for m in BAB.finditer(full):
                pre = full[:m.start()].rstrip()
                if pre and pre[-1] in '.»' and pre.count('«') == pre.count('»'):
                    moved = full[m.start():].strip()
                    full = pre
                    com = (moved + ' ' + com).strip() if com else moved
                    st['babs_moved'] += 1
                    if '«' in moved: flag(key, 'moved_contains_quote', i)
                    break
        isnad = ''
        if full:
            isnad, matn = split_isnad(full)
            if '«' in isnad:   # فصل مشكوك فيه => لا نفصل، ونتركه للمراجعة
                flag(key, 'isnad_not_separated_uncertain', i); isnad, matn = '', full
            if isnad: st['isnad'] += 1
            else: st['no_isnad'] += 1
            full = matn
            # علامات للمراجعة اليدوية
            if isnad and ('«' in isnad): flag(key, 'isnad_contains_quote', i)
            if isnad and len(matn.split()) < 3 and not re.search(r'(نحوه|مثله|بمعناه|الإسناد|بنحوه|بمثله)', nz(matn) and matn): flag(key, 'matn_very_short', i)
            if isnad and len(isnad) > 0.85 * (len(isnad) + len(matn)): flag(key, 'isnad_very_long', i)
        # مراجعة
        for txt in (full, com, isnad):
            if re.search('[\u064B-\u0650]{2}', txt):
                flag(key, 'mixed_adjacent_vowels', i); break
        if full.count('«') != full.count('»'): flag(key, 'unbalanced_quotes', i)
        if re.search(r'\s-\s*$', isnad + ' ' + full) or re.search(r'(\.\.\.|…)\s*$', full): flag(key, 'truncated_in_source', i)
        if re.search(r'[،:]\s*\.', full + isnad): flag(key, 'odd_punctuation', i)
        if not full and not isnad and en: flag(key, 'english_only_no_arabic', i)
        rows.append([i, ch, full, com, ga, gb, en, isnad])
    d['hadiths'] = rows
    json.dump(d, open(f'{OUT}/{key}.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    report[key] = st
    print(key, st, os.path.getsize(f'{OUT}/{key}.json'))

json.dump(review, open(f'{OUT}/review.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for k, v in review.items():
    print(k, {a: len(b) for a, b in v.items()})
