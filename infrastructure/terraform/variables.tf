# Variables for Astra DB and Astra Streaming provisioning

variable "astra_token" {
  description = "DataStax Astra API Token"
  type        = string
  sensitive   = true
}

variable "tenant_id" {
  description = "Unique identifier for the tenant"
  type        = string
}

variable "tenant_name" {
  description = "Name of the tenant organization"
  type        = string
}

variable "cloud_provider" {
  description = "Cloud provider for Astra resources"
  type        = string
  default     = "gcp"
  validation {
    condition     = contains(["aws", "gcp", "azure"], var.cloud_provider)
    error_message = "Valid values for cloud_provider are: aws, gcp, azure."
  }
}

variable "region" {
  description = "Region for Astra resources"
  type        = string
  default     = "us-east1"
}

variable "keyspace" {
  description = "Keyspace name for Astra DB"
  type        = string
  default     = "voc_platform"
}

variable "db_tier" {
  description = "Tier/size for Astra DB"
  type        = string
  default     = "serverless"
}
