IMAGE_NAME=pyclean-test

CONTAINER_ENGINE ?= $(shell command -v podman 2> /dev/null || echo docker)


# regenerate new image when needed
build-image:
	$(CONTAINER_ENGINE) build --rm --tag $(IMAGE_NAME) -f tests/Containerfile


enter-image:
	$(CONTAINER_ENGINE) run -v .:/src_bind:Z -ti $(IMAGE_NAME) bash


test-in-container:
	$(CONTAINER_ENGINE) run -v .:/src_bind -ti $(IMAGE_NAME) bash -c "poetry run pytest -vvv tests/"


test-locally:
	poetry run pytest -vvv tests/
