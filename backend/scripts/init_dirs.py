import os

dirs = [
    'prescripto/domain/prescription',
    'prescripto/domain/analysis',
    'prescripto/domain/medication',
    'prescripto/domain/safety',
    'prescripto/domain/review',
    'prescripto/domain/uncertainty',
    'prescripto/application/dtos',
    'prescripto/application/use_cases',
    'prescripto/api/v1/routers',
    'prescripto/api/v1/schemas',
    'prescripto/pipeline',
    'prescripto/ml',
    'prescripto/knowledge',
    'prescripto/storage',
    'prescripto/db/models',
    'prescripto/db/migrations/versions',
    'prescripto/worker',
    'prescripto/retention',
    'prescripto/auth',
    'prescripto/audit',
    'prescripto/config',
    'tests/unit',
    'tests/integration',
    'tests/contract',
    'docker',
    'scripts',
]

for d in dirs:
    os.makedirs(d, exist_ok=True)
    if not d.startswith(('docker', 'scripts', 'tests')):
        init_path = os.path.join(d, '__init__.py')
        if not os.path.exists(init_path):
            with open(init_path, 'w') as f:
                f.write('')

for t in ['tests', 'tests/unit', 'tests/integration', 'tests/contract']:
    init_path = os.path.join(t, '__init__.py')
    if not os.path.exists(init_path):
        with open(init_path, 'w') as f:
            f.write('')

with open('prescripto/__init__.py', 'w') as f:
    f.write('__version__ = "0.1.0"\n')

print("All directories and packages created successfully.")
