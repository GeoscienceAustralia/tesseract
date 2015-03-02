package main

import (
	"encoding/json"
	"fmt"
	"github.com/gorilla/mux"
	"log"
	"net/http"
	"os/exec"
)

func projectAll(w http.ResponseWriter, r *http.Request) {

	params := mux.Vars(r)
	start_date := params["start_date"]
	end_date := params["end_date"]
	lon := params["lon"]
	lat := params["lat"]

	fmt.Printf("python", "../core/datacube_esteroids.py", start_date, end_date, lon, lat)

	out, err := exec.Command("python", "../core/datacube_steroids.py", start_date, end_date, lon, lat).Output()
	if err != nil {
		log.Fatal(err)
	}

	w.Write([]byte(out))
}

func main() {
	r := mux.NewRouter()

	r.Handle("/", http.RedirectHandler("/web_server/index.html", 302))
	r.HandleFunc("/pixel_drill/{start_date:[A-Z0-9.:-]+}/{end_date:[A-Z0-9.:-]+}/{lon:[0-9.-]+}/{lat:[0-9.-]+}/", projectAll).Methods("GET")
	r.PathPrefix("/web_server/").Handler(http.StripPrefix("/web_server", http.FileServer(http.Dir("./static/"))))

	http.Handle("/", r)

	panic(http.ListenAndServe("127.0.0.1:8081", nil))
}
