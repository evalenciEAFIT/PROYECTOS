package handlers

import (
	"fmt"
	"strconv"

	"SAMA_DATA_API/internal/models"
	"SAMA_DATA_API/internal/service"

	"github.com/gofiber/fiber/v2"
)

type MeasurementHandler struct {
	Service *service.MeasurementService
}

func NewMeasurementHandler(service *service.MeasurementService) *MeasurementHandler {
	return &MeasurementHandler{Service: service}
}

// GetMeasurements godoc
// @Summary Get measurements with filters
// @Description retrieve measurements applying time, station, and variable filters. Supports aggregation. Supports CSV/Excel export.
// @Tags measurements
// @Accept json
// @Produce json
// @Produce text/csv
// @Produce application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
// @Param start_time query string false "Start time (ISO8601)"
// @Param end_time query string false "End time (ISO8601)"
// @Param station_code query string false "Station codes (comma-separated)"
// @Param variable_name query string false "Variable names (comma-separated)"
// @Param aggregate query string false "Time bucket (e.g., 15m, 1h, 1d)"
// @Param format query string false "Format (json, csv, excel)"
// @Param limit query int false "Limit (default 1000)"
// @Param offset query int false "Offset (default 0)"
// @Security ApiKeyAuth
// @Success 200 {object} models.PaginatedResponse
// @Router /api/v1/measurements [get]
func (h *MeasurementHandler) GetMeasurements(c *fiber.Ctx) error {
	startTime := c.Query("start_time")
	endTime := c.Query("end_time")
	stations := c.Query("station_code")
	variables := c.Query("variable_name")
	aggregate := c.Query("aggregate")
	format := c.Query("format", "json") // json, csv, excel

	limitStr := c.Query("limit", "0")
	offsetStr := c.Query("offset", "0")

	limit, err := strconv.Atoi(limitStr)
	if err != nil {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{"error": "Invalid limit"})
	}
	offset, err := strconv.Atoi(offsetStr)
	if err != nil {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{"error": "Invalid offset"})
	}

	// No limit restriction (Sin limite)	// Fetch data via Service -> Repo Layer
	data, err := h.Service.GetMeasurements(limit, offset, aggregate, startTime, endTime, stations, variables)
	if err != nil {
		fmt.Println("DB Query Error:", err)
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{"error": "Error querying measurements"})
	}

	// Dynamic Output Formatting
	switch format {
	case "csv":
		csvBytes, err := h.Service.GenerateCSV(data)
		if err != nil {
			return c.Status(fiber.StatusInternalServerError).SendString("Error generating CSV")
		}
		c.Set("Content-Type", "text/csv")
		c.Set("Content-Disposition", "attachment; filename=measurements.csv")
		return c.Send(csvBytes)

	case "excel":
		excelBytes, err := h.Service.GenerateExcel(data)
		if err != nil {
			return c.Status(fiber.StatusInternalServerError).SendString("Error generating Excel")
		}
		c.Set("Content-Type", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
		c.Set("Content-Disposition", "attachment; filename=measurements.xlsx")
		return c.Send(excelBytes)

	default: // JSON
		response := models.PaginatedResponse{
			Data:      data,
			TotalRows: len(data),
			Offset:    offset,
			Limit:     limit,
		}
		return c.JSON(response)
	}
}
