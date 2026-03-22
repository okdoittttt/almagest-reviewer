# Stage 1: 프론트엔드 빌드
FROM node:22-alpine AS frontend-builder
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: 백엔드 + 프론트엔드 통합
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 프론트엔드 빌드 결과물 복사
COPY --from=frontend-builder /frontend/dist ./frontend/dist

RUN chmod +x entrypoint.sh

EXPOSE 8000

ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV PORT=8000

CMD ["sh", "entrypoint.sh"]
