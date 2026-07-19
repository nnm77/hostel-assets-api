.PHONY: install generate migrate dev docker-up docker-down test lint

install:
	pip install -r requirements.txt

generate:
	prisma generate

migrate:
	prisma db push

dev:
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

docker-up:
	docker-compose up --build -d

docker-down:
	docker-compose down

test:
	pytest tests/ -v

lint:
	ruff check .
