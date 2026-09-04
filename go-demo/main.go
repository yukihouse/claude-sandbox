package main

import (
	"encoding/json"
	"log"
	"net/http"
	"sync"
)

// challengeWorkers は「100人同時押しチャレンジ」で同時に起動する goroutine の数。
const challengeWorkers = 100

// challengeState は同時押しチャレンジ専用のカウンター状態。
// 通常のカウンター（クライアント側JSのみで完結）とは独立している。
type challengeState struct {
	mu          sync.Mutex
	safeCount   int
	unsafeCount int
}

// runSafe は sync.Mutex で排他制御しながら100個のgoroutineで同時にインクリメントする。
// 必ず challengeWorkers 回分がすべて反映される。
func (s *challengeState) runSafe() int {
	s.mu.Lock()
	s.safeCount = 0
	s.mu.Unlock()

	var wg sync.WaitGroup
	wg.Add(challengeWorkers)
	for i := 0; i < challengeWorkers; i++ {
		go func() {
			defer wg.Done()
			s.mu.Lock()
			s.safeCount++
			s.mu.Unlock()
		}()
	}
	wg.Wait()

	s.mu.Lock()
	defer s.mu.Unlock()
	return s.safeCount
}

// runUnsafe はあえて排他制御をせずに100個のgoroutineで同時にインクリメントする。
// read-modify-write が競合し、押した回数より少ない結果になることがある
// （race condition を体感してもらうための実装）。
func (s *challengeState) runUnsafe() int {
	s.unsafeCount = 0

	var wg sync.WaitGroup
	wg.Add(challengeWorkers)
	for i := 0; i < challengeWorkers; i++ {
		go func() {
			defer wg.Done()
			s.unsafeCount++
		}()
	}
	wg.Wait()

	return s.unsafeCount
}

func writeChallengeResult(w http.ResponseWriter, result int) {
	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(map[string]int{
		"result":   result,
		"expected": challengeWorkers,
	})
}

func newMux() *http.ServeMux {
	mux := http.NewServeMux()
	challenge := &challengeState{}

	mux.Handle("/static/", http.StripPrefix("/static/", http.FileServer(http.Dir("static"))))
	mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/" {
			http.NotFound(w, r)
			return
		}
		http.ServeFile(w, r, "templates/index.html")
	})

	mux.HandleFunc("/api/challenge/safe", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
			return
		}
		writeChallengeResult(w, challenge.runSafe())
	})

	mux.HandleFunc("/api/challenge/unsafe", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
			return
		}
		writeChallengeResult(w, challenge.runUnsafe())
	})

	return mux
}

func main() {
	log.Println("Listening on http://localhost:5002")
	if err := http.ListenAndServe(":5002", newMux()); err != nil {
		log.Fatal(err)
	}
}
