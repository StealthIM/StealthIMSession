# StealthIM Session

Session ID 管理 `0.0.1`

> `.proto` 文件：`./proto/session.proto`

## 构建

### 依赖

Go 版本：`1.24.2`

软件包：`protobuf` `protobuf-dev` `make`

> 命令行工具 `protoc` `make`(gnumake)

```bash
go mod download
go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest
```

### 命令行

```bash
make # 构建并运行
make build # 构建可执行文件

# 构建指定环境
make build_windows
make build_linux
make build_docker

make release # 构建所有平台

make proto # 生成 proto

make clean # 清理
```

## 配置

默认会读取当前文件夹 `config.toml` 文件（不存在会自动生成模板）

默认配置：

```toml
```

也可使用 `--config={PATH}` 参数指定配置文件路径
