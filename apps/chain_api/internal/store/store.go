// Package store gives the API read-only access to the industry-chain data (plan 15, D-116).
package store

import "errors"

// ErrNotFound is returned when a company, node or view does not exist.
var ErrNotFound = errors.New("not found")

// RevenueLine is one 主营构成 line of a company with the taxonomy nodes it maps to.
type RevenueLine struct {
	Item string   `json:"item"`
	Pct  float64  `json:"pct"`
	Gm   *float64 `json:"gm"`
	Pids []string `json:"pids"`
	How  string   `json:"how"`
}

// Company is the light record of one listed company (search, makers, networks).
type Company struct {
	Code    string        `json:"code"`
	Name    string        `json:"name"`
	L1      string        `json:"l1"`
	L3      *string       `json:"l3"`
	Sw      []string      `json:"sw"`
	Revenue []RevenueLine `json:"revenue"`
	Links   [][]any       `json:"links"` // [code, kind, pct|null]: c/s top-5, C/S/P/R named in text
}

// CompanyBrief is the short form used in lists and for linked companies.
type CompanyBrief struct {
	Code     string  `json:"code"`
	Name     string  `json:"name"`
	L1       string  `json:"l1,omitempty"`
	L3       *string `json:"l3,omitempty"`
	NLinks   int     `json:"n_links"`
	FirstPid *string `json:"first_pid"`
}

// SearchHit is one search result (a company or a taxonomy node).
type SearchHit struct {
	Kind  string `json:"kind"`
	ID    string `json:"id"`
	Label string `json:"label"`
	Sub   string `json:"sub"`
}

// Maker is a company whose revenue line maps to a node.
type Maker struct {
	Code string  `json:"code"`
	Name string  `json:"name"`
	Item string  `json:"item"`
	Pct  float64 `json:"pct"`
	How  string  `json:"how"`
}

// NetNode and NetEdge form a company network.
type NetNode struct {
	Code     string `json:"code"`
	Name     string `json:"name"`
	InSector bool   `json:"in_sector"`
}

// NetEdge is a directed link: from sells to (kind sells / named), from buys from (buys), or a peer link.
type NetEdge struct {
	From  string `json:"from"`
	To    string `json:"to"`
	Kind  string `json:"kind"`
	Label string `json:"label"`
}

// Network is the company network of one sector.
type Network struct {
	Nodes []NetNode `json:"nodes"`
	Edges []NetEdge `json:"edges"`
}

// Store is the read-only data access the handlers use.
//
// Purpose: one interface over the demo JSON store now and the derived/graph parquet store later
// (plan 15 phase 2), so handlers and the front end never change.
// Contract: all methods are safe for concurrent use; ErrNotFound for unknown ids.
// Test cases: TC-ST-001..006 in json_store_test.go.
type Store interface {
	GetBootstrap() map[string]any
	FindHits(q string, limit int) []SearchHit
	GetCompany(code string) (map[string]any, map[string]CompanyBrief, error)
	ListMakers(nodeID string) []Maker
	ListSectorCompanies(l1 string) []CompanyBrief
	GetSectorNetwork(l1 string, outside bool) Network
	GetView(scope, id string) (map[string]any, error)
}
