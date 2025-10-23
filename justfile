set shell := ["bash", "-uc"]

default:
  @just --list

requirements:
	@echo "gcloud"
	@echo "terraform"
	@echo "ansible"

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
	@chmod 0600 /tmp/ansible-key
	ansible-playbook -i inventories/inventory.gcp.yml playbooks/cluster.yml

[working-directory: 'ansible']
hosts:
	@echo 'Echoing all hosts...'
	ansible-inventory -i inventories/inventory.gcp.yml --graph

ssh-master:
	@ssh-add /tmp/ansible-key
	@ssh -L 8080:localhost:8080 debian@"$(ansible-inventory -i ansible/inventories/inventory.gcp.yml --graph \
		| grep -A 1 "@_master" \
		| tail -n 1 \
		| sed 's/.*--//; s/ //g')"

grafana:
	@echo "Grafana will be available on localhost:3000..."
	@ssh-add /tmp/ansible-key
	@ssh -L 3000:localhost:3000 debian@"$(ansible-inventory -i ansible/inventories/inventory.gcp.yml --graph \
		| grep -A 1 "@_master" \
		| tail -n 1 \
		| sed 's/.*--//; s/ //g')" 'kubectl get secret -n monitoring kube-prometheus-stack-grafana -o jsonpath="{.data.admin-password}" | base64 -d && echo "\n" && kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3000:80'

argocd:
	@echo "ArgoCD will be available on localhost:8080..."
	@ssh-add /tmp/ansible-key
	@ssh -L 8080:localhost:8080 debian@"$(ansible-inventory -i ansible/inventories/inventory.gcp.yml --graph \
		| grep -A 1 "@_master" \
		| tail -n 1 \
		| sed 's/.*--//; s/ //g')" 'kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d && echo "\n" && kubectl port-forward svc/argocd-server -n argocd 8080:443'

cleanup:
  rm -f /tmp/ansible-key plan.out
