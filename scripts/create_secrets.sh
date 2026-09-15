#!/usr/bin/env bash
set -euo pipefail
# Run locally with kubectl connected to the intended cluster. No secrets are written to Git.
for ns in school quality monitoring argocd; do
  kubectl create namespace "$ns" --dry-run=client -o yaml | kubectl apply -f -
done
read -rsp 'School database password (letters/digits, >=20): ' DB_PASSWORD; echo
[[ "$DB_PASSWORD" =~ ^[a-zA-Z0-9]{20,}$ ]] || { echo 'Use at least 20 letters/digits for URL compatibility'; exit 1; }
read -rsp 'School administrator password (8-72 bytes): ' ADMIN_PASSWORD; echo
[[ ${#ADMIN_PASSWORD} -ge 8 && ${#ADMIN_PASSWORD} -le 72 ]] || { echo 'Invalid administrator password length'; exit 1; }
read -rsp 'Sonar database password: ' SONAR_PASSWORD; echo
read -rsp 'Grafana administrator password: ' GRAFANA_PASSWORD; echo
[[ -n "$SONAR_PASSWORD" && -n "$GRAFANA_PASSWORD" ]] || { echo 'Passwords cannot be empty'; exit 1; }
kubectl -n school create secret generic school-secrets \
  --from-literal=POSTGRES_DB=music_school --from-literal=POSTGRES_USER=music \
  --from-literal=POSTGRES_PASSWORD="$DB_PASSWORD" \
  --from-literal=DATABASE_URL="postgres://music:$DB_PASSWORD@db:5432/music_school?sslmode=disable" \
  --from-literal=ADMIN_LOGIN=admin --from-literal=ADMIN_PASSWORD="$ADMIN_PASSWORD" \
  --dry-run=client -o yaml | kubectl apply -f -
kubectl -n quality create secret generic sonar-secrets \
  --from-literal=POSTGRES_DB=sonar --from-literal=POSTGRES_USER=sonar --from-literal=POSTGRES_PASSWORD="$SONAR_PASSWORD" \
  --from-literal=SONAR_JDBC_USERNAME=sonar --from-literal=SONAR_JDBC_PASSWORD="$SONAR_PASSWORD" \
  --dry-run=client -o yaml | kubectl apply -f -
kubectl -n monitoring create secret generic grafana-admin \
  --from-literal=admin-user=admin --from-literal=admin-password="$GRAFANA_PASSWORD" \
  --dry-run=client -o yaml | kubectl apply -f -
read -rsp 'Telegram bot token (empty to configure later): ' TELEGRAM_TOKEN; echo
kubectl -n argocd create secret generic argocd-notifications-secret \
  --from-literal=telegram-token="$TELEGRAM_TOKEN" --dry-run=client -o yaml | kubectl apply -f -
unset DB_PASSWORD ADMIN_PASSWORD SONAR_PASSWORD GRAFANA_PASSWORD TELEGRAM_TOKEN
