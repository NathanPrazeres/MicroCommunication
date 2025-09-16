# Ansible Automation

To run these Ansible playbooks, we first need 2 essential files:

- `/tmp/ansible-key`: the private SSH key that will be used by Ansible to connect to the VMs. Terraform injected the private key in the Secret Manager, so we need to run `gcloud secrets versions access latest --secret=ssh-private-key-secret-name > /tmp/ansible-key` to populate it.

- `/tmp/service-account.json`: the OAuth token for our Google Cloud account, that lets us fetch the dynamic inventory. We need to download it from the Google Cloud Console.

## After Execution

After the execution of the GitOps role, ArgoCD will be deployed, but you will not have access to the dashboard since it's hosted on the GCP. To get access to the dashboard you will need to do port forwarding via `ssh`:

```bash
ssh -L 8080:localhost:8080 debian@<GCP_VM_PUBLIC_IP>
```

and then:

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

But still, you will not have access, because you will not know the password, so you will need to run this:

```bash
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d
echo
```
