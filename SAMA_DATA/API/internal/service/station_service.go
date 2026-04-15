package service

import (
	"SAMA_DATA_API/internal/models"
	"SAMA_DATA_API/internal/repository"
)

type StationService struct {
	Repo *repository.StationRepository
}

func NewStationService(repo *repository.StationRepository) *StationService {
	return &StationService{Repo: repo}
}

func (s *StationService) GetAllStations() ([]models.Station, error) {
	return s.Repo.GetAll()
}
