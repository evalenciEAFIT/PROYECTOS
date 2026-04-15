package config

import (
	"context"
	"fmt"
	"log"
	"os"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/joho/godotenv"
)

var DB *pgxpool.Pool

func LoadEnv() {
	err := godotenv.Load()
	if err != nil {
		log.Println("No .env file found, reading environment variables from OS")
	}
}

func ConnectDB() {
	host := os.Getenv("DB_HOST")
	port := os.Getenv("DB_PORT")
	user := os.Getenv("DB_USER")
	password := os.Getenv("DB_PASSWORD")
	dbname := os.Getenv("DB_NAME")

	dsn := fmt.Sprintf("postgres://%s:%s@%s:%s/%s?sslmode=disable", user, password, host, port, dbname)

	config, err := pgxpool.ParseConfig(dsn)
	if err != nil {
		log.Fatalf("Unable to parse database config: %v\n", err)
	}

	// Optimizations for TimescaleDB / High Performance
	config.MaxConns = 50
	config.MinConns = 10
	config.MaxConnLifetime = time.Hour
	config.MaxConnIdleTime = 30 * time.Minute

	pool, err := pgxpool.NewWithConfig(context.Background(), config)
	if err != nil {
		log.Fatalf("Unable to connect to database: %v\n", err)
	}

	// Ping the DB to ensure connection happens right away
	if err := pool.Ping(context.Background()); err != nil {
		log.Fatalf("Ping to database failed: %v\n", err)
	}

	DB = pool
	log.Println("Connected to PostgreSQL (TimescaleDB) successfully via pgxpool")
}

func CloseDB() {
	if DB != nil {
		DB.Close()
	}
}
