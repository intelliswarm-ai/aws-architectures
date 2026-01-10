output "collection_id" {
  description = "OpenSearch collection ID"
  value       = aws_opensearchserverless_collection.vectors.id
}

output "collection_arn" {
  description = "OpenSearch collection ARN"
  value       = aws_opensearchserverless_collection.vectors.arn
}

output "collection_endpoint" {
  description = "OpenSearch collection endpoint"
  value       = aws_opensearchserverless_collection.vectors.collection_endpoint
}

output "dashboard_endpoint" {
  description = "OpenSearch dashboard endpoint"
  value       = aws_opensearchserverless_collection.vectors.dashboard_endpoint
}

output "collection_name" {
  description = "OpenSearch collection name"
  value       = aws_opensearchserverless_collection.vectors.name
}
