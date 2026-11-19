// Package api serves the read-only HTTP API described in openapi.yaml (plan 15, D-116).
package api

import (
	"encoding/json"
	"errors"
	"net/http"
	"strconv"
	"strings"

	"quantcn/chainapi/internal/store"
)

// Server routes /api/* to the Store and everything else to the static front end.
//
// Purpose: thin HTTP layer; no business logic (APP_STANDARD §1).
// Contract: JSON responses; 400 for bad parameters, 404 for unknown ids, 405 for non-GET,
// 500 when a data file is malformed.
// Test cases: TC-API-001 bootstrap, TC-API-002 search 400/200, TC-API-003 company 404/200,
// TC-API-004 sector network, TC-API-005 views 404, TC-API-006 static fallback,
// TC-API-007 watchlist present / absent (500 when the file is malformed).
// TC-API-008 etf-proxy present / absent (500 when the file is malformed).
// TC-API-009 factor-monitor present / absent (500 when the file is malformed).
// TC-API-010 holdings-risk present / absent (500 when the file is malformed).
type Server struct {
	store  store.Store
	static http.Handler
}

// NewServer builds the server; static may be nil (API only).
func NewServer(s store.Store, static http.Handler) *Server {
	return &Server{store: s, static: static}
}

// ServeHTTP dispatches one request.
func (h *Server) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	if !strings.HasPrefix(r.URL.Path, "/api/") {
		if h.static == nil {
			http.NotFound(w, r)
			return
		}
		h.static.ServeHTTP(w, r)
		return
	}
	if r.Method != http.MethodGet {
		writeError(w, http.StatusMethodNotAllowed, "GET only")
		return
	}
	parts := strings.Split(strings.Trim(strings.TrimPrefix(r.URL.Path, "/api/"), "/"), "/")
	switch {
	case len(parts) == 1 && parts[0] == "bootstrap":
		writeJSON(w, h.store.GetBootstrap())
	case len(parts) == 1 && parts[0] == "search":
		h.handleSearch(w, r)
	case len(parts) == 2 && parts[0] == "companies":
		h.handleCompany(w, parts[1])
	case len(parts) == 3 && parts[0] == "nodes" && parts[2] == "makers":
		writeJSON(w, h.store.ListMakers(parts[1]))
	case len(parts) == 3 && parts[0] == "sectors" && parts[2] == "companies":
		writeJSON(w, h.store.ListSectorCompanies(parts[1]))
	case len(parts) == 3 && parts[0] == "sectors" && parts[2] == "network":
		writeJSON(w, h.store.GetSectorNetwork(parts[1], r.URL.Query().Get("outside") != "false"))
	case len(parts) == 1 && parts[0] == "watchlist":
		h.handleWatchlist(w)
	case len(parts) == 1 && parts[0] == "etf-proxy":
		h.handleEtfProxy(w)
	case len(parts) == 2 && parts[0] == "margin":
		h.handleMargin(w, parts[1])
	case len(parts) == 1 && parts[0] == "futures":
		h.handleFutures(w)
	case len(parts) == 1 && parts[0] == "macro":
		h.handleMacro(w)
	case len(parts) == 1 && parts[0] == "volatility":
		h.handleVolatility(w)
	case len(parts) == 1 && parts[0] == "factor-monitor":
		h.handleFactorMonitor(w)
	case len(parts) == 1 && parts[0] == "holdings-risk":
		h.handleHoldingsRisk(w)
	case len(parts) == 1 && parts[0] == "sector-monitor":
		h.handleSectorMonitor(w)
	case len(parts) == 1 && parts[0] == "rates-fx":
		h.handleRatesFx(w)
	case len(parts) == 1 && parts[0] == "sector-earnings":
		h.handleSectorEarnings(w)
	case len(parts) == 1 && parts[0] == "buyback":
		h.handleBuyback(w)
	case len(parts) == 1 && parts[0] == "tasks":
		h.handleTasks(w)
	case len(parts) == 1 && parts[0] == "opportunities":
		h.handleOpportunities(w)
	case len(parts) == 3 && parts[0] == "views":
		h.handleView(w, parts[1], parts[2])
	default:
		writeError(w, http.StatusNotFound, "unknown endpoint")
	}
}

func (h *Server) handleSearch(w http.ResponseWriter, r *http.Request) {
	q := strings.TrimSpace(r.URL.Query().Get("q"))
	if q == "" {
		writeError(w, http.StatusBadRequest, "q is required")
		return
	}
	limit := 30
	if v := r.URL.Query().Get("limit"); v != "" {
		n, err := strconv.Atoi(v)
		if err != nil || n < 1 || n > 100 {
			writeError(w, http.StatusBadRequest, "limit must be 1..100")
			return
		}
		limit = n
	}
	writeJSON(w, h.store.FindHits(q, limit))
}

func (h *Server) handleCompany(w http.ResponseWriter, code string) {
	c, related, err := h.store.GetCompany(code)
	if errors.Is(err, store.ErrNotFound) {
		writeError(w, http.StatusNotFound, "company not found: "+code)
		return
	}
	writeJSON(w, map[string]any{"company": c, "related": related})
}

func (h *Server) handleView(w http.ResponseWriter, scope, id string) {
	if scope != "product" && scope != "industry" {
		writeError(w, http.StatusBadRequest, "scope must be product or industry")
		return
	}
	v, err := h.store.GetView(scope, id)
	if errors.Is(err, store.ErrNotFound) {
		writeError(w, http.StatusNotFound, "no view")
		return
	}
	writeJSON(w, v)
}

func (h *Server) handleWatchlist(w http.ResponseWriter) {
	wl, err := h.store.GetWatchlist()
	if err != nil {
		writeError(w, http.StatusInternalServerError, "watchlist: "+err.Error())
		return
	}
	writeJSON(w, wl)
}

func (h *Server) handleEtfProxy(w http.ResponseWriter) {
	p, err := h.store.GetEtfProxy()
	if err != nil {
		writeError(w, http.StatusInternalServerError, "etf proxy: "+err.Error())
		return
	}
	writeJSON(w, p)
}

func (h *Server) handleMargin(w http.ResponseWriter, code string) {
	m, err := h.store.GetMargin(code)
	if errors.Is(err, store.ErrNotFound) {
		writeError(w, http.StatusNotFound, "no margin data: "+code)
		return
	}
	if err != nil {
		writeError(w, http.StatusInternalServerError, "margin: "+err.Error())
		return
	}
	writeJSON(w, m)
}

func (h *Server) handleFutures(w http.ResponseWriter) {
	m, err := h.store.GetFuturesMonitor()
	if err != nil {
		writeError(w, http.StatusInternalServerError, "futures monitor: "+err.Error())
		return
	}
	writeJSON(w, m)
}

func (h *Server) handleMacro(w http.ResponseWriter) {
	m, err := h.store.GetMacroMonitor()
	if err != nil {
		writeError(w, http.StatusInternalServerError, "macro monitor: "+err.Error())
		return
	}
	writeJSON(w, m)
}

func (h *Server) handleVolatility(w http.ResponseWriter) {
	m, err := h.store.GetVolatilityMonitor()
	if err != nil {
		writeError(w, http.StatusInternalServerError, "volatility monitor: "+err.Error())
		return
	}
	writeJSON(w, m)
}

func (h *Server) handleFactorMonitor(w http.ResponseWriter) {
	m, err := h.store.GetFactorMonitor()
	if err != nil {
		writeError(w, http.StatusInternalServerError, "factor monitor: "+err.Error())
		return
	}
	writeJSON(w, m)
}

func (h *Server) handleHoldingsRisk(w http.ResponseWriter) {
	d, err := h.store.GetHoldingsRisk()
	if err != nil {
		writeError(w, http.StatusInternalServerError, "holdings risk: "+err.Error())
		return
	}
	writeJSON(w, d)
}

func writeJSON(w http.ResponseWriter, v any) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	_ = json.NewEncoder(w).Encode(v)
}

func writeError(w http.ResponseWriter, status int, msg string) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(map[string]string{"error": msg})
}

// handleBuyback serves buyback_monitor.json (plan 32): 404 before the first
// `make buyback-events`, 500 when the file is malformed. Test cases: TC-API-017.
func (h *Server) handleBuyback(w http.ResponseWriter) {
	m, err := h.store.GetBuybackMonitor()
	if errors.Is(err, store.ErrNotFound) {
		writeError(w, http.StatusNotFound, "no buyback monitor yet: run make buyback-events")
		return
	}
	if err != nil {
		writeError(w, http.StatusInternalServerError, "buyback monitor: "+err.Error())
		return
	}
	writeJSON(w, m)
}

// handleTasks serves task_status.json (plan 38): 404 before the first `make update-all`,
// 500 when the file is malformed. Test cases: TC-API-019.
func (h *Server) handleTasks(w http.ResponseWriter) {
	m, err := h.store.GetTaskStatus()
	if errors.Is(err, store.ErrNotFound) {
		writeError(w, http.StatusNotFound, "no task status yet: run make update-all")
		return
	}
	if err != nil {
		writeError(w, http.StatusInternalServerError, "task status: "+err.Error())
		return
	}
	writeJSON(w, m)
}

// handleOpportunities serves opportunities.json (plan 21 ph5): 404 before the first
// `make opportunity-list`, 500 when the file is malformed. Test cases: TC-API-020.
func (h *Server) handleOpportunities(w http.ResponseWriter) {
	m, err := h.store.GetOpportunities()
	if errors.Is(err, store.ErrNotFound) {
		writeError(w, http.StatusNotFound, "no opportunity list yet: run make opportunity-list")
		return
	}
	if err != nil {
		writeError(w, http.StatusInternalServerError, "opportunities: "+err.Error())
		return
	}
	writeJSON(w, m)
}

// handleSectorEarnings serves sector_earnings_signal.json (plan 35): 404 before the first
// `make sector-earnings-signal`, 500 when the file is malformed. Test cases: TC-API-018.
func (h *Server) handleSectorEarnings(w http.ResponseWriter) {
	m, err := h.store.GetSectorEarningsSignal()
	if errors.Is(err, store.ErrNotFound) {
		writeError(w, http.StatusNotFound, "no sector earnings signal yet: run make sector-earnings-signal")
		return
	}
	if err != nil {
		writeError(w, http.StatusInternalServerError, "sector earnings signal: "+err.Error())
		return
	}
	writeJSON(w, m)
}

// handleRatesFx serves rates_fx_monitor.json (plan 34): 404 before the first
// `make rates-fx-monitor`, 500 when the file is malformed. Test cases: TC-API-016.
func (h *Server) handleRatesFx(w http.ResponseWriter) {
	m, err := h.store.GetRatesFxMonitor()
	if errors.Is(err, store.ErrNotFound) {
		writeError(w, http.StatusNotFound, "no rates-fx monitor yet: run make rates-fx-monitor")
		return
	}
	if err != nil {
		writeError(w, http.StatusInternalServerError, "rates-fx monitor: "+err.Error())
		return
	}
	writeJSON(w, m)
}

// handleSectorMonitor serves sector_monitor.json (plan 31): 404 before the first
// `make sector-monitor`, 500 when the file is malformed. Test cases: TC-API-015.
func (h *Server) handleSectorMonitor(w http.ResponseWriter) {
	m, err := h.store.GetSectorMonitor()
	if errors.Is(err, store.ErrNotFound) {
		writeError(w, http.StatusNotFound, "no sector monitor yet: run make sector-monitor")
		return
	}
	if err != nil {
		writeError(w, http.StatusInternalServerError, "sector monitor: "+err.Error())
		return
	}
	writeJSON(w, m)
}
