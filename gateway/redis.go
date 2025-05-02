package gateway

import (
	pb "StealthIMSession/StealthIM.DBGateway"
	"StealthIMSession/config"
	"context"
	"time"
)

// ExecRedisGet 运行 Redis 查询
func ExecRedisGet(req *pb.RedisGetStringRequest) (*pb.RedisGetStringResponse, error) {
	mainlock.Lock()
	defer mainlock.Unlock()
	conn, err := chooseConn()
	if err != nil {
		return nil, err
	}
	ctx, cancel := context.WithTimeout(context.Background(), time.Duration(config.LatestConfig.DBGateway.Timeout)*time.Millisecond)
	defer cancel()
	c := pb.NewStealthIMDBGatewayClient(conn)
	res, err2 := c.RedisGet(ctx, req)
	return res, err2
}

// ExecRedisSet 运行 Redis 写入
func ExecRedisSet(req *pb.RedisSetStringRequest) (*pb.RedisSetResponse, error) {
	mainlock.Lock()
	defer mainlock.Unlock()
	conn, err := chooseConn()
	if err != nil {
		return nil, err
	}
	ctx, cancel := context.WithTimeout(context.Background(), time.Duration(config.LatestConfig.DBGateway.Timeout)*time.Millisecond)
	defer cancel()
	c := pb.NewStealthIMDBGatewayClient(conn)
	res, err2 := c.RedisSet(ctx, req)
	return res, err2
}

// ExecRedisBGet 运行 Redis 二进制查询
func ExecRedisBGet(req *pb.RedisGetBytesRequest) (*pb.RedisGetBytesResponse, error) {
	mainlock.Lock()
	defer mainlock.Unlock()
	conn, err := chooseConn()
	if err != nil {
		return nil, err
	}
	ctx, cancel := context.WithTimeout(context.Background(), time.Duration(config.LatestConfig.DBGateway.Timeout)*time.Millisecond)
	defer cancel()
	c := pb.NewStealthIMDBGatewayClient(conn)
	res, err2 := c.RedisBGet(ctx, req)
	return res, err2
}

// ExecRedisBSet 运行 Redis 二进制写入
func ExecRedisBSet(req *pb.RedisSetBytesRequest) (*pb.RedisSetResponse, error) {
	mainlock.Lock()
	defer mainlock.Unlock()
	conn, err := chooseConn()
	if err != nil {
		return nil, err
	}
	ctx, cancel := context.WithTimeout(context.Background(), time.Duration(config.LatestConfig.DBGateway.Timeout)*time.Millisecond)
	defer cancel()
	c := pb.NewStealthIMDBGatewayClient(conn)
	res, err2 := c.RedisBSet(ctx, req)
	return res, err2
}

// ExecRedisDel 运行 Redis 删除
func ExecRedisDel(req *pb.RedisDelRequest) (*pb.RedisDelResponse, error) {
	mainlock.Lock()
	defer mainlock.Unlock()
	conn, err := chooseConn()
	if err != nil {
		return nil, err
	}
	ctx, cancel := context.WithTimeout(context.Background(), time.Duration(config.LatestConfig.DBGateway.Timeout)*time.Millisecond)
	defer cancel()
	c := pb.NewStealthIMDBGatewayClient(conn)
	res, err2 := c.RedisDel(ctx, req)
	return res, err2
}
