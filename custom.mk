# you can use this file to add custom make targets and avoid conflicting with the main Pegasus makefile

setup-file-access: ## Set up file access permissions for local and cloud drives
	@./setup_file_access.sh

test-file-access: ## Test file access from within the web container
	@$(DOCKER_COMPOSE) exec web bash test_file_access.sh || echo "Note: Run 'make setup-file-access' first if test script is missing"

file-access-shell: ## Get a shell in the container to manually test file access
	@$(DOCKER_COMPOSE) exec web bash
