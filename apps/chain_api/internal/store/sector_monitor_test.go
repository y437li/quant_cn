package store

import (
	"errors"
	"os"
	"path/filepath"
	"testing"
)

// TC-ST-028: a present file is served; no file is ErrNotFound; bad JSON is an error.
func TestTCST028SectorMonitor(t *testing.T) {
	dir := dirWithBase(t, "")
	s, err := NewJSONStore(dir)
	if err != nil {
		t.Fatal(err)
	}
	if _, err := s.GetSectorMonitor(); !errors.Is(err, ErrNotFound) {
		t.Fatalf("absent: %v", err)
	}
	_ = os.WriteFile(filepath.Join(dir, "sector_monitor.json"), []byte(`{"as_of":"20261117","sectors":[]}`), 0o600)
	m, err := s.GetSectorMonitor()
	if err != nil || m["as_of"] != "20261117" {
		t.Fatalf("present: %v %v", err, m)
	}
	_ = os.WriteFile(filepath.Join(dir, "sector_monitor.json"), []byte(`{bad`), 0o600)
	if _, err := s.GetSectorMonitor(); err == nil || errors.Is(err, ErrNotFound) {
		t.Fatalf("malformed: %v", err)
	}
}
