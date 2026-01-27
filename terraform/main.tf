terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs
resource "google_project_service" "run_api" {
  service            = "run.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "artifact_registry" {
  service            = "artifactregistry.googleapis.com"
  disable_on_destroy = false
}

# Create Artifact Registry repository for Docker images
resource "google_artifact_registry_repository" "docker_repo" {
  location      = var.region
  repository_id = var.artifact_registry_name
  description   = "Docker repository for AEM Assets MCP Server"
  format        = "DOCKER"

  depends_on = [google_project_service.artifact_registry]
}

# Create Secret Manager secrets for sensitive environment variables
resource "google_secret_manager_secret" "aem_client_secret" {
  secret_id = "aem-client-secret"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "aem_client_secret" {
  secret      = google_secret_manager_secret.aem_client_secret.id
  secret_data = var.aem_client_secret
}

# Service account for Cloud Run
resource "google_service_account" "cloudrun_sa" {
  account_id   = "aem-mcp-server"
  display_name = "AEM MCP Server Service Account"
  description  = "Service account for AEM Assets MCP Server on Cloud Run"
}

# Grant Secret Manager access to service account
resource "google_secret_manager_secret_iam_member" "client_secret_access" {
  secret_id = google_secret_manager_secret.aem_client_secret.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloudrun_sa.email}"
}

# Cloud Run service
resource "google_cloud_run_v2_service" "aem_mcp_server" {
  name     = var.service_name
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.cloudrun_sa.email

    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${var.artifact_registry_name}/${var.image_name}:${var.image_tag}"

      env {
        name  = "AEM_BASE_URL"
        value = var.aem_base_url
      }

      env {
        name  = "AEM_CLIENT_ID"
        value = var.aem_client_id
      }

      env {
        name = "AEM_CLIENT_SECRET"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.aem_client_secret.secret_id
            version = "latest"
          }
        }
      }

      resources {
        limits = {
          cpu    = var.cpu_limit
          memory = var.memory_limit
        }
      }

      ports {
        container_port = 8080
      }
    }
  }

  depends_on = [
    google_project_service.run_api,
    google_artifact_registry_repository.docker_repo,
  ]
}

# Allow public access (adjust as needed for production)
resource "google_cloud_run_service_iam_member" "public_access" {
  location = google_cloud_run_v2_service.aem_mcp_server.location
  service  = google_cloud_run_v2_service.aem_mcp_server.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Outputs
output "service_url" {
  description = "URL of the deployed Cloud Run service"
  value       = google_cloud_run_v2_service.aem_mcp_server.uri
}

output "artifact_registry_url" {
  description = "URL of the Artifact Registry repository"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${var.artifact_registry_name}"
}

output "service_account_email" {
  description = "Email of the Cloud Run service account"
  value       = google_service_account.cloudrun_sa.email
}
