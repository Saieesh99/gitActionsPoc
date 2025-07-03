#!/bin/bash
set -e
ENV=$1
cd terraform

terraform workspace new "$ENV"
terraform init
terraform validate
terraform plan

# Optional apply
terraform apply -auto-approve
