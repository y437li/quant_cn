// Command chainapi serves the industry-chain API and the built front end on localhost (plan 15).
package main

import (
	"flag"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"time"

	"quantcn/chainapi/internal/api"
	"quantcn/chainapi/internal/store"
)

func main() {
	data := flag.String("data", "research_space/prototypes/chain_view", "folder with view_data.json, co/, views.json")
	web := flag.String("web", "apps/chain_api/web/dist", "built front end (empty = API only)")
	addr := flag.String("addr", "127.0.0.1:8787", "listen address (localhost only by default)")
	flag.Parse()

	start := time.Now()
	s, err := store.NewJSONStore(*data)
	if err != nil {
		log.Fatalf("load data from %s: %v", *data, err)
	}
	var static http.Handler
	if info, err := os.Stat(filepath.Join(*web, "index.html")); err == nil && !info.IsDir() {
		static = http.FileServer(http.Dir(*web))
	} else {
		log.Printf("no front end at %s: serving the API only", *web)
	}
	log.Printf("loaded data in %s; listening on http://%s", time.Since(start).Round(time.Millisecond), *addr)
	srv := &http.Server{Addr: *addr, Handler: api.NewServer(s, static), ReadHeaderTimeout: 10 * time.Second}
	log.Fatal(srv.ListenAndServe())
}
