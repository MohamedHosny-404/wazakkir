# دمج شرح الموطأ داخل muwatta.json
# الاستخدام:  python3 merge_sharh.py sharh.json
# شكل sharh.json:  { "1": "نص شرح الأثر رقم 1", "2": "..." }   (الرقم = رقم الأثر برواية يحيى / عبد الباقي)
import json, sys
data = json.load(open('muwatta.json', encoding='utf-8'))
add = json.load(open(sys.argv[1], encoding='utf-8'))
data['sharh'].update({str(k): v for k, v in add.items() if str(v).strip()})
json.dump(data, open('muwatta.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('تم دمج', len(add), 'شرح — الإجمالي:', len(data['sharh']))
