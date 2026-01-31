![Deploy Status](https://github.com/KhushiKachhawaha14/My-DevOps-Mentor/actions/workflows/deploy.yml/badge.svg)

# 🤖 My-DevOps-Mentor

**An AI-powered, serverless mentorship bot that turns GitHub activity into actionable DevOps learning missions.**

## 🏗️ Architecture & Workflow

This project evolved from a local Flask prototype into a production-ready, cloud-native application.

```Plaintext
[ GitHub Event ] ➔ [ AWS API Gateway ] ➔ [ AWS Lambda (Docker) ] ➔ [ Gemini AI ]
                                               ▲
                                               │ (CI/CD Pipeline)
                                        [ GitHub Actions ] ➔ [ Amazon ECR ]
```

- **Runtime**: AWS Lambda (Serverless Docker Container)
- **AI Engine**: Google Gemini 1.5 Flash
- **CI/CD**: GitHub Actions with OIDC Federation
- **Container Registry**: Amazon ECR
- **IaC**: Terraform (Infrastructure as Code)

## ⚡ Engineering Challenges Overcome

### 1. Keyless Cloud Authentication (OIDC)

I implemented **OpenID Connect (OIDC)** to eliminate the need for long-lived AWS Access Keys. This involved configuring IAM Trust Policies to allow GitHub Actions to securely assume temporary roles.

### 2. Containerized CI/CD Pipeline

Built a robust pipeline that automates the Docker build process, pushes images to Amazon ECR, and triggers a rolling update to the AWS Lambda function on every push to `main`.

### 3. Automated FinOps (Cost Management)

To maintain the project within the AWS Free Tier, I implemented **AWS Budgets** with automated threshold alerts, ensuring zero-cost operations while maintaining 24/7 availability.

## 🛠️ Tech Stack

- **Backend:** Python / Flask
- **Cloud:** AWS (Lambda, ECR, IAM, API Gateway)
- **DevOps:** GitHub Actions, Docker, Terraform
- **AI:** Google Gemini API
- **CI/CD:** GitHub Actions with OIDC Authentication
- **Containerization:** Docker
- **Security:** IAM Role Federation (Keyless Auth)

## 🚀 Deployment Pipeline

The project uses a fully automated CI/CD pipeline:

- **Build**: Docker image is built on every push to main.

- **Push**: Image is pushed to Amazon ECR.

- **Deploy**: AWS Lambda is updated to pull the latest image immediately.

---
