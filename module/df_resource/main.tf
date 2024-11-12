provider "google-beta" {
  project = data.google_project.project.project_id
  region  = var.region
}

data "google_project" "project" {}

resource "google_managed_kafka_cluster" "cluster" {
  cluster_id = var.cluster_id
  location   = var.region

  capacity_config {
    vcpu_count    = var.vcpu_count
    memory_bytes  = var.memory_bytes
  }

  gcp_config {
    access_config {
      network_configs {
        subnet = var.subnet
      }
    }
  }
}

resource "google_managed_kafka_topic" "example" {
  topic_id          = var.topic_id
  cluster           = google_managed_kafka_cluster.cluster.cluster_id
  location          = var.region
  partition_count   = var.partition_count
  replication_factor = var.replication_factor
  configs = {
    "cleanup.policy" = var.cleanup_policy
  }
}