pipeline {
  agent any

  options {
    timestamps()
    disableConcurrentBuilds()
  }

  environment {
    DOCKER_CREDENTIALS_ID = 'roseaw-dockerhub'
    PUSH_LATEST = 'true'
    PLC_IMAGE = 'cithit/ot-plc-4'
    RIO_IMAGE = 'cithit/ot-rio-4'
    HMI_IMAGE = 'cithit/ot-hmi-4'
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
            --tag "${PLC_IMAGE}:${GIT_SHORT_SHA}" \
            --tag "${PLC_IMAGE}:${BRANCH_TAG}" \
            ./plc

          docker build \
            --pull \
            --tag "${RIO_IMAGE}:${GIT_SHORT_SHA}" \
            --tag "${RIO_IMAGE}:${BRANCH_TAG}" \
            ./io-panel

          docker build \
            --pull \
            --tag "${HMI_IMAGE}:${GIT_SHORT_SHA}" \
            --tag "${HMI_IMAGE}:${BRANCH_TAG}" \
            ./hmi

          if [ "${PUSH_LATEST}" = "true" ]; then
            docker tag "${PLC_IMAGE}:${GIT_SHORT_SHA}" "${PLC_IMAGE}:latest"
            docker tag "${RIO_IMAGE}:${GIT_SHORT_SHA}" "${RIO_IMAGE}:latest"
            docker tag "${HMI_IMAGE}:${GIT_SHORT_SHA}" "${HMI_IMAGE}:latest"
          fi
        '''
      }
    }

    stage('Smoke Test Images') {
      steps {
        sh '''
          set -eu
          docker image inspect "${PLC_IMAGE}:${GIT_SHORT_SHA}" >/dev/null
          docker image inspect "${RIO_IMAGE}:${GIT_SHORT_SHA}" >/dev/null
          docker image inspect "${HMI_IMAGE}:${GIT_SHORT_SHA}" >/dev/null
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

              docker push "${PLC_IMAGE}:${GIT_SHORT_SHA}"
              docker push "${PLC_IMAGE}:${BRANCH_TAG}"

              docker push "${RIO_IMAGE}:${GIT_SHORT_SHA}"
              docker push "${RIO_IMAGE}:${BRANCH_TAG}"

              docker push "${HMI_IMAGE}:${GIT_SHORT_SHA}"
              docker push "${HMI_IMAGE}:${BRANCH_TAG}"

              if [ "${PUSH_LATEST}" = "true" ]; then
                docker push "${PLC_IMAGE}:latest"
                docker push "${RIO_IMAGE}:latest"
                docker push "${HMI_IMAGE}:latest"
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
      echo "Published ${PLC_IMAGE}, ${RIO_IMAGE}, and ${HMI_IMAGE}"
    }
  }
}
