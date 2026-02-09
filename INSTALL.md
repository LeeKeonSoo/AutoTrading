# 🔧 Installation & Setup Guide

## Windows에서 실행하기

### Step 1: Python 확인

```cmd
python --version
```

Python 3.11 이상이 필요합니다. 없다면 [python.org](https://www.python.org/downloads/)에서 설치하세요.

### Step 2: 프로젝트 다운로드

프로젝트 폴더로 이동:
```cmd
cd C:\Users\ksl1165\Desktop\Code\Projects\AutoTrading
```

### Step 3: 가상환경 생성 및 활성화

```cmd
python -m venv venv
venv\Scripts\activate
```

✅ 활성화되면 프롬프트에 `(venv)` 표시가 나타납니다.

### Step 4: 의존성 설치

**⚠️ 중요: 먼저 이전 패키지 제거**

```cmd
pip uninstall google-generativeai -y
pip install -r requirements.txt
```

설치 시간: 약 2-3분

### Step 5: API 키 설정

```cmd
copy .env.example .env
notepad .env
```

필수 설정:
```env
GEMINI_API_KEY=your_gemini_key_here
BINANCE_API_KEY=your_binance_key
BINANCE_API_SECRET=your_binance_secret
BINANCE_DEMO_MODE=true
```

### Step 6: 테스트 실행

```cmd
python run_test.py
```

예상 출력:
```
Testing Gemini Client...
✅ Gemini client working!
```

---

## macOS/Linux에서 실행하기

### Step 1-2: Python & 프로젝트

```bash
cd /path/to/AutoTrading
python3 --version
```

### Step 3: 가상환경

```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 4: 의존성 설치

```bash
pip uninstall google-generativeai -y
pip install -r requirements.txt
```

### Step 5: API 키

```bash
cp .env.example .env
nano .env  # or vim/code .env
```

### Step 6: 테스트

```bash
python run_test.py
```

---

## 실행 방법

### 🧪 개별 컴포넌트 테스트

**Windows:**
```cmd
python run_test.py
python -m src.config.settings
python -m src.data.binance_client
python -m src.strategy.llm_strategy
```

**macOS/Linux:**
```bash
python3 run_test.py
python3 -m src.config.settings
python3 -m src.data.binance_client
python3 -m src.strategy.llm_strategy
```

### 🚀 봇 실행

**Windows:**
```cmd
python main.py
```

**macOS/Linux:**
```bash
python3 main.py
```

---

## 문제 해결

### 1. "ModuleNotFoundError: No module named 'src'"

**해결 방법 A: run_test.py 사용 (권장)**
```cmd
python run_test.py
```

**해결 방법 B: Python path 설정**
```cmd
set PYTHONPATH=%CD%
python src/llm/gemini_client.py
```

**해결 방법 C: 모듈로 실행**
```cmd
python -m src.llm.gemini_client
```

### 2. "FutureWarning: google.generativeai deprecated"

**이미 해결됨!** 새 버전으로 업데이트했습니다.

다시 설치:
```cmd
pip uninstall google-generativeai -y
pip install -r requirements.txt --upgrade
```

### 3. "No module named 'google.genai'"

```cmd
pip install google-genai --upgrade
```

### 4. 가상환경이 활성화 안 됨

**Windows:**
- PowerShell 사용 중이라면: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
- 그 다음: `venv\Scripts\activate`

**macOS/Linux:**
```bash
source venv/bin/activate
```

### 5. "Gemini API key not configured"

`.env` 파일 확인:
- 따옴표 없이 키를 입력했는지 확인
- 공백이 없는지 확인
- 키가 `AIza...`로 시작하는지 확인

### 6. Binance 연결 실패

데모 모드 사용 시:
- `BINANCE_DEMO_MODE=true` 확인
- Binance API 키가 올바른지 확인
- API 키에 거래 권한이 활성화되어 있는지 확인

---

## 업그레이드 가이드

기존 설치를 업그레이드하려면:

```cmd
# 1. 가상환경 활성화
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# 2. 이전 패키지 제거
pip uninstall google-generativeai -y

# 3. 새 패키지 설치
pip install -r requirements.txt --upgrade

# 4. 테스트
python run_test.py
```

---

## 다음 단계

설치 완료 후:
1. ✅ `python run_test.py` - 테스트 통과 확인
2. 📝 `.env` 파일 설정 - API 키 입력
3. 🚀 `python main.py` - 봇 실행

**완료!** 🎉
