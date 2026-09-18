# Engineering Agentic OS — common tasks
.PHONY: help install doctor validate check test hooks

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

install: ## Install EAOS into ~/.claude (front door, 3 boundary agents, checklists, runtime)
	@./setup.sh

hooks: ## Enable the pre-push validation gate (git push runs validation first)
	@git config core.hooksPath .githooks && echo 'pre-push gate enabled'

doctor: ## Check install + current project readiness
	@bash runtime/eaos-doctor.sh

validate: ## Mechanically validate repo consistency (layout, agents, checklists, routing)
	@python3 tests/validate-eaos.py


test: ## Syntax-check shell scripts + run the validator
	@for s in setup.sh runtime/eaos-doctor.sh \
	          runtime/eaos-hook.sh runtime/install-eaos-hooks.sh tests/test_eaos_hooks.sh \
	          lab/scripts/e0_packet.sh lab/scripts/e0_env.sh tests/test_setup_cleanup.sh \
	          .githooks/pre-push; do \
	  bash -n "$$s" && echo "$$s: syntax OK"; done
	@python3 tests/validate-eaos.py
	@python3 tests/test_eaos.py
	@bash tests/test_eaos_hooks.sh
	@bash tests/test_setup_cleanup.sh

check: test ## Alias for test (CI entrypoint)

