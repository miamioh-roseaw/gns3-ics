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
    string(
      name: 'DOCKERHUB_CREDENTIALS_ID',
      defaultValue: 'dockerhub',
      description: 'Jenkins username/password credential ID for Docker Hub'
    )
    booleanParam(
      name: 'PUSH_LATEST',
      defaultValue: true,
      description: 'Also push the latest tag'
    )
  }

  environment {
    PLC_IMAGE = 'gns3-ot-plc-ladder'
    REMOTE_IO_IMAGE = 'gns3-ot-remote-io-panel'
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

          if [ "${PUSH_LATEST}" = "true" ]; then
            docker tag "${DOCKERHUB_NAMESPACE}/${PLC_IMAGE}:${GIT_SHORT_SHA}" "${DOCKERHUB_NAMESPACE}/${PLC_IMAGE}:latest"
            docker tag "${DOCKERHUB_NAMESPACE}/${REMOTE_IO_IMAGE}:${GIT_SHORT_SHA}" "${DOCKERHUB_NAMESPACE}/${REMOTE_IO_IMAGE}:latest"
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
        '''
      }
    }

    stage('Push Images') {
      steps {
        script {
          withCredentials([
            usernamePassword(
              credentialsId: params.DOCKERHUB_CREDENTIALS_ID,
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

              if [ "${PUSH_LATEST}" = "true" ]; then
                docker push "${DOCKERHUB_NAMESPACE}/${PLC_IMAGE}:latest"
                docker push "${DOCKERHUB_NAMESPACE}/${REMOTE_IO_IMAGE}:latest"
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
      echo "Published ${DOCKERHUB_NAMESPACE}/${PLC_IMAGE} and ${DOCKERHUB_NAMESPACE}/${REMOTE_IO_IMAGE}"
    }
  }
}
