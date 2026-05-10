# ---------------------------------------------------------
# Project: SentinelScan AI
# Author:  Shivam Ugale
# Date:    May 2026
# Version: 1.0.0
# License: MIT
# Description: Professional-grade URL Security Analyzer
# ---------------------------------------------------------

provider "oci" {
  tenancy_ocid     = var.tenancy_ocid
  user_ocid        = var.user_ocid
  fingerprint      = var.fingerprint
  private_key_path = var.private_key_path
  region           = var.region
}

# 1. Create the VCN
resource "oci_core_vcn" "sentinel_vcn" {
  cidr_block     = "10.0.0.0/16"
  compartment_id = var.compartment_id
  display_name   = "SentinelScan_VCN"
}

# 2. Create the Internet Gateway (The "Door" to the Internet)
resource "oci_core_internet_gateway" "sentinel_ig" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.sentinel_vcn.id
  display_name   = "SentinelScan_IG"
}

# 3. Create a Route Table (The "Map" for traffic)
resource "oci_core_route_table" "sentinel_rt" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.sentinel_vcn.id
  display_name   = "SentinelScan_RouteTable"

  route_rules {
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
    network_entity_id = oci_core_internet_gateway.sentinel_ig.id
  }
}

# 4. Create the Subnet (Now attached to the Route Table and Security List)
resource "oci_core_subnet" "sentinel_subnet" {
  cidr_block        = "10.0.1.0/24"
  compartment_id    = var.compartment_id
  vcn_id            = oci_core_vcn.sentinel_vcn.id
  display_name      = "SentinelScan_Subnet"
  route_table_id    = oci_core_route_table.sentinel_rt.id
  security_list_ids = [oci_core_security_list.sentinel_security_list.id]
}

# 5. The "Always Free" Compute Instance
resource "oci_core_instance" "sentinel_server" {
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
  compartment_id      = var.compartment_id
  shape               = "VM.Standard.E2.1.Micro"

  display_name = "SentinelScan_AI_Server"

  source_details {
    source_type = "image"
    source_id   = "ocid1.image.oc1.ap-mumbai-1.aaaaaaaaylvxte5i3gmdebb62qgqccwnysjaxso3axoblhjyfofpa4wcd6lq"
  }

  create_vnic_details {
    assign_public_ip = true
    subnet_id        = oci_core_subnet.sentinel_subnet.id
  }

  metadata = {
    ssh_authorized_keys = var.ssh_public_key
  }
}

data "oci_identity_availability_domains" "ads" {
  compartment_id = var.compartment_id
}

# 6. Security List (Firewall)
resource "oci_core_security_list" "sentinel_security_list" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.sentinel_vcn.id
  display_name   = "SentinelScan_Security_List"

  ingress_security_rules {
    protocol = "6" # TCP
    source   = "0.0.0.0/0"
    tcp_options {
      min = 22
      max = 22
    }
  }

  ingress_security_rules {
    protocol = "6"
    source   = "0.0.0.0/0"
    tcp_options {
      min = 5000
      max = 5000
    }
  }
  
  # Allow all outbound traffic (so the server can download updates/Python libs)
  egress_security_rules {
    protocol    = "all"
    destination = "0.0.0.0/0"
  }
}