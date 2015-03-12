package main

import (
        "fmt"
	"github.com/gorilla/mux"
	"log"
	"net/http"
	"os/exec"
)

func drill_fc(w http.ResponseWriter, r *http.Request) {

	params := mux.Vars(r)
	start_date := params["start_date"]
	end_date := params["end_date"]
	lon := params["lon"]
	lat := params["lat"]

	out, err := exec.Command("python", "../core/pixel_drill_fc.py", start_date, end_date, lon, lat).Output()
	if err != nil {
		log.Fatal(err)
	}

        fmt.Println(out)
	w.Write([]byte(out))
}

func drill_wofs(w http.ResponseWriter, r *http.Request) {

	params := mux.Vars(r)
	start_date := params["start_date"]
	end_date := params["end_date"]
	lon := params["lon"]
	lat := params["lat"]
        
        fmt.Println(start_date)
        fmt.Println(end_date)
        fmt.Println(lon)
        fmt.Println(lat)
	out, err := exec.Command("python", "../core/pixel_drill_wofs.py", start_date, end_date, lon, lat).Output()
	if err != nil {
		log.Fatal(err)
	}

        fmt.Println(out)
	w.Write([]byte(out))
}

func drill_era_interim(w http.ResponseWriter, r *http.Request) {

	params := mux.Vars(r)
	start_date := params["start_date"]
	end_date := params["end_date"]
	lon := params["lon"]
	lat := params["lat"]

	out, err := exec.Command("python", "../core/pixel_drill_era_interim.py", start_date, end_date, lon, lat).Output()
	if err != nil {
		log.Fatal(err)
	}

        fmt.Println(out)
	w.Write([]byte(out))
}

func main() {
	r := mux.NewRouter()

	r.Handle("/", http.RedirectHandler("/web_server/index.html", 302))
	r.HandleFunc("/pixel_drill_fc/{start_date:[A-Z0-9.:-]+}/{end_date:[A-Z0-9.:-]+}/{lon:[0-9.-]+}/{lat:[0-9.-]+}/", drill_fc).Methods("GET")
	r.HandleFunc("/pixel_drill_wofs/{start_date:[A-Z0-9.:-]+}/{end_date:[A-Z0-9.:-]+}/{lon:[0-9.-]+}/{lat:[0-9.-]+}/", drill_wofs).Methods("GET")
	r.HandleFunc("/pixel_drill_era_interim/{start_date:[A-Z0-9.:-]+}/{end_date:[A-Z0-9.:-]+}/{lon:[0-9.-]+}/{lat:[0-9.-]+}/", drill_era_interim).Methods("GET")
	r.PathPrefix("/web_server/").Handler(http.StripPrefix("/web_server", http.FileServer(http.Dir("./static/"))))

	http.Handle("/", r)

	panic(http.ListenAndServe("127.0.0.1:8081", nil))
}
