package repository

import (
	"context"

	"SAMA_DATA_API/internal/config"
	"SAMA_DATA_API/internal/models"
)

type VariableRepository struct{}

func NewVariableRepository() *VariableRepository {
	return &VariableRepository{}
}

func (r *VariableRepository) GetAll() ([]models.Variable, error) {
	query := `SELECT variable_id, variable_name, variable_description, variable_unit FROM sama_iot_storage.variables`

	rows, err := config.DB.Query(context.Background(), query)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var variables []models.Variable
	for rows.Next() {
		var v models.Variable
		if err := rows.Scan(&v.VariableID, &v.VariableName, &v.VariableDescription, &v.VariableUnit); err != nil {
			return nil, err
		}
		variables = append(variables, v)
	}

	return variables, nil
}
