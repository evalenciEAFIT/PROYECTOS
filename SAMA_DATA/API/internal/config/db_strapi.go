package config

import (
"context"
"fmt"
"log"
"os"
"time"

"github.com/jackc/pgx/v5/pgxpool"
)

var StrapiDB *pgxpool.Pool

func ConnectStrapiDB() {
host := os.Getenv("DB_HOST")
port := os.Getenv("DB_PORT")
user := os.Getenv("DB_USER")
password := os.Getenv("DB_PASSWORD")
dbname := "sigran_db_strapi"

dsn := fmt.Sprintf("postgres://%s:%s@%s:%s/%s?sslmode=disable", user, password, host, port, dbname)

config, err := pgxpool.ParseConfig(dsn)
if err != nil {
log.Fatalf("Unable to parse Strapi database config: %v\n", err)
}

config.MaxConns = 10
config.MinConns = 2
config.MaxConnLifetime = time.Hour
config.MaxConnIdleTime = 30 * time.Minute

pool, err := pgxpool.NewWithConfig(context.Background(), config)
if err != nil {
log.Fatalf("Unable to connect to Strapi database: %v\n", err)
}

if err := pool.Ping(context.Background()); err != nil {
log.Fatalf("Ping to Strapi database failed: %v\n", err)
}

StrapiDB = pool
log.Println("Connected to PostgreSQL (Strapi) successfully via pgxpool")
}

func CloseStrapiDB() {
if StrapiDB != nil {
StrapiDB.Close()
}
}
