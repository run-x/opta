{{/*
Expand the name of the chart.
*/}}
{{- define "k8s-service.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "k8s-service.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "k8s-service.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "k8s-service.labels" -}}
helm.sh/chart: {{ include "k8s-service.chart" . }}
{{ include "k8s-service.selectorLabels" . }}
{{ include "k8s-service.optaLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "k8s-service.selectorLabels" -}}
app.kubernetes.io/name: {{ include "k8s-service.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{- define "k8s-service.optaLabels" -}}
opta.dev/module-name: {{ .Values.moduleName }}
opta.dev/layer-name: {{ .Values.layerName }}
opta.dev/environment-name: {{ .Values.environmentName }}
{{- end }}

{{/*Namespace name*/}}
{{- define "k8s-service.namespaceName" -}}
{{- .Values.layerName }}
{{- end }}
{{/*Service name*/}}
{{- define "k8s-service.serviceName" -}}
{{- if eq (len .Values.persistentStorage) 0 }}
{{- .Values.moduleName }}
{{- else }}
{{- .Values.moduleName }}-headless
{{- end }}
{{- end }}
{{/*Service Account name*/}}
{{- define "k8s-service.serviceAccountName" -}}
{{- .Values.moduleName }}
{{- end }}

