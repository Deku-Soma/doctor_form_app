import urllib.request, json

BASE = 'http://127.0.0.1:8765'
ok = True

def check(label, passed, detail=''):
    global ok
    s = 'PASS' if passed else 'FAIL'
    print(f'  {s}  {label}' + (f' - {detail}' if detail else ''))
    if not passed:
        ok = False

# /health
r = urllib.request.urlopen(BASE + '/health', timeout=5)
data = json.loads(r.read())
check('GET /health returns {status: ok}', data == {'status': 'ok'})

# /bootstrap
r = urllib.request.urlopen(BASE + '/bootstrap', timeout=5)
secret = json.loads(r.read()).get('secret', '')
check('GET /bootstrap 64-char secret', len(secret) == 64, f'len={len(secret)}')

def api(path, method='GET', body=None):
    req = urllib.request.Request(BASE + path, method=method,
        headers={'x-app-secret': secret, 'Content-Type': 'application/json'})
    if body:
        req.data = json.dumps(body).encode()
    return json.loads(urllib.request.urlopen(req, timeout=5).read())

# Login page (index.html)
html = urllib.request.urlopen(BASE + '/', timeout=5).read().decode()
check('index.html has login-form',         'login-form' in html)
check('index.html has HealthCorp360 brand','HealthCorp360' in html)
check('index.html has email input',        'type="email"' in html)
check('index.html has password input',     'type="password"' in html)
check('index.html has Sign in button',     'Sign in' in html)

# home.html
html2 = urllib.request.urlopen(BASE + '/home.html', timeout=5).read().decode()
check('home.html exists with forms-grid',   'forms-grid' in html2)
check('home.html FORMS array has 11 entries', html2.count("href:  '/forms/") == 11)
check('home.html has logout button',        'logout-btn' in html2)
check('home.html has context bar',          'context-bar' in html2)

# Static files
for path in ['/static/styles.css', '/static/app.js', '/static/signature.js']:
    try:
        content = urllib.request.urlopen(BASE + path, timeout=5).read()
        check(f'{path} served', len(content) > 200, f'{len(content)} bytes')
    except Exception as e:
        check(f'{path} served', False, str(e))

# Wrong secret -> 401
try:
    req = urllib.request.Request(BASE + '/companies',
        headers={'x-app-secret': 'bad_secret'})
    urllib.request.urlopen(req, timeout=5)
    check('Wrong secret -> 401', False, 'Expected 401 but got 200')
except urllib.error.HTTPError as e:
    check('Wrong secret -> 401', e.code == 401, f'HTTP {e.code}')
except Exception as e:
    check('Wrong secret -> 401', False, str(e))

# Bad login -> 401
try:
    api('/auth/login', method='POST', body={'email': 'no@x.com', 'password': 'wrong'})
    check('Bad login -> 401', False, 'Expected 401')
except urllib.error.HTTPError as e:
    check('Bad login -> 401', e.code == 401, f'HTTP {e.code}')
except Exception as e:
    check('Bad login -> 401', False, str(e))

# Autofill endpoint
try:
    data = api('/forms/hot_cold_exposure/autofill?company_id=x&employee_id=y')
    check('Autofill endpoint works', 'autofill' in data)
except Exception as e:
    check('Autofill endpoint works', False, str(e))

print()
print('Phase 7 gate:', 'PASSED' if ok else 'FAILED')
