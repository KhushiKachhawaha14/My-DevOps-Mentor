![Deploy Status](https://github.com/KhushiKachhawaha14/My-DevOps-Mentor/actions/workflows/deploy.yml/badge.svg)

# 🤖 My-DevOps-Mentor
 > An AI-powered, serverless mentorship bot that turns GitHub activity into actionable DevOps learning missions.

## 🏗️ Architecture & Workflow
This project evolved from a local Flask prototype into a production-ready, cloud-native application.
```Plaintext
[ GitHub Event ] ➔ [ AWS API Gateway ] ➔ [ AWS Lambda (Docker) ] ➔ [ Gemini AI ]
                                               ▲
                                               │ (CI/CD Pipeline)
                                        [ GitHub Actions ] ➔ [ Amazon ECR ]
```
## 🛠️ Tech Stack
| Component | Technology |
| :--- | :--- |
| **Cloud Provider** | AWS (Lambda, API Gateway, ECR) |
| **AI Engine** | Google Gemini 1.5 Flash |
| **CI/CD** | GitHub Actions with OIDC Authentication |
| **Containerization** | Docker |
| **Security** | IAM Role Federation (Keyless Auth) |

## ⚡ Engineering Challenges & Solutions
**1. Zero-Trust Security with OIDC**
**Problem**: Storing permanent AWS Access Keys in GitHub is a major security risk.

**Solution**: Implemented OpenID Connect (OIDC) to allow GitHub Actions to securely assume a temporary IAM role. This eliminated the need for static secrets.

**2. Containerized Serverless Deployment**
**Problem**: Managing Python dependencies in Lambda can be brittle.

**Solution**: Packaging the bot as a Docker image and pushing it to Amazon ECR. This ensures the execution environment is identical from dev to prod.

**3. Cost Management & Monitoring**
**Problem**: Unexpected cloud costs can occur in event-driven architectures.

**Solution**: Configured AWS Budgets with automated email alerts at 85% of actual spend to maintain Free Tier compliance.

## 🚀 Deployment Pipeline
The project uses a fully automated CI/CD pipeline:

- **Build**: Docker image is built on every push to main.

- **Push**: Image is pushed to Amazon ECR.

- **Deploy**: AWS Lambda is updated to pull the latest image immediately.

