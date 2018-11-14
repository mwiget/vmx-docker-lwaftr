all: build run

build:
	docker build -t jroutes .

buildclean:
	docker build --no-cache -t jroutes .

run:
	cp ../.vmx1.pwd .
	docker run -ti --rm -v $$PWD:/root/go/src/github.com/vmx-docker-lwaftr:ro jroutes

clean:
	docker system prune -f

stubs:
	@mkdir -p stubs || true
	@mkdir -p stubs/authentication || true
	@mkdir -p stubs/routing || true
	@mkdir -p stubs/jnx_addr || true
	protoc -I proto --go_out=plugins=grpc:stubs/authentication proto/authentication_service.proto
	protoc -I proto --go_out=plugins=grpc:stubs/jnx_addr proto/jnx_addr.proto proto/jnx_base_types.proto
	protoc -I proto --go_out=plugins=grpc,Mjnx_addr.proto=github.com/juniper/vmx-docker-lwaftr/jroutes/stubs/jnx_addr:stubs/routing  proto/bgp_route_service.proto proto/prpd_common.proto

broken:
	@mkdir -p stubs || true
	@mkdir -p stubs/authentication || true
	@mkdir -p stubs/bgp_route || true
	@mkdir -p stubs/jnx_addr || true
	@mkdir -p stubs/prpd_common || true
	protoc -I proto --go_out=plugins=grpc:stubs/authentication proto/authentication_service.proto
	protoc -I proto --go_out=plugins=grpc:stubs/jnx_addr proto/jnx_addr.proto proto/jnx_base_types.proto
	protoc -I proto --go_out=plugins=grpc:Mjnx_addr.proto=../jnx_addr:stubs/prpd_common proto/prpd_common.proto
	protoc -I proto --go_out=plugins=grpc:Mjnx_addr.proto=../jnx_addr:stubs/bgp_route proto/bgp_route_service.proto 
