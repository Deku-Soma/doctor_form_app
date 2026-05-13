import os

ok = True

def check(label, passed):
    global ok
    print(f"{'PASS' if passed else 'FAIL'} - {label}")
    if not passed: ok = False

check("run.bat exists", os.path.exists("run.bat"))

with open("requirements.txt") as f:
    reqs = f.read()
    check("PyQt5 removed from requirements.txt", "PyQt5" not in reqs)

check("main.py removed from root", not os.path.exists("main.py"))
check("pages/ removed from root", not os.path.exists("pages"))

check("archive/pyqt5/main.py exists", os.path.exists(os.path.join("archive", "pyqt5", "main.py")))
check("archive/pyqt5/pages exists", os.path.isdir(os.path.join("archive", "pyqt5", "pages")))

print("\nPhase 9 gate:", "PASSED" if ok else "FAILED")
