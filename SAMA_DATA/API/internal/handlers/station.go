package handlers

import (
	"SAMA_DATA_API/internal/service"

	"github.com/gofiber/fiber/v2"
)

type StationHandler struct {
	Service *service.StationService
}

func NewStationHandler(service *service.StationService) *StationHandler {
	return &StationHandler{Service: service}
}

// GetStations godoc
// @Summary List all stations
// @Description get all available stations from the database
// @Tags stations
// @Accept json
// @Produce json
// @Security ApiKeyAuth
// @Success 200 {object} map[string]interface{}
// @Router /api/v1/stations [get]
func (h *StationHandler) GetStations(c *fiber.Ctx) error {
	stations, err := h.Service.GetAllStations()
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Unable to fetch stations",
		})
	}

	return c.JSON(fiber.Map{
		"data":  stations,
		"count": len(stations),
	})
}
