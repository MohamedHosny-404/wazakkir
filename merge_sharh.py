# دمج شرح كتاب في ملفه المنفصل  sharh-<key>.json   (النص نفسه في <key>.json لا يُلمس)
# الاستخدام:  python3 merge_sharh.py tirmidhi my_sharh.json
#   key = muwatta | abudawud | tirmidhi
#   my_sharh.json = { "6": "شرح الحديث رقم 6", "7": "..." }   (الرقم = رقم الحديث في الكتاب)
import json, sys, os
key, src = sys.argv[1], sys.argv[2]
out = f'sharh-{key}.json'
cur = json.load(open(out, encoding='utf-8')) if os.path.exists(out) else {}
add = json.load(open(src, encoding='utf-8'))
cur.update({str(k): v for k, v in add.items() if str(v).strip()})
json.dump(cur, open(out, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print(out, '— إجمالي الشروح:', len(cur))
