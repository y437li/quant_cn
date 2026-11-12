package store

import (
	"errors"
	"io/fs"
	"path/filepath"
)

// ProxyMark is a dated position (peak or trough) of the national-team ETF proxy.
type ProxyMark struct {
	Date     string   `json:"date"`
	Position *float64 `json:"position"`
}

// ProxyTotals summarises one group (core = national-team ETFs, other = the rest), 亿元.
type ProxyTotals struct {
	Aum             *float64  `json:"aum"`
	Position        *float64  `json:"position"`
	FlowRecent      *float64  `json:"flow_recent"`
	FlowYtd         *float64  `json:"flow_ytd"`
	Peak            ProxyMark `json:"peak"`
	TroughSincePeak ProxyMark `json:"trough_since_peak"`
}

// ProxyDay is one trading day's net flow by group.
type ProxyDay struct {
	Date  string   `json:"date"`
	Core  *float64 `json:"core"`
	Other *float64 `json:"other"`
}

// ProxyWeek is one ISO week: summed flow and the last day's position by group.
type ProxyWeek struct {
	Date          string   `json:"date"`
	CoreFlow      *float64 `json:"core_flow"`
	OtherFlow     *float64 `json:"other_flow"`
	CorePosition  *float64 `json:"core_position"`
	OtherPosition *float64 `json:"other_position"`
}

// ProxyYear is one calendar year's net flow by group.
type ProxyYear struct {
	Year  string   `json:"year"`
	Core  *float64 `json:"core"`
	Other *float64 `json:"other"`
}

// ProxyPoint is one week of a single index: position at the week's last day and summed flow.
type ProxyPoint struct {
	Date     string   `json:"date"`
	Position *float64 `json:"position"`
	Flow     *float64 `json:"flow"`
}

// ProxyIndex is one broad index's ETFs summed.
type ProxyIndex struct {
	Name         string       `json:"name"`
	Reference    string       `json:"reference"`
	NEtf         int          `json:"n_etf"`
	Aum          *float64     `json:"aum"`
	Position     *float64     `json:"position"`
	CorePosition *float64     `json:"core_position"`
	FlowRecent   *float64     `json:"flow_recent"`
	FlowYtd      *float64     `json:"flow_ytd"`
	Weekly       []ProxyPoint `json:"weekly"`
}

// EtfProxy is the etf_proxy.json document written by the Python EtfProxyBuilder (plan 15 ph7b).
type EtfProxy struct {
	AsOf      string                 `json:"as_of"`
	PriceAsOf string                 `json:"price_as_of"`
	Start     string                 `json:"start"`
	NMembers  int                    `json:"n_members"`
	Totals    map[string]ProxyTotals `json:"totals"`
	Recent    []ProxyDay             `json:"recent"`
	Weekly    []ProxyWeek            `json:"weekly"`
	Yearly    []ProxyYear            `json:"yearly"`
	Indices   []ProxyIndex           `json:"indices"`
}

// GetEtfProxy reads etf_proxy.json from the data folder on every call, so `make etf-proxy`
// refreshes the panel without a server restart.
//
// Purpose: serve the Python-built national-team ETF proxy as is (APP_STANDARD §1).
// Contract: no input; returns the document with non-nil totals and slices. A missing file
// returns the empty document and no error; a malformed file returns an error.
// Test cases: TC-ST-010 fixture present, TC-ST-011 file absent / null slices, TC-ST-012 malformed.
func (s *JSONStore) GetEtfProxy() (EtfProxy, error) {
	var p EtfProxy
	err := readJSON(filepath.Join(s.dir, "etf_proxy.json"), &p)
	if errors.Is(err, fs.ErrNotExist) {
		return fillProxy(EtfProxy{}), nil
	}
	if err != nil {
		return EtfProxy{}, err
	}
	return fillProxy(p), nil
}

func fillProxy(p EtfProxy) EtfProxy {
	if p.Totals == nil {
		p.Totals = map[string]ProxyTotals{}
	}
	if p.Recent == nil {
		p.Recent = []ProxyDay{}
	}
	if p.Weekly == nil {
		p.Weekly = []ProxyWeek{}
	}
	if p.Yearly == nil {
		p.Yearly = []ProxyYear{}
	}
	if p.Indices == nil {
		p.Indices = []ProxyIndex{}
	}
	for i := range p.Indices {
		if p.Indices[i].Weekly == nil {
			p.Indices[i].Weekly = []ProxyPoint{}
		}
	}
	return p
}
