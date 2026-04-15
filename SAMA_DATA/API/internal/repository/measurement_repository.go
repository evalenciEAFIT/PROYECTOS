package repository

import (
	"context"
	"fmt"
	"strings"

	"SAMA_DATA_API/internal/config"
	"SAMA_DATA_API/internal/models"
)

type MeasurementRepository struct{}

func NewMeasurementRepository() *MeasurementRepository {
	return &MeasurementRepository{}
}

func (r *MeasurementRepository) GetFiltered(limit, offset int, aggregate, startTime, endTime, stations, variables string) ([]models.Measurement, error) {
	args := []interface{}{}
	argId := 1

	var queryBuilder strings.Builder

	timestampCol := "m.measurement_timestamp"
	isPrecip5m := variables == "precipitacion" && aggregate == "5m"

	if isPrecip5m {
		timestampCol = "m.bucket"
		queryBuilder.WriteString(`
			SELECT 
				m.bucket AS bucket,
				s.station_id,
				s.station_code,
				'precipitacion' AS variable_name,
				'mm' AS variable_unit,
				'AGG' as quality,
				m.precip_sum as value,
				s.latitud AS latitude,
				s.longitud AS longitude,
				s.ubicacion AS location
			FROM sama_iot_storage.mv_precipitation_5min m
			JOIN sama_iot_storage.stations s ON m.station_id = s.station_id
			WHERE 1=1
		`)
	} else if aggregate != "" {
		queryBuilder.WriteString(fmt.Sprintf(`
			SELECT 
				time_bucket('%s', m.measurement_timestamp) AS bucket,
				s.station_id,
				s.station_code,
				v.variable_name,
				v.variable_unit,
				'AGG' as quality,
				CASE 
					WHEN v.variable_name ILIKE 'precipitacion%%' THEN SUM(m.measured_value) 
					ELSE AVG(m.measured_value) 
				END as value,
				s.latitud AS latitude,
				s.longitud AS longitude,
				s.ubicacion AS location
			FROM sama_iot_storage.measurements m
			JOIN sama_iot_storage.stations s ON m.station_id = s.station_id
			JOIN sama_iot_storage.variables v ON m.variable_id = v.variable_id
			WHERE 1=1
		`, aggregate))
	} else {
		queryBuilder.WriteString(`
			SELECT 
				m.measurement_timestamp,
				s.station_id,
				s.station_code,
				v.variable_name,
				v.variable_unit,
				m.quality::text,
				m.measured_value,
				s.latitud AS latitude,
				s.longitud AS longitude,
				s.ubicacion AS location
			FROM sama_iot_storage.measurements m
			JOIN sama_iot_storage.stations s ON m.station_id = s.station_id
			JOIN sama_iot_storage.variables v ON m.variable_id = v.variable_id
			WHERE 1=1
		`)
	}

	// Filters
	if startTime != "" {
		queryBuilder.WriteString(fmt.Sprintf(" AND %s >= $%d", timestampCol, argId))
		args = append(args, startTime)
		argId++
	}
	if endTime != "" {
		queryBuilder.WriteString(fmt.Sprintf(" AND %s <= $%d", timestampCol, argId))
		args = append(args, endTime)
		argId++
	}

	if stations != "" {
		stationList := strings.Split(stations, ",")
		placeholders := []string{}
		for _, st := range stationList {
			placeholders = append(placeholders, fmt.Sprintf("$%d", argId))
			args = append(args, strings.TrimSpace(st))
			argId++
		}
		queryBuilder.WriteString(fmt.Sprintf(" AND s.station_code IN (%s)", strings.Join(placeholders, ",")))
	}

	if isPrecip5m {
		// mv_precipitation_5min only has precipitacion
	} else if variables != "" {
		varList := strings.Split(variables, ",")
		placeholders := []string{}
		for _, va := range varList {
			placeholders = append(placeholders, fmt.Sprintf("$%d", argId))
			args = append(args, strings.TrimSpace(va))
			argId++
		}
		queryBuilder.WriteString(fmt.Sprintf(" AND v.variable_name IN (%s)", strings.Join(placeholders, ",")))
	}

	if isPrecip5m {
		queryBuilder.WriteString(" ORDER BY m.bucket DESC")
	} else if aggregate != "" {
		queryBuilder.WriteString(" GROUP BY bucket, s.station_id, s.station_code, v.variable_name, v.variable_unit, s.latitud, s.longitud, s.ubicacion")
		queryBuilder.WriteString(" ORDER BY bucket DESC")
	} else {
		queryBuilder.WriteString(" ORDER BY m.measurement_timestamp DESC")
	}

	if limit > 0 {
		queryBuilder.WriteString(fmt.Sprintf(" LIMIT $%d OFFSET $%d", argId, argId+1))
		args = append(args, limit, offset)
	} else {
		if offset > 0 {
			queryBuilder.WriteString(fmt.Sprintf(" OFFSET $%d", argId))
			args = append(args, offset)
		}
	}

	query := queryBuilder.String()

	rows, err := config.DB.Query(context.Background(), query, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var data []models.Measurement
	for rows.Next() {
		var m models.Measurement
		if err := rows.Scan(&m.Timestamp, &m.StationID, &m.StationCode, &m.VariableName, &m.VariableUnit, &m.Quality, &m.Value, &m.Latitude, &m.Longitude, &m.Location); err != nil {
			return nil, err
		}
		data = append(data, m)
	}

	if err := rows.Err(); err != nil {
		return nil, err
	}

	return data, nil
}
