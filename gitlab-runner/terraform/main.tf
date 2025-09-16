resource "proxmox_lxc" "gitlab-runner" {
  target_node  = "pve"
  hostname     = "gitlab-terraform"
  vmid         = 118
  ostemplate   = "local:vztmpl/${var.template_name}"
  unprivileged = true

  # Specs of the machine
  cores  = 2
  memory = 256

  features {
    # Ansible will configure this by connecting to the node itself
    # fuse    = true
    nesting = true
  }

  rootfs {
    storage = "local"
    size    = "16G"
  }

  lifecycle {
    ignore_changes = [tags]
  }

  protection = false

  // create this file
  ssh_public_keys = file("../ansible_ssh.pub")
  password        = "gitlab_runner"

  onboot = true
  start  = true

  # Network configuration
  network {
    name   = "eth0"
    bridge = "vmbr0"
    ip     = "192.168.1.218/24"
    gw     = "192.168.1.1"
  }
  network {
    name   = "eth1"
    bridge = "vmbr1"
    ip     = "10.150.0.118/24"
    gw     = "10.150.0.1"
  }

  tags = "docker,terraform_provisioned"
}
