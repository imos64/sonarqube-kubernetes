variable "kubeconfig_path" {
  description = "Path to an existing kubeconfig; credentials are never generated or committed."
  type        = string
  default     = "~/.kube/config"
}

variable "kube_context" {
  description = "Explicit Kubernetes context to deploy into."
  type        = string
  validation {
    condition     = length(trimspace(var.kube_context)) > 0
    error_message = "An explicit kube_context is required."
  }
}

variable "namespace" {
  description = "Existing shared observability namespace, created outside this component's lifecycle."
  type        = string
  default     = "sonarqube"
}

variable "values_files" {
  description = "Ordered absolute paths to non-secret Helm overrides. Store credentials in existing Kubernetes Secrets."
  type        = list(string)
  default     = []
}
