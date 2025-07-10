package errorcode

// 8xx 成功
const (
	// Success 成功处理请求
	Success int32 = 800 + iota
)

// 9xx 通用错误
const (
	// ServerFailed 服务器未捕获异常
	ServerFailed int32 = 900 + iota
	// ServerRefused 服务器未能成功处理请求
	ServerRefused
	// ServerInternalComponentError 服务器运行时错误
	ServerInternalComponentError
	// ServerInternalNetworkError 服务器组件通信错误
	ServerInternalNetworkError
	// ServerOverload 服务器过载
	ServerOverload
	// ServerLimited 请求过大
	ServerLimited
	// ServerError 其它问题
	ServerError
)
