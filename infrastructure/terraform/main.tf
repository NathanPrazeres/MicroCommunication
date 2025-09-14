# NOTE: the alpine linux image needs to be uploaded after we create a project.
# for now, we'll just hope the references to the image are correct

data "google_secret_manager_secret_version" "ssh_key" {
  secret = "ssh-public-key-secret-name"
}

# NOTE: always pick an odd number of workers and masters, to form a quorum

###########  Web Servers   #############
resource "google_compute_instance" "kubernetes_worker_node" {
  count = 3

  name = "worker_${count.index + 1}"

  machine_type = var.GCP_MACHINE_TYPE

  zone = var.GCP_ZONE

  metadata = {
    ssh-keys = "alpine:${data.google_secret_manager_secret_version.ssh_key}"
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

  tags = ["k8s-node", "k8s-worker"]

  labels = {
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

  zone = var.GCP_ZONE

  metadata = {
    # NOTE: alternative can be to use environment variables
    # and define a variable for it
    # export TF_VAR_public_key_content=$(cat /home/vagrant/.ssh/id_rsa.pub) 
    # ssh-keys = "alpine:${var.public_key_content}"

    ssh-keys = "alpine:${data.google_secret_manager_secret_version.ssh_key}"
  }

  boot_disk {
    initialize_params {
      image = "alpine_linux_TODO"
    }
  }

  network_interface {
    network = "default"
  }

  tags = ["k8s-node", "k8s-master"]

  labels = {
    Purpose        = "master"
    Owner          = "G20"
    Environment    = "testing"
    AnsibleManaged = "true"
    AutoShutdown   = "true"
  }
}

# TODO: create Ansible hosts file using the "local" provider from Terraform
