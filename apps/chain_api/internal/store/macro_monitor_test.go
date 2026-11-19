package store

import (
	"os"
	"path/filepath"
	"testing"
)

// TC-ST-021: the fixture is served as written.
func TestTCST021MacroPresent(t *testing.T) {
	m, err := load(t).GetMacroMonitor()
	if err != nil || m.AsOf != "202610" || len(m.Series) != 2 || len(m.NewPrints) != 1 {
		t.Fatalf("macro: %v %+v", err, m)
	}
	cpi := m.Series[0]
	if cpi.Key != "cpi" || *cpi.Value != 0.7 || *cpi.Pct5y != 0.6 || len(cpi.History) != 3 || !cpi.NewPrint {
		t.Fatalf("cpi: %+v", cpi)
	}
	if m.Series[1].Prev != nil {
		t.Fatalf("null prev should stay nil: %+v", m.Series[1])
	}
}

// TC-ST-022: no file gives the empty document; null slices become [].
func TestTCST022MacroAbsent(t *testing.T) {
	for _, body := range []string{"", `{"as_of":"x","series":[{"key":"a","history":null}],"missing":null}`} {
		dir := dirWithBase(t, "")
		if body != "" {
			if err := os.WriteFile(filepath.Join(dir, "macro_monitor.json"), []byte(body), 0o600); err != nil {
				t.Fatal(err)
			}
		}
		s, err := NewJSONStore(dir)
		if err != nil {
			t.Fatal(err)
		}
		m, err := s.GetMacroMonitor()
		if err != nil || m.Missing == nil || m.NewPrints == nil || m.Series == nil {
			t.Fatalf("%q: %v %+v", body, err, m)
		}
		if body != "" && m.Series[0].History == nil {
			t.Fatalf("history nil: %+v", m.Series[0])
		}
	}
}
