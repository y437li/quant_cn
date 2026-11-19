package store

import (
	"errors"
	"os"
	"path/filepath"
	"testing"
)

// TC-ST-030: a present file is served; no file is ErrNotFound; bad JSON is an error.
func TestTCST030BuybackMonitor(t *testing.T) {
	dir := dirWithBase(t, "")
	s, err := NewJSONStore(dir)
	if err != nil {
		t.Fatal(err)
	}
	if _, err := s.GetBuybackMonitor(); !errors.Is(err, ErrNotFound) {
		t.Fatalf("absent: %v", err)
	}
	_ = os.WriteFile(filepath.Join(dir, "buyback_monitor.json"), []byte(`{"as_of":"20261117","buyback":{}}`), 0o600)
	m, err := s.GetBuybackMonitor()
	if err != nil || m["as_of"] != "20261117" {
		t.Fatalf("present: %v %v", err, m)
	}
	_ = os.WriteFile(filepath.Join(dir, "buyback_monitor.json"), []byte(`{bad`), 0o600)
	if _, err := s.GetBuybackMonitor(); err == nil || errors.Is(err, ErrNotFound) {
		t.Fatalf("malformed: %v", err)
	}
}
