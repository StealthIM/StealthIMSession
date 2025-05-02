package config

// Config 主配置
type Config struct {
	DBGateway DBGatewayConfig `toml:"dbgateway"`
	GRPCProxy GRPCProxyConfig `toml:"grpc"`
	Cache     CacheConfig     `toml:"cache"`
	Session   SessionConfig   `toml:"session"`
}

// GRPCProxyConfig grpc Server配置
type GRPCProxyConfig struct {
	Host string `toml:"host"`
	Port int    `toml:"port"`
	Log  bool   `toml:"log"`
}

// CacheConfig 缓存配置
type CacheConfig struct {
	MemTimeout   int `toml:"mem_timeout"`
	MemMaxsize   int `toml:"mem_maxsize"`
	MemCleantime int `toml:"mem_cleantime"`
}

// DBGatewayConfig grpc DBGateway 配置
type DBGatewayConfig struct {
	Host    string `toml:"host"`
	Port    int    `toml:"port"`
	ConnNum int    `toml:"conn_num"`
	Timeout int    `toml:"sql_timeout"`
}

// SessionConfig 会话配置
type SessionConfig struct {
	ExpireHours   int `toml:"expire_hours"`   // 会话过期时间（小时）
	CleanInterval int `toml:"clean_interval"` // 清理间隔（分钟）
}
