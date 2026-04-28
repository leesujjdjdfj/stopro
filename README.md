# StoPro

StoPro는 개인 투자자가 매일 관심종목을 점검하고, 보유 종목의 위험 구간을 관리하기 위한 개인용 주식 분석 웹앱입니다. 화면만 있는 데모가 아니라 FastAPI 백엔드에서 `yfinance`와 한국투자증권 Open API 데이터를 조회하고, 기술적 지표, 손익비, 지지/저항, 백테스트 요약, 뉴스 기반 AI 분석을 계산합니다.

> 본 분석은 개인 참고용이며, 투자 판단과 책임은 사용자 본인에게 있습니다.

## 중요한 범위

- 자동매매 앱이 아닙니다.
- 주문 실행, 브로커 API 연동, 로그인, 소셜 기능은 없습니다.
- 분석 결과는 매수 강요가 아니라 리스크 중심의 판단 보조입니다.
- 무료 데이터는 누락, 정정 가능성이 있습니다.

## 기술 스택

- Frontend: Next.js App Router, TypeScript, Tailwind CSS, Recharts, Lucide React, Zustand, LocalStorage
- Backend: FastAPI, pandas, numpy, yfinance, SQLModel, SQLite
- Data: 한국 주식 현재가/일봉은 KIS Open API 우선, 해외 주식은 yfinance, USD/KRW는 `KRW=X` 우선 조회 후 `.env` fallback
- News/AI: GNews 또는 NewsAPI로 최근 뉴스를 수집하고, Groq 또는 OpenRouter로 투자 참고용 요약을 생성합니다. 키가 없거나 실패하면 rule-based fallback을 사용합니다.

## 주요 기능

- 실제 종목 시세 및 히스토리 조회
- RSI, MACD, Stochastic, MA20/60/200, ATR, Bollinger Band, Volume Ratio 계산
- 매수 후보, 분할 접근, 관망, 주의, 회피 판단
- 진입가, 목표가, 손절가, 무효화 조건 계산
- 가격 기준 진입가, 목표가, 손절가와 R:R 계산
- 리스크 점수와 위험 요인 분해
- 관심종목, 보유종목, 가격 알림, 투자 메모 저장
- 분석 스냅샷 저장
- 최근 2년 규칙 기반 백테스트 요약
- 최근 뉴스와 공시성 이슈 기반 AI 요약
- 데이터 품질과 캐시 여부 표시

## 프로젝트 구조

```txt
stopro/
  apps/
    api/   # FastAPI + SQLite + yfinance 분석 서버
    web/   # Next.js 모바일 우선 대시보드
```

## 환경변수

`apps/api/.env`

```env
USD_KRW=1350
CACHE_TTL_SECONDS=300
EXCHANGE_RATE_CACHE_TTL_SECONDS=1800
DATABASE_URL=sqlite:///./stopro.db

KIS_ENABLED=false
KIS_ENV=paper
KIS_APP_KEY=
KIS_APP_SECRET=
KIS_BASE_URL=https://openapivts.koreainvestment.com:29443
KIS_WS_URL=ws://ops.koreainvestment.com:31000
KIS_QUOTE_CACHE_TTL_SECONDS=5
KIS_TOKEN_CACHE_SECONDS=82800

GNEWS_API_KEY=
NEWS_API_KEY=
NEWS_PROVIDER=gnews

GROQ_API_KEY=
OPENROUTER_API_KEY=
AI_PROVIDER=groq
AI_MODEL=llama-3.1-8b-instant
```

실전투자 도메인을 사용할 경우 `KIS_BASE_URL=https://openapi.koreainvestment.com:9443`로 설정합니다.

KIS access token은 사용자가 매일 직접 발급할 필요가 없습니다. 백엔드의 `KISTokenManager`가 시세 조회용 access token을 자동 발급하고, 기본 23시간(`KIS_TOKEN_CACHE_SECONDS=82800`) 동안 서버 메모리에 재사용합니다. 토큰이 만료되었거나 KIS가 401/토큰 만료 응답을 반환하면 기존 토큰을 폐기하고 1회만 자동 재발급 후 재시도합니다. 주문, 매매, 계좌 API는 구현하지 않으며 시세 조회용 토큰만 관리합니다.

Vercel 배포 시에는 `stopro-api` 프로젝트의 Environment Variables에 `KIS_ENABLED`, `KIS_APP_KEY`, `KIS_APP_SECRET`, `KIS_BASE_URL`을 등록해야 합니다. `KIS_APP_SECRET`과 access token은 백엔드 환경에만 두고, 프론트 `.env`나 `NEXT_PUBLIC_` 변수로 노출하지 않습니다.

뉴스/AI 분석 키 발급:

- GNews: `https://gnews.io/`에서 API Key를 발급한 뒤 `GNEWS_API_KEY`에 입력합니다.
- NewsAPI: `https://newsapi.org/`에서 API Key를 발급한 뒤 `NEWS_API_KEY`에 입력합니다.
- Groq: `https://console.groq.com/keys`에서 API Key를 발급한 뒤 `GROQ_API_KEY`에 입력합니다.
- OpenRouter: `https://openrouter.ai/keys`에서 API Key를 발급한 뒤 `OPENROUTER_API_KEY`에 입력합니다.

API Key는 반드시 `apps/api/.env`에만 저장합니다. `NEXT_PUBLIC_` 접두사를 붙이지 말고 프론트 환경변수로 노출하지 않습니다.

`apps/web/.env.local`

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## 실행 방법

### Backend

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Windows PowerShell:

```powershell
cd apps/api
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Windows에서 `--reload`가 권한 문제로 멈추면 아래처럼 일반 실행을 사용합니다.

```powershell
cd apps/api
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

KIS 연결 테스트:

```powershell
cd apps/api
.venv\Scripts\python.exe app\test_kis.py 005930
.venv\Scripts\python.exe scripts\test_kis_token.py 005930
```

토큰 상태 확인:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/debug/kis/status
```

이 endpoint는 `configured`, `hasToken`, `expiresInSeconds`만 반환하며 access token 값은 절대 반환하지 않습니다.

### Frontend

```bash
cd apps/web
npm install
npm run dev
```

Windows에서 `next dev`가 멈추면 빌드 후 start 모드로 실행합니다.

```powershell
cd apps/web
npm run build
npm run start -- --hostname 127.0.0.1 --port 3000
```

브라우저에서 `http://localhost:3000`을 열면 `/dashboard`로 이동합니다.

## API 요약

- `GET /health`
- `GET /api/stocks/{ticker}/quote`
- `GET /api/stocks/{ticker}/history?period=1y`
- `POST /api/analyze`
- `GET /api/news/{ticker}`
- `POST /api/news-analysis`
- `GET /api/debug/kis/status`
- `POST /api/debug/kis/invalidate`
- `GET /api/dashboard`
- `GET /api/watchlist`
- `POST /api/watchlist`
- `DELETE /api/watchlist/{ticker}`
- `POST /api/watchlist/analyze-all`
- `GET /api/positions`
- `POST /api/positions`
- `PUT /api/positions/{id}`
- `DELETE /api/positions/{id}`
- `GET /api/alerts`
- `POST /api/alerts`
- `PUT /api/alerts/{id}`
- `DELETE /api/alerts/{id}`
- `GET /api/alerts/triggered`
- `GET /api/memos/{ticker}`
- `POST /api/memos`
- `GET /api/settings`
- `PUT /api/settings`

## 무료 데이터 한계

KIS Open API, `yfinance`, GNews, NewsAPI, Groq, OpenRouter 모두 무료/개인용 데이터 사용 조건, 호출 제한, 누락, 정정 가능성이 있습니다. 일부 종목은 기본적 지표가 비어 있을 수 있고, 국내 종목의 기본적 지표는 현재 보조 데이터가 부족할 수 있습니다. 뉴스 기반 AI 분석은 기사 제목과 요약을 기반으로 만든 참고용 해석이며, 원문 기사와 공시를 함께 확인해야 합니다. StoPro는 모든 분석 결과에 데이터 품질과 캐시 사용 여부를 함께 제공합니다.

## 향후 개선 가능 기능

- 사용자별 여러 포트폴리오 분리
- 배당/실적 캘린더 보조 정보
- CSV 가져오기/내보내기
- 더 정교한 백테스트 조건 설정
- 알림 조건의 로컬 브라우저 알림
- 한국 주식용 거래대금/수급 보조 지표
