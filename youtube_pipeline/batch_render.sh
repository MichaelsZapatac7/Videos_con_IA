#!/usr/bin/env bash
# Batch de los 10 videos de datos con el pipeline Remotion (animado, logo, música).
# Secuencial: termina uno y empieza el siguiente. Si ElevenLabs se queda sin
# cuota, produce_remotion falla y el batch PARA (marca BATCH_STOP) para avisar.
# Cada video terminado se commitea y pushea (el contenedor es efímero).
set -u
cd "$(dirname "$0")/.."
PLANS=youtube_pipeline/examples/plans

# pf :: topic :: out-base
LIST=(
"$PLANS/p01_architect_vs_engineer.json::Data Architect vs Data Engineer: quien disena, construye y salva el proyecto::Data_Architect_vs_Engineer"
"$PLANS/p02_lake_warehouse_lakehouse.json::Data Lake, Data Warehouse y Lakehouse explicados con un caso real::Lake_Warehouse_Lakehouse"
"$PLANS/p03_migracion_datos.json::Como disenar una migracion de datos profesional con pipelines y CICD::Migracion_de_Datos"
"$PLANS/p04_excel_al_lakehouse.json::De Excel al Lakehouse arquitectura moderna con GCP AWS y Spark::De_Excel_al_Lakehouse"
"$PLANS/p05_data_governance.json::Data Governance explicado sin humo owner steward custodian linaje::Data_Governance"
"$PLANS/p06_pipeline_de_verdad.json::Montando un pipeline de datos de verdad ingestion raw curated quality::Pipeline_de_Datos"
"$PLANS/p07_gcp_data_engineers.json::GCP para Data Engineers DAGs Jobs Buckets Composer y BigQuery::GCP_para_Data_Engineers"
"$PLANS/p08_aws_data_engineers.json::AWS para Data Engineers S3 Lambda EC2 Glue Athena y CloudWatch::AWS_para_Data_Engineers"
"$PLANS/p09_databricks.json::Databricks desde cero Lakehouse Delta Lake Jobs Clusters Unity Catalog::Databricks_desde_Cero"
"$PLANS/p10_powerbi_tableau_looker.json::Power BI vs Tableau vs Looker el mismo dataset::PowerBI_vs_Tableau_vs_Looker"
)

n=0
for row in "${LIST[@]}"; do
  n=$((n+1))
  pf="${row%%::*}"; rest="${row#*::}"; topic="${rest%%::*}"; ob="${rest##*::}"
  if [ -f "entregas/${ob}_COMPLETO_ANIMADO.mp4" ]; then
    echo "=== SKIP ${n}/10: ${ob} (ya existe) ==="; continue
  fi
  echo "=== START ${n}/10: ${ob} ==="
  if ! python3 -m youtube_pipeline.produce_remotion "$topic" --plan-file "$pf" --out-base "$ob"; then
    echo "BATCH_STOP en ${n}/10 (${ob}) — probablemente ElevenLabs sin cuota u otro error."
    exit 1
  fi
  # guardar la entrega (contenedor efímero)
  git add -f "entregas/${ob}_COMPLETO_ANIMADO.mp4" "entregas/${ob}_SHORT_ANIMADO.mp4" 2>/dev/null
  git commit -q -m "Video animado ${n}/10: ${ob} (completo + short)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_012LEKXEacTLKB6Pnaw1qTTR" 2>/dev/null
  for try in 1 2 3 4; do git push -u origin claude/loving-ride-1ower0 && break || sleep $((try*3)); done
  echo "=== DONE ${n}/10: ${ob} ==="
done
echo "BATCH_COMPLETE"
