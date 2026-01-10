variable "project_prefix" {
  description = "Project name prefix"
  type        = string
}

variable "collection_name" {
  description = "OpenSearch collection name"
  type        = string
}

variable "vector_dimension" {
  description = "Vector dimension for embeddings"
  type        = number
  default     = 1024
}

variable "standby_replicas" {
  description = "Standby replicas setting (ENABLED or DISABLED)"
  type        = string
  default     = "DISABLED"
}

variable "tags" {
  description = "Resource tags"
  type        = map(string)
  default     = {}
}
