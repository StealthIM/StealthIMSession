package grpc

import (
	pb "StealthIMSession/StealthIM.Session"
	"StealthIMSession/autoclean"
	"StealthIMSession/cache"
	"StealthIMSession/config"
	"context"
	"crypto/rand"
	"encoding/hex"
	"log"
	"net"
	"sync"

	"google.golang.org/grpc"
)

var (
	sessionServer   *grpc.Server
	sessionLock     sync.Mutex
	sessionListener net.Listener
	sessionCleaner  *autoclean.SessionCleaner
)

// Set 设置新的会话
func (s *server) Set(ctx context.Context, in *pb.SetRequest) (*pb.SetResponse, error) {
	if config.LatestConfig.GRPCProxy.Log {
		log.Println("[GRPC] Call Set")
	}
	// 生成随机会话ID
	sessionID, err := generateSessionID()
	if err != nil {
		return &pb.SetResponse{
			Result: &pb.Result{
				Code: 1,
				Msg:  "Failed to generate session",
			},
		}, nil
	}

	// 保存会话到数据库
	err = cache.SaveSession(sessionID, in.Uid)
	if err != nil {
		return &pb.SetResponse{
			Result: &pb.Result{
				Code: 2,
				Msg:  "Failed to save session",
			},
		}, nil
	}

	return &pb.SetResponse{
		Result: &pb.Result{
			Code: 0,
			Msg:  "",
		},
		Session: sessionID,
	}, nil
}

// Get 获取会话信息
func (s *server) Get(ctx context.Context, in *pb.GetRequest) (*pb.GetResponse, error) {
	if config.LatestConfig.GRPCProxy.Log {
		log.Println("[GRPC] Call Get")
	}
	uid, err := cache.GetUserIDBySession(in.Session)
	if err != nil {
		return &pb.GetResponse{
			Result: &pb.Result{
				Code: 1,
				Msg:  "Session not found",
			},
		}, nil
	}

	return &pb.GetResponse{
		Result: &pb.Result{
			Code: 0,
			Msg:  "",
		},
		Uid: uid,
	}, nil
}

// Del 删除会话
func (s *server) Del(ctx context.Context, in *pb.DelRequest) (*pb.DelResponse, error) {
	if config.LatestConfig.GRPCProxy.Log {
		log.Println("[GRPC] Call Del")
	}
	err := cache.DeleteSession(in.Session)
	if err != nil {
		return &pb.DelResponse{
			Result: &pb.Result{
				Code: 1,
				Msg:  "Failed to delete session",
			},
		}, nil
	}

	return &pb.DelResponse{
		Result: &pb.Result{
			Code: 0,
			Msg:  "",
		},
	}, nil
}

// Reload 重新加载配置和服务
func (s *server) Reload(ctx context.Context, in *pb.ReloadRequest) (*pb.ReloadResponse, error) {
	log.Println("[Session] Received reload request")

	// 异步执行重载，避免阻塞GRPC调用
	go ReloadSessionService()

	return &pb.ReloadResponse{
		Result: &pb.Result{
			Code: 0,
			Msg:  "",
		},
	}, nil
}

// generateSessionID 生成随机会话ID
func generateSessionID() (string, error) {
	b := make([]byte, 16)
	_, err := rand.Read(b)
	if err != nil {
		return "", err
	}
	return hex.EncodeToString(b), nil
}

// ReloadSessionService 重新加载会话服务
func ReloadSessionService() {
	sessionLock.Lock()
	defer sessionLock.Unlock()

	log.Println("[Config] Reloading config...")

	// 记录重载前的配置
	oldExpireHours := config.LatestConfig.Session.ExpireHours
	oldCleanInterval := config.LatestConfig.Session.CleanInterval

	// 重新加载配置
	config.ReloadConf()

	// 检查清理相关配置是否变化
	configChanged := oldExpireHours != config.LatestConfig.Session.ExpireHours ||
		oldCleanInterval != config.LatestConfig.Session.CleanInterval

	// 只有当清理相关配置变化时才重建清理器
	if configChanged {
		log.Println("[Session] Rebuilding cleaner...")

		// 停止当前清理器
		if sessionCleaner != nil {
			sessionCleaner.Stop()
		}

		// 重新创建清理器
		sessionCleaner = autoclean.NewSessionCleaner()
		sessionCleaner.Start()

		log.Println("[Session] Cleaner rebuilt")
	}

	log.Println("[Config] Reload completed")
}
