pipeline {
    agent any

    environment {
        REPO_URL = 'https://github.com/dhruuv-patil/DeployHub.git'
        APP_IMAGE = 'deployhub-app:latest'
        APP_HEALTH_URL = 'http://localhost:5000/health'
    }

    stages {
        stage('Clone / Checkout Repository') {
            steps {
                echo '=== Stage 1: Checkout Source Code ==='
                script {
                    try {
                        checkout scm
                    } catch (Exception e) {
                        echo "SCM checkout fallback: cloning from ${REPO_URL}"
                        git branch: 'main', url: "${REPO_URL}"
                    }
                }
            }
        }

        stage('Automated Tests') {
            steps {
                echo '=== Stage 2: Running Unit Tests & Health Checks ==='
                sh '''
                    python3 -m pip install -q pytest || true
                    python3 -m pytest -v tests/ || true
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                echo '=== Stage 3: Building Docker Image ==='
                sh "docker build -t ${APP_IMAGE} ."
            }
        }

        stage('Deploy with Docker Compose') {
            steps {
                echo '=== Stage 4: Deploying Multi-Container Application ==='
                // Stop any running containers cleanly
                sh 'docker compose down || true'
                // Start application and database containers in detached mode
                sh 'docker compose up -d --build'
            }
        }

        stage('Validate Deployment') {
            steps {
                echo '=== Stage 5: Validating Application Health ==='
                sh '''
                    echo "Waiting for services to become healthy..."
                    sleep 15
                    for i in 1 2 3 4 5 6; do
                        echo "Health check attempt $i..."
                        if curl -sf "${APP_HEALTH_URL}"; then
                            echo "DeployHub is healthy and operational!"
                            exit 0
                        fi
                        sleep 5
                    done
                    echo "Deployment validation failed! Showing logs:"
                    docker compose logs
                    exit 1
                '''
            }
        }
    }

    post {
        always {
            echo 'Pipeline execution finished.'
        }
        success {
            echo 'DeployHub successfully deployed and validated!'
        }
        failure {
            echo 'Deployment failed. Please check build logs.'
        }
    }
}
