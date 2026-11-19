package store

import (
	"errors"
	"io/fs"
	"path/filepath"
)

// GetBuybackMonitor reads buyback_monitor.json written by the Python BuybackMonitorBuilder
// (plan 32, D-169) and returns it as is.
//
// Purpose: serve the 回购增持 page: per kind (buyback / increase) the live programmes with
// labels, the window's events, totals by purpose or holder type and funding, and months.
// Contract: no file returns ErrNotFound; a malformed file returns an error.
// Test cases: TC-ST-030 present / absent / malformed, TC-API-017 route.
func (s *JSONStore) GetBuybackMonitor() (map[string]any, error) {
	var out map[string]any
	err := readJSON(filepath.Join(s.dir, "buyback_monitor.json"), &out)
	if errors.Is(err, fs.ErrNotExist) {
		return nil, ErrNotFound
	}
	if err != nil {
		return nil, err
	}
	return out, nil
}
