package errorcode

const (
	// SessionInternalError 一般内部错误
	SessionInternalError int32 = 1300 + iota
	// SessionNotFoundError 会话不存在
	SessionNotFoundError
)
