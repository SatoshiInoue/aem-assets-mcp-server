variable "project_id" {
  description = "Google Cloud Project ID"
  type        = string
}

variable "region" {
  description = "Google Cloud region"
  type        = string
  default     = "us-central1"
}

variable "service_name" {
  description = "Name of the Cloud Run service"
  type        = string
  default     = "aem-assets-mcp-server"
}

variable "artifact_registry_name" {
  description = "Name of the Artifact Registry repository"
  type        = string
  default     = "aem-mcp-images"
}

variable "image_name" {
  description = "Name of the Docker image"
  type        = string
  default     = "aem-mcp-server"
}

variable "image_tag" {
  description = "Tag of the Docker image"
  type        = string
  default     = "latest"
}

variable "min_instances" {
  description = "Minimum number of Cloud Run instances"
  type        = number
  default     = 0
}

variable "max_instances" {
  description = "Maximum number of Cloud Run instances"
  type        = number
  default     = 10
}

variable "cpu_limit" {
  description = "CPU limit for Cloud Run container"
  type        = string
  default     = "1"
}

variable "memory_limit" {
  description = "Memory limit for Cloud Run container"
  type        = string
  default     = "512Mi"
}

# AEM Configuration
variable "aem_base_url" {
  description = "AEM Assets API base URL (without trailing slash)"
  type        = string
}

variable "aem_client_id" {
  description = "AEM OAuth Client ID"
  type        = string
}

variable "aem_client_secret" {
  description = "AEM OAuth Client Secret (stored in Secret Manager)"
  type        = string
  sensitive   = true
}
