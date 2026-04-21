"""
Configure Evidence.dev for the current environment.

- Local (no MOTHERDUCK_TOKEN): writes connection.yaml pointing at local DuckDB +
  initialize.sql to set file_search_path so parquet-backed views resolve.
- CI/prod (MOTHERDUCK_TOKEN set): writes connection.yaml pointing at MotherDuck,
  which has real materialized tables — no initialize.sql needed.

Always writes evidence.config.yaml with the correct basePath.
"""
import os
import yaml

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, '..', '..'))
_SOURCES_DIR = os.path.join(_HERE, 'sources', 'fusion')

MOTHERDUCK_TOKEN = os.environ.get('MOTHERDUCK_TOKEN')
EVIDENCE_BASE_PATH = os.environ.get('EVIDENCE_BASE_PATH', '/evidence/build')

os.makedirs(_SOURCES_DIR, exist_ok=True)

# -- connection.yaml --
if MOTHERDUCK_TOKEN:
    connection = {'name': 'fusion', 'type': 'duckdb', 'options': {'filename': 'md:fusion_issues'}}
    init_sql_path = os.path.join(_SOURCES_DIR, 'initialize.sql')
    if os.path.exists(init_sql_path):
        os.remove(init_sql_path)
    print("connection.yaml → MotherDuck (md:fusion_issues)")
else:
    db_path = os.path.join(_REPO_ROOT, 'data', 'fusion_issues.duckdb')
    connection = {'name': 'fusion', 'type': 'duckdb', 'options': {'filename': db_path}}
    transform_path = os.path.join(_REPO_ROOT, 'transform')
    with open(os.path.join(_SOURCES_DIR, 'initialize.sql'), 'w') as f:
        f.write(f"SET file_search_path = '{transform_path}';\n")
    print(f"connection.yaml → local DuckDB | initialize.sql → file_search_path={transform_path}")

with open(os.path.join(_SOURCES_DIR, 'connection.yaml'), 'w') as f:
    yaml.dump(connection, f, default_flow_style=False)

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
