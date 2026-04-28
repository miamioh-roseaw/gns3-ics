# Jenkins Docker Hub Pipeline

The root `Jenkinsfile` builds and pushes three component-tagged images to one Docker Hub repository:

- `cithit/gns3-ics:plc-latest`
- `cithit/gns3-ics:remote-io-latest`
- `cithit/gns3-ics:hmi-latest`

## Jenkins Requirements

The Jenkins agent must have:

- Docker CLI
- access to a running Docker daemon
- permission to build and push images
- Git available on the agent

## Docker Hub Credentials

Create a Jenkins credential:

- Kind: `Username with password`
- ID: `roseaw@miamioh.edu`
- Username: your Docker Hub username
- Password: a Docker Hub access token

Using an access token is preferred over storing your Docker Hub account password.

## Pipeline Parameters

`DOCKERHUB_REPOSITORY`

Docker Hub repository. The default is:

```text
cithit/gns3-ics
```

Change this only if the Docker Hub repository changes.

`PUSH_LATEST`

When enabled, the pipeline also publishes:

```text
component-specific latest tags
```

## Tags Published

For each image, Jenkins publishes:

- the component plus short Git commit SHA
- the component plus branch name
- the component plus `latest`, when `PUSH_LATEST` is enabled

Example:

```text
cithit/gns3-ics:plc-latest
cithit/gns3-ics:plc-main
cithit/gns3-ics:plc-80f0a24abcd1
cithit/gns3-ics:remote-io-latest
cithit/gns3-ics:hmi-latest
```
