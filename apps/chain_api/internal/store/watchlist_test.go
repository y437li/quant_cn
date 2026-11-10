package store

import (
	"os"
	"path/filepath"
	"testing"
)

// dirWithBase makes a temporary data folder holding the fixture view_data.json and, when wl is not
// empty, a watchlist.json with that content.
func dirWithBase(t *testing.T, wl string) string {
	t.Helper()
	dir := t.TempDir()
	b, err := os.ReadFile("testdata/view_data.json")
	if err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(dir, "view_data.json"), b, 0o600); err != nil {
		t.Fatal(err)
	}
	if wl != "" {
		if err := os.WriteFile(filepath.Join(dir, "watchlist.json"), []byte(wl), 0o600); err != nil {
			t.Fatal(err)
		}
	}
	return dir
}

// TC-ST-007: the fixture is served as written (numbers from Python, nulls kept).
func TestTCST007WatchlistPresent(t *testing.T) {
	w, err := load(t).GetWatchlist()
	if err != nil || w.AsOf != "20261106" || len(w.Entries) != 2 {
		t.Fatalf("watchlist: %v %+v", err, w.AsOf)
	}
	e := w.Entries[0]
	if e.Name != "涪陵榨菜" || e.Price != 11.84 || e.GapToBuy != -0.1554 || *e.PeAtBuy != 15.5 || *e.YieldAtBuy != 0.042 || e.Status != "far" {
		t.Fatalf("entry: %+v", e)
	}
	if *e.EpsYear != "2026" || *e.EpsBrokers != 8 || len(e.Weekly) != 52 || w.Missing == nil {
		t.Fatalf("eps / weekly / missing: %+v", e)
	}
}

// TC-ST-008: no watchlist.json gives the empty document, not an error; null slices become [].
func TestTCST008WatchlistAbsent(t *testing.T) {
	s, err := NewJSONStore(dirWithBase(t, ""))
	if err != nil {
		t.Fatal(err)
	}
	w, err := s.GetWatchlist()
	if err != nil || w.AsOf != "" || w.NearPct != 0.1 || w.Entries == nil || len(w.Entries) != 0 || w.Missing == nil {
		t.Fatalf("absent: %v %+v", err, w)
	}
	s, _ = NewJSONStore(dirWithBase(t, `{"as_of":"20261106","entries":[{"code":"x","pe_at_buy":null}],"missing":null}`))
	w, err = s.GetWatchlist()
	if err != nil || w.NearPct != 0.1 || w.Missing == nil || w.Entries[0].Weekly == nil || w.Entries[0].PeAtBuy != nil {
		t.Fatalf("nulls: %v %+v", err, w)
	}
}

// TC-ST-009: a malformed watchlist.json is an error.
func TestTCST009WatchlistMalformed(t *testing.T) {
	s, err := NewJSONStore(dirWithBase(t, "{not json"))
	if err != nil {
		t.Fatal(err)
	}
	if _, err := s.GetWatchlist(); err == nil {
		t.Fatal("malformed file must fail")
	}
}
