all: build run

build:
	docker build -t snabbvmx . --no-cache

run:
	docker run -ti --rm --name snabbvmx -v $$PWD:/u snabbvmx
#	docker run --user $$(id -u):$$(id -g) -ti --rm --name snabbvmx -v $$PWD:/u snabbvmx
