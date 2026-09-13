# Deployment Guide

BusNBox AI is designed to run as an independent, stateless microservice.

---

## 1. Environments

### 1.1 Local Development
Run BusNBox AI locally alongside Spring Boot and React:
- **BusNBox AI**: `http://localhost:8000`
- **Spring Boot Gateway**: `http://localhost:8080`
- **React Frontend**: `http://localhost:5173`

```bash
cd backend
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 1.2 Enterprise Staging & Production
Deploy BusNBox AI into your private Kubernetes cluster, Docker Swarm, or cloud container service (AWS ECS, Google Cloud Run, Azure Container Apps):

- Place BusNBox in a **private subnet**.
- Only the **Spring Boot backend** has network access to port `8000`.
- Browser clients interact only with the company's Spring Boot gateway.

---

## 2. Docker Deployment

A production `Dockerfile` is provided in the root directory.

### Build
```bash
docker build -t busnbox-ai:1.0.0 .
```

### Run
```bash
docker run -d \
  --name busnbox-ai \
  -p 8000:8000 \
  -e GEMINI_API_KEY="your-gemini-api-key" \
  -e INVENTORY_PROVIDER="company" \
  -e INVENTORY_API_BASE_URL="https://inventory.internal.yourcompany.com" \
  busnbox-ai:1.0.0
```

---

## 3. Kubernetes Deployment Example

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: busnbox-ai
spec:
  replicas: 2
  selector:
    matchLabels:
      app: busnbox-ai
  template:
    metadata:
      labels:
        app: busnbox-ai
    spec:
      containers:
      - name: busnbox-ai
        image: your-registry.com/busnbox-ai:1.0.0
        ports:
        - containerPort: 8000
        env:
        - name: GEMINI_API_KEY
          valueFrom:
            secretKeyRef:
              name: busnbox-secrets
              key: gemini-api-key
        - name: INVENTORY_PROVIDER
          value: "company"
        - name: INVENTORY_API_BASE_URL
          value: "http://company-inventory-service:9000"
        livenessProbe:
          httpGet:
            path: /api/v1/health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /api/v1/ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
```
