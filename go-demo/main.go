package main

import (
	"log"
	"net/http"
)

func newMux() *http.ServeMux {
	mux := http.NewServeMux()

	mux.Handle("/static/", http.StripPrefix("/static/", http.FileServer(http.Dir("static"))))
	mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/" {
			http.NotFound(w, r)
			return
		}
		http.ServeFile(w, r, "templates/index.html")
	})

	return mux
}

func main() {
	log.Println("Listening on http://localhost:5002")
	if err := http.ListenAndServe(":5002", newMux()); err != nil {
		log.Fatal(err)
	}
}
