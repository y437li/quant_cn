package store

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"sync"
)

// JSONStore serves the chain_view builder output (view_data.json, co/<l1>.json, views.json) and the
// watchlist builder output (watchlist.json, read per request: watchlist.go).
//
// Purpose: the demo store of plan 15 (phases 3–4), loaded once at start; per-sector company
// detail files are read on first use and cached.
// Contract: NewJSONStore(dir) fails when view_data.json is missing or malformed; a missing
// views.json or shard means empty results, not an error.
// Test cases: TC-ST-001 load, TC-ST-002 company with related briefs, TC-ST-003 search,
// TC-ST-004 makers, TC-ST-005 sector network caps and directions, TC-ST-006 views.
type JSONStore struct {
	dir       string
	boot      map[string]any
	companies []Company
	byCode    map[string]*Company
	nodes     []map[string]any
	views     map[string]map[string]any
	mu        sync.Mutex
	shards    map[string]map[string]map[string]any
}

// NewJSONStore loads the builder output from dir.
func NewJSONStore(dir string) (*JSONStore, error) {
	var raw map[string]json.RawMessage
	if err := readJSON(filepath.Join(dir, "view_data.json"), &raw); err != nil {
		return nil, err
	}
	s := &JSONStore{dir: dir, boot: map[string]any{}, byCode: map[string]*Company{}, shards: map[string]map[string]map[string]any{}}
	if err := json.Unmarshal(raw["companies"], &s.companies); err != nil {
		return nil, fmt.Errorf("companies: %w", err)
	}
	for i := range s.companies {
		s.byCode[s.companies[i].Code] = &s.companies[i]
	}
	for key, msg := range raw {
		if key == "companies" {
			continue
		}
		var v any
		if err := json.Unmarshal(msg, &v); err != nil {
			return nil, fmt.Errorf("%s: %w", key, err)
		}
		s.boot[key] = v
	}
	_ = json.Unmarshal(raw["nodes"], &s.nodes)
	s.boot["quick"] = s.listQuick()
	s.boot["n_companies"] = len(s.companies)
	s.views = map[string]map[string]any{}
	_ = readJSON(filepath.Join(dir, "views.json"), &s.views) // optional
	return s, nil
}

func readJSON(path string, out any) error {
	b, err := os.ReadFile(path)
	if err != nil {
		return err
	}
	if err := json.Unmarshal(b, out); err != nil {
		return fmt.Errorf("%s: %w", filepath.Base(path), err)
	}
	return nil
}

func (s *JSONStore) listQuick() []CompanyBrief {
	codes, _ := s.boot["quick"].([]any)
	out := []CompanyBrief{}
	for _, c := range codes {
		if co, ok := s.byCode[fmt.Sprint(c)]; ok {
			out = append(out, s.toBrief(co))
		}
	}
	return out
}

func (s *JSONStore) toBrief(c *Company) CompanyBrief {
	b := CompanyBrief{Code: c.Code, Name: c.Name, L1: c.L1, L3: c.L3, NLinks: len(c.Links)}
	for _, r := range c.Revenue {
		if len(r.Pids) > 0 {
			p := r.Pids[0]
			b.FirstPid = &p
			break
		}
	}
	return b
}

// GetBootstrap returns the reference data (everything in view_data.json except companies).
func (s *JSONStore) GetBootstrap() map[string]any { return s.boot }

func (s *JSONStore) getShard(l1 string) map[string]map[string]any {
	s.mu.Lock()
	defer s.mu.Unlock()
	if sh, ok := s.shards[l1]; ok {
		return sh
	}
	sh := map[string]map[string]any{}
	_ = readJSON(filepath.Join(s.dir, "co", l1+".json"), &sh)
	s.shards[l1] = sh
	return sh
}

// GetCompany returns the light record merged with its detail, and briefs of every linked company.
func (s *JSONStore) GetCompany(code string) (map[string]any, map[string]CompanyBrief, error) {
	c, ok := s.byCode[code]
	if !ok {
		return nil, nil, ErrNotFound
	}
	var merged map[string]any
	b, _ := json.Marshal(c)
	_ = json.Unmarshal(b, &merged)
	l1 := c.L1
	if l1 == "" {
		l1 = "other"
	}
	for k, v := range s.getShard(l1)[code] {
		merged[k] = v
	}
	related := map[string]CompanyBrief{}
	collectCodes(merged, func(other string) {
		if o, ok := s.byCode[other]; ok && other != code {
			related[other] = s.toBrief(o)
		}
	})
	return merged, related, nil
}

// collectCodes walks a decoded JSON value and reports every string under a "code" key and every
// link target (first element of a links entry).
func collectCodes(v any, report func(string)) {
	switch x := v.(type) {
	case map[string]any:
		for k, e := range x {
			if k == "code" {
				if s, ok := e.(string); ok {
					report(s)
				}
			}
			if k == "links" {
				if arr, ok := e.([]any); ok {
					for _, l := range arr {
						if t, ok := l.([]any); ok && len(t) > 0 {
							report(fmt.Sprint(t[0]))
						}
					}
				}
			}
			collectCodes(e, report)
		}
	case []any:
		for _, e := range x {
			collectCodes(e, report)
		}
	}
}

// GetView returns a synthesized broker view of a product or industry.
func (s *JSONStore) GetView(scope, id string) (map[string]any, error) {
	v, ok := s.views[scope][id]
	if !ok {
		return nil, ErrNotFound
	}
	m, _ := v.(map[string]any)
	return m, nil
}

// ListSectorCompanies lists the companies of an L1 sector, most connected first.
func (s *JSONStore) ListSectorCompanies(l1 string) []CompanyBrief {
	out := []CompanyBrief{}
	for i := range s.companies {
		if s.companies[i].L1 == l1 {
			out = append(out, s.toBrief(&s.companies[i]))
		}
	}
	sort.SliceStable(out, func(a, b int) bool { return out[a].NLinks > out[b].NLinks })
	return out
}
