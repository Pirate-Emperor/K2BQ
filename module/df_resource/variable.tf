variable "cluster_id" {
  description = "The ID of the Kafka cluster."
  type        = string
  default     = "my-cluster"
}

variable "region" {
  description = "The region to deploy the Kafka cluster."
  type        = string
  default     = "us-central1"
}

variable "vcpu_count" {
  description = "Number of vCPUs for Kafka cluster capacity."
  type        = number
  default     = 3
}

variable "memory_bytes" {
  description = "Memory in bytes for Kafka cluster capacity."
  type        = number
  default     = 3221225472
}

variable "subnet" {
  description = "Subnetwork to attach the Kafka cluster to."
  type        = string
  default     = "projects/valid-verbena-437709-h5/regions/us-central1/subnetworks/default"
}

variable "topic_id" {
  description = "The ID of the Kafka topic."
  type        = string
  default     = "example-topic"
}

variable "partition_count" {
  description = "Number of partitions for the Kafka topic."
  type        = number
  default     = 2
}

variable "replication_factor" {
  description = "Replication factor for the Kafka topic."
  type        = number
  default     = 3
}

variable "cleanup_policy" {
  description = "Cleanup policy for the Kafka topic."
  type        = string
  default     = "compact"
}
