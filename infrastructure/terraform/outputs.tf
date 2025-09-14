# TODO:
# Iterate over every GCP instance node, and get it's hostname and IP
# also check it's metadata to separate into sections in the inventory

# NOTE: this is just an example from my home server

output "ansible_inventory_hosts" {
  value = {
    # for hostname, lxc in proxmox_lxc.container : hostname => {
    #   ansible_host  = lxc.network[0].ip
    #   ansible_user  = "root"
    #   playbook_name = lxc.playbook_name
    # }
  }
}
