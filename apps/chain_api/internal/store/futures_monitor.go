package store

import (
	"errors"
	"io/fs"
	"path/filepath"
)

// FuturesPoint is one dated value (price or ratio) of a history.
type FuturesPoint struct {
	D string  `json:"d"`
	V float64 `json:"v"`
}

// FuturesCurvePoint is one listed month on today's curve.
type FuturesCurvePoint struct {
	Month string  `json:"month"`
	Price float64 `json:"price"`
	Oi    float64 `json:"oi"`
}

// FuturesBroker is the top-20 brokers' net over a family's contracts (ph7l).
type FuturesBroker struct {
	AsOf          string   `json:"as_of"`
	Net           *float64 `json:"net"`
	Gross         *float64 `json:"gross"`
	NetShare      *float64 `json:"net_share"`
	NetShareChg5d *float64 `json:"net_share_chg_5d"`
	NetSharePct5y *float64 `json:"net_share_pct_5y"`
}

// IndexBasisPoint is one weekly point of an index-futures product.
type IndexBasisPoint struct {
	D     string   `json:"d"`
	Basis *float64 `json:"basis"`
	Net   *float64 `json:"net"`
}

// IndexFuture is one CFFEX index-futures product: basis to its index and top-20 net (ph7k).
type IndexFuture struct {
	Product         string            `json:"product"`
	Name            string            `json:"name"`
	Index           string            `json:"index"`
	AsOf            string            `json:"as_of"`
	MainContract    string            `json:"main_contract"`
	Price           *float64          `json:"price"`
	Spot            *float64          `json:"spot"`
	BasisPct        *float64          `json:"basis_pct"`
	BasisAnnualised *float64          `json:"basis_annualised"`
	BasisPct5y      *float64          `json:"basis_pct_5y"`
	Net             *float64          `json:"net"`
	NetChg5d        *float64          `json:"net_chg_5d"`
	NetPct5y        *float64          `json:"net_pct_5y"`
	Oi              *float64          `json:"oi"`
	OiChg5d         *float64          `json:"oi_chg_5d"`
	Regime          string            `json:"regime"`
	History         []IndexBasisPoint `json:"history"`
}

// FuturesFamily is one watched contract family: dominant price, curve shape, open interest.
type FuturesFamily struct {
	Family        string              `json:"family"`
	Name          string              `json:"name"`
	Group         string              `json:"group"`
	AsOf          string              `json:"as_of"`
	Contract      string              `json:"contract"`
	Price         *float64            `json:"price"`
	Pct1y         *float64            `json:"pct_1y"`
	Pct5y         *float64            `json:"pct_5y"`
	Chg1w         *float64            `json:"chg_1w"`
	Chg3m         *float64            `json:"chg_3m"`
	Chg1y         *float64            `json:"chg_1y"`
	FrontVs4th    *float64            `json:"front_vs_4th"`
	FrontVs4thPct *float64            `json:"front_vs_4th_pct"`
	FrontVs12m    *float64            `json:"front_vs_12m"`
	FrontVs12mPct *float64            `json:"front_vs_12m_pct"`
	Shape         string              `json:"shape"`
	Oi            *float64            `json:"oi"`
	OiChg5d       *float64            `json:"oi_chg_5d"`
	OiZ           *float64            `json:"oi_z"`
	Curve         []FuturesCurvePoint `json:"curve"`
	PriceHistory  []FuturesPoint      `json:"price_history"`
	CurveHistory  []FuturesPoint      `json:"curve_history"`
	Broker        *FuturesBroker      `json:"broker"`
}

// FuturesSpread is one value-chain spread built from the legs' dominant prices.
type FuturesSpread struct {
	Key     string         `json:"key"`
	Name    string         `json:"name"`
	Unit    string         `json:"unit"`
	Kind    string         `json:"kind"`
	AsOf    string         `json:"as_of"`
	Value   *float64       `json:"value"`
	Chg1w   *float64       `json:"chg_1w"`
	Pct5y   *float64       `json:"pct_5y"`
	History []FuturesPoint `json:"history"`
}

// FuturesFlag is one signal: curve or spread at a 5-year extreme, or an open-interest jump.
type FuturesFlag struct {
	Key     string `json:"key"`
	Kind    string `json:"kind"`
	Name    string `json:"name"`
	Message string `json:"message"`
}

// FuturesMonitor is the futures_monitor.json document written by the Python
// FuturesMonitorBuilder (plan 15 ph7i).
type FuturesMonitor struct {
	AsOf     string          `json:"as_of"`
	Families []FuturesFamily `json:"families"`
	Spreads  []FuturesSpread `json:"spreads"`
	Index    []IndexFuture   `json:"index_futures"`
	Flags    []FuturesFlag   `json:"flags"`
	NewFlags []string        `json:"new_flags"`
	Missing  []string        `json:"missing"`
}

// GetFuturesMonitor reads futures_monitor.json on every call, so `make futures-monitor`
// refreshes the page without a server restart.
//
// Purpose: serve the Python-built futures monitor as is (APP_STANDARD §1).
// Contract: no input; returns the document with non-nil slices. A missing file returns the
// empty document and no error; a malformed file returns an error.
// Test cases: TC-ST-023 fixture present, TC-ST-024 file absent / null slices, TC-API-013 route.
func (s *JSONStore) GetFuturesMonitor() (FuturesMonitor, error) {
	var m FuturesMonitor
	err := readJSON(filepath.Join(s.dir, "futures_monitor.json"), &m)
	if errors.Is(err, fs.ErrNotExist) {
		return fillFutures(FuturesMonitor{}), nil
	}
	if err != nil {
		return FuturesMonitor{}, err
	}
	return fillFutures(m), nil
}

func fillFutures(m FuturesMonitor) FuturesMonitor {
	if m.Families == nil {
		m.Families = []FuturesFamily{}
	}
	if m.Spreads == nil {
		m.Spreads = []FuturesSpread{}
	}
	if m.Index == nil {
		m.Index = []IndexFuture{}
	}
	for i := range m.Index {
		if m.Index[i].History == nil {
			m.Index[i].History = []IndexBasisPoint{}
		}
	}
	if m.Flags == nil {
		m.Flags = []FuturesFlag{}
	}
	if m.NewFlags == nil {
		m.NewFlags = []string{}
	}
	if m.Missing == nil {
		m.Missing = []string{}
	}
	for i := range m.Families {
		f := &m.Families[i]
		if f.Curve == nil {
			f.Curve = []FuturesCurvePoint{}
		}
		if f.PriceHistory == nil {
			f.PriceHistory = []FuturesPoint{}
		}
		if f.CurveHistory == nil {
			f.CurveHistory = []FuturesPoint{}
		}
	}
	for i := range m.Spreads {
		if m.Spreads[i].History == nil {
			m.Spreads[i].History = []FuturesPoint{}
		}
	}
	return m
}
