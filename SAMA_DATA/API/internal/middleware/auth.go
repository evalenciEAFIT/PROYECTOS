package middleware

import (
	"os"

	"github.com/gofiber/fiber/v2"
)

// APIKeyAuth validates that the incoming request has a valid X-API-Key header
func APIKeyAuth(c *fiber.Ctx) error {
	apiKey := c.Get("X-API-Key")
	expectedKey := os.Getenv("API_KEY")

	if expectedKey == "" {
		// If no key is configured in the environment, we might want to block all or allow all.
		// For security, blocking if not configured is better, but depends on use case.
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "API Key is not configured on the server",
		})
	}

	if apiKey != expectedKey {
		return c.Status(fiber.StatusUnauthorized).JSON(fiber.Map{
			"error": "Unauthorized. Invalid or missing X-API-Key header",
		})
	}

	// Continue to the next handler
	return c.Next()
}
