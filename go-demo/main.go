package main

import (
	"log"
	"net/http"
)

func main() {
	mux := http.NewServeMux()

	mux.Handle("/static/", http.StripPrefix("/static/", http.FileServer(http.Dir("static"))))
	mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		http.ServeFile(w, r, "templates/index.html")
	})

	log.Println("Listening on http://localhost:5002")
	if err := http.ListenAndServe(":5002", mux); err != nil {
		log.Fatal(err)
	}
}
