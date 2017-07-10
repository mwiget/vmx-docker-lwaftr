all: build b4cpe

build:	Dockerfile.build
	git submodule update
	docker build -f Dockerfile.build -t build .
	docker run -ti --rm -v $$PWD:/u build
	docker build -t $$(cat VERSION) .
	docker-compose build

up:
	docker-compose up -d

ps:
	docker-compose ps

down:
	docker-compose down

shell:
	docker exec -ti $$(docker ps |grep lwaftr|cut -d' ' -f1) bash

attach:
	./getpass.sh | grep lwaftr
	docker attach $$(docker ps |grep lwaftr|cut -d' ' -f1) 

b4cpe: b4cpe/Dockerfile
	$(MAKE) -C b4cpe

clean:
	docker rmi build
	docker rmi `docker images | grep "^<none>" | awk '{print $$3}'` 2>/dev/null || true

