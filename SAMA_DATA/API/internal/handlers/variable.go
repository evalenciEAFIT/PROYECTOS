package handlers

import (
	"SAMA_DATA_API/internal/service"

	"github.com/gofiber/fiber/v2"
)

type VariableHandler struct {
	Service *service.VariableService
}

func NewVariableHandler(service *service.VariableService) *VariableHandler {
	return &VariableHandler{Service: service}
}

// GetVariables godoc
// @Summary List all variables
// @Description get all available variables from the database
// @Tags variables
// @Accept json
// @Produce json
// @Security ApiKeyAuth
// @Success 200 {object} map[string]interface{}
// @Router /api/v1/variables [get]
func (h *VariableHandler) GetVariables(c *fiber.Ctx) error {
	variables, err := h.Service.GetAllVariables()
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Unable to fetch variables",
		})
	}

	return c.JSON(fiber.Map{
		"data":  variables,
		"count": len(variables),
	})
}
