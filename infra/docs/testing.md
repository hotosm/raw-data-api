# Testing the infrastructure

## Format, Syntax and provider config

```
terraform fmt
terraform init
terraform validate
```

## Costs using infracost
TBD

## Terrascan
TBD

## BDD Testing

We can declare our own compliance rules using Gherkin `.feature` files in order to exercise behaviour-driven-development (BDD). In this paradigm, we write feature files in plain English declaring what our desired compliance criteria are. We can then use the `terraform-compliance` tool in-order to check for compliance.

### Writing feature files

Feature files are written using [Gherkin](https://cucumber.io/docs/gherkin/reference/) format. Roughly, we declare a feature - which is an overarching goal, and Scenarios - components that achieve the goal. For example:

```
Feature: Cloudfront Distribution should follow modern best practices
         Like using HTTP2 and IPv6 and the latest Security protocols

        Scenario: Cloudfront distribution must have IPv6 enabled
                Given I have aws_cloudfront_distribution defined
                Then it must have is_ipv6_enabled
                And its value must be true

        Scenario: Cloudfront distribution must have http2 enabled
                Given I have aws_cloudfront_distribution defined
                Then it must have http_version
                And its value must be http2

```

The feature files are fairly self-explanatory.  We can now save this to a file called cdn.feature and then use it to cehck compliance.

### Setting up terraform-compliance

Terraform compliance tool can be configured to run in a container. Here we use podman (a docker alternative) to run terraform-compliance safely.

```
# Install podman
sudo apt install -y podman
function terraform-compliance { 
  podman run --rm -v $(pwd):/target -i -t docker.io/eerkunt/terraform-compliance "$@"; 
}
```

### Checking compliance

We need to:

1. Generate a plan file using terraform plan
2. Convert it to JSON
3. Run compliance checks over it

```
terraform plan -out=plan.out
terraform show -json plan.out > plan.out.json
terraform-compliance -f tests/compliance -p plan.out.json
```

Note that plan files cannot be generated when configured for remote backends.

## Errata

We should be able to use a backend config to temporarily override remote backend.

```
terraform init -backend=false
```

Alternatively, if using a local backend config file: config.local.tfbackend
```
terraform init -backend-config=config.local.tfbackend
```
