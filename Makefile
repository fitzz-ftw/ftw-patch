# --- Configuration ---
DEPLOY_BRANCH = master
TAG_FILE      = TAGMESSAGE.txt
OLD_MSG_DIR   = old_messages
CLEAN_DIRS    = docs/build dist build .tox .pytest_cache .mypy_cache 

GIT    = git
MAKE   = make
TWINE  = twine
PYTHON = python3

# --- Colors ---
RED    = \033[0;31m
YELLOW = \033[0;33m
GREEN  = \033[0;32m
NC     = \033[0m

.PHONY: help prepare-master init-msg prepare-tag deploy clean html tox \
        test-deploy check-gitclean check-upstream check-v clean-test-tags check-tools

# Default goal: check environment first, then show help
.DEFAULT_GOAL := default
default: check-tools help

help:
	@printf "\n$(GREEN)%s$(NC)\n" "Python Project Management - Makefile"
	@printf "$(YELLOW)%s$(NC)\n" "Usage: make <target> [V=x.y.z]"
	@printf "  $(YELLOW)make help$(NC)                Show this help message (standard info)\n\n"
	@printf "$(GREEN)%s$(NC)\n" "Main Workflows:"
	@printf "  $(YELLOW)make deploy V=x.y.z$(NC)      Full release (Master check, Upstream sync, Tox, HTML, Tag, Push)\n"
	@printf "  $(YELLOW)make test-deploy V=x.y.z$(NC) Test release (TestPyPI, Twine check, Tag vV-test)\n\n"
	@printf "$(GREEN)%s$(NC)\n" "Quality Assurance & Documentation:"
	@printf "  $(YELLOW)make tox$(NC)                 Run all tests using tox\n"
	@printf "  $(YELLOW)make build$(NC)               Build package (sdist & wheel) via tox\\n"
	@printf "  $(YELLOW)make html$(NC)                Generate Sphinx HTML documentation\n"
	@printf "  $(YELLOW)make check-tools$(NC)         Show versions and paths of used tools\n\n"
	@printf "$(GREEN)%s$(NC)\n" "Validation & Safety (Internal):$(NC)\n"
	@printf "  $(YELLOW)make ci-prepare$(NC)          Prepare CI environment (Install tools like tox/build)\\n"
	@printf "  $(YELLOW)make check-gitclean$(NC)      Check for uncommitted changes\n"
	@printf "  $(YELLOW)make check-upstream$(NC)      Check sync status with origin\n"
	@printf "  $(YELLOW)make check-v V=...$(NC)       Validate version format (SemVer)\n\n"
	@printf "$(GREEN)%s$(NC)\n" "Cleanup:"
	@printf "  $(YELLOW)make clean$(NC)               Remove build artifacts and caches\n"
	@printf "  $(YELLOW)make clean-test-tags$(NC)     Remove all v*-test tags locally\n"

# --- Tool Check ---
check-tools:
	@printf "$(GREEN)%s$(NC)\n" "--- Installed Tool Environment ---"
	@printf "$(YELLOW)PYTHON:$(NC) %s\n" "$$(which $(PYTHON))"
	@      printf "        %s\n" "$$($(PYTHON) --version 2>&1)"
	@printf "$(YELLOW)GIT:$(NC)    %s\n" "$$(which $(GIT))"
	@      printf "        %s\n" "$$($(GIT) --version)"
	@printf "$(YELLOW)TOX:$(NC)    %s\n" "$$(which tox 2>/dev/null || echo 'NOT FOUND')"
	@      printf "        %s\n" "$$(tox --version 2>/dev/null || echo 'n/a')"
	@printf "$(YELLOW)TWINE:$(NC)  %s\n" "$$(which $(TWINE) 2>/dev/null || echo 'NOT FOUND')"
	@      printf "        %s\n" "$$($(TWINE) --version 2>/dev/null | head -n 1 || echo 'n/a')"
	@printf "$(YELLOW)MAKE:$(NC)   %s\n" "$$(which $(MAKE))"
	@      printf "        %s\n" "$$($(MAKE) --version | head -n 1)"

# --- Validation ---
check-v:
	@if [ -z "$(V)" ]; then \
		printf "$(RED)%s$(NC)\n" "ERROR: Variable V is missing (e.g., V=1.2.3)"; exit 1; \
	fi
	@if ! echo "$(V)" | grep -Eiq '^[0-9]+\.[0-9]+\.[0-9]+.*$$'; then \
		printf "$(RED)%s$(NC)\n" "ERROR: '$(V)' is not a valid SemVer format"; exit 1; \
	fi

check-gitclean:
	@if [ -n "$$($(GIT) status --porcelain)" ]; then \
		printf "$(RED)%s$(NC)\n" "ERROR: Working directory is not clean!"; exit 1; \
	fi

check-upstream:
	@printf "%s\n" "--- Checking Remote Status ---"
	@$(GIT) fetch --quiet
	@LOCAL=$$(git rev-parse HEAD); \
	REMOTE=$$(git rev-parse @{u} 2>/dev/null || echo $$LOCAL); \
	if [ "$$LOCAL" != "$$REMOTE" ]; then \
		printf "$(YELLOW)%s$(NC)\n" "****************************************************************" ; \
		printf "$(YELLOW)%s$(NC)\n" "WARNING: Local branch has diverged from origin!" ; \
		if [ "$(EXIT_ON_FAIL)" = "1" ]; then \
			printf "$(RED)%s$(NC)\n" "ABORT: Release only allowed when synchronized with remote!" ; \
			exit 1; \
		fi; \
		printf "%s\n" "Note: Continuing with test build..." ; \
		printf "$(YELLOW)%s$(NC)\n" "****************************************************************" ; \
	else \
		printf "$(GREEN)%s$(NC)\n" "Status: Synchronized with server." ; \
	fi

# --- Workflows ---
prepare-master:
	@curr_branch=$$($(GIT) rev-parse --abbrev-ref HEAD); \
	if [ "$$curr_branch" != "$(DEPLOY_BRANCH)" ]; then \
		printf "$(YELLOW)%s$(NC)\n" "Switching to $(DEPLOY_BRANCH)..." ; \
		$(GIT) switch $(DEPLOY_BRANCH) || exit 1; \
	fi

init-msg:
	@mkdir -p $(OLD_MSG_DIR)
	@if [ ! -f $(TAG_FILE) ]; then touch $(TAG_FILE); fi

prepare-tag: init-msg
	@if [ ! -s $(TAG_FILE) ]; then \
		printf "$(RED)%s$(NC)\n" "ERROR: $(TAG_FILE) is empty!"; exit 1; \
	fi

deploy: prepare-master check-gitclean
	@$(MAKE) check-upstream EXIT_ON_FAIL=1
	@$(MAKE) check-v prepare-tag tox html
	$(GIT) tag -a v$(V) -F $(TAG_FILE)
	@cp $(TAG_FILE) $(OLD_MSG_DIR)/$(TAG_FILE).v$(V)_$$(date +%Y%m%d_%H%M%S).bak
	@> $(TAG_FILE)
	$(GIT) push origin $(DEPLOY_BRANCH)
	$(GIT) push origin v$(V)
	@printf "$(GREEN)%s$(NC)\n" "SUCCESS: v$(V) published."

test-deploy: check-gitclean
	@$(MAKE) check-upstream EXIT_ON_FAIL=0
	@$(MAKE) check-v prepare-tag tox
	$(GIT) tag -a v$(V)-test -F $(TAG_FILE)
	@cp $(TAG_FILE) $(OLD_MSG_DIR)/$(TAG_FILE).v$(V)-test_$$(date +%Y%m%d_%H%M%S).bak
	rm -rf dist/
	$(PYTHON) -m build
	$(TWINE) check dist/* || { printf "$(RED)%s$(NC)\n" "ERROR: Twine check failed!"; exit 1; }
	$(TWINE) upload --repository testpypi dist/*
	@printf "$(GREEN)%s$(NC)\n" "SUCCESS: Test version v$(V) uploaded."

clean-test-tags:
	@printf "$(YELLOW)%s$(NC)\n" "--- Removing local test tags ---"
	@for tag in $$(git tag -l "*-test"); do \
		git tag -d $$tag; \
	done

clean: 
	@printf "%s\n" "--- Cleaning up project ---"
	rm -rf $(CLEAN_DIRS)
	@if [ -d doc ]; then $(MAKE) -C doc clean; fi

html:
	$(MAKE) -C doc html

tox:
	@printf "%s\n" "--- Starting Tests ---"
	tox

# --- CI Support ---
.PHONY: ci-prepare

ci-prepare:
	@printf "$(YELLOW)%s$(NC)\n" "Preparing CI environment..."
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install tox 
	@printf "$(GREEN)%s$(NC)\n" "CI environment ready."

# --- Build & Distribution ---
.PHONY: build

build: clean ## Build sdist and wheel using tox
	@printf "$(YELLOW)%s$(NC)\n" "Starting isolated build via tox..."
	tox -e build
	@printf "$(GREEN)%s$(NC)\n" "Build finished. Check dist/ for artifacts."
