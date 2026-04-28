pipeline {
  agent any

  options {
    timestamps()
    disableConcurrentBuilds()
  }

  parameters {
    string(
      name: 'DOCKERHUB_REPOSITORY',
      defaultValue: 'cithit/gns3-ics',
      description: 'Docker Hub repository that will receive the component-tagged images'
    )
    booleanParam(
      name: 'PUSH_LATEST',
      defaultValue: true,
      description: 'Also push the latest tag'
    )
  }

  environment {
    DOCKER_CREDENTIALS_ID = 'roseaw@miamioh.edu'
    PLC_TAG_PREFIX = 'plc'
    REMOTE_IO_TAG_PREFIX = 'remote-io'
    HMI_TAG_PREFIX = 'hmi'
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
        script {
          env.GIT_SHORT_SHA = sh(
            script: 'git rev-parse --short=12 HEAD',
            returnStdout: true
          ).trim()
          def branchName = env.BRANCH_NAME ?: sh(
            script: 'git rev-parse --abbrev-ref HEAD',
            returnStdout: true
          ).trim()
          env.BRANCH_TAG = branchName
            .toLowerCase()
            .replaceAll(/[^a-z0-9_.-]+/, '-')
            .replaceAll(/^-+|-+$/, '')
          if (!env.BRANCH_TAG || env.BRANCH_TAG == 'head') {
            env.BRANCH_TAG = env.GIT_SHORT_SHA
          }
        }
      }
    }

    stage('Build Images') {
      steps {
        sh '''
          set -eu

          docker build \
            --pull \
            --tag "${DOCKERHUB_REPOSITORY}:${PLC_TAG_PREFIX}-${GIT_SHORT_SHA}" \
            --tag "${DOCKERHUB_REPOSITORY}:${PLC_TAG_PREFIX}-${BRANCH_TAG}" \
            ./plc

          docker build \
            --pull \
            --tag "${DOCKERHUB_REPOSITORY}:${REMOTE_IO_TAG_PREFIX}-${GIT_SHORT_SHA}" \
            --tag "${DOCKERHUB_REPOSITORY}:${REMOTE_IO_TAG_PREFIX}-${BRANCH_TAG}" \
            ./io-panel

          docker build \
            --pull \
            --tag "${DOCKERHUB_REPOSITORY}:${HMI_TAG_PREFIX}-${GIT_SHORT_SHA}" \
            --tag "${DOCKERHUB_REPOSITORY}:${HMI_TAG_PREFIX}-${BRANCH_TAG}" \
            ./hmi

          if [ "${PUSH_LATEST}" = "true" ]; then
            docker tag "${DOCKERHUB_REPOSITORY}:${PLC_TAG_PREFIX}-${GIT_SHORT_SHA}" "${DOCKERHUB_REPOSITORY}:${PLC_TAG_PREFIX}-latest"
            docker tag "${DOCKERHUB_REPOSITORY}:${REMOTE_IO_TAG_PREFIX}-${GIT_SHORT_SHA}" "${DOCKERHUB_REPOSITORY}:${REMOTE_IO_TAG_PREFIX}-latest"
            docker tag "${DOCKERHUB_REPOSITORY}:${HMI_TAG_PREFIX}-${GIT_SHORT_SHA}" "${DOCKERHUB_REPOSITORY}:${HMI_TAG_PREFIX}-latest"
          fi
        '''
      }
    }

    stage('Smoke Test Images') {
      steps {
        sh '''
          set -eu
          docker image inspect "${DOCKERHUB_REPOSITORY}:${PLC_TAG_PREFIX}-${GIT_SHORT_SHA}" >/dev/null
          docker image inspect "${DOCKERHUB_REPOSITORY}:${REMOTE_IO_TAG_PREFIX}-${GIT_SHORT_SHA}" >/dev/null
          docker image inspect "${DOCKERHUB_REPOSITORY}:${HMI_TAG_PREFIX}-${GIT_SHORT_SHA}" >/dev/null
        '''
      }
    }

    stage('Push Images') {
      steps {
        script {
          withCredentials([
            usernamePassword(
              credentialsId: env.DOCKER_CREDENTIALS_ID,
              usernameVariable: 'DOCKERHUB_USERNAME',
              passwordVariable: 'DOCKERHUB_PASSWORD'
            )
          ]) {
            sh '''
              set -eu

              printf '%s' "${DOCKERHUB_PASSWORD}" | docker login \
                --username "${DOCKERHUB_USERNAME}" \
                --password-stdin

              docker push "${DOCKERHUB_REPOSITORY}:${PLC_TAG_PREFIX}-${GIT_SHORT_SHA}"
              docker push "${DOCKERHUB_REPOSITORY}:${PLC_TAG_PREFIX}-${BRANCH_TAG}"

              docker push "${DOCKERHUB_REPOSITORY}:${REMOTE_IO_TAG_PREFIX}-${GIT_SHORT_SHA}"
              docker push "${DOCKERHUB_REPOSITORY}:${REMOTE_IO_TAG_PREFIX}-${BRANCH_TAG}"

              docker push "${DOCKERHUB_REPOSITORY}:${HMI_TAG_PREFIX}-${GIT_SHORT_SHA}"
              docker push "${DOCKERHUB_REPOSITORY}:${HMI_TAG_PREFIX}-${BRANCH_TAG}"

              if [ "${PUSH_LATEST}" = "true" ]; then
                docker push "${DOCKERHUB_REPOSITORY}:${PLC_TAG_PREFIX}-latest"
                docker push "${DOCKERHUB_REPOSITORY}:${REMOTE_IO_TAG_PREFIX}-latest"
                docker push "${DOCKERHUB_REPOSITORY}:${HMI_TAG_PREFIX}-latest"
              fi

              docker logout
            '''
          }
        }
      }
    }
  }

  post {
    success {
      echo "Published PLC, remote I/O, and HMI tags to ${DOCKERHUB_REPOSITORY}"
    }
  }
}
