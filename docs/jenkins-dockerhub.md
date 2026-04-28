# Jenkins Docker Hub Pipeline

The root `Jenkinsfile` builds and pushes three Docker Hub images:

- `cithit/ot-plc-3`
- `cithit/ot-rio-3`
- `cithit/ot-hmi-3`

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

## Tags Published

For each image, Jenkins publishes:

- the short Git commit SHA
- the branch name
- `latest`

Example:

```text
cithit/ot-plc-3:latest
cithit/ot-plc-3:main
cithit/ot-plc-3:80f0a24abcd1
cithit/ot-rio-3:latest
cithit/ot-hmi-3:latest
```
