pipeline {
  agent any

  environment {
    MS_IMAGE       = "ci-demo/microservice-fastapi:${env.BUILD_NUMBER}"
    TESTS_IMAGE    = "ci-demo/api-tests:${env.BUILD_NUMBER}"
    CONTAINER_NAME = "ci-ms-${env.BUILD_NUMBER}"

    // Usa SSH si tu repo de tests es privado (recomendado en tu entorno)
    TESTS_REPO     = "git@github.com:Hefes10/demo-api-tests-behave.git"
    TESTS_BRANCH   = "main"

    // Para GitHub CLI (merge de PR)
    GH_CRED_ID     = "github-token"
  }

  options {
    // quita esta línea si no tenés el plugin Timestamper
    timestamps()
    buildDiscarder(logRotator(numToKeepStr: '25'))
  }

  stages {

    stage('Checkout Repo A') {
      steps {
        checkout scm
      }
    }

    stage('Build & Run Microservice (Docker)') {
      steps {
        sh '''
          set -e
          docker build -t "$MS_IMAGE" .

          # Red dedicada (idempotente)
          docker network create ci-net >/dev/null 2>&1 || true

          # Levantar microservicio en la red
          docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true
          docker run -d --name "$CONTAINER_NAME" --network ci-net "$MS_IMAGE"

          # Healthcheck desde la misma red (no uses localhost)
          for i in $(seq 1 30); do
            docker run --rm --network ci-net curlimages/curl:8.10.1 \
              -sf "http://$CONTAINER_NAME:3000/health" && break || sleep 1
          done

          docker run --rm --network ci-net curlimages/curl:8.10.1 -sf "http://$CONTAINER_NAME:3000/health"
        '''
      }
    }

    stage('Checkout Repo B (API tests)') {
      steps {
        dir('api-tests') {
          // checkout por SSH usando credencial 'github-ssh'
          git branch: env.TESTS_BRANCH, url: env.TESTS_REPO, credentialsId: 'github-ssh'
        }
      }
    }

    stage('Build & Run Tests (Docker)') {
      steps {
        dir('api-tests') {
          sh '''
            set -e
            docker build -t "$TESTS_IMAGE" .
            docker run --rm --network ci-net \
              -e BASE_URL="http://$CONTAINER_NAME:3000" \
              "$TESTS_IMAGE"
          '''
        }
      }
    }
  }

  post {
    success {
      script {
        // Merge automático solo si es PR hacia main
        if (env.CHANGE_ID && env.CHANGE_TARGET && env.CHANGE_TARGET == 'main') {
          withCredentials([string(credentialsId: env.GH_CRED_ID, variable: 'GH_TOKEN')]) {
            sh '''
              set -e
              export GH_TOKEN="$GH_TOKEN"
              # Derivar org/repo sin '.git'
              REPO_URL=$(git config --get remote.origin.url)
              REPO=$(echo "$REPO_URL" | sed -E 's#.*github.com[:/](.*?)(\\.git)?$#\\1#' | sed 's/\\.git$//')
              gh auth status || gh auth login --with-token <<< "$GH_TOKEN"
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
              REPO=$(echo "$REPO_URL" | sed -E 's#.*github.com[:/](.*?)(\\.git)?$#\\1#' | sed 's/\\.git$//')
              gh auth status || gh auth login --with-token <<< "$GH_TOKEN"
              gh pr comment "$CHANGE_ID" --repo "$REPO" --body "❌ CI falló: revisar logs de Jenkins (build #$BUILD_NUMBER). No se realizó el merge."
            '''
          }
        }
      }
      echo 'Pruebas fallaron → NO merge.'
    }

    always {
      script {
        try {
          sh '''
            docker logs "$CONTAINER_NAME" || true
            docker rm -f "$CONTAINER_NAME" || true
            docker rmi "$MS_IMAGE" "$TESTS_IMAGE" || true
            docker network rm ci-net >/dev/null 2>&1 || true
          '''
        } catch (ignored) {
          echo 'Cleanup omitido (sin workspace/recursos).'
        }
      }
    }
  }
}
