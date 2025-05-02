package cache

import (
	"StealthIMSession/config"
	"math/rand"
	"sync"
	"time"
)

type item struct {
	value      int32
	expiration int64
}

// Cache 表示一个具有字符串键和int32值的内存缓存
type Cache struct {
	items    map[string]item
	mu       sync.RWMutex
	maxItems int // 最大缓存项数量
}

// New 创建一个新的缓存，并启动一个定期清理过期项目的协程
func New() *Cache {
	c := &Cache{
		items:    make(map[string]item),
		maxItems: config.LatestConfig.Cache.MemMaxsize,
	}

	// 启动一个协程定期清理过期项目
	go c.janitor()

	return c
}

// Set 向缓存添加一个键值对
func (c *Cache) Set(key string, value int32) {
	expiration := time.Now().Add(time.Duration(config.LatestConfig.Cache.MemTimeout) * time.Second).UnixNano()

	c.mu.Lock()
	defer c.mu.Unlock()

	// 检查是否超过项目数量限制
	if len(c.items) >= config.LatestConfig.Cache.MemMaxsize && c.items[key] == (item{}) {
		// 需要淘汰一个随机项
		c.evictRandom()
	}

	c.items[key] = item{
		value:      value,
		expiration: expiration,
	}
}

// evictRandom 随机淘汰一个缓存项
func (c *Cache) evictRandom() {
	// 确保在调用此方法前已获取写锁
	if len(c.items) == 0 {
		return
	}

	// 获取所有键
	keys := make([]string, 0, len(c.items))
	for k := range c.items {
		keys = append(keys, k)
	}

	// 随机选择一个键淘汰
	randomIndex := rand.Intn(len(keys))
	delete(c.items, keys[randomIndex])
}

// Get 通过键从缓存中检索值
// 第二个返回值表示键是否被找到
func (c *Cache) Get(key string) (int32, bool) {
	now := time.Now().UnixNano()

	c.mu.RLock()
	item, found := c.items[key]
	if !found || now > item.expiration {
		c.mu.RUnlock()
		return 0, false
	}
	c.mu.RUnlock()

	return item.value, true
}

// janitor 定期从缓存中删除过期的项目
func (c *Cache) janitor() {
	time.Sleep(1*time.Second)
	ticker := time.NewTicker(time.Duration(config.LatestConfig.Cache.MemCleantime) * time.Second)
	defer ticker.Stop()

	for range ticker.C {
		c.deleteExpired()
	}
}

// deleteExpired 高效地从缓存中删除所有过期项目
func (c *Cache) deleteExpired() {
	now := time.Now().UnixNano()

	// 预分配一个切片来存储需要删除的键
	// 这避免了在迭代时删除，并减少了锁定时间
	var keysToDelete []string

	// 第一阶段：识别过期的键（读锁）
	c.mu.RLock()
	// 以合理的容量预分配，避免重新分配
	keysToDelete = make([]string, 0, len(c.items)/10)
	for k, v := range c.items {
		if now > v.expiration {
			keysToDelete = append(keysToDelete, k)
		}
	}
	c.mu.RUnlock()

	// 只有在有项目需要删除时才获取写锁
	if len(keysToDelete) > 0 {
		c.mu.Lock()
		for _, k := range keysToDelete {
			// 在写锁下再次检查过期时间，因为它可能已经改变
			if item, found := c.items[k]; found && now > item.expiration {
				delete(c.items, k)
			}
		}
		c.mu.Unlock()
	}
}

// Delete 从缓存中删除一个键值对
func (c *Cache) Delete(key string) {
	c.mu.Lock()
	defer c.mu.Unlock()

	delete(c.items, key)
}
