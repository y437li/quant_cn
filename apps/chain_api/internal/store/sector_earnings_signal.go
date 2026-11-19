package store

import (
	"errors"
	"io/fs"
	"path/filepath"
)

// GetSectorEarningsSignal reads sector_earnings_signal.json written by the Python
// SectorEarningsSignalBuilder (plan 35, D-172) and returns it as is.
//
// Purpose: serve the 财报季信号 table of the 行业监控 page: per Shenwan L2 sector the
// season's reading (share reported, best-surprise pre / reaction excess, prior rally,
// holders, status), recent history, past firings with outcomes and the record.
// Contract: no file returns ErrNotFound; a malformed file returns an error.
// Test cases: TC-ST-031 present / absent / malformed, TC-API-018 route.
func (s *JSONStore) GetSectorEarningsSignal() (map[string]any, error) {
	var out map[string]any
	err := readJSON(filepath.Join(s.dir, "sector_earnings_signal.json"), &out)
	if errors.Is(err, fs.ErrNotExist) {
		return nil, ErrNotFound
	}
	if err != nil {
		return nil, err
	}
	return out, nil
}
