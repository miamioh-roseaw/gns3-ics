# Jenkins Docker Hub Pipeline

The root `Jenkinsfile` builds and pushes three Docker images:

- `gns3-ot-plc-ladder`
- `gns3-ot-remote-io-panel`
- `gns3-ot-hmi`

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

`DOCKERHUB_NAMESPACE`

Docker Hub username or organization. The default is:

```text
miamioh-roseaw
```

Change this if your Docker Hub namespace is different from your GitHub namespace.

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
miamioh-roseaw/gns3-ot-plc-ladder:latest
miamioh-roseaw/gns3-ot-plc-ladder:main
miamioh-roseaw/gns3-ot-plc-ladder:80f0a24abcd1
```
