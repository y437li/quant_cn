package store

import (
	"errors"
	"io/fs"
	"path/filepath"
)

// GetTaskStatus reads task_status.json written by the Python TaskStatusBuilder after
// `make update-all` (plan 38, D-181) and returns it as is.
//
// Purpose: serve the 更新状态 panel: the latest run (counts, every step with status, seconds,
// as_of, last message line) and per configured step its last status, last success and history.
// Contract: no file returns ErrNotFound; a malformed file returns an error.
// Test cases: TC-ST-032 present / absent / malformed, TC-API-019 route.
func (s *JSONStore) GetTaskStatus() (map[string]any, error) {
	var out map[string]any
	err := readJSON(filepath.Join(s.dir, "task_status.json"), &out)
	if errors.Is(err, fs.ErrNotExist) {
		return nil, ErrNotFound
	}
	if err != nil {
		return nil, err
	}
	return out, nil
}
