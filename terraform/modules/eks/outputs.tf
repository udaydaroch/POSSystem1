output "cluster_name"              { value = aws_eks_cluster.main.name }
output "cluster_endpoint"          { value = aws_eks_cluster.main.endpoint }
output "cluster_ca"                { value = aws_eks_cluster.main.certificate_authority[0].data }
output "cluster_security_group_id" { value = aws_security_group.cluster.id }
output "ecr_urls" {
  value = { for k, v in aws_ecr_repository.services : k => v.repository_url }
}
output "ecr_registry" {
  value = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${data.aws_region.current.name}.amazonaws.com"
}
