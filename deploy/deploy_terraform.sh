#!/bin/bash
set -e
ENV=$1
cd terraform

terraform workspace new "$ENV"
terraform init
terraform validate
terraform plan -var="aws_region=$AWS_REGION"

# Optional apply
terraform apply -auto-approve
