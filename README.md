# Local LLM API Gateway (FastAPI + Ollama)

Jetson Orin Nano에서 동작하는 로컬 LLM API 게이트웨이입니다.

이 서버는 Ollama 앞단에서 동작하며, 외부 클라이언트가 OpenAI/Anthropic 호환 API 형태로 로컬 모델을 호출할 수 있게 해줍니다.

테스트 전 코드로, jetson 배포환경의 api 호출 테스트 예정.
nginx 같은 서버배포환경 세팅파일도 올릴지 고민중

## 핵심 기능

- FastAPI 기반 비동기 API 서버
- Ollama 연동 (`http://127.0.0.1:11434` 기본)
- OpenAI 호환 엔드포인트
	- `POST /v1/chat/completions`
- Anthropic 호환 엔드포인트
	- `POST /v1/messages`
- 모델 alias 선택 지원 (`model` 필드)
- API Key 인증 (`Authorization: Bearer ...`, `x-api-key`)
- SSE 스트리밍 지원
- 요청 ID 및 기본 구조화 로깅

## 모델 선택 방식

클라이언트는 공개 alias를 `model` 필드에 넣어 호출합니다.

- `qwen-chat` -> `qwen3.5:2b`
- `exaone-chat` -> `exaone3.5:2.4b`

`GET /v1/models`는 공개 alias만 반환합니다.

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
			anthropic.py
	schemas/
		common.py
		openai.py
		anthropic.py
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

예시:

```bash
ollama pull qwen3.5:2b
ollama pull exaone3.5:2.4b
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

MODEL_QWEN_ALIAS=qwen-chat
MODEL_QWEN_NAME=qwen3.5:2b
MODEL_EXAONE_ALIAS=exaone-chat
MODEL_EXAONE_NAME=exaone3.5:2.4b
```

## 실행

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## API 예시

아래 예시에서 API 키는 `sk-local-dev`를 사용합니다.

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

### 4) OpenAI 호환 - qwen-chat

```bash
curl -X POST http://127.0.0.1:8000/v1/chat/completions \
	-H "Content-Type: application/json" \
	-H "Authorization: Bearer sk-local-dev" \
	-d '{
		"model": "qwen-chat",
		"messages": [
			{"role": "system", "content": "You are a helpful Korean assistant."},
			{"role": "user", "content": "안녕"}
		],
		"temperature": 0.2,
		"max_tokens": 256,
		"stream": false
	}'
```

### 5) OpenAI 호환 - exaone-chat

```bash
curl -X POST http://127.0.0.1:8000/v1/chat/completions \
	-H "Content-Type: application/json" \
	-H "Authorization: Bearer sk-local-dev" \
	-d '{
		"model": "exaone-chat",
		"messages": [
			{"role": "user", "content": "Jetson에서 추론 속도 최적화 팁 알려줘"}
		],
		"stream": false
	}'
```

### 6) Anthropic 호환 - qwen-chat (x-api-key)

```bash
curl -X POST http://127.0.0.1:8000/v1/messages \
	-H "Content-Type: application/json" \
	-H "x-api-key: sk-local-dev" \
	-d '{
		"model": "qwen-chat",
		"system": "Respond in Korean.",
		"messages": [
			{"role": "user", "content": "안녕하세요"}
		],
		"max_tokens": 256,
		"stream": false
	}'
```

### 7) Anthropic 호환 - exaone-chat (Bearer)

```bash
curl -X POST http://127.0.0.1:8000/v1/messages \
	-H "Content-Type: application/json" \
	-H "Authorization: Bearer sk-local-dev" \
	-d '{
		"model": "exaone-chat",
		"messages": [
			{"role": "user", "content": "자기소개 해줘"}
		],
		"max_tokens": 128,
		"stream": false
	}'
```

## 스트리밍 사용

- OpenAI 호환: `POST /v1/chat/completions` + `"stream": true`
- Anthropic 호환: `POST /v1/messages` + `"stream": true`

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
