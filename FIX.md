# 🔧 빠른 수정 가이드

## 지금 발생한 오류 해결

### 문제 1: "google.generativeai deprecated" 경고
✅ **해결됨**: 새 `google-genai` 패키지로 업데이트

### 문제 2: "ModuleNotFoundError: No module named 'src'"
✅ **해결됨**: `run_test.py` 사용

---

## 👉 지금 바로 실행하기

### Windows (당신의 환경)

```cmd
cd C:\Users\ksl1165\Desktop\Code\Projects\AutoTrading

REM 1. 가상환경 활성화
venv\Scripts\activate

REM 2. 이전 패키지 제거
pip uninstall google-generativeai -y

REM 3. 새 패키지 설치
pip install -r requirements.txt --upgrade

REM 4. 테스트
python run_test.py

REM 5. 봇 실행
python main.py
```

---

## 빠른 체크리스트

- [ ] 프로젝트 폴더로 이동
- [ ] 가상환경 활성화 (`venv\Scripts\activate`)
- [ ] 이전 패키지 제거 (`pip uninstall google-generativeai -y`)
- [ ] 새 패키지 설치 (`pip install -r requirements.txt --upgrade`)
- [ ] `.env` 파일 설정 (API 키)
- [ ] 테스트 (`python run_test.py`)
- [ ] 봇 실행 (`python main.py`)

---

## 예상 출력

### ✅ 정상 실행:
```
Testing Gemini Client...
2026-02-08 14:30:00 | INFO     | GeminiClient initialized with model gemini-2.0-flash-exp (temp=0.7)
2026-02-08 14:30:01 | INFO     | Gemini API connection OK
✅ Gemini client working!
```

### ❌ 오류가 계속 나타난다면:

1. **가상환경 재생성**
```cmd
rmdir /s venv
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

2. **Python 경로 확인**
```cmd
where python
```
가상환경의 Python이 사용되는지 확인

3. **패키지 확인**
```cmd
pip list | findstr google
```
`google-genai`만 있어야 함 (`google-generativeai`는 없어야 함)

---

## 도움이 필요하면

1. 오류 메시지 전체를 복사
2. 다음 정보 함께 제공:
   - Python 버전 (`python --version`)
   - 설치된 패키지 (`pip list`)
   - 실행한 명령어
   - 전체 오류 로그

---

## 정상 작동 확인

```cmd
python run_test.py
```

✅ "Gemini client working!" 메시지가 나오면 성공!

이제 `python main.py`로 봇을 실행할 수 있습니다.
