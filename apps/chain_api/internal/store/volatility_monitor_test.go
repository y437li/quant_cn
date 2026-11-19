package store

import (
	"os"
	"path/filepath"
	"testing"
)

// TC-ST-025: the fixture is served as written.
func TestTCST025VolatilityPresent(t *testing.T) {
	m, err := load(t).GetVolatilityMonitor()
	if err != nil || m.AsOf != "20261113" || len(m.Lines) != 2 || len(m.Flags) != 1 || len(m.NewFlags) != 1 {
		t.Fatalf("volatility: %v %+v", err, m)
	}
	us := m.Lines[0]
	if us.Key != "us_vix" || us.Value != 18.7 || *us.Pct != 0.7 || len(us.History) != 3 || *us.Alerts.Level != 25 {
		t.Fatalf("us: %+v", us)
	}
	if m.Lines[1].Chg != nil || m.Lines[1].Pct != nil || m.Lines[1].Alerts.Level != nil {
		t.Fatalf("null fields should stay nil: %+v", m.Lines[1])
	}
}

// TC-ST-026: no file gives the empty document; null slices become [].
func TestTCST026VolatilityAbsent(t *testing.T) {
	for _, body := range []string{"", `{"as_of":"x","lines":[{"key":"a","history":null}],"flags":null}`} {
		dir := dirWithBase(t, "")
		if body != "" {
			if err := os.WriteFile(filepath.Join(dir, "volatility_monitor.json"), []byte(body), 0o600); err != nil {
				t.Fatal(err)
			}
		}
		s, err := NewJSONStore(dir)
		if err != nil {
			t.Fatal(err)
		}
		m, err := s.GetVolatilityMonitor()
		if err != nil || m.Lines == nil || m.Flags == nil || m.NewFlags == nil || m.Missing == nil {
			t.Fatalf("%q: %v %+v", body, err, m)
		}
		if body != "" && m.Lines[0].History == nil {
			t.Fatalf("history nil: %+v", m.Lines[0])
		}
	}
}

// TC-ST-027: smallcap_watch.json is attached as SmallCap (margin history and the ph6 weekly share included); absent → nil; malformed → error.
func TestTCST027SmallCapWatch(t *testing.T) {
	m, err := load(t).GetVolatilityMonitor()
	if err != nil || m.SmallCap == nil {
		t.Fatalf("small cap: %v %+v", err, m.SmallCap)
	}
	w := m.SmallCap
	if w.AsOf != "20261117" || len(w.Rows) != 4 || len(w.History) != 3 || w.Triggered[0] != "gap" || w.NewTriggered == nil {
		t.Fatalf("watch: %+v", w)
	}
	if *w.Rows[2].Pct != 0.972 || w.Rows[0].Pct != nil || w.Rows[3].Value != nil || w.History[2].GapPct != nil {
		t.Fatalf("optional fields: %+v %+v", w.Rows, w.History[2])
	}
	if h := w.History[0]; *h.Rz != 22572 || *h.RzCirc != 0.0252 || w.History[1].Rz != nil {
		t.Fatalf("margin history: %+v %+v", h, w.History[1])
	}
	if l := w.MarginShareLong; len(l) != 2 || l[0].Share != 2.078 || *l[0].Small != 4498 || l[1].Small != nil {
		t.Fatalf("margin share long (ph6): %+v", l)
	}
	dir := dirWithBase(t, "")
	s, err := NewJSONStore(dir)
	if err != nil {
		t.Fatal(err)
	}
	if m, err := s.GetVolatilityMonitor(); err != nil || m.SmallCap != nil {
		t.Fatalf("absent: %v %+v", err, m.SmallCap)
	}
	if err := os.WriteFile(filepath.Join(dir, "smallcap_watch.json"), []byte(`{"as_of":"x","rows":null}`), 0o600); err != nil {
		t.Fatal(err)
	}
	if m, err := s.GetVolatilityMonitor(); err != nil || m.SmallCap == nil || m.SmallCap.Rows == nil || m.SmallCap.History == nil || m.SmallCap.MarginShareLong == nil {
		t.Fatalf("null slices: %v %+v", err, m.SmallCap)
	}
	if err := os.WriteFile(filepath.Join(dir, "smallcap_watch.json"), []byte("{bad"), 0o600); err != nil {
		t.Fatal(err)
	}
	if _, err := s.GetVolatilityMonitor(); err == nil {
		t.Fatal("malformed smallcap_watch.json should be an error")
	}
}
