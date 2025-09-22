set shell := ["bash", "-uc"]

default:
  @just --list

requirements:
	echo "gcloud"
	echo "terraform"
	echo "ansible"

login:
	gcloud auth login

setup_project project:
	@echo 'Setting GCP project as {{ project }}'
	gcloud config set project {{ project }}

[working-directory: 'terraform']
provision:
	@echo 'Applying terraform resources...'
	terraform plan -out plan.out
	terraform apply plan.out

[working-directory: 'terraform']
stop:
	@echo 'Destroying all resources...'
	terraform destroy

[working-directory: 'ansible']
configure:
	@echo 'Preparing Ansible playbook...'
	ssh-add -D
	gcloud secrets versions access latest --secret=ssh-private-key-secret-name > /tmp/ansible-key
	ansible-playbook -i inventories/inventory.gcp.yml playbooks/cluster.yml

[working-directory: 'ansible']
hosts:
	@echo 'Echoing all hosts...'
	ansible-inventory -i inventories/inventory.gcp.yml --graph

ssh-master:
	ssh -L 8080:localhost:8080 debian@"$(ansible-inventory -i ansible/inventories/inventory.gcp.yml --graph \
		| grep -A 1 "@_master" \
		| tail -n 1 \
		| sed 's/.*--//; s/ //g')"

cleanup:
    rm -f /tmp/ansible-key plan.out
