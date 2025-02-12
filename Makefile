include custom.mk

setup-env:
	@[ ! -f ./.env ] && cp ./.env.example ./.env || echo ".env file already exists."

start: ## Start the docker containers
	@echo "Starting the docker containers"
	@docker compose up

stop: ## Stop Containers
	@docker compose down

restart: stop start ## Restart Containers

start-bg:  ## Run containers in the background
	@docker compose up -d

build: ## Build Containers
	@docker compose build

ssh: ## SSH into running web container
	docker compose exec web bash

bash: ## Get a bash shell into the web container
	docker compose run --rm --no-deps web bash

manage: ## Run any manage.py command. E.g. `make manage ARGS='createsuperuser'`
	@docker compose run --rm web python manage.py ${ARGS}

migrations: ## Create DB migrations in the container
	@docker compose run --rm web python manage.py makemigrations

migrate: ## Run DB migrations in the container
	@docker compose run --rm web python manage.py migrate

translations:
	@docker compose run --rm --no-deps web python manage.py makemessages --all --ignore node_modules --ignore venv --ignore .venv
	@docker compose run --rm --no-deps web python manage.py makemessages -d djangojs --all --ignore node_modules --ignore venv --ignore .venv
	@docker compose run --rm --no-deps web python manage.py compilemessages --ignore venv --ignore .venv

shell: ## Get a Django shell
	@docker compose run --rm web python manage.py shell

dbshell: ## Get a Database shell
	@docker compose exec db psql -U postgres portfolio_strategist

test: ## Run Django tests
	@docker compose run --rm web python manage.py test ${ARGS}

init: setup-env start-bg migrations migrate bootstrap_content  ## Quickly get up and running (start containers and migrate DB)

uv: ## Run a uv command
	@docker compose run --rm web uv $(filter-out $@,$(MAKECMDGOALS))

uv-sync: ## Sync dependencies
	@docker compose run --rm web uv sync --frozen

requirements: uv-sync build stop start-bg  ## Rebuild your requirements and restart your containers

ruff-format: ## Runs ruff formatter on the codebase
	@docker compose run --rm --no-deps web ruff format .

ruff-lint:  ## Runs ruff linter on the codebase
	@docker compose run --rm --no-deps web ruff check --fix  .

format: ruff-format ruff-lint ## Formatting and linting using Ruff

npm-install: ## Runs npm install in the container
	@docker compose run --rm --no-deps web npm install $(filter-out $@,$(MAKECMDGOALS))

npm-uninstall: ## Runs npm uninstall in the container
	@docker compose run --rm --no-deps web npm uninstall $(filter-out $@,$(MAKECMDGOALS))

npm-build: ## Runs npm build in the container (for production assets)
	@docker compose run --rm --no-deps web npm run build

npm-dev: ## Runs npm dev in the container
	@docker compose run --rm --no-deps web npm run dev

npm-watch: ## Runs npm watch in the container (recommended for dev)
	@docker compose run --rm --no-deps web npm run dev-watch

npm-type-check: ## Runs the type checker on the front end TypeScript code
	@docker compose run --rm --no-deps web npm run type-check

build-api-client:  ## Update the JavaScript API client code.
	@docker run --rm --network host -v $(shell pwd)/api-client:/local openapitools/openapi-generator-cli:v7.9.0 generate \
	-i http://localhost:8000/api/schema/ \
	-g typescript-fetch \
	-o /local/

bootstrap_content:  ## Initializes your Wagtail content with some example pages and blog posts
	@docker compose run --rm web python manage.py bootstrap_content

upgrade: requirements migrations migrate npm-install npm-dev

.PHONY: help
.DEFAULT_GOAL := help

help:
	@grep -hE '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

# catch-all for any undefined targets - this prevents error messages
# when running things like make npm-install <package>
%:
	@:
