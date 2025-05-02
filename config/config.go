package config

import (
	"flag"
	"log"
	"os"

	"github.com/pelletier/go-toml/v2"
)

// Version 版本号
const Version = "0.0.1"

var cfgPath = "config.toml"

var LatestConfig = &Config{}

// ReadConf 读取配置
func ReadConf() Config {
	flag.StringVar(&cfgPath, "config", "config.toml", "配置文件位置")
	flag.Parse()
	initCfg()
	data, err := os.ReadFile(cfgPath)
	if err != nil {
		log.Fatalf("Error reading config file: %v\n", err)
	}
	var config Config
	err = toml.Unmarshal(data, &config)
	if err != nil {
		log.Fatalf("Error unmarshalling config file: %v\n", err)
	}
	LatestConfig = &config
	return config
}

// ReloadConf 重新加载配置
func ReloadConf() {
	log.Printf("[Config] Reloading configuration from %s...", cfgPath)
	data, err := os.ReadFile(cfgPath)
	if err != nil {
		log.Printf("[Config] Error reading config file: %v\n", err)
		return
	}
	var config Config
	err = toml.Unmarshal(data, &config)
	if err != nil {
		log.Printf("[Config] Error unmarshalling config file: %v\n", err)
		return
	}
	LatestConfig = &config
	log.Printf("[Config] Configuration reloaded successfully")
}
