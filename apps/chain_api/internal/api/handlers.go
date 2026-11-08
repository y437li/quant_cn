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
// Contract: JSON responses; 400 for bad parameters, 404 for unknown ids, 405 for non-GET.
// Test cases: TC-API-001 bootstrap, TC-API-002 search 400/200, TC-API-003 company 404/200,
// TC-API-004 sector network, TC-API-005 views 404, TC-API-006 static fallback.
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

func writeJSON(w http.ResponseWriter, v any) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	_ = json.NewEncoder(w).Encode(v)
}

func writeError(w http.ResponseWriter, status int, msg string) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(map[string]string{"error": msg})
}
