#!/bin/bash
celery -A app.celery_app worker --loglevel=info &
celery -A app.celery_app beat --loglevel=info &
uvicorn app.main:app --host 0.0.0.0 --port 10000