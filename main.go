package main

import (
	"StealthIMSession/autoclean"
	"StealthIMSession/cache"
	"StealthIMSession/config"
	"StealthIMSession/gateway"
	"StealthIMSession/grpc"
	"log"
	"os"
)

func main() {
	cfg := config.ReadConf()
	log.Printf("Start server [%v]\n", config.Version)
	log.Printf("+ GRPC\n")
	log.Printf("    Host: %s\n", cfg.GRPCProxy.Host)
	log.Printf("    Port: %d\n", cfg.GRPCProxy.Port)
	log.Printf("+ DBGateway\n")
	log.Printf("    Host: %s\n", cfg.DBGateway.Host)
	log.Printf("    Port: %d\n", cfg.DBGateway.Port)
	log.Printf("    ConnNum: %d\n", cfg.DBGateway.ConnNum)
	log.Printf("+ Cache\n")
	log.Printf("    MemMaxsize: %d\n", cfg.Cache.MemMaxsize)
	log.Printf("    MemTimeout: %d\n", cfg.Cache.MemTimeout)
	log.Printf("    MemCleantime: %d\n", cfg.Cache.MemCleantime)

	// 初始化会话缓存
	cache.InitSessionCache()

	// 启动 DBGateway
	go gateway.InitConns()

	// 启动会话清理器
	disableCleaner := os.Getenv("STIMSESSION_DISABLE_CLEANER")
	if disableCleaner != "" {
		log.Println("Session cleaner is disabled")
	} else {
		sessionCleaner := autoclean.NewSessionCleaner()
		sessionCleaner.Start()
	}

	// 启动 GRPC 服务
	grpc.Start(cfg)
}
