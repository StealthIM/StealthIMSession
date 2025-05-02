package gateway

import (
	pb "StealthIMSession/StealthIM.DBGateway"
	"StealthIMSession/config"
	"context"
	"fmt"
	"log"
	"sync"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
)

var conns []*grpc.ClientConn
var mainlock sync.Mutex

func createConn(connID int) {
	log.Printf("[DB]Connect %d", connID+1)
	conn, err := grpc.NewClient(fmt.Sprintf("%s:%d", config.LatestConfig.DBGateway.Host, config.LatestConfig.DBGateway.Port),
		grpc.WithTransportCredentials(
			insecure.NewCredentials()))
	if conn == nil {
		log.Printf("[DB]Connect %d Error %v\n", connID+1, err)
		conns[connID] = nil
		return
	}
	if err != nil {
		log.Printf("[DB]Connect %d Error %v\n", connID+1, err)
		conns[connID] = nil
		return
	}
	conns[connID] = conn
}

func checkAlive(connID int) {
	if len(conns) <= connID {
		return
	}
	for {
		if len(conns) <= connID {
			return
		}
		mainlock.Lock()
		if conns[connID] != nil {
			cli := pb.NewStealthIMDBGatewayClient(conns[connID])
			ctx, cancel := context.WithTimeout(context.Background(), time.Second)
			_, err := cli.Ping(ctx, &pb.PingRequest{})
			cancel()
			if err == nil {
				mainlock.Unlock()
				continue
			}
		}
		createConn(connID)
		mainlock.Unlock()
		time.Sleep(5 * time.Second)
	}
}

// InitConns 扩缩容连接
func InitConns() {
	defer func() {
		mainlock.Lock()
		for _, conn := range conns {
			conn.Close()
		}
		mainlock.Unlock()
	}()
	log.Printf("[DB]Init Conns\n")
	for {
		time.Sleep(time.Second * 1)
		var lenTmp = len(conns)
		if lenTmp < config.LatestConfig.DBGateway.ConnNum {
			log.Printf("[DB]Create Conn %d\n", lenTmp+1)
			mainlock.Lock()
			conns = append(conns, nil)
			mainlock.Unlock()
			go checkAlive(lenTmp)
		} else if lenTmp > config.LatestConfig.DBGateway.ConnNum {
			log.Printf("[DB]Delete Conn %d\n", lenTmp)
			mainlock.Lock()
			conns[lenTmp-1].Close()
			conns = conns[:lenTmp-1]
			mainlock.Unlock()
		} else {
			time.Sleep(time.Second * 5)
		}
	}
}
