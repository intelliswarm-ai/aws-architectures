variable "name_prefix" {
  type = string
}

variable "table_name" {
  type = string
}

variable "hash_key" {
  type = string
}

variable "range_key" {
  type    = string
  default = null
}

variable "billing_mode" {
  type    = string
  default = "PAY_PER_REQUEST"
}

variable "enable_ttl" {
  type    = bool
  default = false
}

variable "ttl_attribute" {
  type    = string
  default = "ttl"
}

variable "enable_pitr" {
  type    = bool
  default = false
}

variable "kms_key_arn" {
  type    = string
  default = null
}

variable "global_secondary_indexes" {
  type = list(object({
    name      = string
    hash_key  = string
    range_key = optional(string)
  }))
  default = []
}

variable "tags" {
  type    = map(string)
  default = {}
}
