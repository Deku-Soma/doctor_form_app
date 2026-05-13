"""Phase 8 gate — verify all 11 form HTML pages are served correctly."""
import urllib.request, json

BASE = 'http://127.0.0.1:8765'
ok = True

def check(label, passed, detail=''):
    global ok
    s = 'PASS' if passed else 'FAIL'
    print(f'  {s}  {label}' + (f' - {detail}' if detail else ''))
    if not passed:
        ok = False

# 1. Server alive
try:
    r = urllib.request.urlopen(BASE + '/health', timeout=5)
    check('Server alive', json.loads(r.read()) == {'status': 'ok'})
except Exception as e:
    check('Server alive', False, str(e))

# 2. All 11 form HTML pages served
FORMS = [
    'annexure3_cwb',
    'certificate_of_fitness',
    'complete_wellbeing',
    'workplace_drug_testing',
    'cwb_medical_referral',
    'heights_questionnaire',
    'hot_cold_exposure',
    'confined_spaces_questionnaire',
    'musculoskeletal_questionnaire',
    'psychology_questionnaire',
    'vitamin_b_consent',
]

for form_type in FORMS:
    try:
        html = urllib.request.urlopen(f'{BASE}/forms/{form_type}.html', timeout=5).read().decode()
        has_form    = '<form' in html
        has_apijs   = 'app.js' in html
        has_submit  = 'submitForm' in html
        has_approve = 'approve-btn' in html
        all_ok      = has_form and has_apijs and has_submit and has_approve
        check(f'forms/{form_type}.html', all_ok, f'form={has_form} apijs={has_apijs} submit={has_submit}')
    except Exception as e:
        check(f'forms/{form_type}.html', False, str(e))

# 3. Signature.js served
try:
    js = urllib.request.urlopen(BASE + '/static/signature.js', timeout=5).read().decode()
    check('signature.js served with initSignaturePad', 'initSignaturePad' in js)
except Exception as e:
    check('signature.js served', False, str(e))

# 4. home.html links to all 11 forms
try:
    html = urllib.request.urlopen(BASE + '/home.html', timeout=5).read().decode()
    missing = [f for f in FORMS if f"'/forms/{f}.html'" not in html]
    check("home.html links all 11 forms", len(missing) == 0, f'missing={missing}')
except Exception as e:
    check('home.html links', False, str(e))

print()
print('Phase 8 gate:', 'PASSED' if ok else 'FAILED')
