package grpc

import (
	pb "StealthIMSession/StealthIM.Session"
	"StealthIMSession/config"
	"context"
	"log"
	"net"
	"strconv"

	"google.golang.org/grpc"
)

var cfg config.Config

type server struct {
	pb.StealthIMSessionServer
}

func (s *server) Ping(ctx context.Context, in *pb.PingRequest) (*pb.Pong, error) {
	return &pb.Pong{}, nil
}

// Start 启动 GRPC 服务
func Start(rCfg config.Config) {
	cfg = rCfg
	lis, err := net.Listen("tcp", rCfg.GRPCProxy.Host+":"+strconv.Itoa(rCfg.GRPCProxy.Port))
	if err != nil {
		log.Fatalf("[GRPC]Failed to listen: %v", err)
	}
	s := grpc.NewServer()
	pb.RegisterStealthIMSessionServer(s, &server{})
	log.Printf("[GRPC]Server listening at %v", lis.Addr())
	if err := s.Serve(lis); err != nil {
		log.Fatalf("[GRPC]Failed to serve: %v", err)
	}
}
