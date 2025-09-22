resource "google_compute_network" "k8s_vpc" {
  name                    = "k8s-vpc"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "k8s_subnetwork" {
  name          = "k8s-subnetwork"
  ip_cidr_range = "10.0.0.0/16"
  region        = var.GCP_REGION
  network       = google_compute_network.k8s_vpc.self_link
}

resource "google_compute_address" "master_ip" {
  name   = "k8s-master-ip"
  region = var.GCP_REGION
}

resource "google_compute_firewall" "internal_k8s_traffic" {
  name    = "k8s-internal"
  network = google_compute_network.k8s_vpc.self_link

  allow {
    protocol = "all"
  }

  source_ranges = [google_compute_subnetwork.k8s_subnetwork.ip_cidr_range]
}

resource "google_compute_firewall" "ssh_access" {
  name    = "ssh-access"
  network = google_compute_network.k8s_vpc.self_link

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  # TODO: create variable with only our IPs or allow from all sources?
  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["k8s-node"]
}

resource "google_compute_firewall" "kubernetes_api" {
  name    = "kubernetes-api"
  network = google_compute_network.k8s_vpc.self_link

  allow {
    protocol = "tcp"
    ports    = ["6443"]
  }

  # TODO: create variable with only our IPs or allow from all sources?
  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["k8s-node"]
}


resource "google_compute_firewall" "block_rdp" {
  name    = "block-rdp-port"
  network = google_compute_network.k8s_vpc.self_link

  deny {
    protocol = "tcp"
    # Block RDP port
    ports = ["3389"]
  }

  # TODO: create variable with only our IPs or allow from all sources?
  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["k8s-node"]
}

resource "google_compute_firewall" "calicp_bpg" {
  name    = "calico-bpg"
  network = google_compute_network.k8s_vpc.self_link

  allow {
    protocol = "tcp"
    ports    = ["179"]
  }

  # TODO: create variable with only our IPs or allow from all sources?
  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["k8s-node"]
}

resource "google_compute_firewall" "calico_ipip" {
  name    = "calico-ipip"
  network = google_compute_network.k8s_vpc.self_link

  allow {
    protocol = "ipip"
  }

  # TODO: create variable with only our IPs or allow from all sources?
  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["k8s-node"]
}

resource "google_compute_firewall" "app_ingress" {
  name    = "app-ingress"
  network = google_compute_network.k8s_vpc.self_link

  allow {
    protocol = "tcp"
    ports    = ["80", "443"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["k8s-node"]
}
