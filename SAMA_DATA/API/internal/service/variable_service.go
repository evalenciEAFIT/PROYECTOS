package service

import (
	"SAMA_DATA_API/internal/models"
	"SAMA_DATA_API/internal/repository"
)

type VariableService struct {
	Repo *repository.VariableRepository
}

func NewVariableService(repo *repository.VariableRepository) *VariableService {
	return &VariableService{Repo: repo}
}

func (s *VariableService) GetAllVariables() ([]models.Variable, error) {
	return s.Repo.GetAll()
}
