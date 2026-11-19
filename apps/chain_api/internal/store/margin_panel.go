package store

import (
	"errors"
	"io/fs"
	"path/filepath"
	"regexp"
)

var marginCode = regexp.MustCompile(`^[0-9]{6}\.(SH|SZ|BJ)$`)

// GetMargin reads margin/<code>.json written by the Python MarginPanelBuilder (plan 15 ph7m) and
// returns it as is.
//
// Purpose: serve one stock's 融资融券 series and forced-liquidation ladder.
// Contract: code must look like 600000.SH; a code without a file returns ErrNotFound; a
// malformed file returns an error.
// Test cases: TC-ST-025 file present / absent / bad code, TC-API-014 route.
func (s *JSONStore) GetMargin(code string) (map[string]any, error) {
	if !marginCode.MatchString(code) {
		return nil, ErrNotFound
	}
	var out map[string]any
	err := readJSON(filepath.Join(s.dir, "margin", code+".json"), &out)
	if errors.Is(err, fs.ErrNotExist) {
		return nil, ErrNotFound
	}
	if err != nil {
		return nil, err
	}
	return out, nil
}
