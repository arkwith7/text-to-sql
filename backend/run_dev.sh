#!/bin/bash
# 개발 서버 실행 스크립트
# --reload: 코드 변경 시 자동 리로드
# --reload-delay: 리로드 전 1초 지연 (CancelledError 방지)
uvicorn main:app --host 0.0.0.0 --port 8000 --reload --reload-delay 1 