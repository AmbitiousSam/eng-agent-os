# Engineering Agentic OS — common tasks
.PHONY: help install doctor validate check test hooks push

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

install: ## Install EAOS into ~/.claude (clones agency-agents, installs command + agents + config)
	@./setup.sh

hooks: ## Enable the pre-push validation gate (git push runs validation first)
	@bash scripts/install-hooks.sh

doctor: ## Check install + current project readiness
	@bash scripts/eaos-doctor.sh

validate: ## Mechanically validate repo consistency (routing, personas, templates)
	@python3 scripts/validate-eaos.py

test: ## Syntax-check shell scripts + run the validator
	@for s in setup.sh scripts/eaos-doctor.sh scripts/push-to-github.sh scripts/install-hooks.sh .githooks/pre-push; do \
	  bash -n "$$s" && echo "$$s: syntax OK"; done
	@python3 scripts/validate-eaos.py

check: test ## Alias for test (CI entrypoint)

push: validate ## Validate, then create/push the GitHub repo (push only after validation)
	@./scripts/push-to-github.sh
