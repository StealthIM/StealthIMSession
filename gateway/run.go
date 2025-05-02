package gateway

import (
	"errors"
	"math/rand"

	"google.golang.org/grpc"
)

// chooseConn 随机选择链接
func chooseConn() (*grpc.ClientConn, error) {
	if len(conns) == 0 {
		return nil, errors.New("No available connections")
	}
	for {
		conntmp := conns[rand.Intn(len(conns))]
		if conntmp != nil {
			return conntmp, nil
		}
	}
}
