# Test Terraform file with vulnerable provider versions

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "2.0.0"  # VULNERABLE! CVE-2020-7955
    }
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "2.0.0"  # VULNERABLE! CVE-2020-13170
    }
    google = {
      source  = "hashicorp/google"
      version = "3.0.0"  # VULNERABLE! CVE-2021-22902
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

provider "azurerm" {
  features {}
}

provider "google" {
  project = "test-project"
  region  = "us-central1"
}

# Some sample resources to make it look realistic
resource "aws_s3_bucket" "test" {
  bucket = "test-bucket"
}

resource "azurerm_storage_account" "test" {
  name                = "testaccount"
  resource_group_name = "test"
}

resource "google_storage_bucket" "test" {
  name = "test-bucket"
}
