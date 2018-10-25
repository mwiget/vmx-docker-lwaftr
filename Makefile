all: build

build: snabb/src/snabb
	cd snabb && make clean && make docker && make -j && cd src && make -j
	docker-compose build

snabb/src/snabb:
	git clone -b passthru https://github.com/mwiget/snabb

pull:
	docker-compose pull

license-eval.txt:
	curl -o license-eval.txt https://www.juniper.net/us/en/dm/free-vmx-trial/E421992502.txt

id_rsa.pub:
	cp ~/.ssh/id_rsa.pub .

up:
	docker-compose up -d --build
	./start-snabb-lwaftr.sh &

ps:
	docker-compose ps
	./getpass.sh

down:
	sudo pkill snabb || true
	docker-compose down
	rm -f .*.pwd

clean:
	docker system prune -f
	docker network prune -f

