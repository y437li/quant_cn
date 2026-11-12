package store

import (
	"os"
	"path/filepath"
	"testing"
)

// monitorDir makes a data folder with the fixture view_data.json and, when body is set,
// factor_monitor.json.
func monitorDir(t *testing.T, body string) string {
	t.Helper()
	dir := dirWithBase(t, "")
	if body != "" {
		if err := os.WriteFile(filepath.Join(dir, "factor_monitor.json"), []byte(body), 0o600); err != nil {
			t.Fatal(err)
		}
	}
	return dir
}

// TC-ST-013: the fixture is served as written; null series become [], null numbers stay nil.
func TestTCST013FactorMonitorPresent(t *testing.T) {
	m, err := load(t).GetFactorMonitor()
	if err != nil || m.AsOf != "20261111" || len(m.Dates) != 2 || len(m.Factors) != 3 {
		t.Fatalf("monitor: %v %+v", err, m.AsOf)
	}
	mom := m.Factors[1]
	if mom.Kind != "style" || mom.Ret.M1 != nil || *mom.SigmaMove != -1.2 || mom.Realized == nil || mom.Cum[0] != nil {
		t.Fatalf("momentum: %+v", mom)
	}
	if m.Factors[2].Label != "农林牧渔" || *m.Factors[0].VolRatio != 1.153846 {
		t.Fatalf("labels / ratio: %+v", m.Factors[2])
	}
}

// TC-ST-014: no file gives the empty document with non-nil slices; null slices become [].
func TestTCST014FactorMonitorAbsent(t *testing.T) {
	for _, body := range []string{"", `{"as_of":"x","dates":null,"factors":[{"factor":"a","cum":null}]}`} {
		s, err := NewJSONStore(monitorDir(t, body))
		if err != nil {
			t.Fatal(err)
		}
		m, err := s.GetFactorMonitor()
		if err != nil || m.Dates == nil || m.Factors == nil {
			t.Fatalf("%q: %v %+v", body, err, m)
		}
		if body != "" && (m.Factors[0].Cum == nil || m.Factors[0].Forecast == nil) {
			t.Fatalf("factor series nil: %+v", m.Factors[0])
		}
	}
}

// TC-ST-015: a malformed file is an error.
func TestTCST015FactorMonitorMalformed(t *testing.T) {
	s, err := NewJSONStore(monitorDir(t, "{bad"))
	if err != nil {
		t.Fatal(err)
	}
	if _, err := s.GetFactorMonitor(); err == nil {
		t.Fatal("malformed factor_monitor.json must fail")
	}
}
