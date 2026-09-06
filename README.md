🏥 NigerCare Medical Centre — Cloud-Native EMR System

A secure, scalable, and cost-optimized Electronic Medical Records (EMR) platform designed for NigerCare Medical Centre and built using modern cloud-native, serverless, DevOps, and Infrastructure-as-Code practices.

The platform is designed to centralize patient records, appointments, prescriptions, notifications, document management, authentication, auditing, and healthcare workflows while providing a foundation for future mobile applications, analytics, AI-assisted healthcare, and telemedicine capabilities.

---

🚀 Project Overview

NigerCare Medical Centre EMR is a cloud-native healthcare management platform designed around a serverless AWS architecture.

The system separates the application into a modern frontend, Python backend services, infrastructure-as-code, and automated CI/CD workflows.

The project focuses heavily on:

- ☁️ AWS Cloud Architecture
- 🏗️ Infrastructure as Code
- 🔄 DevOps & CI/CD Automation
- 🐳 Docker Containerization
- 🔐 Cloud Security
- 📊 Monitoring & Auditing
- 🗄️ NoSQL Database Architecture
- 💰 AWS Free-Tier Cost Optimization
- 🏥 Healthcare Data Management
- 📱 Future Mobile Application Support
- 🤖 Future AI & Analytics Integration

---

🏗️ Architecture

The development architecture is based on AWS serverless technologies to minimize infrastructure management and operational costs while allowing the platform to scale as usage increases.

Core AWS Services

Service| Purpose
AWS Lambda| Serverless backend application logic
Amazon API Gateway| Secure REST API layer
Amazon DynamoDB| Patient and application data
Amazon S3| Medical documents and file storage
Amazon Cognito| Authentication and identity management
IAM| Access control and least-privilege permissions
Amazon CloudWatch| Application monitoring and logging
AWS CloudTrail| AWS activity and audit logging
Route 53| DNS management
AWS Certificate Manager| HTTPS/SSL certificates
SNS/SES| SMS and email notifications

---

🧩 Application Components

Frontend

The frontend provides dedicated interfaces for different healthcare users.

Patient Portal

Patients can access:

- Personal profile
- Medical records
- Appointments
- Prescriptions
- Notifications
- Uploaded documents

Doctor Portal

Doctors can manage:

- Patient information
- Appointments
- Medical records
- Prescriptions
- Patient documents
- Notifications

Admin Portal

Administrators can manage:

- Users
- Roles
- System configuration
- Audit information
- Operational monitoring

The frontend is designed to be responsive and suitable for desktop and mobile access.

---

⚙️ Backend

The backend is implemented using Python and AWS Lambda.

Backend responsibilities include:

- Patient management
- Doctor management
- Appointment management
- Prescription management
- Notification processing
- Authentication and authorization
- Audit logging
- Secure document operations
- API request validation

The serverless approach allows backend functions to scale automatically without maintaining traditional always-running application servers.

---

🗄️ Database Architecture

The application uses Amazon DynamoDB instead of a traditional relational database.

Core data domains include:

- Patients
- Doctors
- Appointments
- Prescriptions
- Notifications
- Audit Logs

The database architecture considers:

- Partition keys
- Sort keys
- Global Secondary Indexes (GSIs)
- Access patterns
- Efficient querying
- On-demand capacity
- Scalability
- Cost optimization

This approach is designed to support the expected development workload while providing a path to significantly larger workloads in the future.

---

📁 Secure Medical File Storage

Amazon S3 is used for healthcare-related documents such as:

- Medical scans
- Prescriptions
- Patient documents
- Other authorized healthcare files

Security considerations include:

- Server-side encryption
- Private S3 buckets
- IAM-controlled access
- Pre-signed URLs
- Upload validation
- Lifecycle policies
- Restricted public access

Medical files are not intended to be exposed through publicly accessible S3 URLs.

---

🔐 Authentication & Security

The platform uses Amazon Cognito for identity management and JWT-based authentication.

Role-based access control is designed around:

- 👨‍⚕️ Doctors
- 👩‍⚕️ Nurses
- 🧑‍💼 Administrators
- 🧑‍🤝‍🧑 Patients

Security principles include:

- Least-privilege IAM
- JWT authorization
- Secure API access
- Input validation
- API throttling
- CORS configuration
- Encrypted storage
- Audit logging
- Secure file access
- Environment-based configuration

The architecture is designed with NDPR-aware healthcare data protection and HIPAA-inspired security principles in mind.

---

🏗️ Infrastructure as Code

The AWS infrastructure is managed using Terraform.

Infrastructure is organized into reusable components covering areas such as:

terraform/
├── api_gateway/
├── cognito/
├── dynamodb/
├── iam/
├── lambda/
├── monitoring/
├── route53/
├── s3/
└── security/

Terraform provides:

- Repeatable deployments
- Infrastructure version control
- Environment consistency
- Automated infrastructure changes
- Easier disaster recovery
- Reduced configuration drift

---

🔄 CI/CD & DevOps

The project includes GitHub Actions for automated software and infrastructure validation.

The CI/CD workflow is designed to perform checks such as:

Code Push
    ↓
GitHub Actions
    ↓
Terraform Format
    ↓
Terraform Validate
    ↓
Application Tests
    ↓
Build Frontend
    ↓
Build Backend
    ↓
Docker Build
    ↓
Security Checks
    ↓
Terraform Plan
    ↓
Deployment
    ↓
Post-Deployment Validation

This approach helps detect infrastructure, application, configuration, and deployment problems before they reach the target environment.

---

🐳 Docker

Docker support is included to provide consistent development and testing environments.

The repository includes:

docker-compose.yml

Docker is used to standardize the local application environment and reduce differences between developer machines and deployment environments.

The container architecture provides a future migration path toward container platforms such as:

- Amazon ECS
- Amazon EKS
- Kubernetes

without requiring the application to be completely redesigned.

---

📊 Monitoring & Auditing

Operational visibility is provided through AWS monitoring and auditing services.

CloudWatch

Used for:

- Lambda logs
- Application monitoring
- Metrics
- Alarms
- Operational troubleshooting

CloudTrail

Used for:

- AWS API activity
- Security auditing
- Investigation
- Compliance-related visibility

Audit logging is particularly important because the system handles sensitive healthcare information.

---

💰 Cost Optimization

The development environment is intentionally designed around AWS Free Tier and serverless-first principles.

Cost optimization strategies include:

- Serverless Lambda architecture
- DynamoDB on-demand capacity
- S3-based storage
- Minimal always-on infrastructure
- Controlled CloudWatch retention
- Avoiding unnecessary EC2 infrastructure
- Avoiding NAT Gateway where possible
- Automated infrastructure management
- Cost monitoring and budget alerts

The objective is to maintain a near-$0 development environment where AWS Free Tier eligibility allows, while avoiding unnecessary recurring infrastructure costs.

«Actual AWS charges depend on account eligibility, current AWS pricing, data transfer, usage volume, and Free Tier limits.»

---

📈 Scalability

The architecture is designed to support an initial workload of approximately:

150–300 daily users

The serverless components can scale independently as demand increases.

Potential scaling path:

Development
     ↓
AWS Serverless
     ↓
Higher Traffic
     ↓
Event-Driven Architecture
     ↓
Containerized Services
     ↓
ECS / Kubernetes

The architecture therefore provides a foundation for gradually increasing infrastructure complexity only when the workload requires it.

---

🤖 Future AI Integration

The platform is designed with future AI capabilities in mind.

Potential future functionality includes:

- AI-assisted diagnostics
- Clinical decision-support tools
- Healthcare analytics
- Predictive analytics
- Automated reporting
- Intelligent patient insights

Potential AWS technologies include:

- Amazon Bedrock
- Amazon SageMaker
- Event-driven processing
- Analytics services
- Vector search technologies

AI functionality will be introduced as an additional layer rather than tightly coupling the core EMR system to a specific AI provider.

---

📱 Future Mobile Application

The backend APIs are designed to support a future Android application.

The planned mobile platform could provide:

- Patient access
- Appointment management
- Notifications
- Prescription access
- Secure document access
- Healthcare communication

The API-first architecture allows the web and mobile applications to consume the same backend services.

---

🔮 Future Roadmap

Planned capabilities include:

- [ ] Android mobile application
- [ ] Telemedicine
- [ ] AI diagnostic assistant
- [ ] Advanced healthcare analytics
- [ ] Automated reporting
- [ ] Enhanced monitoring dashboards
- [ ] Advanced disaster recovery
- [ ] Additional security automation
- [ ] Containerized production deployment
- [ ] Kubernetes/EKS migration when justified

---

🛠️ Technology Stack

Frontend

- React
- TypeScript
- Tailwind CSS

Backend

- Python
- AWS Lambda
- API Gateway

Database

- Amazon DynamoDB

Storage

- Amazon S3

Authentication

- Amazon Cognito
- JWT

Infrastructure

- Terraform
- AWS

DevOps

- Git
- GitHub
- GitHub Actions
- Docker
- Docker Compose

Monitoring & Security

- CloudWatch
- CloudTrail
- IAM
- AWS security services

---

📂 Repository Structure

.
├── .github/
│   └── workflows/
│
├── backend/
│   └── Python backend services
│
├── frontend/
│   └── React frontend application
│
├── terraform/
│   └── AWS infrastructure
│
├── docker-compose.yml
├── .gitignore
└── trust-policy.json

---

🎯 Project Goals

The primary goals of NigerCare Medical Centre EMR are to demonstrate how modern cloud technologies can be used to build a healthcare platform that is:

Secure → Scalable → Automated → Observable → Cost-Optimized → Maintainable

The project also serves as a practical demonstration of AWS Cloud Engineering, DevOps, Infrastructure as Code, Serverless Architecture, Docker, CI/CD, and Cloud Security.

---

👨‍💻 Engineering Focus

This project demonstrates practical experience in:

- AWS Cloud Engineering
- Serverless Architecture
- Infrastructure as Code
- Terraform
- DevOps
- CI/CD Automation
- Docker
- Python
- React
- DynamoDB
- Cloud Security
- IAM
- Authentication & Authorization
- Monitoring & Logging
- API Design
- Cost Optimization
- Production Deployment Planning

---

📌 Project Status

Development / Cloud-Native Implementation

The infrastructure and application are being developed with a strong emphasis on automated validation, secure deployment, maintainability, and future production scalability.

---

⚠️ Disclaimer

This project is a technical implementation and demonstration of a cloud-native EMR architecture. It should undergo appropriate clinical, security, legal, privacy, compliance, and operational reviews before being used with real patient data in a production healthcare environment.
