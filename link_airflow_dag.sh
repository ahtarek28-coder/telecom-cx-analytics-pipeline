#!/bin/bash
# (Re)links this project's Airflow DAG into AIRFLOW_HOME/dags/, pointing at
# wherever this project currently lives. Rerun this after moving the project
# folder -- a plain directory move leaves the old symlink dangling.
set -e
cd "$(dirname "$0")"

AIRFLOW_HOME="${AIRFLOW_HOME:-$HOME/airflow}"
mkdir -p "$AIRFLOW_HOME/dags"
rm -f "$AIRFLOW_HOME/dags/telecom_cx_pipeline_dag.py"
ln -s "$(pwd)/dags/telecom_cx_pipeline_dag.py" "$AIRFLOW_HOME/dags/"

echo "Linked $(pwd)/dags/telecom_cx_pipeline_dag.py -> $AIRFLOW_HOME/dags/"
