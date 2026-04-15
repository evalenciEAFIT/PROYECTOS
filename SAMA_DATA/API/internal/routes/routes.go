package routes

import (
	"SAMA_DATA_API/internal/handlers"
	"SAMA_DATA_API/internal/middleware"

	"github.com/gofiber/fiber/v2"
)

func SetupRoutes(app *fiber.App, sh *handlers.StationHandler, vh *handlers.VariableHandler, mh *handlers.MeasurementHandler) {
	// Healthcheck (Public)
	app.Get("/health", func(c *fiber.Ctx) error {
		return c.JSON(fiber.Map{"status": "OK", "message": "API is running fast 🚀"})
	})

	api := app.Group("/api/v1")

	// Apply Auth Middleware to all /api/v1 routes
	api.Use(middleware.APIKeyAuth)

	api.Get("/stations", sh.GetStations)
	api.Get("/variables", vh.GetVariables)
	api.Get("/measurements", mh.GetMeasurements)
}
