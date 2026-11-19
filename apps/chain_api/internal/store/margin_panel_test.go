package store

import (
	"errors"
	"os"
	"path/filepath"
	"testing"
)

// TC-ST-025: a present file is served; no file or a bad code is ErrNotFound; bad JSON is an error.
func TestTCST025Margin(t *testing.T) {
	dir := dirWithBase(t, "")
	_ = os.MkdirAll(filepath.Join(dir, "margin"), 0o700)
	_ = os.WriteFile(filepath.Join(dir, "margin", "301358.SZ.json"), []byte(`{"code":"301358.SZ","rz_yi":17.18}`), 0o600)
	_ = os.WriteFile(filepath.Join(dir, "margin", "000001.SZ.json"), []byte(`{bad`), 0o600)
	s, err := NewJSONStore(dir)
	if err != nil {
		t.Fatal(err)
	}
	m, err := s.GetMargin("301358.SZ")
	if err != nil || m["rz_yi"] != 17.18 {
		t.Fatalf("present: %v %v", err, m)
	}
	for _, code := range []string{"600000.SH", "../x", "abc"} {
		if _, err := s.GetMargin(code); !errors.Is(err, ErrNotFound) {
			t.Fatalf("%s: %v", code, err)
		}
	}
	if _, err := s.GetMargin("000001.SZ"); err == nil || errors.Is(err, ErrNotFound) {
		t.Fatalf("malformed: %v", err)
	}
}
