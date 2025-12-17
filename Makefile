include custom.mk

# detect available compose command; prefer plugin (docker compose) with fallback to docker-compose
DOCKER_COMPOSE ?= $(shell if docker compose version >/dev/null 2>&1; then echo docker compose; elif command -v docker-compose >/dev/null 2>&1; then echo docker-compose; else echo docker compose; fi)

setup-env:
	@[ ! -f ./.env ] && cp ./.env.example ./.env || echo ".env file already exists."

start: ## Start the docker containers
	@echo "Starting the docker containers"
	@$(DOCKER_COMPOSE) up

stop: ## Stop Containers
	@$(DOCKER_COMPOSE) down

restart: stop start ## Restart Containers

start-bg:  ## Run containers in the background
	@$(DOCKER_COMPOSE) up -d

build: ## Build Containers
	@$(DOCKER_COMPOSE) build

ssh: ## SSH into running web container
	$(DOCKER_COMPOSE) exec web bash

bash: ## Get a bash shell into the web container
	$(DOCKER_COMPOSE) run --rm --no-deps web bash

manage: ## Run any manage.py command. E.g. `make manage ARGS='createsuperuser'`
	@$(DOCKER_COMPOSE) run --rm web python manage.py ${ARGS}

migrations: ## Create DB migrations in the container
	@$(DOCKER_COMPOSE) run --rm web python manage.py makemigrations

migrate: ## Run DB migrations in the container
	@$(DOCKER_COMPOSE) run --rm web python manage.py migrate

translations:
	@$(DOCKER_COMPOSE) run --rm --no-deps web python manage.py makemessages --all --ignore node_modules --ignore venv --ignore .venv
	@$(DOCKER_COMPOSE) run --rm --no-deps web python manage.py makemessages -d djangojs --all --ignore node_modules --ignore venv --ignore .venv
	@$(DOCKER_COMPOSE) run --rm --no-deps web python manage.py compilemessages --ignore venv --ignore .venv

shell: ## Get a Django shell
	@$(DOCKER_COMPOSE) run --rm web python manage.py shell

dbshell: ## Get a Database shell
	@$(DOCKER_COMPOSE) exec db psql -U postgres portfolio_strategist

test: ## Run Django tests
	@$(DOCKER_COMPOSE) run --rm web python manage.py test ${ARGS}

init: setup-env start-bg migrations migrate bootstrap_content  ## Quickly get up and running (start containers and migrate DB)

uv: ## Run a uv command
	@$(DOCKER_COMPOSE) run --rm web uv $(filter-out $@,$(MAKECMDGOALS))

uv-sync: ## Sync dependencies
	@$(DOCKER_COMPOSE) run --rm web uv sync --frozen

requirements: uv-sync build stop start-bg  ## Rebuild your requirements and restart your containers

ruff-format: ## Runs ruff formatter on the codebase
	@$(DOCKER_COMPOSE) run --rm --no-deps web ruff format .

ruff-lint:  ## Runs ruff linter on the codebase
	@$(DOCKER_COMPOSE) run --rm --no-deps web ruff check --fix  .

format: ruff-format ruff-lint ## Formatting and linting using Ruff

npm-install: ## Runs npm install in the container
	@$(DOCKER_COMPOSE) run --rm --no-deps web npm install $(filter-out $@,$(MAKECMDGOALS))

npm-uninstall: ## Runs npm uninstall in the container
	@$(DOCKER_COMPOSE) run --rm --no-deps web npm uninstall $(filter-out $@,$(MAKECMDGOALS))

npm-build: ## Runs npm build in the container (for production assets)
	@$(DOCKER_COMPOSE) run --rm --no-deps web npm run build

npm-dev: ## Runs npm dev in the container
	@$(DOCKER_COMPOSE) run --rm --no-deps web npm run dev

npm-watch: ## Runs npm watch in the container (recommended for dev)
	@$(DOCKER_COMPOSE) run --rm --no-deps web npm run dev-watch

npm-type-check: ## Runs the type checker on the front end TypeScript code
	@$(DOCKER_COMPOSE) run --rm --no-deps web npm run type-check

build-api-client:  ## Update the JavaScript API client code.
	@docker run --rm --network host -v $(shell pwd)/api-client:/local openapitools/openapi-generator-cli:v7.9.0 generate \
	-i http://localhost:8000/api/schema/ \
	-g typescript-fetch \
	-o /local/

bootstrap_content:  ## Initializes your Wagtail content with some example pages and blog posts
	@$(DOCKER_COMPOSE) run --rm web python manage.py bootstrap_content

upgrade: requirements migrations migrate npm-install npm-dev

.PHONY: help
.DEFAULT_GOAL := help

help:
	@grep -hE '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

functions: ## Alias for help to list available commands
	@$(MAKE) help

# catch-all for any undefined targets - this prevents error messages
# when running things like make npm-install <package>
%:
	@:
