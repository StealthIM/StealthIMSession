package autoclean

import (
	pb "StealthIMSession/StealthIM.DBGateway"
	"StealthIMSession/config"
	"StealthIMSession/gateway"
	"fmt"
	"log"
	"time"
)

// SessionCleaner 会话清理器
type SessionCleaner struct {
	running       bool
	stopChan      chan struct{}
	expireHours   int
	cleanInterval int
}

// NewSessionCleaner 创建新的会话清理器
func NewSessionCleaner() *SessionCleaner {
	return &SessionCleaner{
		running:       false,
		stopChan:      make(chan struct{}),
		expireHours:   config.LatestConfig.Session.ExpireHours,
		cleanInterval: config.LatestConfig.Session.CleanInterval,
	}
}

// Start 开始会话清理任务
func (sc *SessionCleaner) Start() {
	if sc.running {
		log.Println("[Cleaner] Cleaner already running")
		return
	}

	sc.running = true
	log.Printf("[Cleaner] Session cleaner started.\n")

	// 延迟10秒启动清理循环
	go func() {
		time.Sleep(10 * time.Second)
		sc.cleanerLoop()
	}()
}

// Stop 停止会话清理任务
func (sc *SessionCleaner) Stop() {
	if !sc.running {
		return
	}

	log.Println("[Cleaner] Stopping cleaner...")
	sc.stopChan <- struct{}{}
	sc.running = false
}

// cleanerLoop 定期清理过期会话的循环
func (sc *SessionCleaner) cleanerLoop() {
	// 首次启动时执行一次清理
	sc.cleanExpiredSessions()

	// 创建定时器，按照配置的间隔时间定时执行
	ticker := time.NewTicker(time.Duration(sc.cleanInterval) * time.Minute)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			sc.cleanExpiredSessions()
		case <-sc.stopChan:
			log.Println("[Cleaner] Session cleaner stopped")
			return
		}
	}
}

// cleanExpiredSessions 执行过期会话清理
func (sc *SessionCleaner) cleanExpiredSessions() {
	log.Println("[Cleaner] Starting to clean...")

	// 计算过期时间点
	expirationTime := time.Now().Add(-time.Duration(sc.expireHours) * time.Hour)
	formattedTime := expirationTime.Format("2006-01-02 15:04:05")

	// 构建SQL查询，删除所有过期的会话
	sqlQuery := fmt.Sprintf("DELETE FROM session_db WHERE created_at < '%s'", formattedTime)

	// 使用 START TRANSACTION 和 COMMIT 将查询挂到后台
	backgroundQuery := fmt.Sprintf("START TRANSACTION; %s; COMMIT;", sqlQuery)

	sqlReq := &pb.SqlRequest{
		Sql: backgroundQuery,
		Db:  pb.SqlDatabases_Session,
	}

	// 执行SQL
	_, err := gateway.ExecSQL(sqlReq)
	if err != nil {
		log.Printf("[Cleaner] Error cleaning expired sessions: %v", err)
		return
	}

	log.Printf("[Cleaner] Clean started.")
}
