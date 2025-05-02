package config

import (
	_ "embed" // Embed
	"fmt"
	"os"
)

//go:embed config.sample.toml
var defaultConfig string

func initCfg() {
	_, err := os.Stat(cfgPath)
	if err != nil {
		file, err := os.Create(cfgPath)
		if err != nil {
			fmt.Println("Error opening file:", err)
			os.Exit(10)
			return
		}
		_, err = file.WriteString(defaultConfig)
		if err != nil {
			file.Close()
			fmt.Println("Error writing to file:", err)
			os.Exit(10)
			return
		}
		file.Close()
		fmt.Println("Default Config Created")

		os.Exit(1)
	}
}
