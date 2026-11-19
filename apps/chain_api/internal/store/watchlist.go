package store

import (
	"errors"
	"io/fs"
	"path/filepath"
)

// WeeklyClose is one weekly close of a watched stock.
type WeeklyClose struct {
	Date  string  `json:"date"`
	Close float64 `json:"close"`
}

// WatchlistEntry is one stock of the 观察账本 with every number already computed in Python
// (WatchlistBuilder, plan 15 phase 7). Pointer fields are null when the source has no value
// (no EPS, no broker target, no dividend).
type WatchlistEntry struct {
	Code string `json:"code"`
	Name string `json:"name"`
	// Kind is "stock" or "etf" (ETF rows priced from fund_daily, no valuation; ph7p).
	Kind       string   `json:"kind,omitempty"`
	BuyLow     float64  `json:"buy_low"`
	BuyHigh    float64  `json:"buy_high"`
	Added      string   `json:"added"`
	Thesis     string   `json:"thesis"`
	Watch      string   `json:"watch"`
	Price      float64  `json:"price"`
	PriceDate  string   `json:"price_date"`
	PeTTM      *float64 `json:"pe_ttm"`
	Pb         *float64 `json:"pb"`
	DivYield   *float64 `json:"div_yield"`
	DpsTTM     *float64 `json:"dps_ttm"`
	EpsYear    *string  `json:"eps_year"`
	EpsFy      *float64 `json:"eps_fy"`
	EpsBrokers *int     `json:"eps_brokers"`
	TargetLow  *float64 `json:"target_low"`
	TargetHigh *float64 `json:"target_high"`
	Low52w     *float64 `json:"low_52w"`
	High52w    *float64 `json:"high_52w"`
	GapToBuy   float64  `json:"gap_to_buy"`
	PeAtBuy    *float64 `json:"pe_at_buy"`
	YieldAtBuy *float64 `json:"yield_at_buy"`
	// Shareholder yield (dividends + executed buybacks, 12 months) and the largest live buyback
	// plan as % of market cap (plan 23 ph5).
	ShareholderYield *float64 `json:"shareholder_yield"`
	BuybackPlanPct   *float64 `json:"buyback_plan_pct"`
	// Latest 散户温度计 reading (plan 21 ph5): retail_gauge pct, gauge_exp_change, gauge_avoid /
	// gauge_avoid_strong / gauge_leaving flags (1 / 0), gauge_lo_streak / gauge_hi_streak.
	Retail map[string]*float64 `json:"retail"`
	Status string              `json:"status"`
	Weekly []WeeklyClose       `json:"weekly"`
	// Conditions besides the price range (plan 15 ph7f); ConditionsNeeded null = all of them.
	Conditions       []ConditionResult `json:"conditions"`
	ConditionsNeeded *int              `json:"conditions_needed"`
	ConditionStatus  string            `json:"condition_status"`
}

// Watchlist is the watchlist.json document.
type Watchlist struct {
	AsOf    string           `json:"as_of"`
	NearPct float64          `json:"near_pct"`
	Entries []WatchlistEntry `json:"entries"`
	Missing []string         `json:"missing"`
}

// GetWatchlist reads watchlist.json from the data folder on every call, so `make watchlist`
// refreshes the page without a server restart.
//
// Purpose: serve the Python-built watchlist as is (no recomputation, APP_STANDARD §1).
// Contract: no input; returns the document with non-nil entries, missing and weekly slices.
// A missing file returns the empty document {as_of:"", near_pct:0.1, entries:[], missing:[]}
// and no error; a malformed file returns an error.
// Test cases: TC-ST-007 fixture present, TC-ST-008 file absent, TC-ST-009 malformed.
func (s *JSONStore) GetWatchlist() (Watchlist, error) {
	w := Watchlist{NearPct: 0.1}
	err := readJSON(filepath.Join(s.dir, "watchlist.json"), &w)
	if errors.Is(err, fs.ErrNotExist) {
		return Watchlist{NearPct: 0.1, Entries: []WatchlistEntry{}, Missing: []string{}}, nil
	}
	if err != nil {
		return Watchlist{}, err
	}
	if w.Entries == nil {
		w.Entries = []WatchlistEntry{}
	}
	if w.Missing == nil {
		w.Missing = []string{}
	}
	for i := range w.Entries {
		if w.Entries[i].Weekly == nil {
			w.Entries[i].Weekly = []WeeklyClose{}
		}
		if w.Entries[i].Retail == nil {
			w.Entries[i].Retail = map[string]*float64{}
		}
		if w.Entries[i].Conditions == nil {
			w.Entries[i].Conditions = []ConditionResult{}
		}
	}
	return w, nil
}
