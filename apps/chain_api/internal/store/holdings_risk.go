package store

import (
	"errors"
	"io/fs"
	"path/filepath"
)

// HoldingPosition is one stock of the book valued at the session close.
type HoldingPosition struct {
	Code    string   `json:"code"`
	Name    string   `json:"name"`
	Shares  *float64 `json:"shares"`
	Cost    *float64 `json:"cost"`
	Close   *float64 `json:"close"`
	Value   *float64 `json:"value"`
	Weight  *float64 `json:"weight"`
	Pnl     *float64 `json:"pnl"`
	PnlPct  *float64 `json:"pnl_pct"`
	Vol     *float64 `json:"vol"`
	Contrib *float64 `json:"contrib"`
}

// HoldingFactor is the book's exposure to one risk-model factor and its share of risk.
type HoldingFactor struct {
	Factor   string   `json:"factor"`
	Label    string   `json:"label"`
	Kind     string   `json:"kind"`
	Exposure *float64 `json:"exposure"`
	Active   *float64 `json:"active"`
	Contrib  *float64 `json:"contrib"`
}

// Correlation is the model-implied correlation between the covered stocks.
type Correlation struct {
	Codes  []string    `json:"codes"`
	Matrix [][]float64 `json:"matrix"`
}

// StockExposureRow is one stock's style exposures (order of StockExposures.Styles) and industry.
type StockExposureRow struct {
	Code     string     `json:"code"`
	Industry string     `json:"industry"`
	Values   []*float64 `json:"values"`
}

// StockExposures is the stocks x styles exposure table of the book.
type StockExposures struct {
	Styles []string           `json:"styles"`
	Rows   []StockExposureRow `json:"rows"`
}

// HoldingsRisk is the holdings_risk.json document written by the Python HoldingsRiskBuilder
// (plan 15 ph7d, D-132).
type HoldingsRisk struct {
	AsOf        string              `json:"as_of"`
	Model       string              `json:"model"`
	Benchmark   string              `json:"benchmark"`
	Cash        float64             `json:"cash"`
	Value       float64             `json:"value"`
	StockValue  float64             `json:"stock_value"`
	Pnl         float64             `json:"pnl"`
	Risk        map[string]*float64 `json:"risk"`
	Positions   []HoldingPosition   `json:"positions"`
	Factors     []HoldingFactor     `json:"factors"`
	Correlation Correlation         `json:"correlation"`
	Stocks      StockExposures      `json:"stock_exposures"`
	Missing     []string            `json:"missing"`
}

// GetHoldingsRisk reads holdings_risk.json from the data folder on every call.
//
// Purpose: serve the Python-built holdings risk as is (APP_STANDARD §1).
// Contract: no input; returns the document with non-nil maps and slices. A missing file
// returns the empty document and no error; a malformed file returns an error.
// Test cases: TC-ST-016 fixture present, TC-ST-017 file absent / null slices, TC-ST-018 malformed.
func (s *JSONStore) GetHoldingsRisk() (HoldingsRisk, error) {
	var h HoldingsRisk
	err := readJSON(filepath.Join(s.dir, "holdings_risk.json"), &h)
	if errors.Is(err, fs.ErrNotExist) {
		return fillHoldings(HoldingsRisk{}), nil
	}
	if err != nil {
		return HoldingsRisk{}, err
	}
	return fillHoldings(h), nil
}

func fillHoldings(h HoldingsRisk) HoldingsRisk {
	if h.Risk == nil {
		h.Risk = map[string]*float64{}
	}
	if h.Positions == nil {
		h.Positions = []HoldingPosition{}
	}
	if h.Factors == nil {
		h.Factors = []HoldingFactor{}
	}
	if h.Correlation.Codes == nil {
		h.Correlation.Codes = []string{}
	}
	if h.Correlation.Matrix == nil {
		h.Correlation.Matrix = [][]float64{}
	}
	if h.Stocks.Styles == nil {
		h.Stocks.Styles = []string{}
	}
	if h.Stocks.Rows == nil {
		h.Stocks.Rows = []StockExposureRow{}
	}
	if h.Missing == nil {
		h.Missing = []string{}
	}
	return h
}
