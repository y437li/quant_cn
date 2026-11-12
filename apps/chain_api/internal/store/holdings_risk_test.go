package store

import (
	"os"
	"path/filepath"
	"testing"
)

func holdingsDir(t *testing.T, body string) string {
	t.Helper()
	dir := dirWithBase(t, "")
	if body != "" {
		if err := os.WriteFile(filepath.Join(dir, "holdings_risk.json"), []byte(body), 0o600); err != nil {
			t.Fatal(err)
		}
	}
	return dir
}

// TC-ST-016: the fixture is served as written; a position without a close keeps nil numbers.
func TestTCST016HoldingsPresent(t *testing.T) {
	h, err := load(t).GetHoldingsRisk()
	if err != nil || h.AsOf != "20261111" || len(h.Positions) != 3 || len(h.Factors) != 3 {
		t.Fatalf("holdings: %v %+v", err, h.AsOf)
	}
	if *h.Risk["active_total"] != 0.151 || h.Positions[2].Close != nil || h.Missing[0] != "000000.SZ" {
		t.Fatalf("risk / missing: %+v", h.Risk)
	}
	if len(h.Stocks.Styles) != 2 || h.Stocks.Rows[1].Values[1] != nil || *h.Stocks.Rows[0].Values[0] != 1.38 {
		t.Fatalf("stock exposures: %+v", h.Stocks)
	}
	if h.Correlation.Matrix[0][1] != 0.14 || h.Factors[2].Label != "农林牧渔" {
		t.Fatalf("correlation / labels: %+v", h.Correlation)
	}
}

// TC-ST-017: no file gives the empty document; null slices and maps become empty.
func TestTCST017HoldingsAbsent(t *testing.T) {
	for _, body := range []string{"", `{"as_of":"x","positions":null,"risk":null}`} {
		s, err := NewJSONStore(holdingsDir(t, body))
		if err != nil {
			t.Fatal(err)
		}
		h, err := s.GetHoldingsRisk()
		if err != nil || h.Risk == nil || h.Positions == nil || h.Factors == nil || h.Missing == nil || h.Correlation.Codes == nil || h.Stocks.Rows == nil {
			t.Fatalf("%q: %v %+v", body, err, h)
		}
	}
}

// TC-ST-018: a malformed file is an error.
func TestTCST018HoldingsMalformed(t *testing.T) {
	s, err := NewJSONStore(holdingsDir(t, "{bad"))
	if err != nil {
		t.Fatal(err)
	}
	if _, err := s.GetHoldingsRisk(); err == nil {
		t.Fatal("malformed holdings_risk.json must fail")
	}
}
