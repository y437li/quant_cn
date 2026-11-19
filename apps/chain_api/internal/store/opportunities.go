package store

import (
	"errors"
	"io/fs"
	"path/filepath"
)

// GetOpportunities reads opportunities.json written by the Python OpportunityDocument
// (`make opportunity-list`, plan 21 ph5) and returns it as is.
//
// Purpose: serve the 机会清单 page: the day's listed names (new first, then the ones that
// stayed), near-misses with the missing rule, the names that dropped off and the rule
// thresholds.
// Contract: no file returns ErrNotFound; a malformed file returns an error.
// Test cases: TC-ST-033 present / absent / malformed, TC-API-020 route.
func (s *JSONStore) GetOpportunities() (map[string]any, error) {
	var out map[string]any
	err := readJSON(filepath.Join(s.dir, "opportunities.json"), &out)
	if errors.Is(err, fs.ErrNotExist) {
		return nil, ErrNotFound
	}
	if err != nil {
		return nil, err
	}
	return out, nil
}
