package main

import (
	"bytes"
	"encoding/json"
	"log"
	"net/http"
	"os"
	"sync"
	"time"

	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/logger"
	"github.com/gofiber/fiber/v2/middleware/recover"
	"github.com/gofiber/template/html/v2"
	"github.com/joho/godotenv"
)

func main() {
	if err := godotenv.Load(); err != nil {
		log.Println("No .env file found")
	}

	engine := html.New("./views", ".html")
	app := fiber.New(fiber.Config{
		Views: engine,
	})

	app.Use(logger.New())
	app.Use(recover.New())

	// Static files
	app.Static("/public", "./public")

	// Render Main Page
	app.Get("/", func(c *fiber.Ctx) error {
		return c.Render("index", fiber.Map{
			"Title": "SAMA DATA - Dashboard Geoespacial",
		})
	})

	// Render Manual Page
	app.Get("/manual", func(c *fiber.Ctx) error {
		return c.Render("manual", fiber.Map{
			"Title": "SAMA DATA - Manual de Usuario",
		})
	})

	apiGroup := app.Group("/proxy/api")

	apiGroup.All("/*", proxyToAPI)

	// Logging Endpoint
	var logMutex sync.Mutex
	app.Post("/log_download", func(c *fiber.Ctx) error {
		type LogEntry struct {
			Name          string `json:"name"`
			Email         string `json:"email"`
			Institution   string `json:"institution"`
			Purpose       string `json:"purpose"`
			Format        string `json:"format"`
			StationCodes  string `json:"station_codes"`
			StationTypes  string `json:"station_types"`
			FilterSummary string `json:"filter_summary"`
			FileName      string `json:"file_name"`
			RecordCount   string `json:"record_count"`
			IPAddress     string `json:"ip_address"`
			OS            string `json:"os"`
			Browser       string `json:"browser"`
			Timestamp     string `json:"timestamp"`
		}

		var entry LogEntry
		if err := c.BodyParser(&entry); err != nil {
			return c.Status(400).JSON(fiber.Map{"error": "Invalid JSON"})
		}

		entry.IPAddress = c.IP()

		// Fill timestamp if empty
		if entry.Timestamp == "" {
			entry.Timestamp = time.Now().Format(time.RFC3339)
		}

		logLine, _ := json.Marshal(entry)
		logLine = append(logLine, '\n')

		logMutex.Lock()
		defer logMutex.Unlock()

		f, err := os.OpenFile("downloads.log", os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
		if err != nil {
			return c.Status(500).SendString("Error opening log file")
		}
		defer f.Close()

		if _, err := f.Write(logLine); err != nil {
			return c.Status(500).SendString("Error writing log")
		}

		return c.SendStatus(200)
	})

	// View Logs Endpoint
	app.Get("/downloads.log", func(c *fiber.Ctx) error {
		return c.SendFile("./downloads.log")
	})

	port := os.Getenv("PORT")
	if port == "" {
		port = "4000"
	}

	log.Fatal(app.Listen(":" + port))
}

func proxyToAPI(c *fiber.Ctx) error {
	apiBaseUrl := os.Getenv("API_BASE_URL")
	apiKey := os.Getenv("API_KEY")

	// Extract the sub-path requested (e.g. /proxy/api/stations -> /stations)
	path := c.Params("*")

	// Create request to target API
	targetUrl := apiBaseUrl + "/" + path
	if len(c.Request().URI().QueryString()) > 0 {
		targetUrl += "?" + string(c.Request().URI().QueryString())
	}

	req, err := http.NewRequest(c.Method(), targetUrl, bytes.NewReader(c.Body()))
	if err != nil {
		return c.Status(500).JSON(fiber.Map{"error": "Failed to create proxy request"})
	}

	// Copy content type if present
	if len(c.Request().Header.ContentType()) > 0 {
		req.Header.Set("Content-Type", string(c.Request().Header.ContentType()))
	}

	// Inject the secret API KEY
	req.Header.Set("X-API-Key", apiKey)

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return c.Status(500).JSON(fiber.Map{"error": "Failed to reach target API"})
	}

	// Copy response headers
	for k, vv := range resp.Header {
		for _, v := range vv {
			c.Set(k, v)
		}
	}

	c.Status(resp.StatusCode)

	// Stream the body for memory efficiency, preventing Dashboard OOMs with large CSVs
	// SendStream takes ownership and automatically calls Close() on the io.ReadCloser
	return c.SendStream(resp.Body)
}
