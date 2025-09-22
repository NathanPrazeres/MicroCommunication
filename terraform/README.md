# Terraform

## Interacting with GCP

For both Terraform provisioning and Ansible configuration, you'll need a service account to interact with GCP.

### Creating Service Account

Go to the Google Cloud Console > IAM > Service Accounts, and create a new service account.

Remember to give it Google Compute Engine permissions.

### Downloading the Service Account JSON

Through gcloud, you can run:

```bash
gcloud iam service-accounts keys create KEY_FILE \
    --iam-account=SA_NAME@PROJECT_ID.iam.gserviceaccount.com
```

So, for our project, it could be:

```bash
gcloud iam service-accounts keys create ~/service-account.json \
    --iam-account=agisit@agisit-g20.iam.gserviceaccount.com
```

---

OR

---

There should be an existing Service Account.

Click on it, and navigate to "Keys".

Click Add Key > Create new key > JSON.

And it should download it for you
