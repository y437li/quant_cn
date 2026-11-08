package store

import "testing"

func load(t *testing.T) *JSONStore {
	t.Helper()
	s, err := NewJSONStore("testdata")
	if err != nil {
		t.Fatal(err)
	}
	return s
}

// TC-ST-001: load; bootstrap has reference data, quick list and count, but no companies.
func TestTCST001Load(t *testing.T) {
	s := load(t)
	b := s.GetBootstrap()
	if _, ok := b["companies"]; ok {
		t.Fatal("bootstrap must not carry companies")
	}
	if q := b["quick"].([]CompanyBrief); len(q) != 1 || q[0].Name != "宁德时代" {
		t.Fatalf("quick: %+v", q)
	}
	if b["n_companies"].(int) != 4 {
		t.Fatal("count")
	}
	if _, err := NewJSONStore("missing"); err == nil {
		t.Fatal("missing folder must fail")
	}
}

// TC-ST-002: company merges its shard detail; related briefs cover links and table codes.
func TestTCST002Company(t *testing.T) {
	s := load(t)
	c, rel, err := s.GetCompany("300750.SZ")
	if err != nil || c["source"] != "2025 年年报" {
		t.Fatalf("detail not merged: %v %v", err, c["source"])
	}
	for _, code := range []string{"002594.SZ", "600104.SH", "300014.SZ"} {
		if _, ok := rel[code]; !ok {
			t.Fatalf("related misses %s", code)
		}
	}
	if *rel["002594.SZ"].FirstPid != "MKT_EV" {
		t.Fatal("first pid")
	}
	if _, _, err := s.GetCompany("000000.SZ"); err != ErrNotFound {
		t.Fatal("unknown company must be ErrNotFound")
	}
}

// TC-ST-003: search finds companies by name and code, nodes by name, English name and alias.
func TestTCST003Search(t *testing.T) {
	s := load(t)
	if h := s.FindHits("宁德", 10); len(h) != 1 || h[0].Kind != "company" {
		t.Fatalf("name: %+v", h)
	}
	if h := s.FindHits("300014", 10); len(h) != 1 || h[0].ID != "300014.SZ" {
		t.Fatalf("code: %+v", h)
	}
	if h := s.FindHits("power", 10); len(h) != 1 || h[0].ID != "PROD_A" {
		t.Fatalf("english: %+v", h)
	}
	if h := s.FindHits("锂电", 10); len(h) != 1 || h[0].Kind != "node" {
		t.Fatalf("alias: %+v", h)
	}
	if h := s.FindHits("  ", 10); len(h) != 0 {
		t.Fatal("blank query")
	}
}

// TC-ST-004: makers of a node, largest share first.
func TestTCST004Makers(t *testing.T) {
	m := load(t).ListMakers("PROD_A")
	if len(m) != 3 || m[0].Code != "300750.SZ" || m[2].Code != "002594.SZ" {
		t.Fatalf("makers: %+v", m)
	}
}

// TC-ST-005: sector network edge directions; outside=false keeps only sector members.
func TestTCST005Network(t *testing.T) {
	s := load(t)
	n := s.GetSectorNetwork("630000", true)
	kinds := map[string]NetEdge{}
	for _, e := range n.Edges {
		kinds[e.Kind+e.To] = e
	}
	if e := kinds["sells002594.SZ"]; e.From != "300750.SZ" || e.Label != "9.50%" {
		t.Fatalf("sells edge: %+v", n.Edges)
	}
	if _, ok := kinds["named600104.SH"]; !ok {
		t.Fatal("named edge")
	}
	inner := s.GetSectorNetwork("630000", false)
	for _, nd := range inner.Nodes {
		if !nd.InSector {
			t.Fatalf("outside node with outside=false: %+v", nd)
		}
	}
	if len(s.ListSectorCompanies("630000")) != 2 {
		t.Fatal("sector companies")
	}
}

// TC-ST-006: views by scope and id.
func TestTCST006Views(t *testing.T) {
	s := load(t)
	if v, err := s.GetView("product", "PROD_A"); err != nil || v["summary"] != "多数用2026E PE" {
		t.Fatal("product view")
	}
	if _, err := s.GetView("industry", "x"); err != ErrNotFound {
		t.Fatal("missing view")
	}
}
