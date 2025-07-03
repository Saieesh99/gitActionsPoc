#!/bin/bash
set -e

cd terraform

terraform workspace new dev
terraform init
terraform validate
terraform plan

# Optional apply
terraform apply -auto-approve
