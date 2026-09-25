"""
Configure Evidence.dev for the current environment.

- Source queries: writes one thin `select * from <model>` file per dashboard
  model named in dashboard/tiles.yml (Evidence requires a source file per
  table) and removes source files for models that left the contract. Pages do
  the ordering (`order by` from tiles.yml) over these sources.
- Local (no MOTHERDUCK_TOKEN): connection.yaml points at the local DuckDB file
  (FUSION_DB or data/fusion_issues.duckdb), opened read-only by Evidence.
- CI/prod (MOTHERDUCK_TOKEN set): connection.yaml points at MotherDuck.

Always writes evidence.config.yaml with the correct basePath.
"""
import glob
import os

import yaml

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, '..', '..'))
_SOURCES_DIR = os.path.join(_HERE, 'sources', 'fusion')
_MANIFEST = yaml.safe_load(open(os.path.join(_HERE, '..', 'tiles.yml')))

MOTHERDUCK_TOKEN = os.environ.get('MOTHERDUCK_TOKEN')
EVIDENCE_BASE_PATH = os.environ.get('EVIDENCE_BASE_PATH', '/evidence/build')

os.makedirs(_SOURCES_DIR, exist_ok=True)

# -- one thin source query per contract model --
models = [_MANIFEST['meta']['model']] + [
    tile['model'] for section in _MANIFEST['sections'] for tile in section['tiles']
]
for model in models:
    with open(os.path.join(_SOURCES_DIR, f'{model}.sql'), 'w') as f:
        f.write(f'select * from {model}\n')
for path in glob.glob(os.path.join(_SOURCES_DIR, '*.sql')):
    if os.path.splitext(os.path.basename(path))[0] not in models:
        os.remove(path)
print(f"sources/fusion → {len(models)} source queries from tiles.yml")

# -- connection.yaml --
if MOTHERDUCK_TOKEN:
    filename = 'md:fusion_issues'
else:
    db_path = os.environ.get('FUSION_DB') or os.path.join(_REPO_ROOT, 'data', 'fusion_issues.duckdb')
    # The duckdb plugin joins filename onto the source directory, so it must be relative.
    filename = os.path.relpath(os.path.abspath(db_path), _SOURCES_DIR)
connection = {'name': 'fusion', 'type': 'duckdb', 'options': {'filename': filename}}
with open(os.path.join(_SOURCES_DIR, 'connection.yaml'), 'w') as f:
    yaml.dump(connection, f, default_flow_style=False)
print(f"connection.yaml → {filename}")

# -- evidence.config.yaml --
config = {
    'deployment': {'basePath': EVIDENCE_BASE_PATH},
    'plugins': {
        'components': {'@evidence-dev/core-components': {'overrides': []}},
        'datasources': {'@evidence-dev/duckdb': {'overrides': []}},
    },
}
with open(os.path.join(_HERE, 'evidence.config.yaml'), 'w') as f:
    yaml.dump(config, f, default_flow_style=False)
print(f"evidence.config.yaml → basePath={EVIDENCE_BASE_PATH}")
