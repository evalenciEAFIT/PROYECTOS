package repository

import (
	"context"

	"SAMA_DATA_API/internal/config"
	"SAMA_DATA_API/internal/models"
)

type StationRepository struct{}

func NewStationRepository() *StationRepository {
	return &StationRepository{}
}

func (r *StationRepository) GetAll() ([]models.Station, error) {
	query := `
		SELECT 
			station_id, 
			station_code, 
			latitud, 
			longitud, 
			ubicacion, 
			municipio, 
			region,
			tipo
		FROM sama_iot_storage.stations
	`

	rows, err := config.DB.Query(context.Background(), query)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var stations []models.Station
	for rows.Next() {
		var s models.Station
		if err := rows.Scan(&s.StationID, &s.StationCode, &s.Latitude, &s.Longitude, &s.Location, &s.Municipio, &s.Region, &s.Tipo); err != nil {
			return nil, err
		}
		stations = append(stations, s)
	}

	if err := rows.Err(); err != nil {
		return nil, err
	}

	return stations, nil
}
