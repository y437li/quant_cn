package store

import (
	"errors"
	"io/fs"
	"path/filepath"
)

// VolPoint is one session's value of a volatility index.
type VolPoint struct {
	Date  string  `json:"date"`
	Value float64 `json:"value"`
}

// VolAlerts are a line's configured alert thresholds (nil = not set).
type VolAlerts struct {
	Level *float64 `json:"level"`
	Jump  *float64 `json:"jump"`
	Pct   *float64 `json:"pct"`
}

// VolLine is one monitored volatility index: latest value, one-day change, 1-year percentile
// and range, quality flag and the one-year history.
type VolLine struct {
	Key         string     `json:"key"`
	Name        string     `json:"name"`
	Group       string     `json:"group"`
	Kind        string     `json:"kind"`
	Code        string     `json:"code"`
	Date        string     `json:"date"`
	Value       float64    `json:"value"`
	Chg         *float64   `json:"chg"`
	ChgPct      *float64   `json:"chg_pct"`
	Pct         *float64   `json:"pct"`
	Median      float64    `json:"median"`
	Low         float64    `json:"low"`
	High        float64    `json:"high"`
	NObs        int        `json:"n_obs"`
	QualityFlag string     `json:"quality_flag"`
	Alerts      VolAlerts  `json:"alerts"`
	History     []VolPoint `json:"history"`
}

// VolFlag is one alert that fired.
type VolFlag struct {
	Key     string `json:"key"`
	Kind    string `json:"kind"`
	Name    string `json:"name"`
	Message string `json:"message"`
}

// VolatilityMonitor is the volatility_monitor.json document written by the Python
// VolatilityMonitorBuilder (plan 03 ph6, D-152).
type VolatilityMonitor struct {
	AsOf     string    `json:"as_of"`
	Window   int       `json:"window"`
	Lines    []VolLine `json:"lines"`
	Flags    []VolFlag `json:"flags"`
	NewFlags []string  `json:"new_flags"`
	Missing  []string  `json:"missing"`
	// SmallCap is smallcap_watch.json (plan 30 ph2), nil when the file is absent.
	SmallCap *SmallCapWatch `json:"smallcap"`
}

// SmallCapRow is one 小盘观察 signal: latest value against its trigger and its state
// (on / near / off / info). Pct is set only on percentile rows.
type SmallCapRow struct {
	Key     string   `json:"key"`
	Group   string   `json:"group"`
	Name    string   `json:"name"`
	Value   *float64 `json:"value"`
	Unit    string   `json:"unit"`
	Trigger *float64 `json:"trigger"`
	State   string   `json:"state"`
	Note    string   `json:"note"`
	Date    string   `json:"date"`
	Pct     *float64 `json:"pct,omitempty"`
}

// SmallCapPoint is one session of the watch history (中证1000 close, breadth, vol gap, margin).
type SmallCapPoint struct {
	Date       string   `json:"date"`
	Small      *float64 `json:"small"`
	LimitDowns *float64 `json:"limit_downs"`
	LowShare   *float64 `json:"low_share"`
	Gap        *float64 `json:"gap"`
	GapPct     *float64 `json:"gap_pct"`
	// 杠杆 (plan 30 ph4): financing balance and its mean (亿), share of float market cap (fraction)
	Rz     *float64 `json:"rz,omitempty"`
	RzMa   *float64 `json:"rz_ma,omitempty"`
	RzCirc *float64 `json:"rz_circ,omitempty"`
}

// SmallCapSharePoint is one week of the long 融资余额 / 流通市值 chart (plan 30 ph6):
// share in %, 中证1000 close (nil when missing), balance in 亿 (ph7; nil in older files).
type SmallCapSharePoint struct {
	Date  string   `json:"date"`
	Share float64  `json:"share"`
	Small *float64 `json:"small"`
	Rz    *float64 `json:"rz,omitempty"`
}

// SmallCapEpisode is one past 融资余额 去杠杆 episode (plan 30 ph7): depth = trough / high - 1.
type SmallCapEpisode struct {
	Name   string  `json:"name"`
	Depth  float64 `json:"depth"`
	Months int     `json:"months"`
}

// SmallCapWatch is the smallcap_watch.json document written by the Python
// SmallCapWatchBuilder (plan 30).
type SmallCapWatch struct {
	AsOf         string          `json:"as_of"`
	Rows         []SmallCapRow   `json:"rows"`
	History      []SmallCapPoint `json:"history"`
	Triggered    []string        `json:"triggered"`
	NewTriggered []string        `json:"new_triggered"`
	Missing      []string        `json:"missing"`
	// MarginShareLong is the weekly share since 2019 (ph6); empty in older files.
	MarginShareLong []SmallCapSharePoint `json:"margin_share_long"`
	// MarginEpisodes are the past 去杠杆 episodes (ph7); empty in older files.
	MarginEpisodes []SmallCapEpisode `json:"margin_episodes"`
}

// GetVolatilityMonitor reads volatility_monitor.json and smallcap_watch.json on every call, so
// `make volatility-monitor` / `make smallcap-watch` refresh the page without a server restart.
//
// Purpose: serve the Python-built volatility monitor and 小盘观察 watch as is (APP_STANDARD §1).
// Contract: no input; returns the document with non-nil slices and SmallCap set when
// smallcap_watch.json exists (its slices non-nil too). A missing file returns the empty part
// and no error; a malformed file returns an error.
// Test cases: TC-ST-025 fixture present, TC-ST-026 file absent / null slices, TC-ST-027
// small-cap watch present / absent / malformed, TC-API-014 route.
func (s *JSONStore) GetVolatilityMonitor() (VolatilityMonitor, error) {
	var m VolatilityMonitor
	err := readJSON(filepath.Join(s.dir, "volatility_monitor.json"), &m)
	if err != nil && !errors.Is(err, fs.ErrNotExist) {
		return VolatilityMonitor{}, err
	}
	m.SmallCap = nil
	var w SmallCapWatch
	err = readJSON(filepath.Join(s.dir, "smallcap_watch.json"), &w)
	if err != nil && !errors.Is(err, fs.ErrNotExist) {
		return VolatilityMonitor{}, err
	}
	if err == nil {
		m.SmallCap = fillSmallCap(w)
	}
	return fillVolatility(m), nil
}

func fillSmallCap(w SmallCapWatch) *SmallCapWatch {
	if w.Rows == nil {
		w.Rows = []SmallCapRow{}
	}
	if w.History == nil {
		w.History = []SmallCapPoint{}
	}
	if w.Triggered == nil {
		w.Triggered = []string{}
	}
	if w.NewTriggered == nil {
		w.NewTriggered = []string{}
	}
	if w.Missing == nil {
		w.Missing = []string{}
	}
	if w.MarginShareLong == nil {
		w.MarginShareLong = []SmallCapSharePoint{}
	}
	if w.MarginEpisodes == nil {
		w.MarginEpisodes = []SmallCapEpisode{}
	}
	return &w
}

func fillVolatility(m VolatilityMonitor) VolatilityMonitor {
	if m.Lines == nil {
		m.Lines = []VolLine{}
	}
	if m.Flags == nil {
		m.Flags = []VolFlag{}
	}
	if m.NewFlags == nil {
		m.NewFlags = []string{}
	}
	if m.Missing == nil {
		m.Missing = []string{}
	}
	for i := range m.Lines {
		if m.Lines[i].History == nil {
			m.Lines[i].History = []VolPoint{}
		}
	}
	return m
}
