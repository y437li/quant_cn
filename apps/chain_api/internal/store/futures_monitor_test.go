package store

import (
	"os"
	"path/filepath"
	"testing"
)

// TC-ST-023: the fixture is served as written; null slices of a family become [].
func TestTCST023FuturesPresent(t *testing.T) {
	m, err := load(t).GetFuturesMonitor()
	if err != nil || m.AsOf != "20261113" || len(m.Families) != 2 || len(m.Spreads) != 1 || len(m.NewFlags) != 1 {
		t.Fatalf("futures: %v %+v", err, m.AsOf)
	}
	cu := m.Families[0]
	if *cu.FrontVs4th != 0.038 || len(cu.Curve) != 3 || cu.Shape != "backwardation" {
		t.Fatalf("cu: %+v", cu)
	}
	if cu.Broker == nil || *cu.Broker.NetShare != -0.011 || m.Families[1].Broker != nil {
		t.Fatalf("broker: %+v", cu.Broker)
	}
	if len(m.Index) != 1 || *m.Index[0].BasisAnnualised != -15.5 || len(m.Index[0].History) != 2 {
		t.Fatalf("index futures: %+v", m.Index)
	}
	lh := m.Families[1]
	if lh.Chg3m != nil || lh.Curve == nil || lh.CurveHistory == nil {
		t.Fatalf("lh: %+v", lh)
	}
}

// TC-ST-024: no file gives the empty document; null slices become [].
func TestTCST024FuturesAbsent(t *testing.T) {
	for _, body := range []string{"", `{"as_of":"x","families":[{"family":"a","curve":null}],"spreads":[{"key":"s"}]}`} {
		dir := dirWithBase(t, "")
		if body != "" {
			if err := os.WriteFile(filepath.Join(dir, "futures_monitor.json"), []byte(body), 0o600); err != nil {
				t.Fatal(err)
			}
		}
		s, err := NewJSONStore(dir)
		if err != nil {
			t.Fatal(err)
		}
		m, err := s.GetFuturesMonitor()
		if err != nil || m.Families == nil || m.Spreads == nil || m.Flags == nil || m.NewFlags == nil || m.Missing == nil || m.Index == nil {
			t.Fatalf("%q: %v %+v", body, err, m)
		}
		if body != "" && (m.Families[0].Curve == nil || m.Spreads[0].History == nil) {
			t.Fatalf("nil slices: %+v", m)
		}
	}
}
