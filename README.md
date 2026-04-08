# Local LLM API Gateway (FastAPI + Ollama)

Jetson Orin Nano에서 동작하는 로컬 LLM API 게이트웨이입니다.

이 서버는 Ollama 앞단에서 동작하며, 외부 클라이언트가 OpenAI 호환 API 형태로 로컬 모델을 호출할 수 있게 해줍니다.

코드 수정기능의 비용부담을 완화하기 위해 local llm을 api화하여 사용하려는 목적으로 만들었습니다.

## 핵심 기능

- FastAPI 기반 비동기 API 서버
- Ollama 연동 (`http://127.0.0.1:11434` 기본)
- OpenAI 호환 엔드포인트
  - `POST /v1/chat/completions`
- 모델 선택 지원 (`model` 필드)
- API Key 인증 (`Authorization: Bearer ...`)
- SSE 스트리밍 지원
- 요청 ID 및 기본 구조화 로깅

## 모델

기본 공개 모델(`model` 필드 값)은 아래 3개입니다.

- `qwen2.5-coder:3b`
- `qwen3:8b`
- `exaone-deep:2.4b`

`GET /v1/models`는 위 공개 모델 ID를 그대로 반환합니다.

참고: `exaone-deep:2.4b`는 응답 대기시간이 길어 기본 `OLLAMA_TIMEOUT=300` 환경에서 타임아웃이 잦을 수 있습니다. 필요하면 `OLLAMA_TIMEOUT` 값을 더 크게 설정해 주세요.

## 프로젝트 구조

```text
app/
  main.py
  core/
    config.py
    logging.py
    security.py
    errors.py
  api/
    routes/
      health.py
      models.py
      openai.py
  schemas/
    common.py
    openai.py
    ollama.py
  services/
    ollama_client.py
    model_registry.py
    response_mapper.py
    streaming.py
  middleware/
    request_id.py
README.md
requirements.txt
.env.example
```

## 사전 준비 (Jetson / Ubuntu)

1. Python 3.10+ 확인
2. Ollama 설치 및 실행
3. 모델 다운로드

```bash
ollama pull qwen2.5-coder:3b
ollama pull qwen3:8b
ollama pull exaone-deep:2.4b
```

Ollama 서버가 로컬에서 떠 있어야 합니다.

```bash
ollama serve
```

## 설치

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

환경 변수 파일 작성:

```bash
cp .env.example .env
```

## 환경 변수

기본값은 아래와 같습니다.

```env
HOST=0.0.0.0
PORT=8000
API_KEYS=sk-local-dev
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_TIMEOUT=300
OLLAMA_KEEP_ALIVE=15m
LOG_LEVEL=INFO

MODEL_QWEN_ALIAS=qwen2.5-coder:3b
MODEL_QWEN_NAME=qwen2.5-coder:3b
MODEL_QWEN3_ALIAS=qwen3:8b
MODEL_QWEN3_NAME=qwen3:8b
MODEL_EXAONE_ALIAS=exaone-deep:2.4b
MODEL_EXAONE_NAME=exaone-deep:2.4b
```

## 실행

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## API 예시

아래 예시에서 API 키는 `sk-local-dev`를 사용합니다.

Swagger docs 사용 시 인증 방법:

- `/docs` 우측 상단 `Authorize` 클릭
- `Value`에 API 키 입력 (예: `sk-local-dev`)
- Swagger가 `Authorization: Bearer <API_KEY>` 헤더를 자동 추가

### 1) Health

```bash
curl http://127.0.0.1:8000/healthz
```

### 2) Readiness (Ollama 연결 확인)

```bash
curl http://127.0.0.1:8000/readyz
```

### 3) 모델 목록

```bash
curl -H "Authorization: Bearer sk-local-dev" \
  http://127.0.0.1:8000/v1/models
```

### 4) Chat Completions - qwen2.5-coder:3b

```bash
curl -X POST http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-local-dev" \
  -d '{
    "model": "qwen2.5-coder:3b",
    "messages": [
      {"role": "system", "content": "You are a helpful Korean assistant."},
      {"role": "user", "content": "안녕"}
    ],
    "temperature": 0.2,
    "max_tokens": 256,
    "stream": false
  }'
```

### 5) Chat Completions - exaone-deep:2.4b

```bash
curl -X POST http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-local-dev" \
  -d '{
    "model": "exaone-deep:2.4b",
    "messages": [
      {"role": "user", "content": "Jetson에서 추론 속도 최적화 팁 알려줘"}
    ],
    "stream": false
  }'
```

### 6) Chat Completions 요청 명세 (중요)

`POST /v1/chat/completions`

필수 필드:

- `model` (string): 모델 alias (`qwen2.5-coder:3b`, `qwen3:8b`, `exaone-deep:2.4b`)
- `messages` (array, 최소 1개): 각 항목은 `{ "role": "system|user|assistant|tool", "content": "..." }`

선택 필드:

- `temperature` (number)
- `top_p` (number)
- `max_tokens` (integer)
- `stream` (boolean, 기본값 `false`)

최소 요청 예시(정상):

```json
{
  "model": "qwen2.5-coder:3b",
  "messages": [
    {
      "role": "user",
      "content": "파이썬으로 두 수의 합을 반환하는 함수만 작성해줘."
    }
  ],
  "stream": false
}
```

## 스트리밍 사용

- `POST /v1/chat/completions` + `"stream": true`

`stream` 값 의미:

- `false`: 응답이 모두 생성된 뒤 한 번에 JSON 반환 (`application/json`)
- `true`: 생성 중인 토큰 조각을 순차 전송 (`text/event-stream`, SSE)

응답은 `text/event-stream`으로 반환됩니다.

## 에러 형식

일관된 JSON 형식을 반환합니다.

```json
{
  "error": {
    "type": "invalid_request_error",
    "message": "..."
  }
}
```

주요 케이스:

- API 키 누락/불일치 (`401`)
- 모델 누락/형식 오류 (`400`)
- 지원하지 않는 모델 alias (`400`)
- Ollama 미가용 (`503`)
- Ollama 타임아웃 (`504`)

## 참고

- 이 프로젝트는 로컬 LLM API 게이트웨이 MVP입니다.
- DB, 사용자 계정, 과금, Redis, Docker/K8s 등은 포함하지 않습니다.
