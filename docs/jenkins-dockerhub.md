# Jenkins Docker Hub Pipeline

The root `Jenkinsfile` builds and pushes three Docker Hub images:

- `cithit/plc`
- `cithit/rio`
- `cithit/hmi`

## Jenkins Requirements

The Jenkins agent must have:

- Docker CLI
- access to a running Docker daemon
- permission to build and push images
- Git available on the agent

## Docker Hub Credentials

Create a Jenkins credential:

- Kind: `Username with password`
- ID: `roseaw-dockerhub`
- Username: your Docker Hub username
- Password: a Docker Hub access token

Using an access token is preferred over storing your Docker Hub account password.

## Pipeline Parameters

`PUSH_LATEST`

When enabled, the pipeline also publishes:

```text
latest
```

## Tags Published

For each image, Jenkins publishes:

- the short Git commit SHA
- the branch name
- `latest`, when `PUSH_LATEST` is enabled

Example:

```text
cithit/plc:latest
cithit/plc:main
cithit/plc:80f0a24abcd1
cithit/rio:latest
cithit/hmi:latest
```
