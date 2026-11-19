package store

import (
	"errors"
	"io/fs"
	"path/filepath"
)

// GetRatesFxMonitor reads rates_fx_monitor.json written by the Python RatesFxMonitorBuilder
// (plan 34, D-171) and returns it as is.
//
// Purpose: serve the 利率汇率 page: bond and RMB rows (level, changes, percentile, alerts,
// history), flags and the government curve snapshot.
// Contract: no file returns ErrNotFound; a malformed file returns an error.
// Test cases: TC-ST-029 present / absent / malformed, TC-API-016 route.
func (s *JSONStore) GetRatesFxMonitor() (map[string]any, error) {
	var out map[string]any
	err := readJSON(filepath.Join(s.dir, "rates_fx_monitor.json"), &out)
	if errors.Is(err, fs.ErrNotExist) {
		return nil, ErrNotFound
	}
	if err != nil {
		return nil, err
	}
	return out, nil
}
