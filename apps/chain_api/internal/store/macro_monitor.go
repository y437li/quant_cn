package store

import (
	"errors"
	"io/fs"
	"path/filepath"
)

// MacroPoint is one monthly print of a macro line.
type MacroPoint struct {
	Month string  `json:"month"`
	Value float64 `json:"value"`
}

// MacroSeries is one monitored line: latest and previous print, change, 5-year percentile.
type MacroSeries struct {
	Key       string       `json:"key"`
	Name      string       `json:"name"`
	Group     string       `json:"group"`
	Unit      string       `json:"unit"`
	Month     string       `json:"month"`
	Value     *float64     `json:"value"`
	PrevMonth string       `json:"prev_month"`
	Prev      *float64     `json:"prev"`
	Change    *float64     `json:"change"`
	Pct5y     *float64     `json:"pct_5y"`
	NewPrint  bool         `json:"new_print"`
	History   []MacroPoint `json:"history"`
}

// MacroMonitor is the macro_monitor.json document written by the Python MacroMonitorBuilder
// (plan 15 ph7h).
type MacroMonitor struct {
	AsOf      string        `json:"as_of"`
	Missing   []string      `json:"missing"`
	NewPrints []string      `json:"new_prints"`
	Series    []MacroSeries `json:"series"`
}

// GetMacroMonitor reads macro_monitor.json on every call, so `make macro-monitor` refreshes the
// page without a server restart.
//
// Purpose: serve the Python-built macro monitor as is (APP_STANDARD §1).
// Contract: no input; returns the document with non-nil slices. A missing file returns the
// empty document and no error; a malformed file returns an error.
// Test cases: TC-ST-021 fixture present, TC-ST-022 file absent / null slices, TC-API-012 route.
func (s *JSONStore) GetMacroMonitor() (MacroMonitor, error) {
	var m MacroMonitor
	err := readJSON(filepath.Join(s.dir, "macro_monitor.json"), &m)
	if errors.Is(err, fs.ErrNotExist) {
		return fillMacro(MacroMonitor{}), nil
	}
	if err != nil {
		return MacroMonitor{}, err
	}
	return fillMacro(m), nil
}

func fillMacro(m MacroMonitor) MacroMonitor {
	if m.Missing == nil {
		m.Missing = []string{}
	}
	if m.NewPrints == nil {
		m.NewPrints = []string{}
	}
	if m.Series == nil {
		m.Series = []MacroSeries{}
	}
	for i := range m.Series {
		if m.Series[i].History == nil {
			m.Series[i].History = []MacroPoint{}
		}
	}
	return m
}
