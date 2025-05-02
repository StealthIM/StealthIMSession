PROTOCCMD = protoc
PROTOGEN_PATH = $(shell which protoc-gen-go) 
PROTOGENGRPC_PATH = $(shell which protoc-gen-go-grpc) 

GO_FILES := $(shell find $(SRC_DIR) -name '*.go')

GOCMD := go
GOBUILD := $(GOCMD) build
GOCLEAN := $(GOCMD) clean

LDFLAGS := -s -w

ifeq ($(OS), Windows_NT)
	DEFAULT_BUILD_FILENAME := StealthIMSession.exe
else
	DEFAULT_BUILD_FILENAME := StealthIMSession
endif

run: build
	./bin/$(DEFAULT_BUILD_FILENAME)

StealthIM.DBGateway/db_gateway_grpc.pb.go StealthIM.DBGateway/db_gateway.pb.go: proto/db_gateway.proto
	$(PROTOCCMD) --plugin=protoc-gen-go=$(PROTOGEN_PATH) --plugin=protoc-gen-go-grpc=$(PROTOGENGRPC_PATH) --go-grpc_out=. --go_out=. proto/db_gateway.proto

StealthIM.Session/session_grpc.pb.go StealthIM.Session/session.pb.go: proto/session.proto
	$(PROTOCCMD) --plugin=protoc-gen-go=$(PROTOGEN_PATH) --plugin=protoc-gen-go-grpc=$(PROTOGENGRPC_PATH) --go-grpc_out=. --go_out=. proto/session.proto

proto: ./StealthIM.DBGateway/db_gateway_grpc.pb.go ./StealthIM.DBGateway/db_gateway.pb.go ./StealthIM.Session/session_grpc.pb.go ./StealthIM.Session/session.pb.go


build: ./bin/$(DEFAULT_BUILD_FILENAME)

./bin/StealthIMSession.exe: $(GO_FILES) proto
	GOOS=windows GOARCH=amd64 go build -ldflags="$(LDFLAGS)" -o ./bin/StealthIMSession.exe

./bin/StealthIMSession: $(GO_FILES) proto
	GOOS=linux GOARCH=amd64 go build -ldflags="-s -w" -o ./bin/StealthIMSession

build_win: ./bin/StealthIMSession.exe
build_linux: ./bin/StealthIMSession

docker_run:
	docker-compose up

./bin/StealthIMSession.docker.zst: $(GO_FILES) proto
	docker-compose build
	docker save stealthimsession-app > ./bin/StealthIMSession.docker
	zstd ./bin/StealthIMSession.docker -19
	@rm ./bin/StealthIMSession.docker

build_docker: ./bin/StealthIMSession.docker.zst

release: build_win build_linux build_docker

clean:
	@rm -rf ./StealthIM.DBGateway
	@rm -rf ./StealthIM.Session
	@rm -rf ./bin
	@rm -rf ./__debug*

dev:
	./run_env.sh

debug_proto:
	cd test && python -m grpc_tools.protoc -I. --python_out=. --mypy_out=.  --grpclib_python_out=. --proto_path=../proto session.proto
