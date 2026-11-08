package store

import (
	"fmt"
	"sort"
	"strings"
)

const (
	networkCore    = 90 // most connected companies of the sector
	networkOutside = 70 // most connected companies linked to them
)

var typeZh = map[string]string{"product": "产品", "segment": "细分", "material": "材料", "technology": "技术", "end_market": "终端市场"}

// FindHits searches company names and codes first, then taxonomy node names, English names and aliases.
func (s *JSONStore) FindHits(q string, limit int) []SearchHit {
	q = strings.ToLower(strings.TrimSpace(q))
	out := []SearchHit{}
	if q == "" {
		return out
	}
	for i := range s.companies {
		c := &s.companies[i]
		if strings.Contains(strings.ToLower(c.Name), q) || strings.Contains(strings.ToLower(c.Code), q) {
			out = append(out, SearchHit{Kind: "company", ID: c.Code, Label: c.Name, Sub: "公司 " + c.Code})
			if len(out) >= limit/2 {
				break
			}
		}
	}
	for _, n := range s.nodes {
		if len(out) >= limit {
			break
		}
		if matchNode(n, q) {
			out = append(out, SearchHit{Kind: "node", ID: fmt.Sprint(n["id"]), Label: fmt.Sprint(n["n"]), Sub: typeZh[fmt.Sprint(n["t"])]})
		}
	}
	return out
}

func matchNode(n map[string]any, q string) bool {
	if strings.Contains(strings.ToLower(fmt.Sprint(n["n"])), q) {
		return true
	}
	if en, ok := n["en"].(string); ok && strings.Contains(strings.ToLower(en), q) {
		return true
	}
	als, _ := n["al"].([]any)
	for _, a := range als {
		if strings.Contains(strings.ToLower(fmt.Sprint(a)), q) {
			return true
		}
	}
	return false
}

// ListMakers lists companies whose revenue lines map to the node, largest share first.
func (s *JSONStore) ListMakers(nodeID string) []Maker {
	out := []Maker{}
	for i := range s.companies {
		c := &s.companies[i]
		for _, r := range c.Revenue {
			for _, p := range r.Pids {
				if p == nodeID {
					out = append(out, Maker{Code: c.Code, Name: c.Name, Item: r.Item, Pct: r.Pct / float64(len(r.Pids)), How: r.How})
				}
			}
		}
	}
	sort.SliceStable(out, func(a, b int) bool { return out[a].Pct > out[b].Pct })
	return out
}

// GetSectorNetwork returns the company network of an L1 sector: the networkCore most connected
// members and, when outside is true, the networkOutside companies most linked to them.
func (s *JSONStore) GetSectorNetwork(l1 string, outside bool) Network {
	var core []*Company
	for i := range s.companies {
		if c := &s.companies[i]; c.L1 == l1 && len(c.Links) > 0 {
			core = append(core, c)
		}
	}
	sort.SliceStable(core, func(a, b int) bool { return len(core[a].Links) > len(core[b].Links) })
	if len(core) > networkCore {
		core = core[:networkCore]
	}
	inCore := map[string]bool{}
	for _, c := range core {
		inCore[c.Code] = true
	}
	allowed := s.pickOutside(core, inCore, l1, outside)
	net := Network{Nodes: []NetNode{}, Edges: []NetEdge{}}
	seen := map[string]bool{}
	addNode := func(code string) {
		if !seen[code] {
			seen[code] = true
			o := s.byCode[code]
			net.Nodes = append(net.Nodes, NetNode{Code: code, Name: o.Name, InSector: o.L1 == l1})
		}
	}
	for _, c := range core {
		addNode(c.Code)
		for _, l := range c.Links {
			other := fmt.Sprint(l[0])
			if _, ok := s.byCode[other]; !ok || other == c.Code || !(inCore[other] || allowed[other]) {
				continue
			}
			addNode(other)
			net.Edges = append(net.Edges, toEdge(c.Code, other, fmt.Sprint(l[1]), l[2]))
		}
	}
	return net
}

func (s *JSONStore) pickOutside(core []*Company, inCore map[string]bool, l1 string, outside bool) map[string]bool {
	deg := map[string]int{}
	for _, c := range core {
		for _, l := range c.Links {
			o, ok := s.byCode[fmt.Sprint(l[0])]
			if ok && !inCore[o.Code] && (outside || o.L1 == l1) {
				deg[o.Code]++
			}
		}
	}
	codes := make([]string, 0, len(deg))
	for c := range deg {
		codes = append(codes, c)
	}
	sort.SliceStable(codes, func(a, b int) bool {
		if deg[codes[a]] != deg[codes[b]] {
			return deg[codes[a]] > deg[codes[b]]
		}
		return codes[a] < codes[b]
	})
	allowed := map[string]bool{}
	for i, c := range codes {
		if i >= networkOutside {
			break
		}
		allowed[c] = true
	}
	return allowed
}

func toEdge(from, to, kind string, pct any) NetEdge {
	label := ""
	if f, ok := pct.(float64); ok {
		label = fmt.Sprintf("%.2f%%", f)
	}
	switch kind {
	case "c":
		return NetEdge{From: from, To: to, Kind: "sells", Label: label}
	case "C":
		return NetEdge{From: from, To: to, Kind: "named", Label: label}
	case "s", "S":
		return NetEdge{From: to, To: from, Kind: "buys", Label: label}
	case "P":
		return NetEdge{From: from, To: to, Kind: "peer", Label: "竞争"}
	default:
		return NetEdge{From: from, To: to, Kind: "peer", Label: "合作"}
	}
}
