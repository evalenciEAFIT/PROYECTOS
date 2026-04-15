package service

import (
	"bytes"
	"encoding/csv"
	"fmt"

	"SAMA_DATA_API/internal/models"
	"SAMA_DATA_API/internal/repository"

	"github.com/xuri/excelize/v2"
)

type MeasurementService struct {
	Repo *repository.MeasurementRepository
}

func NewMeasurementService(repo *repository.MeasurementRepository) *MeasurementService {
	return &MeasurementService{Repo: repo}
}

func (s *MeasurementService) GetMeasurements(limit, offset int, aggregate, startTime, endTime, stations, variables string) ([]models.Measurement, error) {
	return s.Repo.GetFiltered(limit, offset, aggregate, startTime, endTime, stations, variables)
}

// GenerateCSV exports models to CSV format byte buffer
func (s *MeasurementService) GenerateCSV(data []models.Measurement) ([]byte, error) {
	var buf bytes.Buffer
	writer := csv.NewWriter(&buf)

	// Headers
	writer.Write([]string{"Timestamp", "Station Code", "Variable Name", "Variable Unit", "Quality", "Value"})

	for _, m := range data {
		record := []string{
			m.Timestamp.Format("2006-01-02 15:04:05-07:00"),
			m.StationCode,
			m.VariableName,
			m.VariableUnit,
			m.Quality,
			fmt.Sprintf("%f", m.Value),
		}
		if err := writer.Write(record); err != nil {
			return nil, err
		}
	}
	writer.Flush()
	return buf.Bytes(), nil
}

// GenerateExcel exports models to Excel format byte buffer
func (s *MeasurementService) GenerateExcel(data []models.Measurement) ([]byte, error) {
	f := excelize.NewFile()
	defer f.Close()

	sheet := "Sheet1"

	f.SetCellValue(sheet, "A1", "Timestamp")
	f.SetCellValue(sheet, "B1", "Station Code")
	f.SetCellValue(sheet, "C1", "Variable Name")
	f.SetCellValue(sheet, "D1", "Variable Unit")
	f.SetCellValue(sheet, "E1", "Quality")
	f.SetCellValue(sheet, "F1", "Value")

	for i, m := range data {
		row := i + 2 // 1 is header
		f.SetCellValue(sheet, fmt.Sprintf("A%d", row), m.Timestamp.Format("2006-01-02 15:04:05-07:00"))
		f.SetCellValue(sheet, fmt.Sprintf("B%d", row), m.StationCode)
		f.SetCellValue(sheet, fmt.Sprintf("C%d", row), m.VariableName)
		f.SetCellValue(sheet, fmt.Sprintf("D%d", row), m.VariableUnit)
		f.SetCellValue(sheet, fmt.Sprintf("E%d", row), m.Quality)
		f.SetCellValue(sheet, fmt.Sprintf("F%d", row), m.Value)
	}

	var buf bytes.Buffer
	if err := f.Write(&buf); err != nil {
		return nil, err
	}

	return buf.Bytes(), nil
}
