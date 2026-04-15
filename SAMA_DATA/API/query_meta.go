package main

import (
	"SAMA_DATA_API/internal/config"
	"context"
	"fmt"
	"log"
)

func mainQueryMeta() {
	config.LoadEnv()
	config.ConnectDB()
	defer config.CloseDB()

	rows, err := config.DB.Query(context.Background(), "SELECT column_name, data_type FROM information_schema.columns WHERE table_schema='sama_iot_storage' AND table_name='metadata'")
	if err != nil {
		log.Fatal(err)
	}
	defer rows.Close()

	for rows.Next() {
		var col, typ string
		rows.Scan(&col, &typ)
		fmt.Printf("%s: %s\n", col, typ)
	}
}
