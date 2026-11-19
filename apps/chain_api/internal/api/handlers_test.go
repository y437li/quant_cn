package api

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"testing"

	"quantcn/chainapi/internal/store"
)

func newServer(t *testing.T) *Server {
	t.Helper()
	s, err := store.NewJSONStore("../store/testdata")
	if err != nil {
		t.Fatal(err)
	}
	static := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { _, _ = w.Write([]byte("static")) })
	return NewServer(s, static)
}

func get(t *testing.T, h http.Handler, path string) (int, map[string]any, []any) {
	t.Helper()
	rec := httptest.NewRecorder()
	h.ServeHTTP(rec, httptest.NewRequest(http.MethodGet, path, nil))
	var obj map[string]any
	var arr []any
	if json.Unmarshal(rec.Body.Bytes(), &obj) != nil {
		_ = json.Unmarshal(rec.Body.Bytes(), &arr)
	}
	return rec.Code, obj, arr
}

// TC-API-001: bootstrap returns sectors and nodes.
func TestTCAPI001Bootstrap(t *testing.T) {
	code, obj, _ := get(t, newServer(t), "/api/bootstrap")
	if code != 200 || obj["sectors"] == nil || obj["nodes"] == nil {
		t.Fatalf("%d %v", code, obj)
	}
}

// TC-API-002: search needs q (400) and validates limit.
func TestTCAPI002Search(t *testing.T) {
	h := newServer(t)
	if code, _, _ := get(t, h, "/api/search"); code != 400 {
		t.Fatal("missing q")
	}
	if code, _, _ := get(t, h, "/api/search?q=x&limit=500"); code != 400 {
		t.Fatal("bad limit")
	}
	if code, _, arr := get(t, h, "/api/search?q=%E5%AE%81%E5%BE%B7"); code != 200 || len(arr) != 1 {
		t.Fatalf("search: %d %v", code, arr)
	}
}

// TC-API-003: company 200 with related, 404 for unknown.
func TestTCAPI003Company(t *testing.T) {
	h := newServer(t)
	if code, obj, _ := get(t, h, "/api/companies/300750.SZ"); code != 200 || obj["related"] == nil {
		t.Fatalf("company: %d", code)
	}
	if code, obj, _ := get(t, h, "/api/companies/000000.SZ"); code != 404 || obj["error"] == nil {
		t.Fatalf("unknown: %d", code)
	}
}

// TC-API-004: sector network and companies.
func TestTCAPI004Sector(t *testing.T) {
	h := newServer(t)
	if code, obj, _ := get(t, h, "/api/sectors/630000/network"); code != 200 || len(obj["edges"].([]any)) == 0 {
		t.Fatalf("network: %d", code)
	}
	if code, _, arr := get(t, h, "/api/sectors/630000/companies"); code != 200 || len(arr) != 2 {
		t.Fatalf("companies: %d", code)
	}
}

// TC-API-005: views 404 and scope check; makers list.
func TestTCAPI005Views(t *testing.T) {
	h := newServer(t)
	if code, _, _ := get(t, h, "/api/views/industry/x"); code != 404 {
		t.Fatal("missing view")
	}
	if code, _, _ := get(t, h, "/api/views/sector/x"); code != 400 {
		t.Fatal("bad scope")
	}
	if code, _, arr := get(t, h, "/api/nodes/PROD_A/makers"); code != 200 || len(arr) != 3 {
		t.Fatal("makers")
	}
}

// TC-API-006: non-API paths go to the static handler; POST is rejected.
func TestTCAPI006Static(t *testing.T) {
	h := newServer(t)
	rec := httptest.NewRecorder()
	h.ServeHTTP(rec, httptest.NewRequest(http.MethodGet, "/", nil))
	if rec.Body.String() != "static" {
		t.Fatal("static fallback")
	}
	rec = httptest.NewRecorder()
	h.ServeHTTP(rec, httptest.NewRequest(http.MethodPost, "/api/bootstrap", nil))
	if rec.Code != 405 {
		t.Fatal("POST must be 405")
	}
}

// TC-API-007: /api/watchlist serves the fixture; an absent file gives the empty document; a
// malformed file gives 500.
func TestTCAPI007Watchlist(t *testing.T) {
	code, obj, _ := get(t, newServer(t), "/api/watchlist")
	entries, _ := obj["entries"].([]any)
	if code != 200 || obj["as_of"] != "20261106" || len(entries) != 2 {
		t.Fatalf("present: %d %v", code, obj["as_of"])
	}
	if e := entries[1].(map[string]any); e["name"] != "盐津铺子" || e["gap_to_buy"] != -0.3941 || e["status"] != "far" {
		t.Fatalf("entry: %v", e)
	}
	for wl, want := range map[string]int{"": 200, "{bad": 500} {
		s, err := store.NewJSONStore(dataDir(t, wl))
		if err != nil {
			t.Fatal(err)
		}
		code, obj, _ := get(t, NewServer(s, nil), "/api/watchlist")
		if code != want {
			t.Fatalf("%q: %d %v", wl, code, obj)
		}
		if want == 200 && (obj["as_of"] != "" || obj["near_pct"] != 0.1 || len(obj["entries"].([]any)) != 0 || obj["missing"] == nil) {
			t.Fatalf("empty document: %v", obj)
		}
	}
}

// TC-API-008: /api/etf-proxy serves the fixture; an absent file gives the empty document; a
// malformed file gives 500.
func TestTCAPI008EtfProxy(t *testing.T) {
	code, obj, _ := get(t, newServer(t), "/api/etf-proxy")
	indices, _ := obj["indices"].([]any)
	if code != 200 || obj["as_of"] != "20261106" || len(indices) != 2 {
		t.Fatalf("present: %d %v", code, obj["as_of"])
	}
	for body, want := range map[string]int{"": 200, "{bad": 500} {
		dir := dataDir(t, "")
		if body != "" {
			_ = os.WriteFile(filepath.Join(dir, "etf_proxy.json"), []byte(body), 0o600)
		}
		s, err := store.NewJSONStore(dir)
		if err != nil {
			t.Fatal(err)
		}
		code, obj, _ := get(t, NewServer(s, nil), "/api/etf-proxy")
		if code != want {
			t.Fatalf("%q: %d %v", body, code, obj)
		}
		if want == 200 && (obj["as_of"] != "" || len(obj["indices"].([]any)) != 0 || obj["totals"] == nil) {
			t.Fatalf("empty document: %v", obj)
		}
	}
}

// dataDir copies the fixture view_data.json into a temporary folder, plus watchlist.json when wl is set.
func dataDir(t *testing.T, wl string) string {
	t.Helper()
	dir := t.TempDir()
	b, err := os.ReadFile("../store/testdata/view_data.json")
	if err != nil {
		t.Fatal(err)
	}
	_ = os.WriteFile(filepath.Join(dir, "view_data.json"), b, 0o600)
	if wl != "" {
		_ = os.WriteFile(filepath.Join(dir, "watchlist.json"), []byte(wl), 0o600)
	}
	return dir
}

// TC-API-009: /api/factor-monitor serves the fixture; an absent file gives the empty document;
// a malformed file gives 500.
func TestTCAPI009FactorMonitor(t *testing.T) {
	code, obj, _ := get(t, newServer(t), "/api/factor-monitor")
	factors, _ := obj["factors"].([]any)
	if code != 200 || obj["as_of"] != "20261111" || len(factors) != 3 {
		t.Fatalf("present: %d %v", code, obj["as_of"])
	}
	for body, want := range map[string]int{"": 200, "{bad": 500} {
		dir := dataDir(t, "")
		if body != "" {
			_ = os.WriteFile(filepath.Join(dir, "factor_monitor.json"), []byte(body), 0o600)
		}
		s, err := store.NewJSONStore(dir)
		if err != nil {
			t.Fatal(err)
		}
		code, obj, _ := get(t, NewServer(s, nil), "/api/factor-monitor")
		if code != want {
			t.Fatalf("%q: %d %v", body, code, obj)
		}
		if want == 200 && (obj["as_of"] != "" || len(obj["factors"].([]any)) != 0 || obj["dates"] == nil) {
			t.Fatalf("empty document: %v", obj)
		}
	}
}

// TC-API-010: /api/holdings-risk serves the fixture; an absent file gives the empty document;
// a malformed file gives 500.
func TestTCAPI010HoldingsRisk(t *testing.T) {
	code, obj, _ := get(t, newServer(t), "/api/holdings-risk")
	positions, _ := obj["positions"].([]any)
	if code != 200 || obj["as_of"] != "20261111" || len(positions) != 3 {
		t.Fatalf("present: %d %v", code, obj["as_of"])
	}
	for body, want := range map[string]int{"": 200, "{bad": 500} {
		dir := dataDir(t, "")
		if body != "" {
			_ = os.WriteFile(filepath.Join(dir, "holdings_risk.json"), []byte(body), 0o600)
		}
		s, err := store.NewJSONStore(dir)
		if err != nil {
			t.Fatal(err)
		}
		code, obj, _ := get(t, NewServer(s, nil), "/api/holdings-risk")
		if code != want {
			t.Fatalf("%q: %d %v", body, code, obj)
		}
		if want == 200 && (obj["as_of"] != "" || len(obj["positions"].([]any)) != 0 || obj["risk"] == nil) {
			t.Fatalf("empty document: %v", obj)
		}
	}
}

// TC-API-012: /api/macro serves the fixture; a malformed file is a 500.
func TestTCAPI012Macro(t *testing.T) {
	code, obj, _ := get(t, newServer(t), "/api/macro")
	series, _ := obj["series"].([]any)
	if code != 200 || obj["as_of"] != "202610" || len(series) != 2 {
		t.Fatalf("present: %d %v", code, obj)
	}
	dir := dataDir(t, "")
	_ = os.WriteFile(filepath.Join(dir, "macro_monitor.json"), []byte("{bad"), 0o600)
	s, err := store.NewJSONStore(dir)
	if err != nil {
		t.Fatal(err)
	}
	if code, _, _ := get(t, NewServer(s, nil), "/api/macro"); code != 500 {
		t.Fatalf("malformed: %d", code)
	}
}

// TC-API-013: /api/futures serves the fixture; a malformed file is a 500.
func TestTCAPI013Futures(t *testing.T) {
	code, obj, _ := get(t, newServer(t), "/api/futures")
	fams, _ := obj["families"].([]any)
	if code != 200 || obj["as_of"] != "20261113" || len(fams) != 2 {
		t.Fatalf("present: %d %v", code, obj["as_of"])
	}
	dir := dataDir(t, "")
	_ = os.WriteFile(filepath.Join(dir, "futures_monitor.json"), []byte("{bad"), 0o600)
	s, err := store.NewJSONStore(dir)
	if err != nil {
		t.Fatal(err)
	}
	if code, _, _ := get(t, NewServer(s, nil), "/api/futures"); code != 500 {
		t.Fatalf("malformed: %d", code)
	}
}

// TC-API-014: /api/volatility serves the fixture; a malformed file is a 500.
func TestTCAPI014Volatility(t *testing.T) {
	code, obj, _ := get(t, newServer(t), "/api/volatility")
	lines, _ := obj["lines"].([]any)
	if code != 200 || obj["as_of"] != "20261113" || len(lines) != 2 {
		t.Fatalf("present: %d %v", code, obj["as_of"])
	}
	dir := dataDir(t, "")
	_ = os.WriteFile(filepath.Join(dir, "volatility_monitor.json"), []byte("{bad"), 0o600)
	s, err := store.NewJSONStore(dir)
	if err != nil {
		t.Fatal(err)
	}
	if code, _, _ := get(t, NewServer(s, nil), "/api/volatility"); code != 500 {
		t.Fatalf("malformed: %d", code)
	}
}

// TC-API-014: /api/margin/{code} serves the file; unknown code is a 404.
func TestTCAPI014Margin(t *testing.T) {
	dir := dataDir(t, "")
	_ = os.MkdirAll(filepath.Join(dir, "margin"), 0o700)
	_ = os.WriteFile(filepath.Join(dir, "margin", "301358.SZ.json"), []byte(`{"code":"301358.SZ"}`), 0o600)
	s, err := store.NewJSONStore(dir)
	if err != nil {
		t.Fatal(err)
	}
	if code, obj, _ := get(t, NewServer(s, nil), "/api/margin/301358.SZ"); code != 200 || obj["code"] != "301358.SZ" {
		t.Fatalf("present: %d %v", code, obj)
	}
	if code, _, _ := get(t, NewServer(s, nil), "/api/margin/600000.SH"); code != 404 {
		t.Fatalf("absent: %d", code)
	}
}

// TC-API-015: /api/sector-monitor serves the file; none is a 404; a malformed file is a 500.
func TestTCAPI015SectorMonitor(t *testing.T) {
	dir := dataDir(t, "")
	s, err := store.NewJSONStore(dir)
	if err != nil {
		t.Fatal(err)
	}
	if code, _, _ := get(t, NewServer(s, nil), "/api/sector-monitor"); code != 404 {
		t.Fatalf("absent: %d", code)
	}
	_ = os.WriteFile(filepath.Join(dir, "sector_monitor.json"), []byte(`{"as_of":"20261117","sectors":[{"key":"games"}]}`), 0o600)
	code, obj, _ := get(t, NewServer(s, nil), "/api/sector-monitor")
	if sectors, _ := obj["sectors"].([]any); code != 200 || len(sectors) != 1 {
		t.Fatalf("present: %d %v", code, obj)
	}
	_ = os.WriteFile(filepath.Join(dir, "sector_monitor.json"), []byte("{bad"), 0o600)
	if code, _, _ := get(t, NewServer(s, nil), "/api/sector-monitor"); code != 500 {
		t.Fatalf("malformed: %d", code)
	}
}

// TC-API-016: /api/rates-fx serves the file; none is a 404; a malformed file is a 500.
func TestTCAPI016RatesFx(t *testing.T) {
	dir := dataDir(t, "")
	s, err := store.NewJSONStore(dir)
	if err != nil {
		t.Fatal(err)
	}
	if code, _, _ := get(t, NewServer(s, nil), "/api/rates-fx"); code != 404 {
		t.Fatalf("absent: %d", code)
	}
	_ = os.WriteFile(filepath.Join(dir, "rates_fx_monitor.json"), []byte(`{"as_of":"20261117","rows":[{"key":"cn_10y"}]}`), 0o600)
	code, obj, _ := get(t, NewServer(s, nil), "/api/rates-fx")
	if rows, _ := obj["rows"].([]any); code != 200 || len(rows) != 1 {
		t.Fatalf("present: %d %v", code, obj)
	}
	_ = os.WriteFile(filepath.Join(dir, "rates_fx_monitor.json"), []byte("{bad"), 0o600)
	if code, _, _ := get(t, NewServer(s, nil), "/api/rates-fx"); code != 500 {
		t.Fatalf("malformed: %d", code)
	}
}

// TC-API-017: /api/buyback serves the file; none is a 404; a malformed file is a 500.
func TestTCAPI017Buyback(t *testing.T) {
	dir := dataDir(t, "")
	s, err := store.NewJSONStore(dir)
	if err != nil {
		t.Fatal(err)
	}
	if code, _, _ := get(t, NewServer(s, nil), "/api/buyback"); code != 404 {
		t.Fatalf("absent: %d", code)
	}
	_ = os.WriteFile(filepath.Join(dir, "buyback_monitor.json"), []byte(`{"as_of":"20261117","buyback":{"live":[{"code":"A"}]}}`), 0o600)
	code, obj, _ := get(t, NewServer(s, nil), "/api/buyback")
	if bb, _ := obj["buyback"].(map[string]any); code != 200 || len(bb["live"].([]any)) != 1 {
		t.Fatalf("present: %d %v", code, obj)
	}
	_ = os.WriteFile(filepath.Join(dir, "buyback_monitor.json"), []byte("{bad"), 0o600)
	if code, _, _ := get(t, NewServer(s, nil), "/api/buyback"); code != 500 {
		t.Fatalf("malformed: %d", code)
	}
}

// TC-API-018: /api/sector-earnings serves the file; none is a 404; a malformed file is a 500.
func TestTCAPI018SectorEarnings(t *testing.T) {
	dir := dataDir(t, "")
	s, err := store.NewJSONStore(dir)
	if err != nil {
		t.Fatal(err)
	}
	if code, _, _ := get(t, NewServer(s, nil), "/api/sector-earnings"); code != 404 {
		t.Fatalf("absent: %d", code)
	}
	_ = os.WriteFile(filepath.Join(dir, "sector_earnings_signal.json"), []byte(`{"as_of":"20261117","rows":[{"code":"801735.SI"}]}`), 0o600)
	code, obj, _ := get(t, NewServer(s, nil), "/api/sector-earnings")
	if rows, _ := obj["rows"].([]any); code != 200 || len(rows) != 1 {
		t.Fatalf("present: %d %v", code, obj)
	}
	_ = os.WriteFile(filepath.Join(dir, "sector_earnings_signal.json"), []byte("{bad"), 0o600)
	if code, _, _ := get(t, NewServer(s, nil), "/api/sector-earnings"); code != 500 {
		t.Fatalf("malformed: %d", code)
	}
}

// TC-API-019: /api/tasks serves task_status.json; none is a 404; a malformed file is a 500.
func TestTCAPI019Tasks(t *testing.T) {
	dir := dataDir(t, "")
	s, err := store.NewJSONStore(dir)
	if err != nil {
		t.Fatal(err)
	}
	if code, _, _ := get(t, NewServer(s, nil), "/api/tasks"); code != 404 {
		t.Fatalf("absent: %d", code)
	}
	_ = os.WriteFile(filepath.Join(dir, "task_status.json"), []byte(`{"last_run":null,"steps":[{"task":"a"}]}`), 0o600)
	code, obj, _ := get(t, NewServer(s, nil), "/api/tasks")
	if code != 200 || len(obj["steps"].([]any)) != 1 {
		t.Fatalf("present: %d %v", code, obj)
	}
	_ = os.WriteFile(filepath.Join(dir, "task_status.json"), []byte("{bad"), 0o600)
	if code, _, _ := get(t, NewServer(s, nil), "/api/tasks"); code != 500 {
		t.Fatalf("malformed: %d", code)
	}
}

// TC-API-020: /api/opportunities serves the file; none is a 404; a malformed file is a 500.
func TestTCAPI020Opportunities(t *testing.T) {
	dir := dataDir(t, "")
	s, err := store.NewJSONStore(dir)
	if err != nil {
		t.Fatal(err)
	}
	if code, _, _ := get(t, NewServer(s, nil), "/api/opportunities"); code != 404 {
		t.Fatalf("absent: %d", code)
	}
	_ = os.WriteFile(filepath.Join(dir, "opportunities.json"), []byte(`{"as_of":"20261118","rows":[{"code":"605365.SH"}]}`), 0o600)
	code, obj, _ := get(t, NewServer(s, nil), "/api/opportunities")
	if code != 200 || obj["as_of"] != "20261118" {
		t.Fatalf("present: %d %v", code, obj)
	}
	_ = os.WriteFile(filepath.Join(dir, "opportunities.json"), []byte("{bad"), 0o600)
	if code, _, _ := get(t, NewServer(s, nil), "/api/opportunities"); code != 500 {
		t.Fatalf("malformed: %d", code)
	}
}
