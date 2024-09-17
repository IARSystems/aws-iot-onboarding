# AWS Cloud Onboarding

Further to the AWS Cloud Onboarding application note, this repository contains
implementations for:

- Manual onboarding without CA (using eSecIP production records)
- Just-in-time onboarding

Individual README.md files can be found for each implementation in the
```manual_onboarding_development```, ```manual_onboarding_production```
and ```just_in_time_provisioning``` folders respectively.

## AWS Account Setup

Before running the cloud onboarding implementations, you first must create an
AWS account. The AWS account User will require the following permissions:

- `AmazonS3FullAccess`
- `AWSLambda_FullAccess`
- `IAMFullAccess`
- `AWSIoTFullAccess`
- `IAMAccessAnalyzerFullAccess`

Create Access Key credentials (ID and secret) for the AWS User. You will then
need to follow the steps below to bring in the Access Key ID and Access Key
Secret into the devcontainer as environment variables.

Assuming you are using a bash terminal executing from the repository root:

```bash
# Create a new environment variable file and insert your id and secret
# (Modify the commands with your own id and secret)
echo AWS_ACCESS_KEY_ID=<your access key id> > .devcontainer/devcontainer.env
echo AWS_SECRET_ACCESS_KEY=<your access key secret> >> .devcontainer/devcontainer.env

# Modify devcontainer.json so use your new environment file
sed -i 's/devcontainer.env.example/devcontainer.env/' .devcontainer/devcontainer.json
```

When you rebuild the devcontainer, it will now automatically pull in your
Access Key ID and Access Key Secret as environment variables within the
container.

SECURITY WARNING: .gitignore file is set to ignore all .env files in order to
avoid your Access Key credentials accidentally being committed to version
control.
