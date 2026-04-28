# Jenkins Docker Hub Pipeline

The root `Jenkinsfile` builds and pushes three Docker Hub images:

- `cithit/ot-plc`
- `cithit/ot-rio`
- `cithit/ot-hmi`

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
cithit/ot-plc:latest
cithit/ot-plc:main
cithit/ot-plc:80f0a24abcd1
cithit/ot-rio:latest
cithit/ot-hmi:latest
```
