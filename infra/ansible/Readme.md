# Ansible for configuration management

## What is ansible and why use it?

TBD

## Building your server inventory

TBD

## Using OpenSSH client config aliases in place of FQDN in the inventory

TBD 

## Validating ansible playbooks

```
ansible-playbook --check -i inventory/raw-data -l prod setup.yml
```

## Running ansible playbooks

```
$ ansible-playbook -i inventory/raw-data -l prod setup.yml
```

## Templating and variables

TBD
