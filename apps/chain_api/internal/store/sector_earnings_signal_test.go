package store

import (
	"errors"
	"os"
	"path/filepath"
	"testing"
)

// TC-ST-031: a present file is served; no file is ErrNotFound; bad JSON is an error.
func TestTCST031SectorEarningsSignal(t *testing.T) {
	dir := dirWithBase(t, "")
	s, err := NewJSONStore(dir)
	if err != nil {
		t.Fatal(err)
	}
	if _, err := s.GetSectorEarningsSignal(); !errors.Is(err, ErrNotFound) {
		t.Fatalf("absent: %v", err)
	}
	_ = os.WriteFile(filepath.Join(dir, "sector_earnings_signal.json"), []byte(`{"as_of":"20261117","rows":[]}`), 0o600)
	m, err := s.GetSectorEarningsSignal()
	if err != nil || m["as_of"] != "20261117" {
		t.Fatalf("present: %v %v", err, m)
	}
	_ = os.WriteFile(filepath.Join(dir, "sector_earnings_signal.json"), []byte(`{bad`), 0o600)
	if _, err := s.GetSectorEarningsSignal(); err == nil || errors.Is(err, ErrNotFound) {
		t.Fatalf("malformed: %v", err)
	}
}
