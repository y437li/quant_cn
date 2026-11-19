package store

import (
	"os"
	"path/filepath"
	"testing"
)

// proxyDir makes a data folder with the fixture view_data.json and, when body is set, etf_proxy.json.
func proxyDir(t *testing.T, body string) string {
	t.Helper()
	dir := dirWithBase(t, "")
	if body != "" {
		if err := os.WriteFile(filepath.Join(dir, "etf_proxy.json"), []byte(body), 0o600); err != nil {
			t.Fatal(err)
		}
	}
	return dir
}

// TC-ST-010: the fixture is served as written (index rhythm and 近3月 window fields included); null index weekly becomes [].
func TestTCST010EtfProxyPresent(t *testing.T) {
	p, err := load(t).GetEtfProxy()
	if err != nil || p.AsOf != "20261106" || p.NMembers != 161 || len(p.Indices) != 2 {
		t.Fatalf("proxy: %v %+v", err, p.AsOf)
	}
	core := p.Totals["core"]
	if *core.Position != 9162.2 || core.Peak.Date != "20241011" || *core.TroughSincePeak.Position != 3236.1 {
		t.Fatalf("core: %+v", core)
	}
	if len(p.Styles) != 2 || p.Styles[0].Status != "hot" || *p.Styles[0].Z != 1.99 || p.Styles[1].History == nil {
		t.Fatalf("styles: %+v", p.Styles)
	}
	if p.Indices[1].CorePosition != nil || p.Indices[1].Weekly == nil || len(p.Weekly) != 2 || *p.Yearly[1].Core != -9471.7 {
		t.Fatalf("index / weekly / yearly: %+v", p.Indices[1])
	}
	if x := p.Indices[0]; x.Peak.Date != "20250425" || *x.TroughSincePeak.Position != 1872 || *x.SinceTrough != 2870.5 || *x.FlowWeeks != 2136 || *x.Drawdown != -21.4 {
		t.Fatalf("index rhythm: %+v", x)
	}
	if w := p.Indices[0].Window; *w.Pct != 96.8 || *w.Low != 2335.9 || w.Days != 63 || p.Indices[1].Window.Pct != nil {
		t.Fatalf("index window: %+v", w)
	}
	if p.RhythmWeeks != 4 || p.PctWindowDays != 63 || p.MatrixWeeks != 14 || *core.Window.High != 9162.2 || *core.FlowWeeks != 2474.6 {
		t.Fatalf("settings / core window: %+v", core)
	}
}

// TC-ST-011: no file gives the empty document with non-nil slices; null slices become [].
func TestTCST011EtfProxyAbsent(t *testing.T) {
	for _, body := range []string{"", `{"as_of":"x","recent":null,"indices":[{"name":"a","weekly":null}]}`} {
		s, err := NewJSONStore(proxyDir(t, body))
		if err != nil {
			t.Fatal(err)
		}
		p, err := s.GetEtfProxy()
		if err != nil || p.Totals == nil || p.Recent == nil || p.Weekly == nil || p.Yearly == nil || p.Indices == nil || p.Styles == nil {
			t.Fatalf("%q: %v %+v", body, err, p)
		}
		if body != "" && p.Indices[0].Weekly == nil {
			t.Fatalf("index weekly nil: %+v", p.Indices[0])
		}
	}
}

// TC-ST-012: a malformed file is an error.
func TestTCST012EtfProxyMalformed(t *testing.T) {
	s, err := NewJSONStore(proxyDir(t, "{bad"))
	if err != nil {
		t.Fatal(err)
	}
	if _, err := s.GetEtfProxy(); err == nil {
		t.Fatal("malformed etf_proxy.json must fail")
	}
}
