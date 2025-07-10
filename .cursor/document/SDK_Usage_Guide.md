# API 使用指南 (AI 视角)

本文档总结了 `gateway/` 目录中提供的核心 API 函数的使用方法，旨在帮助 AI 理解如何调用这些接口以完成特定任务。

**注意**: 在本指南中，`pb` 是一个常用的别名，用于导入 Protobuf 定义包。例如，`*pb.RedisGetStringRequest` 实际上指的是 `*StealthIM.DBGateway.RedisGetStringRequest`，而 `*pb.SendMessageRequest` 则指的是 `*StealthIM.MSAP.SendMessageRequest`。具体 `pb` 别名代表哪个包取决于其在代码中的导入声明。

**注意**: 如果在一个 go 中文件需要使用多个不同的包，`pb` 应 改为如 `pbgtw`、`pbmsap` 这类全小写的使用缩写的别名。当前模块所对应的 proto 必须使用 `pb`。

## `gateway/` 目录 API

`gateway/` 目录提供了与 DBGateway gRPC 服务交互的功能，用于执行数据库操作。

### `gateway.ExecRedisGet(req *pb.RedisGetStringRequest) (*pb.RedisGetStringResponse, error)`

* **功能**: 执行 Redis GET 命令，获取字符串类型的值。
* **参数**:
  * `req`: `*pb.RedisGetStringRequest` 类型，包含要查询的键。
* **返回**: `*pb.RedisGetStringResponse` (包含查询结果) 和 `error`。
* **AI 使用场景**: 从 Redis 缓存中读取字符串数据，例如用户会话信息、配置参数等。

**相关 Protobuf 定义**:

```protobuf
// proto/db_gateway.proto
message RedisGetStringRequest {
  int32 DBID = 1;
  string key = 2;
}
message RedisGetStringResponse {
  int32 DBID = 1;
  Result result = 2;
  string value = 3;
}
message Result {
  int32 code = 1;
  string msg = 2;
}
```

**Go 调用示例**:

```go
package main

import (
 "StealthIMMSAP/gateway"
 pb "StealthIMMSAP/StealthIM.DBGateway" // 导入对应的 Protobuf 包
 "log"
)

func main() {
 // 假设 DBGateway 连接已初始化
 // gateway.InitConns() // 在实际应用中，这会在后台运行

 req := &pb.RedisGetStringRequest{
  DBID: 0, // 示例数据库ID
  Key:  "my_string_key",
 }

 res, err := gateway.ExecRedisGet(req)
 if err != nil {
  log.Printf("Failed to get Redis string: %v", err)
 } else {
  if res.Result.Code == 800 { // 假设 800 是成功代码
   log.Printf("Successfully got Redis string: Key='%s', Value='%s'", req.Key, res.Value)
  } else {
   log.Printf("Failed to get Redis string: Code=%d, Msg='%s'", res.Result.Code, res.Result.Msg)
  }
 }
}
```

### `gateway.ExecRedisSet(req *pb.RedisSetStringRequest) (*pb.RedisSetResponse, error)`

* **功能**: 执行 Redis SET 命令，设置字符串类型的值。
* **参数**:
  * `req`: `*pb.RedisSetStringRequest` 类型，包含要设置的键、值和过期时间。
* **返回**: `*pb.RedisSetResponse` (包含操作结果) 和 `error`。
* **AI 使用场景**: 向 Redis 缓存写入字符串数据，例如存储用户会话、临时数据等。

**相关 Protobuf 定义**:

```protobuf
// proto/db_gateway.proto
message RedisSetStringRequest {
  int32 DBID = 1;
  string key = 2;
  string value = 3;
  int32 ttl = 4;
}
message RedisSetResponse { Result result = 1; }
message Result {
  int32 code = 1;
  string msg = 2;
}
```

**Go 调用示例**:

```go
package main

import (
 "StealthIMMSAP/gateway"
 pb "StealthIMMSAP/StealthIM.DBGateway" // 导入对应的 Protobuf 包
 "log"
)

func main() {
 // 假设 DBGateway 连接已初始化
 // gateway.InitConns() // 在实际应用中，这会在后台运行

 req := &pb.RedisSetStringRequest{
  DBID:  0, // 示例数据库ID
  Key:   "my_new_string_key",
  Value: "some_value",
  Ttl:   60, // 60秒过期
 }

 res, err := gateway.ExecRedisSet(req)
 if err != nil {
  log.Printf("Failed to set Redis string: %v", err)
 } else {
  if res.Result.Code == 800 { // 假设 800 是成功代码
   log.Printf("Successfully set Redis string: Key='%s', Value='%s'", req.Key, req.Value)
  } else {
   log.Printf("Failed to set Redis string: Code=%d, Msg='%s'", res.Result.Code, res.Result.Msg)
  }
 }
}
```

### `gateway.ExecRedisBGet(req *pb.RedisGetBytesRequest) (*pb.RedisGetBytesResponse, error)`

* **功能**: 执行 Redis GET 命令，获取二进制类型的值。
* **参数**:
  * `req`: `*pb.RedisGetBytesRequest` 类型，包含要查询的键。
* **返回**: `*pb.RedisGetBytesResponse` (包含查询结果) 和 `error`。
* **AI 使用场景**: 从 Redis 缓存中读取二进制数据，例如序列化的对象、图片等。

**相关 Protobuf 定义**:

```protobuf
// proto/db_gateway.proto
message RedisGetBytesRequest {
  int32 DBID = 1;
  string key = 2;
}
message RedisGetBytesResponse {
  int32 DBID = 1;
  Result result = 2;
  bytes value = 3;
}
message Result {
  int32 code = 1;
  string msg = 2;
}
```

**Go 调用示例**:

```go
package main

import (
 "StealthIMMSAP/gateway"
 pb "StealthIMMSAP/StealthIM.DBGateway" // 导入对应的 Protobuf 包
 "log"
)

func main() {
 // 假设 DBGateway 连接已初始化
 // gateway.InitConns() // 在实际应用中，这会在后台运行

 req := &pb.RedisGetBytesRequest{
  DBID: 0, // 示例数据库ID
  Key:  "my_binary_key",
 }

 res, err := gateway.ExecRedisBGet(req)
 if err != nil {
  log.Printf("Failed to get Redis binary: %v", err)
 } else {
  if res.Result.Code == 800 { // 假设 800 是成功代码
   log.Printf("Successfully got Redis binary: Key='%s', ValueLength=%d", req.Key, len(res.Value))
  } else {
   log.Printf("Failed to get Redis binary: Code=%d, Msg='%s'", res.Result.Code, res.Result.Msg)
  }
 }
}
```

### `gateway.ExecRedisBSet(req *pb.RedisSetBytesRequest) (*pb.RedisSetResponse, error)`

* **功能**: 执行 Redis SET 命令，设置二进制类型的值。
* **参数**:
  * `req`: `*pb.RedisSetBytesRequest` 类型，包含要设置的键、值和过期时间。
* **返回**: `*pb.RedisSetResponse` (包含操作结果) 和 `error`。
* **AI 使用场景**: 向 Redis 缓存写入二进制数据，例如存储序列化的对象、图片等。

**相关 Protobuf 定义**:

```protobuf
// proto/db_gateway.proto
message RedisSetBytesRequest {
  int32 DBID = 1;
  string key = 2;
  bytes value = 3;
  int32 ttl = 4;
}
message RedisSetResponse { Result result = 1; }
message Result {
  int32 code = 1;
  string msg = 2;
}
```

**Go 调用示例**:

```go
package main

import (
 "StealthIMMSAP/gateway"
 pb "StealthIMMSAP/StealthIM.DBGateway" // 导入对应的 Protobuf 包
 "log"
)

func main() {
 // 假设 DBGateway 连接已初始化
 // gateway.InitConns() // 在实际应用中，这会在后台运行

 req := &pb.RedisSetBytesRequest{
  DBID:  0, // 示例数据库ID
  Key:   "my_new_binary_key",
  Value: []byte("some binary data"),
  Ttl:   60, // 60秒过期
 }

 res, err := gateway.ExecRedisBSet(req)
 if err != nil {
  log.Printf("Failed to set Redis binary: %v", err)
 } else {
  if res.Result.Code == 800 { // 假设 800 是成功代码
   log.Printf("Successfully set Redis binary: Key='%s', ValueLength=%d", req.Key, len(req.Value))
  } else {
   log.Printf("Failed to set Redis binary: Code=%d, Msg='%s'", res.Result.Code, res.Result.Msg)
  }
 }
}
```

### `gateway.ExecRedisDel(req *pb.RedisDelRequest) (*pb.RedisDelResponse, error)`

* **功能**: 执行 Redis DEL 命令，删除一个或多个键。
* **参数**:
  * `req`: `*pb.RedisDelRequest` 类型，包含要删除的键列表。
* **返回**: `*pb.RedisDelResponse` (包含删除的键数量) 和 `error`。
* **AI 使用场景**: 从 Redis 缓存中删除不再需要的数据。

**相关 Protobuf 定义**:

```protobuf
// proto/db_gateway.proto
message RedisDelRequest {
  int32 DBID = 1;
  string key = 2;
}
message RedisDelResponse { Result result = 1; }
message Result {
  int32 code = 1;
  string msg = 2;
}
```

**Go 调用示例**:

```go
package main

import (
 "StealthIMMSAP/gateway"
 pb "StealthIMMSAP/StealthIM.DBGateway" // 导入对应的 Protobuf 包
 "log"
)

func main() {
 // 假设 DBGateway 连接已初始化
 // gateway.InitConns() // 在实际应用中，这会在后台运行

 req := &pb.RedisDelRequest{
  DBID: 0, // 示例数据库ID
  Key:  "my_key_to_delete",
 }

 res, err := gateway.ExecRedisDel(req)
 if err != nil {
  log.Printf("Failed to delete Redis key: %v", err)
 } else {
  if res.Result.Code == 800 { // 假设 800 是成功代码
   log.Printf("Successfully deleted Redis key: Key='%s'", req.Key)
  } else {
   log.Printf("Failed to delete Redis key: Code=%d, Msg='%s'", res.Result.Code, res.Result.Msg)
  }
 }
}
```

### `gateway.ExecSQL(sql *pb.SqlRequest) (*pb.SqlResponse, error)`

* **功能**: 执行 SQL 语句。
* **参数**:
  * `sql`: `*pb.SqlRequest` 类型，包含要执行的 SQL 语句和参数。
* **返回**: `*pb.SqlResponse` (包含查询结果或受影响的行数) 和 `error`。
* **AI 使用场景**: 执行数据库查询、插入、更新或删除操作。

**相关 Protobuf 定义**:

```protobuf
// proto/db_gateway.proto
message SqlRequest {
  string sql = 1;
  SqlDatabases db = 2;
  repeated InterFaceType params = 3;
  bool commit = 4;
  bool get_row_count = 5;
  bool get_last_insert_id = 6;
}

enum SqlDatabases {
  Users = 0;
  Msg = 1;
  File = 2;
  Logging = 3;
  Groups = 4;
  Masterdb = 5;
  Session = 6;
};

message InterFaceType {
  oneof response {
    string str = 1;
    int32 int32 = 2;
    int64 int64 = 3;
    bool bool = 4;
    float float = 5;
    double double = 6;
    bytes blob = 7;
  }
  bool null = 8;
}

message SqlLine { repeated InterFaceType result = 1; }

message SqlResponse {
  Result result = 1;
  int64 rows_affected = 2;
  int64 last_insert_id = 3;
  repeated SqlLine data = 4;
}
message Result {
  int32 code = 1;
  string msg = 2;
}
```

**Go 调用示例**:

```go
package main

import (
 "StealthIMMSAP/gateway"
 pb "StealthIMMSAP/StealthIM.DBGateway" // 导入对应的 Protobuf 包
 "log"
)

func main() {
 // 假设 DBGateway 连接已初始化
 // gateway.InitConns() // 在实际应用中，这会在后台运行

 // 示例：插入数据
 insertReq := &pb.SqlRequest{
  Sql:    "INSERT INTO users (username, nickname) VALUES (?, ?)",
  Db:     pb.SqlDatabases_Users,
  Params: []*pb.InterFaceType{{Str: "testuser"}, {Str: "Test Nickname"}},
  Commit: true,
  GetLastInsertId: true,
 }

 insertRes, err := gateway.ExecSQL(insertReq)
 if err != nil {
  log.Printf("Failed to insert user: %v", err)
 } else {
  if insertRes.Result.Code == 800 {
   log.Printf("Successfully inserted user. Last Insert ID: %d", insertRes.LastInsertId)
  } else {
   log.Printf("Failed to insert user: Code=%d, Msg='%s'", insertRes.Result.Code, insertRes.Result.Msg)
  }
 }

 // 示例：查询数据
 queryReq := &pb.SqlRequest{
  Sql:    "SELECT username, nickname FROM users WHERE username = ?",
  Db:     pb.SqlDatabases_Users,
  Params: []*pb.InterFaceType{{Str: "testuser"}},
 }

 queryRes, err := gateway.ExecSQL(queryReq)
 if err != nil {
  log.Printf("Failed to query user: %v", err)
 } else {
  if queryRes.Result.Code == 800 {
   log.Printf("Successfully queried user. Rows: %d", len(queryRes.Data))
   for _, row := range queryRes.Data {
    log.Printf("  Username: %s, Nickname: %s", row.Result[0].Str, row.Result[1].Str)
   }
  } else {
   log.Printf("Failed to query user: Code=%d, Msg='%s'", queryRes.Result.Code, queryRes.Result.Msg)
  }
 }
}
```

! 无论如何你应该优先使用上述 sdk 而不是直接链接！
! 无论如何你应该优先使用上述 sdk 而不是直接链接！
! 无论如何你应该优先使用上述 sdk 而不是直接链接！
