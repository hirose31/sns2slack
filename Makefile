
.PHONY: help
.DEFAULT_GOAL := help

include config.mk

TARGETS = $(CONFIG_FILES:json=target)

help:
	@grep -h -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

deploy: $(TARGETS)  ## deploy

%.target: %.json
	$(eval FUNC_NAME := $(shell cat $< | jq '.name' -r))
	@echo $(FUNC_NAME)
	lambda-uploader --profile $(AWS_PROFILE) \
	  --config $< \
	  --variables '$(shell aws --profile $(AWS_PROFILE) \
	  lambda get-function --function-name $(FUNC_NAME) | jq -c ".Configuration.Environment.Variables")'
	@echo finished

