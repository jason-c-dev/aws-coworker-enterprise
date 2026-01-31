# Security Pillar

## Overview
The Security pillar focuses on protecting information, systems, and assets while delivering business value through risk assessments and mitigation strategies. It encompasses how you manage identity and access, protect infrastructure, and detect and respond to security events. Security is a shared responsibility between AWS and customers, requiring a defense-in-depth approach.

## Design Principles
- Implement a strong identity foundation
- Enable traceability
- Apply security at all layers
- Automate security best practices
- Protect data in transit and at rest
- Keep people away from data
- Prepare for security events

## Best Practices

### Identity and Access Management
- Use AWS Identity and Access Management (IAM) for least privilege access
- Implement multi-factor authentication (MFA) for all users
- Use temporary security credentials instead of long-term access keys
- Implement federated access with AWS Single Sign-On (AWS SSO)
- Regularly audit and review IAM permissions
- Separate duties and responsibilities

### Infrastructure Protection
- Use AWS VPC for network isolation
- Implement security groups and network ACLs
- Use AWS WAF to protect web applications
- Implement VPN or AWS Direct Connect for secure network connectivity
- Deploy in multiple Availability Zones for resilience
- Use VPC Flow Logs to monitor network traffic

### Data Protection
- Enable encryption for data at rest (EBS, S3, RDS)
- Use TLS for data in transit
- Implement key management with AWS KMS
- Use S3 Block Public Access to prevent accidental exposure
- Enable versioning and MFA Delete on S3 buckets
- Classify and tag sensitive data

### Detection and Response
- Enable AWS CloudTrail for API auditing
- Use Amazon GuardDuty for threat detection
- Implement Amazon Security Hub for security findings
- Create response procedures for security incidents
- Use AWS Config for compliance monitoring
- Enable AWS Lambda for automated response actions

### Compliance
- Understand compliance requirements for your industry
- Use AWS Artifact for compliance documentation
- Implement tagging strategy for compliance tracking
- Regular security assessments and penetration testing
- Document security controls and evidence

## Key AWS Services
| Service | How It Supports This Pillar |
|---------|----------------------------|
| AWS IAM | Identity and access management with fine-grained permissions |
| Amazon VPC | Network isolation and segmentation |
| AWS KMS | Key management for encryption |
| AWS Secrets Manager | Secure storage and rotation of secrets |
| AWS WAF | Web application firewall protection |
| Amazon GuardDuty | Threat detection and monitoring |
| AWS Security Hub | Centralized security findings and compliance |
| AWS CloudTrail | API call logging and auditing |
| AWS Config | Configuration compliance tracking |
| AWS Firewall Manager | Centralized firewall management |
| Amazon Inspector | Vulnerability scanning |
| AWS Certificate Manager | SSL/TLS certificate management |

## Common Anti-Patterns
- Hardcoding credentials or secrets in code
- Using overly permissive IAM policies
- Disabling MFA for convenience
- Lack of encryption for sensitive data
- No monitoring or logging of API calls
- Ignoring security findings and alerts
- Insufficient network segmentation
- Manual, inconsistent security controls
- Single point of failure for authentication
- No incident response plan

## Assessment Questions
- How do you manage access to your AWS environment?
- How do you define and enforce authentication mechanisms?
- How do you monitor and log activity in your AWS environment?
- How do you protect your data in transit and at rest?
- How do you implement infrastructure protection?
- How do you manage secrets and credentials?
- What incident response processes do you have in place?
- How do you validate compliance with security policies?

## Related Skills
- AWS IAM Deep Dive
- AWS VPC and Network Security
- AWS Data Encryption Strategies
- AWS Compliance and Governance
- AWS Incident Response
- AWS Threat Detection and Response
