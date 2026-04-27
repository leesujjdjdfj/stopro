# StoPro

StoPro는 개인 투자자가 매일 관심종목을 점검하고, 보유 종목의 위험 구간을 관리하기 위한 개인용 주식 분석 웹앱입니다. 화면만 있는 데모가 아니라 FastAPI 백엔드에서 `yfinance`와 한국투자증권 Open API 데이터를 조회하고, 기술적 지표, 손익비, 포지션 사이징, 백테스트 요약을 계산합니다.

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

## 주요 기능

- 실제 종목 시세 및 히스토리 조회
- RSI, MACD, Stochastic, MA20/60/200, ATR, Bollinger Band, Volume Ratio 계산
- 매수 후보, 분할 접근, 관망, 주의, 회피 판단
- 진입가, 목표가, 손절가, 무효화 조건 계산
- 투자금과 리스크 성향 기준 권장 수량 계산
- 목표/손절 손익 시뮬레이션과 R:R 계산
- 리스크 점수와 위험 요인 분해
- 관심종목, 보유종목, 가격 알림, 투자 메모 저장
- 분석 스냅샷 저장
- 최근 2년 규칙 기반 백테스트 요약
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
```

실전투자 도메인을 사용할 경우 `KIS_BASE_URL=https://openapi.koreainvestment.com:9443`로 설정합니다. KIS 토큰은 1분당 1회 발급 제한이 있어 `.kis_token_cache.json`에 로컬 캐시되며, 이 파일은 git에 포함하지 않습니다.

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
```

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

KIS Open API와 `yfinance` 모두 무료/개인용 데이터 사용 조건, 호출 제한, 누락, 정정 가능성이 있습니다. 일부 종목은 기본적 지표가 비어 있을 수 있고, 국내 종목의 기본적 지표는 현재 보조 데이터가 부족할 수 있습니다. StoPro는 모든 분석 결과에 데이터 품질과 캐시 사용 여부를 함께 제공합니다.

## 향후 개선 가능 기능

- 사용자별 여러 포트폴리오 분리
- 배당/실적 캘린더 보조 정보
- CSV 가져오기/내보내기
- 더 정교한 백테스트 조건 설정
- 알림 조건의 로컬 브라우저 알림
- 한국 주식용 거래대금/수급 보조 지표
