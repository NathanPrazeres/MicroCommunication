# NOTE: the alpine linux image needs to be uploaded after we create a project.
# for now, we'll just hope the references to the image are correct

###########  Web Servers   #############
resource "google_compute_instance" "kubernetes_worker_node" {
  # number of nodes
  count = 3

  name = "worker_${count.index + 1}"

  machine_type = var.GCP_MACHINE_TYPE

  zone = var.GCP_ZONE

  metadata = {
    ssh-keys = "alpine:${file("/home/vagrant/.ssh/id_rsa.pub")}"
  }

  boot_disk {
    initialize_params {
      image = "alpine_linux_TODO"
    }
  }

  network_interface {
    network = "default"
    access_config {
      # TODO:
    }
  }

  tags = {
    Purpose        = "worker"
    Owner          = "G20"
    Environment    = "testing"
    AnsibleManaged = "true"
    AutoShutdown   = "true"
  }
}

###########  Master   #############
resource "google_compute_instance" "kubernetes_master_node" {
  name = "master"

  machine_type = var.GCP_MACHINE_TYPE

  metadata = {
    ssh-keys = "alpine:${file("/home/vagrant/.ssh/id_rsa.pub")}"
  }

  boot_disk {
    initialize_params {
      image = "alpine_linux_TODO"
    }
  }

  network_interface {
    network = "default"
  }


  tags = {
    Purpose        = "master"
    Owner          = "G20"
    Environment    = "testing"
    AnsibleManaged = "true"
    AutoShutdown   = "true"
  }
}

# TODO: create Ansible hosts file using the "local" provider from Terraform
