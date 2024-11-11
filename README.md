# K2BQ - Dataflow Kafka to BigQuery

## Overview

**K2BQ** is a dataflow pipeline designed to stream data from Kafka to Google BigQuery. The project provides a scalable and efficient solution for transferring large volumes of data from Kafka topics into BigQuery for real-time analytics. This project leverages Google Cloud’s managed Kafka service and Dataflow to enable seamless data integration, processing, and storage in BigQuery.

## Features

- **Kafka Integration**: Collect data from Kafka topics for real-time processing.
- **BigQuery Integration**: Directly stream the processed data into BigQuery for fast analytics.
- **Scalable Architecture**: Leverages Google Cloud's managed services for scaling based on demand.
- **Automated Data Pipeline**: Automates the data transfer process from Kafka to BigQuery with minimal intervention.

## Components

The pipeline consists of the following components:
1. **Google Cloud Managed Kafka Cluster**: Used to store and stream data through Kafka topics.
2. **Google Dataflow**: Used to process data from Kafka and load it into BigQuery.
3. **BigQuery**: The final destination where the processed data is stored for analysis.

## Installation

### Prerequisites

- Google Cloud Platform (GCP) account.
- Terraform installed on your local machine.
- Google Cloud SDK configured with the necessary permissions.
- Access to Google BigQuery and Kafka services.

### Setting Up the Project

1. **Clone the repository:**

   ```bash
   git clone https://github.com/Pirate-Emperor/K2BQ.git
   cd K2BQ
   ```

2. **Configure Terraform:**

   Ensure that you have your `main.tf`, `variable.tf`, and any other required Terraform files set up as mentioned in the following sections.

3. **Install required Terraform providers:**

   In the root directory, run the following command to initialize Terraform providers:

   ```bash
   terraform init
   ```

4. **Apply the Terraform configuration:**

   Run the following command to create the resources in your Google Cloud project:

   ```bash
   terraform apply
   ```

   This command will create the Kafka cluster, Kafka topics, and Dataflow pipeline. Review the changes and confirm the application when prompted.

## Terraform Configuration Files

### `main.tf`

This Terraform configuration sets up the Google Cloud resources required for the Kafka-to-BigQuery data pipeline.

```hcl
provider "google-beta" {
  project = data.google_project.project.project_id
  region  = "us-central1"
}

data "google_project" "project" {}

module "kafka_cluster" {
  source = "./module/df_resource"  # Update with the actual path to your module
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
```

### `variable.tf`

This file defines the necessary variables for the Kafka cluster configuration.

```hcl
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
```

## Dataflow Pipeline

The Dataflow pipeline reads data from the Kafka topic and writes it to BigQuery. This setup allows for continuous streaming of data for analysis and reporting.

### Key steps:
1. **Reading Data**: Data is consumed from the Kafka topic.
2. **Processing Data**: Data is processed and transformed as per the requirements (e.g., filtering, aggregation).
3. **Writing to BigQuery**: After processing, the data is written to BigQuery tables for querying and analysis.

## Conclusion

The **K2BQ** project simplifies the integration between Kafka and BigQuery, offering a robust solution for real-time data processing. With Terraform managing the infrastructure setup and Dataflow handling the pipeline, this solution provides scalability, performance, and ease of maintenance for your data streaming needs.

## License

This project is licensed under the Pirate-Emperor License. See the [LICENSE](LICENSE) file for details.

## Author

**Pirate-Emperor**

[![Twitter](https://skillicons.dev/icons?i=twitter)](https://twitter.com/PirateKingRahul)
[![Discord](https://skillicons.dev/icons?i=discord)](https://discord.com/users/1200728704981143634)
[![LinkedIn](https://skillicons.dev/icons?i=linkedin)](https://www.linkedin.com/in/piratekingrahul)

[![Reddit](https://img.shields.io/badge/Reddit-FF5700?style=for-the-badge&logo=reddit&logoColor=white)](https://www.reddit.com/u/PirateKingRahul)
[![Medium](https://img.shields.io/badge/Medium-42404E?style=for-the-badge&logo=medium&logoColor=white)](https://medium.com/@piratekingrahul)

- GitHub: [Pirate-Emperor](https://github.com/Pirate-Emperor)
- Reddit: [PirateKingRahul](https://www.reddit.com/u/PirateKingRahul/)
- Twitter: [PirateKingRahul](https://twitter.com/PirateKingRahul)
- Discord: [PirateKingRahul](https://discord.com/users/1200728704981143634)
- LinkedIn: [PirateKingRahul](https://www.linkedin.com/in/piratekingrahul)
- Skype: [Join Skype](https://join.skype.com/invite/yfjOJG3wv9Ki)
- Medium: [PirateKingRahul](https://medium.com/@piratekingrahul)

---