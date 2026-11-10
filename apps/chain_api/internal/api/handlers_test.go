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
