resource "tls_private_key" "ssh_key" {
  algorithm = "ED25519"
}

resource "google_secret_manager_secret" "ssh_private_key_secret" {
  secret_id = "ssh-private-key-secret-name"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "ssh_private_key_version" {
  secret      = google_secret_manager_secret.ssh_private_key_secret.id
  secret_data = tls_private_key.ssh_key.private_key_openssh
}

resource "google_secret_manager_secret" "ssh_key_secret" {
  secret_id = "ssh-public-key-secret-name"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "ssh_key_version" {
  secret      = google_secret_manager_secret.ssh_key_secret.id
  secret_data = tls_private_key.ssh_key.public_key_openssh
}

# NOTE: always pick an odd number of workers and masters, to form a quorum

###########  Workers   #############
resource "google_compute_instance" "kubernetes_worker_node" {
  count = 3

  name = "worker-${count.index + 1}"

  machine_type = var.GCP_MACHINE_TYPE

  zone = var.GCP_ZONE

  metadata = {
    ssh-keys = "${var.GCE_HOSTNAME}:${tls_private_key.ssh_key.public_key_openssh}"
  }

  boot_disk {
    initialize_params {
      image = var.LINUX_IMAGE
    }
  }

  network_interface {
    network    = google_compute_network.k8s_vpc.self_link
    subnetwork = google_compute_subnetwork.k8s_subnetwork.self_link
    access_config {
      # TODO:
    }
  }

  tags = ["k8s-node", "k8s-worker"]

  labels = {
    purpose         = "worker"
    owner           = "g20"
    environment     = "testing"
    ansible_managed = "true"
    auto_shutdown   = "true"
  }
}

###########  Control Plane   #############
resource "google_compute_instance" "kubernetes_master_node" {
  name = "master"

  machine_type = var.GCP_MACHINE_TYPE

  zone = var.GCP_ZONE

  metadata = {
    # NOTE: alternative can be to use environment variables
    # and define a variable for it
    # export TF_VAR_public_key_content=$(cat /home/vagrant/.ssh/id_rsa.pub)
    # ssh-keys = "alpine:${var.public_key_content}"

    ssh-keys = "${var.GCE_HOSTNAME}:${tls_private_key.ssh_key.public_key_openssh}"
  }

  boot_disk {
    initialize_params {
      image = var.LINUX_IMAGE
    }
  }

  network_interface {
    network    = google_compute_network.k8s_vpc.self_link
    subnetwork = google_compute_subnetwork.k8s_subnetwork.self_link
    access_config {
      nat_ip = google_compute_address.master_ip.address
    }
  }

  tags = ["k8s-node", "k8s-master"]

  labels = {
    purpose         = "master"
    owner           = "g20"
    environment     = "testing"
    ansible_managed = "true"
    auto_shutdown   = "true"
  }
}
