package models

import (
	"time"
)

type Station struct {
	StationID   int16    `json:"station_id"`   // smallint serial
	StationCode string   `json:"station_code"` // char(7)
	Latitude    *float64 `json:"latitude"`
	Longitude   *float64 `json:"longitude"`
	Location    *string  `json:"location"`
	Municipio   *string  `json:"municipio"`
	Region      *string  `json:"region"`
	Tipo        *string  `json:"tipo"`
}

type Variable struct {
	VariableID          int16  `json:"variable_id"`          // smallint serial
	VariableName        string `json:"variable_name"`        // varchar(20)
	VariableDescription string `json:"variable_description"` // text
	VariableUnit        string `json:"variable_unit"`        // varchar(10)
}

type Measurement struct {
	Timestamp    time.Time `json:"timestamp"`
	StationID    int16     `json:"station_id,omitempty"`
	StationCode  string    `json:"station_code"`
	VariableName string    `json:"variable_name"`
	VariableUnit string    `json:"variable_unit"`
	Quality      string    `json:"quality"`
	Value        float32   `json:"value"`
	Latitude     *float64  `json:"latitude"`
	Longitude    *float64  `json:"longitude"`
	Location     *string   `json:"location"`
}

// Struct for paginated, filtered responses
type PaginatedResponse struct {
	Data       []Measurement `json:"data"`
	TotalRows  int           `json:"total_rows"`
	Offset     int           `json:"offset"`
	Limit      int           `json:"limit"`
	NextCursor *time.Time    `json:"next_cursor,omitempty"`
}
