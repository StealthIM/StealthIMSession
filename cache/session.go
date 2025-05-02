package cache

import (
	pb "StealthIMSession/StealthIM.DBGateway"
	"StealthIMSession/gateway"
	"fmt"
	"log"
	"strconv"
)

var sessionCache *Cache

// InitSessionCache 初始化会话缓存
func InitSessionCache() {
	sessionCache = New()
	log.Println("[Cache] Session cache initialized")
}

// GetUserIDBySession 根据会话ID获取用户ID
// 实现三级缓存查询：内存缓存 -> Redis -> MySQL
func GetUserIDBySession(sessionID string) (int32, error) {
	// 1. 检查内存缓存
	if uid, found := sessionCache.Get(sessionID); found {
		// 如果值为-1，表示无效会话
		if uid == -1 {
			return 0, fmt.Errorf("invalid session: %s", sessionID)
		}
		return uid, nil
	}

	// 2. 检查Redis缓存
	redisKey := fmt.Sprintf("session:session:%s", sessionID)
	redisReq := &pb.RedisGetStringRequest{
		Key: redisKey,
	}

	redisResp, err := gateway.ExecRedisGet(redisReq)
	if err == nil && redisResp != nil && redisResp.Value != "" {
		// Redis中找到了数据
		uid, err := strconv.ParseInt(redisResp.Value, 10, 32)
		if err == nil {
			// 如果值为-1，表示无效会话
			if uid == -1 {
				// 存入内存缓存
				sessionCache.Set(sessionID, -1)
				return 0, fmt.Errorf("invalid session: %s", sessionID)
			}
			// 存入内存缓存
			sessionCache.Set(sessionID, int32(uid))
			return int32(uid), nil
		}
	}

	// 3. 从MySQL数据库查询
	sqlQuery := fmt.Sprintf("SELECT uid FROM session_db WHERE session_id = '%s' LIMIT 1", sessionID)
	sqlReq := &pb.SqlRequest{
		Sql: sqlQuery,
		Db:  pb.SqlDatabases_Session,
	}

	sqlResp, err := gateway.ExecSQL(sqlReq)
	if err != nil {
		// 查询失败，将-1写入缓存
		cacheInvalidSession(sessionID)
		return 0, fmt.Errorf("database error: %v", err)
	}

	// 检查是否有返回数据
	if sqlResp == nil || len(sqlResp.Data) == 0 {
		// 未找到会话，将-1写入缓存
		cacheInvalidSession(sessionID)
		return 0, fmt.Errorf("session not found: %s", sessionID)
	}

	// 提取 uid 值
	row := sqlResp.Data[0]
	if len(row.Result) == 0 {
		// 结果为空，将-1写入缓存
		cacheInvalidSession(sessionID)
		return 0, fmt.Errorf("empty result from database")
	}

	// 获取第一个字段（uid）
	uidValue := row.Result[0]
	var uid int32

	// 根据返回值类型确定UID
	switch v := uidValue.Response.(type) {
	case *pb.InterFaceType_Int32:
		uid = v.Int32
	case *pb.InterFaceType_Int64:
		uid = int32(v.Int64)
	case *pb.InterFaceType_Str:
		i, err := strconv.ParseInt(v.Str, 10, 32)
		if err != nil {
			// 无效UID，将-1写入缓存
			cacheInvalidSession(sessionID)
			return 0, fmt.Errorf("invalid uid string: %s", v.Str)
		}
		uid = int32(i)
	default:
		// 意外类型，将-1写入缓存
		cacheInvalidSession(sessionID)
		return 0, fmt.Errorf("unexpected uid type")
	}

	if uid <= 0 {
		// 无效UID，将-1写入缓存
		cacheInvalidSession(sessionID)
		return 0, fmt.Errorf("invalid uid: %d", uid)
	}

	// 将结果存入Redis (永远使用3600秒作为TTL)
	redisSetReq := &pb.RedisSetStringRequest{
		Key:   redisKey,
		Value: strconv.FormatInt(int64(uid), 10),
		Ttl:   3600, // 1小时
	}

	gateway.ExecRedisSet(redisSetReq)

	// 将结果存入内存缓存
	sessionCache.Set(sessionID, uid)

	return uid, nil
}

// 缓存无效会话（将-1写入缓存）
func cacheInvalidSession(sessionID string) {
	// 内存缓存设为-1
	sessionCache.Set(sessionID, -1)

	// Redis缓存设为-1
	redisKey := fmt.Sprintf("session:session:%s", sessionID)
	redisSetReq := &pb.RedisSetStringRequest{
		Key:   redisKey,
		Value: "-1",
		Ttl:   3600, // 1小时
	}
	gateway.ExecRedisSet(redisSetReq)
}

// SaveSession 保存新的会话信息（仅保存到数据库）
func SaveSession(sessionID string, uid int32) error {
	// 保存到数据库
	sqlQuery := fmt.Sprintf("INSERT INTO session_db (session_id, uid) VALUES ('%s', %d)", sessionID, uid)
	sqlReq := &pb.SqlRequest{
		Sql: sqlQuery,
		Db:  pb.SqlDatabases_Session,
	}

	_, err := gateway.ExecSQL(sqlReq)
	if err != nil {
		return fmt.Errorf("database error: %v", err)
	}

	return nil
}

// DeleteSession 删除会话
func DeleteSession(sessionID string) error {
	// 1. 从数据库删除
	sqlQuery := fmt.Sprintf("DELETE FROM session_db WHERE session_id = '%s'", sessionID)
	sqlReq := &pb.SqlRequest{
		Sql: sqlQuery,
		Db:  pb.SqlDatabases_Session,
	}

	_, err := gateway.ExecSQL(sqlReq)
	if err != nil {
		return fmt.Errorf("database error: %v", err)
	}

	// 2. 将缓存替换为无效内容（-1）
	cacheInvalidSession(sessionID)

	return nil
}
