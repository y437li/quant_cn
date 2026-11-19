package store

import (
	"errors"
	"io/fs"
	"path/filepath"
)

// GetSectorMonitor reads sector_monitor.json written by the Python SectorMonitorBuilder (plan 31
// ph4) and returns it as is.
//
// Purpose: serve the 行业监控 page: per sector the charts (70-city prices, sales briefs, contract
// liabilities, impairment, game approvals, 获利盘, realised vol) and the company table.
// Contract: no file returns ErrNotFound; a malformed file returns an error.
// Test cases: TC-ST-028 present / absent / malformed, TC-API-015 route.
func (s *JSONStore) GetSectorMonitor() (map[string]any, error) {
	var out map[string]any
	err := readJSON(filepath.Join(s.dir, "sector_monitor.json"), &out)
	if errors.Is(err, fs.ErrNotExist) {
		return nil, ErrNotFound
	}
	if err != nil {
		return nil, err
	}
	return out, nil
}
