#!/usr/bin/env bash
set -euo pipefail
# Run from the repository root with kubectl and Helm connected to the cloud K3s.
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add argo https://argoproj.github.io/argo-helm
helm repo add jetstack https://charts.jetstack.io
helm repo update
helm upgrade --install cert-manager jetstack/cert-manager --namespace cert-manager --create-namespace --set crds.enabled=true --wait --timeout 10m
kubectl apply -f deploy/platform/issuer.yaml
helm upgrade --install monitoring prometheus-community/kube-prometheus-stack --namespace monitoring --create-namespace -f deploy/monitoring/values.yaml --wait --timeout 15m
kubectl apply -f deploy/monitoring/service-monitor.yaml
kubectl apply -f deploy/monitoring/dashboard.yaml
helm upgrade --install argocd argo/argo-cd --namespace argocd --create-namespace -f deploy/argocd/notifications-values.yaml --wait --timeout 10m
kubectl apply -f deploy/platform/sonarqube.yaml
echo 'Platform installed. Configure SonarQube quality gate and deploy/argocd/application.yaml next.'
