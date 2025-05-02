# 使用官方的 Golang 镜像作为构建环境
FROM golang:1.24.2-alpine

# 设置工作目录
WORKDIR /app

RUN sed -i 's/dl-cdn\.alpinelinux\.org/mirrors.aliyun.com/g' /etc/apk/repositories && \
    apk update && \
    apk add --no-cache make protobuf protobuf-dev

COPY . .

RUN GOPROXY=https://goproxy.cn,direct \
    go mod download && \
    GOPROXY=https://goproxy.cn,direct GOBIN=/usr/bin \
    go install google.golang.org/protobuf/cmd/protoc-gen-go@latest && \
    GOPROXY=https://goproxy.cn,direct GOBIN=/usr/bin \
    go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest

RUN make build

# 使用更小的镜像来运行应用
FROM alpine:latest

# 设置工作目录
WORKDIR /app

# 将编译好的二进制文件复制到新镜像中
COPY --from=0 /app/bin .

# 暴露端口
EXPOSE 50054

# 运行编译好的二进制文件
CMD ["./StealthIMSession","--config=./config/config.toml"]
