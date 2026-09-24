{{/*
The pinned upstream chart also uses image.tag as a Kubernetes version label.
Keep tag@sha256 image references intact and use only their tag for display labels.
Helm loads parent named-template overrides after dependency templates.
*/}}
{{- define "sonarqube.workloadLabels" -}}
{{- include "sonarqube.labels" . }}
app.kubernetes.io/name: {{ .Release.Name }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: sonarqube
app.kubernetes.io/component: {{ include "sonarqube.fullname" . }}
app.kubernetes.io/version: {{ first (splitList "@" (tpl (include "image.tag" .) .)) | trunc 63 | trimSuffix "-" | quote }}
{{- end -}}
