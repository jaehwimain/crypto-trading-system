#!/bin/bash

echo "🚀 Google Cloud 배포 시작..."

# 프로젝트 ID 설정
read -p "Google Cloud 프로젝트 ID 입력: " PROJECT_ID
read -p "Telegram Bot Token 입력: " TELEGRAM_TOKEN
read -p "Telegram Chat ID 입력: " TELEGRAM_CHAT_ID
read -p "배포 지역 선택 (asia-northeast1): " REGION
REGION=${REGION:-asia-northeast1}

# gcloud 설정
gcloud config set project $PROJECT_ID

# 1. API 활성화
echo "📡 필요한 API 활성화 중..."
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  cloudscheduler.googleapis.com \
  secretmanager.googleapis.com \
  artifactregistry.googleapis.com

# 2. Cloud Run 배포
echo "🐳 Cloud Run 배포 중..."
gcloud run deploy crypto-bot \
  --source . \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 512Mi \
  --timeout 3600 \
  --set-env-vars TELEGRAM_TOKEN=$TELEGRAM_TOKEN,TELEGRAM_CHAT_ID=$TELEGRAM_CHAT_ID \
  --no-gen2

# Cloud Run URL 가져오기
CLOUD_RUN_URL=$(gcloud run services describe crypto-bot --region $REGION --format='value(status.url)')
echo "✅ Cloud Run 배포 완료: $CLOUD_RUN_URL"

# 3. Cloud Scheduler 설정 (5분마다 실행)
echo "⏰ Cloud Scheduler 설정 중..."

# 기존 job 삭제 (있으면)
gcloud scheduler jobs delete crypto-bot-scheduler --quiet 2>/dev/null || true

# 새 job 생성
gcloud scheduler jobs create http crypto-bot-scheduler \
  --schedule="*/5 * * * *" \
  --time-zone="Asia/Seoul" \
  --uri="$CLOUD_RUN_URL" \
  --http-method=POST \
  --location=$REGION

echo "✅ Cloud Scheduler 설정 완료!"

echo ""
echo "🎉 배포 완료!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📍 Cloud Run URL: $CLOUD_RUN_URL"
echo "🔄 실행 주기: 5분마다"
echo "📊 모의투자 결과: data/simulations/ 에 저장"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
