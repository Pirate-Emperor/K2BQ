provider "google-beta" {
  project = data.google_project.project.project_id
  region  = "us-central1"
}

data "google_project" "project" {}

module "kafka_cluster" {
  source = "./module/df_resource" # Update with the actual path to your module
  cluster_id         = "dataops-kafka"
  region             = "us-central1"
  vcpu_count         = 4
  memory_bytes       = 4294967296
  subnet             = "projects/valid-verbena-437709-h5/regions/us-central1/subnetworks/default"
  topic_id           = "dataops-kafka-topic"
  partition_count    = 3
  replication_factor = 3
  cleanup_policy     = "compact"
}
