# AWS Two-Tier Flask Application

A production-style two-tier web application built using Flask and MySQL, containerized with Docker and deployed on AWS EC2. The project demonstrates modern DevOps practices including containerization, CI/CD automation, cloud deployment, and application monitoring.

## Overview

This project showcases the deployment of a Flask-based web application with a MySQL database in a two-tier architecture. The application is containerized using Docker, orchestrated with Docker Compose, and deployed on AWS EC2. CI/CD automation is implemented using Jenkins to streamline the build and deployment process.

## Architecture

```text
GitHub
   │
   ▼
Jenkins CI/CD
   │
   ▼
AWS EC2 Instance
   │
   ▼
Docker Compose
 ├── Flask Application
 └── MySQL Database
```

## Tech Stack

### Backend
- Python
- Flask
- MySQL

### DevOps & Cloud
- Docker
- Docker Compose
- Jenkins
- AWS EC2
- Linux (Ubuntu)

### Version Control
- Git
- GitHub

## Features

- Flask-based web application
- MySQL database integration
- Docker containerization
- Multi-container deployment using Docker Compose
- Jenkins CI/CD pipeline
- AWS EC2 deployment
- Health monitoring and logging
- Automated build and deployment workflow

## Project Structure

```text
.
├── app/
├── templates/
├── static/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── Jenkinsfile
└── README.md
```

## Getting Started

### Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/aws-two-tier-flask-app.git
cd aws-two-tier-flask-app
```

### Run with Docker Compose

```bash
docker-compose up -d
```

### Verify Containers

```bash
docker ps
```

### Access Application

```text
http://localhost:5000
```

## AWS Deployment

1. Launch an AWS EC2 instance.
2. Install Docker and Docker Compose.
3. Clone the repository.
4. Configure environment variables.
5. Start services using Docker Compose.
6. Verify application health.

## CI/CD Pipeline

The Jenkins pipeline automates:

- Source code retrieval from GitHub
- Docker image build
- Container deployment
- Application restart
- Deployment validation

## Learning Outcomes

Through this project I gained practical experience in:

- Flask application development
- Containerization with Docker
- Docker Compose orchestration
- AWS EC2 deployment
- Jenkins CI/CD pipelines
- Linux server management
- DevOps workflow automation

## Future Improvements

- Nginx reverse proxy
- HTTPS with SSL certificates
- AWS CloudWatch monitoring
- Infrastructure as Code (Terraform)
- Kubernetes deployment
- Automated testing pipeline

## Author

**Dhruv Patil**

## Disclaimer

This project is intended for educational and learning purposes to demonstrate cloud deployment and DevOps concepts.
