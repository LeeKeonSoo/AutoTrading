# 🔄 Changelog: Testnet → Demo Mode & Gemini Model Update

## Date: 2026-02-08

## Summary of Changes

이 업데이트는 두 가지 주요 변경사항을 반영합니다:
1. **Binance Testnet 종료** → Demo Mode로 전환
2. **Gemini 모델 업데이트** → `gemini-3-flash-preview` (최신 모델)

---

## 📋 변경된 파일 목록

### 1. 설정 파일
- ✅ `.env.example`
  - `BINANCE_TESTNET=true` → `BINANCE_DEMO_MODE=true`
  - `GEMINI_MODEL=gemini-2.0-flash-exp` → `GEMINI_MODEL=gemini-3-flash-preview`
  - 테스트넷 종료 안내 주석 추가

### 2. 핵심 코드 파일
- ✅ `src/config/settings.py`
  - 필드명 변경: `binance_testnet` → `binance_demo_mode`
  - 메서드 변경: `is_testnet()` → `is_demo_mode()`
  - Gemini 기본 모델: `gemini-3-flash-preview`
  - `print_summary()` 출력 업데이트

- ✅ `src/data/binance_client.py`
  - 생성자 파라미터: `testnet` → `demo_mode`
  - 테스트넷 URL 설정 제거 (더 이상 필요 없음)
  - 데모 모드 경고 메시지 추가
  - 테스트 코드 업데이트: `BinanceClient(testnet=True)` → `BinanceClient(demo_mode=True)`

- ✅ `src/data/indicators.py`
  - 테스트 코드 업데이트: `BinanceClient(testnet=True)` → `BinanceClient(demo_mode=True)`

### 3. 문서 파일
- ✅ `README.md`
  - LLM 변경: "Claude" → "Gemini"
  - API 문서 링크: Anthropic → Google Gemini
  - 모든 testnet 참조 → demo mode로 변경
  - API 키 가이드 업데이트

- ✅ `QUICKSTART.md`
  - Binance testnet 가입 안내 → Binance API 키 생성 안내
  - 설정 예제 업데이트
  - 트러블슈팅 섹션 업데이트

- ✅ `INSTALL.md`
  - 테스트넷 참조 → 데모 모드로 변경
  - 환경 설정 가이드 업데이트

---

## 🔍 주요 변경 사항 상세

### Demo Mode 작동 방식

**이전 (Testnet):**
```python
# Binance testnet 서버로 연결
exchange = ccxt.binance({
    'urls': {
        'api': 'https://testnet.binance.vision/api'
    }
})
```

**현재 (Demo Mode):**
```python
# 동일한 Binance API를 사용하지만, 실제 주문을 실행하지 않음
if self.demo_mode:
    logger.warning("⚠️  Demo mode enabled - No real orders will be placed!")
# 주문 실행 시 demo_mode이면 실제 주문을 보내지 않고 시뮬레이션만 수행
```

### Gemini 모델 변경

**이전:**
- `gemini-2.0-flash-exp` (실험 모델)

**현재:**
- `gemini-3-flash-preview` (최신 안정 모델)

---

## ✅ 검증 체크리스트

업데이트 후 다음을 확인하세요:

### 환경 설정 확인
- [ ] `.env` 파일에서 `BINANCE_TESTNET` → `BINANCE_DEMO_MODE` 변경
- [ ] `GEMINI_MODEL=gemini-3-flash-preview` 설정 확인
- [ ] API 키가 올바르게 설정되어 있는지 확인

### 코드 실행 확인
```bash
# 1. 기본 테스트
python run_test.py

# 2. 설정 확인
python -m src.config.settings

# 3. Binance 클라이언트 테스트
python -m src.data.binance_client

# 4. Gemini 클라이언트 테스트
python -m src.llm.gemini_client
```

### 예상 출력
```
🤖 Auto Trading Bot - Configuration Summary
============================================================
Trading Mode:     BACKTEST
Market Type:      SPOT
Demo Mode:        True (Paper Trading)  ← 이 부분 확인!
Symbol:           BTC/USDT
...
LLM Model:        gemini-3-flash-preview  ← 이 부분 확인!
```

---

## 🚨 주의사항

### 1. 실거래 전환 시
Demo Mode를 비활성화하고 실거래를 시작할 때:
```env
BINANCE_DEMO_MODE=false  # 실제 주문 실행
TRADING_MODE=live        # 라이브 거래 모드
```

### 2. API 키 권한
- Demo mode에서도 API 키에 거래 권한이 필요합니다
- Binance에서 "Enable Spot & Margin Trading" 활성화 필수

### 3. Gemini 모델 요금
- `gemini-3-flash-preview`는 Google AI Studio에서 무료 티어 제공
- 요금제 확인: https://ai.google.dev/pricing

---

## 🔄 이전 버전으로 되돌리기

만약 문제가 발생하면 Git에서 이전 버전으로 되돌릴 수 있습니다:

```bash
git log --oneline  # 커밋 히스토리 확인
git checkout <commit-hash>  # 특정 커밋으로 되돌리기
```

---

## 📞 문제 해결

### "No module named 'loguru'" 오류
```bash
pip install -r requirements.txt --upgrade
```

### "Binance connection failed" 오류
1. API 키 확인
2. `BINANCE_DEMO_MODE=true` 설정 확인
3. 인터넷 연결 확인

### "Gemini API error" 오류
1. API 키 확인
2. 모델명이 `gemini-3-flash-preview`인지 확인
3. API 할당량 확인

---

## ✨ 다음 단계

1. ✅ 업데이트 완료 확인
2. 🧪 `python run_test.py`로 테스트
3. 📊 백테스팅 실행
4. 💰 페이퍼 트레이딩으로 검증
5. 🚀 준비되면 실거래 시작

---

**업데이트 완료!** 🎉

모든 코드와 문서가 최신 상태로 업데이트되었습니다.
