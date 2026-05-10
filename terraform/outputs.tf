output "instance_public_ip" {
  value = oci_core_instance.sentinel_server.public_ip
  description = "The public IP address of the SentinelScan AI server."
}

output "instance_state" {
  value = oci_core_instance.sentinel_server.state
}