import sys, io, json, datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import openpyxl

def to_date(v):
    if isinstance(v, datetime.datetime):
        return v.strftime('%Y-%m-%d')
    if isinstance(v, (int, float)):
        return (datetime.datetime(1899, 12, 30) + datetime.timedelta(days=int(v))).strftime('%Y-%m-%d')
    return None

wb = openpyxl.load_workbook('E:/workspace_monitor/docs/2026专项管理.xlsx', data_only=True)
ws = wb['项目里程碑']

cp = None
cg = None
result = {}
for row in ws.iter_rows(min_row=2, values_only=True):
    if row[0]: cp = row[0]
    if row[5]: cg = row[5]
    d = to_date(row[6])
    e = row[7]
    g = cg
    if not e and g:
        e = g
    if not e: continue
    if cp not in result: result[cp] = []
    result[cp].append((cg, d, str(e)[:200]))

f = open('E:/workspace_monitor/docs/milestones_data.py', 'w', encoding='utf-8')
f.write('MILESTONES_SEED = {\n')
for proj, items in result.items():
    f.write(f'    "{proj}": [\n')
    for g, d, e in items:
        f.write(f'        {{"group": {json.dumps(g, ensure_ascii=False)}, "date": {json.dumps(d)}, "event": {json.dumps(e, ensure_ascii=False)}}},\n')
    f.write('    ],\n')
f.write('}\n')
f.close()
print(f'Written {sum(len(v) for v in result.values())} milestones for {len(result)} projects')
