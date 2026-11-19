package store

import (
	"errors"
	"os"
	"path/filepath"
	"testing"
)

// TC-ST-033: a present file is served; no file is ErrNotFound; bad JSON is an error.
func TestTCST033Opportunities(t *testing.T) {
	dir := dirWithBase(t, "")
	s, err := NewJSONStore(dir)
	if err != nil {
		t.Fatal(err)
	}
	if _, err := s.GetOpportunities(); !errors.Is(err, ErrNotFound) {
		t.Fatalf("absent: %v", err)
	}
	_ = os.WriteFile(filepath.Join(dir, "opportunities.json"), []byte(`{"as_of":"20261118","rows":[]}`), 0o600)
	m, err := s.GetOpportunities()
	if err != nil || m["as_of"] != "20261118" {
		t.Fatalf("present: %v %v", err, m)
	}
	_ = os.WriteFile(filepath.Join(dir, "opportunities.json"), []byte(`{bad`), 0o600)
	if _, err := s.GetOpportunities(); err == nil || errors.Is(err, ErrNotFound) {
		t.Fatalf("malformed: %v", err)
	}
}
