package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

func TestHomePage(t *testing.T) {
	req := httptest.NewRequest(http.MethodGet, "/", nil)
	w := httptest.NewRecorder()
	newMux().ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d", w.Code)
	}
	if !strings.Contains(w.Body.String(), "カウンターデモ (Go版)") {
		t.Fatalf("expected counter page body, got %q", w.Body.String())
	}
}

func TestStaticStyle(t *testing.T) {
	req := httptest.NewRequest(http.MethodGet, "/static/style.css", nil)
	w := httptest.NewRecorder()
	newMux().ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d", w.Code)
	}
}

func TestNotFound(t *testing.T) {
	req := httptest.NewRequest(http.MethodGet, "/unknown", nil)
	w := httptest.NewRecorder()
	newMux().ServeHTTP(w, req)

	if w.Code != http.StatusNotFound {
		t.Fatalf("expected 404, got %d", w.Code)
	}
}

func TestChallengeSafeAlwaysMatchesExpected(t *testing.T) {
	req := httptest.NewRequest(http.MethodPost, "/api/challenge/safe", nil)
	w := httptest.NewRecorder()
	newMux().ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d", w.Code)
	}

	var body map[string]int
	if err := json.NewDecoder(w.Body).Decode(&body); err != nil {
		t.Fatalf("failed to decode response: %v", err)
	}
	if body["expected"] != challengeWorkers {
		t.Fatalf("expected %d, got %d", challengeWorkers, body["expected"])
	}
	if body["result"] != body["expected"] {
		t.Fatalf("mutex-protected challenge must never lose increments: got %d, want %d", body["result"], body["expected"])
	}
}

func TestChallengeUnsafeRespondsWithExpectedCount(t *testing.T) {
	req := httptest.NewRequest(http.MethodPost, "/api/challenge/unsafe", nil)
	w := httptest.NewRecorder()
	newMux().ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d", w.Code)
	}

	var body map[string]int
	if err := json.NewDecoder(w.Body).Decode(&body); err != nil {
		t.Fatalf("failed to decode response: %v", err)
	}
	if body["expected"] != challengeWorkers {
		t.Fatalf("expected %d, got %d", challengeWorkers, body["expected"])
	}
	if body["result"] < 0 || body["result"] > challengeWorkers {
		t.Fatalf("result out of range: got %d", body["result"])
	}
}

func TestChallengeRejectsNonPost(t *testing.T) {
	for _, path := range []string{"/api/challenge/safe", "/api/challenge/unsafe"} {
		req := httptest.NewRequest(http.MethodGet, path, nil)
		w := httptest.NewRecorder()
		newMux().ServeHTTP(w, req)

		if w.Code != http.StatusMethodNotAllowed {
			t.Fatalf("%s: expected 405, got %d", path, w.Code)
		}
	}
}
