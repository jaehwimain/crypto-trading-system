# Python 3.11 slim 이미지 사용 (가볍고 빠름)
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필수 도구 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# TA-Lib 라이브러리 설치 (기술 지표 계산용)
RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz && \
    tar -xzf ta-lib-0.4.0-src.tar.gz && \
    cd ta-lib && \
    ./configure --prefix=/usr && \
    make && \
    make install && \
    cd .. && \
    rm -rf ta-lib ta-lib-0.4.0-src.tar.gz && \
    ldconfig

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 환경변수 설정
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Cloud Run은 $PORT 환경변수에서 포트를 읽음
EXPOSE 8080

# gunicorn으로 메인 애플리케이션 실행
CMD exec gunicorn --bind :$PORT --workers 1 --timeout 3600 main:run_trading_bot
