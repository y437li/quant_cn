package store

import (
	"errors"
	"io/fs"
	"path/filepath"
)

// FactorReturns are compounded factor returns over fixed windows (fractions).
type FactorReturns struct {
	D1  *float64 `json:"d1"`
	W1  *float64 `json:"w1"`
	M1  *float64 `json:"m1"`
	M3  *float64 `json:"m3"`
	Ytd *float64 `json:"ytd"`
	Y1  *float64 `json:"y1"`
}

// MonitoredFactor is one risk-model factor: window returns, volatility and daily series.
type MonitoredFactor struct {
	Factor        string        `json:"factor"`
	Label         string        `json:"label"`
	Kind          string        `json:"kind"`
	Ret           FactorReturns `json:"ret"`
	ForecastVol   *float64      `json:"forecast_vol"`
	RealizedVol21 *float64      `json:"realized_vol_21"`
	RealizedVol63 *float64      `json:"realized_vol_63"`
	VolRatio      *float64      `json:"vol_ratio"`
	SigmaMove     *float64      `json:"sigma_move"`
	Cum           []*float64    `json:"cum"`
	Forecast      []*float64    `json:"forecast"`
	Realized      []*float64    `json:"realized"`
}

// FactorMonitor is the factor_monitor.json document written by the Python
// FactorMonitorBuilder (plan 15 ph7c, D-132).
type FactorMonitor struct {
	AsOf      string            `json:"as_of"`
	Model     string            `json:"model"`
	NSessions int               `json:"n_sessions"`
	Dates     []string          `json:"dates"`
	Factors   []MonitoredFactor `json:"factors"`
}

// GetFactorMonitor reads factor_monitor.json from the data folder on every call, so
// `make factor-monitor` refreshes the page without a server restart.
//
// Purpose: serve the Python-built factor monitor as is (APP_STANDARD §1).
// Contract: no input; returns the document with non-nil slices. A missing file returns the
// empty document and no error; a malformed file returns an error.
// Test cases: TC-ST-013 fixture present, TC-ST-014 file absent / null slices, TC-ST-015 malformed.
func (s *JSONStore) GetFactorMonitor() (FactorMonitor, error) {
	var m FactorMonitor
	err := readJSON(filepath.Join(s.dir, "factor_monitor.json"), &m)
	if errors.Is(err, fs.ErrNotExist) {
		return fillMonitor(FactorMonitor{}), nil
	}
	if err != nil {
		return FactorMonitor{}, err
	}
	return fillMonitor(m), nil
}

func fillMonitor(m FactorMonitor) FactorMonitor {
	if m.Dates == nil {
		m.Dates = []string{}
	}
	if m.Factors == nil {
		m.Factors = []MonitoredFactor{}
	}
	for i := range m.Factors {
		f := &m.Factors[i]
		if f.Cum == nil {
			f.Cum = []*float64{}
		}
		if f.Forecast == nil {
			f.Forecast = []*float64{}
		}
		if f.Realized == nil {
			f.Realized = []*float64{}
		}
	}
	return m
}
