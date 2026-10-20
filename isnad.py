# -*- coding: utf-8 -*-
# فصل الإسناد (سلسلة الرواة) عن متن الحديث — قواعد نصية، وليست فهمًا للمعنى.
# split_isnad(text) -> (isnad, matn)
import re

def nz(t):
    t = re.sub(r'[\u064B-\u0652\u0670\u0640\u200f\u200e]', '', t)
    t = t.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا').replace('ى', 'ي')
    return t.strip('،.:؛«»()[]{}"\'').strip()

CHAIN_VERBS = {'حدثنا', 'حدثني', 'اخبرنا', 'اخبرني', 'انبانا', 'انباني', 'سمعت?'}
CHAIN_VERBS.discard('سمعت?')
# كلمات تبدأ المتن
STARTERS = {'قال', 'قالت', 'يقول', 'ان', 'انه', 'انها', 'كان', 'كانت', 'سمعت', 'سمعنا',
            'رايت', 'كنا', 'كنت', 'سئل', 'سالت', 'سال', 'اتي', 'جاء', 'جاءت', 'نهي',
            'امر', 'قام', 'خرج', 'دخل', 'صليت', 'صلينا', 'اتيت', 'شهدت', 'ان'}
STRONG = {'قال', 'قالت', 'ان', 'انه', 'انها', 'سمعت', 'كان', 'كانت', 'كنا', 'كنت', 'رايت', 'يقول'}
SALAM = ['صلي', 'الله', 'عليه', 'وسلم']


def _strip_w(t):
    t = nz(t)
    if len(t) > 3 and t[0] in 'وف' and t[1:] in CHAIN_VERBS:
        return t[1:]
    return t


def _is_chain_start(nt):
    if not nt:
        return False
    first = _strip_w(nt[0])
    if first in CHAIN_VERBS or first == 'ح':
        return True
    if first == 'قال' and len(nt) > 1 and _strip_w(nt[1]) in CHAIN_VERBS:
        return True
    if first in ('عن',) :
        return True
    return False


def split_isnad(text):
    r = _split(text)
    return r


def _post(toks, nt, k):
    # تكرار "سمعت فلانًا يقول، سمعت فلانًا يقول" كله من السند
    n = len(toks)
    while k < n and nt[k] == 'سمعت':
        c = None
        for q in range(k, min(n, k + 9)):
            if toks[q].endswith('،'):
                c = q; break
        if c is not None and c + 1 < n and nt[c + 1] == 'سمعت':
            k = c + 1
        else:
            break
    return k


FALLBACK = {'بهذا', 'بمثله', 'بنحوه', 'نحوه', 'مثله', 'بمعناه', 'بمثل', 'بنحو', 'نحو', 'مثل'}


def _split(text):
    toks = text.split(' ')
    nt = [nz(t) for t in toks]
    dash = [0] * (len(toks) + 1)
    for i, t in enumerate(toks):
        dash[i + 1] = dash[i] ^ (1 if t == '-' else 0)
    if not _is_chain_start(nt):
        return '', text
    n = len(toks)
    # حدود المقاطع بحسب الفاصلة العربية
    segs = []
    s = 0
    for i, t in enumerate(toks):
        if t.endswith('،') or t.endswith('،.') :
            segs.append((s, i + 1)); s = i + 1
    if s < n:
        segs.append((s, n))

    for si, (a, b) in enumerate(segs):
        seg = nt[a:b]
        if not seg:
            continue
        f = _strip_w(seg[0])
        # مقطع يبدأ بفعل بدء المتن (بعد الفاصلة) => هنا يبدأ المتن
        if si > 0 and f in STRONG and not dash[a] and not (f == 'قال' and len(seg) > 1 and _strip_w(seg[1]) in CHAIN_VERBS):
            k = a
            # "قال قال رسول الله" / "قال سمعت" => "قال" الأولى للإسناد
            if f in ('قال', 'قالت') and len(seg) > 1 and seg[1] in ('قال', 'سمعت', 'يقول'):
                k = a + 1
            k = _post(toks, nt, k)
            return ' '.join(toks[:k]).strip(), ' '.join(toks[k:]).strip()
        # مقطع طويل أو فيه اقتباس أو صلى الله عليه وسلم => يحتمل أن فيه بداية المتن
        j = a
        while j < b:
            w = _strip_w(nt[j])
            # نهاية "عن النبي صلى الله عليه وسلم" => الإسناد ينتهي هنا
            if w == 'صلي' and nt[j:j + 4] == SALAM and j > a and nt[j - 1] in ('النبي', 'الله'):
                # نتأكد أن ما قبل النبي هو "عن"
                p = j - 1
                if nt[j - 1] == 'الله': p = j - 2  # رسول الله
                if nt[j - 1] == 'الله' and j - 2 >= a: p = j - 2
                before = nt[max(a, p - 1)] if p - 1 >= a else ''
                if before == 'عن' or nt[a] == 'عن' and nt[j - 1] == 'النبي' and nt[j - 2] == 'عن':
                    k = j + 4
                    if k <= n and k >= 1:
                        if k >= n:
                            return ' '.join(toks).strip(), ''
                        k = _post(toks, nt, k)
                        return ' '.join(toks[:k]).strip(), ' '.join(toks[k:]).strip()
            if j - a >= 2 and w in STRONG and not dash[j] and not (w == 'قال' and j + 1 < b and _strip_w(nt[j + 1]) in CHAIN_VERBS):
                k = j
                if w in ('قال', 'قالت') and j + 1 < n and nt[j + 1] in ('قال', 'سمعت', 'يقول'):
                    k = j + 1
                k = _post(toks, nt, k)
                return ' '.join(toks[:k]).strip(), ' '.join(toks[k:]).strip()
            if '«' in toks[j] and j - a >= 2 and not dash[j]:
                k = j
                k = _post(toks, nt, k)
                return ' '.join(toks[:k]).strip(), ' '.join(toks[k:]).strip()
            j += 1
        # مقطع طويل جدًا بلا أي علامة => غالبًا ليس إسنادًا
        if (b - a) > 14 and si > 0:
            return ' '.join(toks[:a]).strip(), ' '.join(toks[a:]).strip()
    for q in range(6, n):
        if nt[q] in FALLBACK:
            return ' '.join(toks[:q]).strip(), ' '.join(toks[q:]).strip()
    return '', text
