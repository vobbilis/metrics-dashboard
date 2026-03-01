#!/usr/bin/env python3.11
import subprocess
import os
import sys

# Change to backend directory
os.chdir('/Users/vobbilis/go/src/github.com/vobbilis/codegen/metrics-dashboard/backend')

print("=== VALIDATION TEST ===")

# Run the validation command from the task
validation_code = '''
from fastapi.testclient import TestClient
from main import app, store
store.clear()
c = TestClient(app)
c.post('/metrics', json={'name': 'cpu', 'value': 10.0})
c.post('/metrics', json={'name': 'cpu', 'value': 20.0})
r = c.get('/metrics/cpu/history')
assert r.status_code == 200, f'Expected 200, got {r.status_code}'
assert len(r.json()) == 2, f'Expected 2, got {len(r.json())}'
r2 = c.get('/metrics/cpu/history?limit=1')
assert len(r2.json()) == 1, f'Expected 1, got {len(r2.json())}'
r3 = c.get('/metrics/nonexistent/history')
assert r3.status_code == 404, f'Expected 404, got {r3.status_code}'
r4 = c.get('/metrics/summary')
assert r4.status_code == 200, f'Summary broken, got {r4.status_code}'
r5 = c.get('/metrics/cpu')
assert r5.status_code == 200, f'by_name broken, got {r5.status_code}'
store.clear()
print('ALL CHECKS PASSED')
'''

try:
    result = subprocess.run(['python3.11', '-c', validation_code], 
                          capture_output=True, text=True, cwd=os.getcwd())
    
    print("STDOUT:", result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    print("Return code:", result.returncode)
    
    if result.returncode == 0:
        print("\n✅ VALIDATION PASSED!")
    else:
        print("\n❌ VALIDATION FAILED!")
        sys.exit(1)
        
except Exception as e:
    print(f"Error running validation: {e}")
    sys.exit(1)

print("\n=== RUNNING NEW TESTS ===")
# Also run the new tests specifically
try:
    test_result = subprocess.run(['python3.11', '-m', 'pytest', 
                                 'tests/test_api.py::test_get_metric_history', 
                                 'tests/test_api.py::test_route_ordering_history_vs_by_name', 
                                 '-v'], 
                                capture_output=True, text=True)
    
    print("Test output:")
    print(test_result.stdout)
    if test_result.stderr:
        print("Test stderr:", test_result.stderr)
    
    if test_result.returncode == 0:
        print("\n✅ NEW TESTS PASSED!")
    else:
        print("\n❌ NEW TESTS FAILED!")
        sys.exit(1)
        
except Exception as e:
    print(f"Error running tests: {e}")
    sys.exit(1)

print("\n=== RUNNING LINT CHECK ===")
# Check code style
try:
    lint_result = subprocess.run(['ruff', 'check', '.'], 
                                capture_output=True, text=True)
    
    if lint_result.returncode == 0:
        print("✅ LINT PASSED!")
    else:
        print("❌ LINT FAILED!")
        print("Lint output:", lint_result.stdout)
        print("Lint stderr:", lint_result.stderr)
        sys.exit(1)
        
except Exception as e:
    print(f"Error running lint: {e}")
    sys.exit(1)

print("\n🎉 ALL VALIDATIONS COMPLETED SUCCESSFULLY!")