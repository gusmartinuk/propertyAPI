up:
	docker compose up -d --build

down:
	docker compose down

contract-test:
	docker compose run --rm api bash /app/scripts/contract_test.sh
