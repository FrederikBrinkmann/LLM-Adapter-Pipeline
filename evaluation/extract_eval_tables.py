import json
from collections import defaultdict
import statistics

with open('evaluation/results/evaluation_results.json') as f:
    data = json.load(f)
results = data['results']

# Per-model aggregation
models = defaultdict(lambda: {
    'count': 0, 'success': 0, 'failed': 0,
    'field_acc': [], 'critical_acc': [], 'schema_valid': 0,
    'mf_precision': [], 'mf_recall': [], 'mf_f1': [],
    'time_ms': []
})

for r in results:
    m = r['model_id']
    models[m]['count'] += 1
    if r['status'] == 'success':
        models[m]['success'] += 1
        models[m]['field_acc'].append(r['field_accuracy'])
        models[m]['critical_acc'].append(r['critical_field_accuracy'])
        if r['schema_valid']:
            models[m]['schema_valid'] += 1
        models[m]['mf_precision'].append(r['missing_fields_precision'])
        models[m]['mf_recall'].append(r['missing_fields_recall'])
        models[m]['mf_f1'].append(r['missing_fields_f1'])
        models[m]['time_ms'].append(r['time_ms'])
    else:
        models[m]['failed'] += 1

def avg(lst):
    return round(sum(lst)/len(lst), 2) if lst else 0

def pct(a, b):
    return round(a/b*100, 1) if b else 0

print("=== TABELLE 1: Gesamtübersicht pro Modell ===")
print()
header = f"{'Modell':<20} {'n':<5} {'Success':<9} {'Failed':<8} {'Schema-Valid':<14}"
print(header)
print("-" * len(header))
for model, d in sorted(models.items()):
    n = d['success']
    print(f"{model:<20} {d['count']:<5} {d['success']:<9} {d['failed']:<8} {d['schema_valid']}/{n} ({pct(d['schema_valid'],n)}%)")

print()
print("=== TABELLE 2: Feldgenauigkeit (Field Accuracy) ===")
print()
header2 = f"{'Modell':<20} {'Ø Field Acc':<14} {'Ø Critical Acc':<16} {'Min FA':<8} {'Max FA':<8} {'StdDev FA'}"
print(header2)
print("-" * len(header2))
for model, d in sorted(models.items()):
    fa = d['field_acc']
    ca = d['critical_acc']
    std = round(statistics.stdev(fa), 2) if len(fa) > 1 else 0
    print(f"{model:<20} {avg(fa):<14} {avg(ca):<16} {min(fa):<8} {max(fa):<8} {std}")

print()
print("=== TABELLE 3: Missing-Fields-Erkennung (Precision / Recall / F1) ===")
print()
header3 = f"{'Modell':<20} {'Ø Precision':<14} {'Ø Recall':<12} {'Ø F1':<8}"
print(header3)
print("-" * len(header3))
for model, d in sorted(models.items()):
    print(f"{model:<20} {avg(d['mf_precision']):<14} {avg(d['mf_recall']):<12} {avg(d['mf_f1']):<8}")

print()
print("=== TABELLE 4: Antwortzeiten (ms) ===")
print()
header4 = f"{'Modell':<20} {'Ø Zeit (ms)':<14} {'Ø Zeit (s)':<12} {'Min (ms)':<10} {'Max (ms)':<10} {'p50 (ms)'}"
print(header4)
print("-" * len(header4))
for model, d in sorted(models.items()):
    t = d['time_ms']
    p50 = round(sorted(t)[len(t)//2], 0)
    print(f"{model:<20} {avg(t):<14} {round(avg(t)/1000,2):<12} {round(min(t),0):<10} {round(max(t),0):<10} {p50}")

# Per scenario breakdown
print()
print("=== TABELLE 5: Field Accuracy pro Modell und E-Mail-Kategorie ===")
print("(alle 100 E-Mails, Ø Field Accuracy)")
print()

# Check if email_id contains category info
sample_ids = [r['email_id'] for r in results[:20]]
print("Beispiel Email-IDs:", sample_ids[:10])

# Try to load the dataset to get email metadata
try:
    with open('evaluation/data/synthetic_test_emails.json') as f:
        emails_raw = json.load(f)
    # Try to detect structure
    if isinstance(emails_raw, list):
        emails = {e.get('email_id', e.get('id', str(i))): e for i, e in enumerate(emails_raw)}
    elif isinstance(emails_raw, dict):
        emails = emails_raw
    print("\nEmail dataset keys (first item):", list(list(emails.values())[0].keys()) if emails else "empty")
except Exception as ex:
    print("Could not load email dataset:", ex)
    emails = {}

# Per scenario (scenario/mood/info_level from email dataset)
if emails:
    print()
    # Aggregate by scenario type
    scenario_model = defaultdict(lambda: defaultdict(list))
    for r in results:
        if r['status'] != 'success':
            continue
        email_meta = emails.get(r['email_id'], {})
        scenario = email_meta.get('scenario', email_meta.get('claim_type', 'unknown'))
        scenario_model[scenario][r['model_id']].append(r['field_accuracy'])

    all_models = sorted(models.keys())
    print(f"\n=== TABELLE 5a: Ø Field Accuracy nach Szenario ===")
    header5 = f"{'Szenario':<25}" + "".join(f"{m:<22}" for m in all_models)
    print(header5)
    print("-" * len(header5))
    for scenario in sorted(scenario_model.keys()):
        row = f"{scenario:<25}"
        for m in all_models:
            vals = scenario_model[scenario][m]
            row += f"{avg(vals):<22}"
        print(row)

    # By mood/tone
    mood_model = defaultdict(lambda: defaultdict(list))
    for r in results:
        if r['status'] != 'success':
            continue
        email_meta = emails.get(r['email_id'], {})
        mood = email_meta.get('mood', email_meta.get('tone', 'unknown'))
        mood_model[mood][r['model_id']].append(r['field_accuracy'])

    print(f"\n=== TABELLE 5b: Ø Field Accuracy nach Tonalität/Mood ===")
    header5b = f"{'Tonalität':<20}" + "".join(f"{m:<22}" for m in all_models)
    print(header5b)
    print("-" * len(header5b))
    for mood in sorted(mood_model.keys()):
        row = f"{mood:<20}"
        for m in all_models:
            vals = mood_model[mood][m]
            row += f"{avg(vals):<22}"
        print(row)

    # By info_level
    info_model = defaultdict(lambda: defaultdict(list))
    for r in results:
        if r['status'] != 'success':
            continue
        email_meta = emails.get(r['email_id'], {})
        info = email_meta.get('info_level', email_meta.get('completeness', 'unknown'))
        info_model[info][r['model_id']].append(r['field_accuracy'])

    print(f"\n=== TABELLE 5c: Ø Field Accuracy nach Informationsvollständigkeit ===")
    header5c = f"{'Info-Level':<20}" + "".join(f"{m:<22}" for m in all_models)
    print(header5c)
    print("-" * len(header5c))
    for info in sorted(info_model.keys()):
        row = f"{info:<20}"
        for m in all_models:
            vals = info_model[info][m]
            row += f"{avg(vals):<22}"
        print(row)

# Per-email detailed table (all 300 rows: email_id, model, field_acc, critical_acc, schema_valid, time_ms)
print()
print("=== TABELLE 6: Vollständige Ergebnistabelle (alle 300 Tests) ===")
print(f"{'Email-ID':<18} {'Modell':<22} {'Status':<10} {'FA':<8} {'CFA':<8} {'Schema':<8} {'MF-F1':<8} {'Zeit(ms)'}")
print("-" * 95)
for r in sorted(results, key=lambda x: (x['model_id'], x['email_id'])):
    fa = round(r.get('field_accuracy', 0), 1) if r['status'] == 'success' else '-'
    cfa = round(r.get('critical_field_accuracy', 0), 1) if r['status'] == 'success' else '-'
    sv = 'ja' if r.get('schema_valid') else 'nein'
    mff1 = round(r.get('missing_fields_f1', 0), 2) if r['status'] == 'success' else '-'
    t = round(r.get('time_ms', 0), 0)
    print(f"{r['email_id']:<18} {r['model_id']:<22} {r['status']:<10} {str(fa):<8} {str(cfa):<8} {sv:<8} {str(mff1):<8} {t}")
