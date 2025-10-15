pipeline {
  agent any

  environment {
    MS_IMAGE = "ci-demo/microservice-fastapi:${env.BUILD_NUMBER}"
    TESTS_IMAGE = "ci-demo/api-tests:${env.BUILD_NUMBER}"
    CONTAINER_NAME = "ci-ms-${env.BUILD_NUMBER}"
    TESTS_REPO = "https://github.com/Hefes10/demo-api-tests-behave.git"
    TESTS_BRANCH = "main"
    GH_CRED_ID = "github-token"
  }

  options {
    timestamps()
    buildDiscarder(logRotator(numToKeepStr: '25'))
  }

  stages {
    stage('Checkout Repo A') {
      steps { checkout scm }
    }

    stage('Build & Run Microservice (Docker)') {
      steps {
        sh '''
          docker build -t "$MS_IMAGE" .
          docker rm -f "$CONTAINER_NAME" 2>/dev/null || true
          docker run -d --name "$CONTAINER_NAME" -p 3000:3000 "$MS_IMAGE"
          for i in $(seq 1 30); do
            curl -sf http://localhost:3000/health && break || sleep 1
          done
          curl -sf http://localhost:3000/health
        '''
      }
    }

    stage('Checkout Repo B (API tests)') {
      steps {
        dir('api-tests') { git branch: env.TESTS_BRANCH, url: env.TESTS_REPO }
      }
    }

    stage('Build & Run Tests (Docker)') {
      steps {
        dir('api-tests') {
          sh '''
            docker build -t "$TESTS_IMAGE" .
            docker run --rm --network host -e BASE_URL="http://localhost:3000" "$TESTS_IMAGE"
          '''
        }
      }
    }
  }

  post {
    success {
      script {
        if (env.CHANGE_ID && env.CHANGE_TARGET && env.CHANGE_TARGET == 'main') {
          withCredentials([string(credentialsId: env.GH_CRED_ID, variable: 'GH_TOKEN')]) {
            sh '''
              export GH_TOKEN="$GH_TOKEN"
              REPO_URL=$(git config --get remote.origin.url)
              REPO=$(echo "$REPO_URL" | sed -E 's#.*github.com[:/](.*?)(\\.git)?$#\\1#')
              gh pr merge "$CHANGE_ID" --merge --delete-branch --repo "$REPO" --auto=false
            '''
          }
        } else {
          echo "No es PR a main → no se hace merge."
        }
      }
    }
    failure {
      script {
        if (env.CHANGE_ID) {
          withCredentials([string(credentialsId: env.GH_CRED_ID, variable: 'GH_TOKEN')]) {
            sh '''
              export GH_TOKEN="$GH_TOKEN"
              REPO_URL=$(git config --get remote.origin.url)
              REPO=$(echo "$REPO_URL" | sed -E 's#.*github.com[:/](.*?)(\\.git)?$#\\1#')
              gh pr comment "$CHANGE_ID" --repo "$REPO" --body "❌ CI falló: revisar logs de Jenkins (build #$BUILD_NUMBER). No se realizó el merge."
            '''
          }
        }
      }
      echo 'Pruebas fallaron → NO merge.'
    }
    always {
      sh '''
        docker logs "$CONTAINER_NAME" || true
        docker rm -f "$CONTAINER_NAME" || true
        docker rmi "$MS_IMAGE" "$TESTS_IMAGE" || true
      '''
    }
  }
}
