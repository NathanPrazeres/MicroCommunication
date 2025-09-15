<div align="center">
  <h1>MicroCommunication</h1>
  <h2>Micro-Service based communications App</h2>
  <h3>agisit25-g20</h3>
</div>

## Development

For development, the principle was to get the templates and setup **right**.

For this, we defined a GitLab CI that would validate and lint all our Terraform files, as well as any YAML files (since there isn't any "code" here, due to it all being IaC, this was the best way to ensure only well-formatted files, reached the repo)

The CI includes the [pre-commit-terraform](https://github.com/antonbabenko/pre-commit-terraform) to validate all terraform files, and [yamllint](https://github.com/adrienverge/yamllint).

### Pre-requisites


## File Structure

The idea was to have a structure that would encapsulate each step in setting up the environment, so that's exactly what we did, with the names being as explicit as possible:

- `application`: where the actual application is hosted, along with the code that makes up the front and back ends. This includes the Kubernetes ConfigMap since it's "part" of the application

- `configuration`: this is where all the configuration scripts are hosted. They are managed by Ansible, but other tools could be hosted here

- `infrastructure`: how the kubernetes nodes are provisioned. Along with that, the GCP machine specifications and networks

- `monitoring`: all monitoring software used to ensure uptime and logging.

```txt
── application
│   ├── back-end
│   ├── database
│   ├── front-end
│   └── kubernetes
├── configuration
│   └── ansible
│       ├── inventory.ini
│       ├── playbooks
│       └── roles
├── infrastructure
│   └── terraform
├── monitoring
│   ├── grafana
│   └── prometheus
```

Each folder handles its workload and setup up the work for the next layer.

The workflow is the following:

TODO

## Application architecture

The idea here is to have a microservice for each "service", a.k.a functionality of the application that can be self-contained and isolated in a container. They all communicate to the DB through a secure connection.

Each microservice will correspond to:

- Message Queueing

- Authentication

- User Actions

- Chat Actions
