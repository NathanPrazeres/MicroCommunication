resource "google_compute_disk" "postgres_data_disk" {
  name = "postgres-data-disk"
  type = "pd-ssd"
  zone = "europe-southwest-1a"
  size = 20
}
