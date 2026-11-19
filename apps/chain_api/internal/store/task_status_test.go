package store

import (
	"errors"
	"os"
	"path/filepath"
	"testing"
)

// TC-ST-032: a present file is served; no file is ErrNotFound; bad JSON is an error.
func TestTCST032TaskStatus(t *testing.T) {
	dir := dirWithBase(t, "")
	s, err := NewJSONStore(dir)
	if err != nil {
		t.Fatal(err)
	}
	if _, err := s.GetTaskStatus(); !errors.Is(err, ErrNotFound) {
		t.Fatalf("absent: %v", err)
	}
	_ = os.WriteFile(filepath.Join(dir, "task_status.json"), []byte(`{"last_run":{"run_id":"r1"},"steps":[]}`), 0o600)
	m, err := s.GetTaskStatus()
	if err != nil || m["last_run"].(map[string]any)["run_id"] != "r1" {
		t.Fatalf("present: %v %v", err, m)
	}
	_ = os.WriteFile(filepath.Join(dir, "task_status.json"), []byte(`{bad`), 0o600)
	if _, err := s.GetTaskStatus(); err == nil || errors.Is(err, ErrNotFound) {
		t.Fatalf("malformed: %v", err)
	}
}
