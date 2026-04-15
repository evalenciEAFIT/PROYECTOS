package main

import (
	"SAMA_DATA_API/internal/config"
	"context"
	"fmt"
	"log"
)

func mainQuerySchema() {
	config.LoadEnv()
	config.ConnectDB()
	defer config.CloseDB()

	rows, err := config.DB.Query(context.Background(), "SELECT table_name FROM information_schema.tables WHERE table_schema='sama_iot_storage'")
	if err != nil {
		log.Fatal(err)
	}
	defer rows.Close()

	for rows.Next() {
		var table string
		rows.Scan(&table)
		fmt.Println(table)
	}
}
