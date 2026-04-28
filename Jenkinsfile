pipeline {
  agent any

  options {
    timestamps()
    disableConcurrentBuilds()
  }

  parameters {
    string(
      name: 'DOCKERHUB_NAMESPACE',
      defaultValue: 'miamioh-roseaw',
      description: 'Docker Hub username or organization that will receive the images'
    )
    booleanParam(
      name: 'PUSH_LATEST',
      defaultValue: true,
      description: 'Also push the latest tag'
    )
  }

  environment {
    DOCKER_CREDENTIALS_ID = 'roseaw-dockerhub'
    KUBECONFIG = credentials('roseaw-225')
    PLC_IMAGE = 'gns3-ot-plc-ladder'
    REMOTE_IO_IMAGE = 'gns3-ot-remote-io-panel'
    HMI_IMAGE = 'gns3-ot-hmi'
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
            --tag "${DOCKERHUB_NAMESPACE}/${PLC_IMAGE}:${GIT_SHORT_SHA}" \
            --tag "${DOCKERHUB_NAMESPACE}/${PLC_IMAGE}:${BRANCH_TAG}" \
            ./plc

          docker build \
            --pull \
            --tag "${DOCKERHUB_NAMESPACE}/${REMOTE_IO_IMAGE}:${GIT_SHORT_SHA}" \
            --tag "${DOCKERHUB_NAMESPACE}/${REMOTE_IO_IMAGE}:${BRANCH_TAG}" \
            ./io-panel

          docker build \
            --pull \
            --tag "${DOCKERHUB_NAMESPACE}/${HMI_IMAGE}:${GIT_SHORT_SHA}" \
            --tag "${DOCKERHUB_NAMESPACE}/${HMI_IMAGE}:${BRANCH_TAG}" \
            ./hmi

          if [ "${PUSH_LATEST}" = "true" ]; then
            docker tag "${DOCKERHUB_NAMESPACE}/${PLC_IMAGE}:${GIT_SHORT_SHA}" "${DOCKERHUB_NAMESPACE}/${PLC_IMAGE}:latest"
            docker tag "${DOCKERHUB_NAMESPACE}/${REMOTE_IO_IMAGE}:${GIT_SHORT_SHA}" "${DOCKERHUB_NAMESPACE}/${REMOTE_IO_IMAGE}:latest"
            docker tag "${DOCKERHUB_NAMESPACE}/${HMI_IMAGE}:${GIT_SHORT_SHA}" "${DOCKERHUB_NAMESPACE}/${HMI_IMAGE}:latest"
          fi
        '''
      }
    }

    stage('Smoke Test Images') {
      steps {
        sh '''
          set -eu
          docker image inspect "${DOCKERHUB_NAMESPACE}/${PLC_IMAGE}:${GIT_SHORT_SHA}" >/dev/null
          docker image inspect "${DOCKERHUB_NAMESPACE}/${REMOTE_IO_IMAGE}:${GIT_SHORT_SHA}" >/dev/null
          docker image inspect "${DOCKERHUB_NAMESPACE}/${HMI_IMAGE}:${GIT_SHORT_SHA}" >/dev/null
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

              docker push "${DOCKERHUB_NAMESPACE}/${PLC_IMAGE}:${GIT_SHORT_SHA}"
              docker push "${DOCKERHUB_NAMESPACE}/${PLC_IMAGE}:${BRANCH_TAG}"

              docker push "${DOCKERHUB_NAMESPACE}/${REMOTE_IO_IMAGE}:${GIT_SHORT_SHA}"
              docker push "${DOCKERHUB_NAMESPACE}/${REMOTE_IO_IMAGE}:${BRANCH_TAG}"

              docker push "${DOCKERHUB_NAMESPACE}/${HMI_IMAGE}:${GIT_SHORT_SHA}"
              docker push "${DOCKERHUB_NAMESPACE}/${HMI_IMAGE}:${BRANCH_TAG}"

              if [ "${PUSH_LATEST}" = "true" ]; then
                docker push "${DOCKERHUB_NAMESPACE}/${PLC_IMAGE}:latest"
                docker push "${DOCKERHUB_NAMESPACE}/${REMOTE_IO_IMAGE}:latest"
                docker push "${DOCKERHUB_NAMESPACE}/${HMI_IMAGE}:latest"
              fi

              docker logout
            '''
          }
        }
      }
    }
  }

  post {
    always {
      sh 'docker logout || true'
    }
    success {
      echo "Published ${DOCKERHUB_NAMESPACE}/${PLC_IMAGE}, ${DOCKERHUB_NAMESPACE}/${REMOTE_IO_IMAGE}, and ${DOCKERHUB_NAMESPACE}/${HMI_IMAGE}"
    }
  }
}
