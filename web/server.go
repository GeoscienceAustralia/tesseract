package main

import (
	"encoding/json"
	"github.com/gorilla/mux"
	"net/http"
	"os/exec"
)

func projectAll(w http.ResponseWriter, r *http.Request) {

	//params := mux.Vars(r)
	//year := params["year"]
	//exp_name := params["exp_name"]
	//source := params["source"]
	//date := params["date"]

	//var filePath = HomeFolder + year + "/" + exp_name + "/" + source + "/" + date + "/"

	var result = exec.Command("python", "../core/datacube_esteroids.py", "1985-08-01T00:00:00.000Z",
	"2000-09-01T00:00:00.000Z", "147.542", "-30.6234").Run()
	jsonBytes, _ := json.Marshal(result)
	w.Write([]byte(jsonBytes))
}

func main() {
	r := mux.NewRouter()

	r.Handle("/", http.RedirectHandler("/web_server/index.html", 302))
	r.HandleFunc("/pixel_drill/{year:[0-9]+}/{exp_name:[A-Za-z0-9._ %-]+}/{source:[A-Za-z0-9._ %-]+}/{date:[0-9]+}/", projectAll).Methods("GET")
	r.PathPrefix("/web_server/").Handler(http.StripPrefix("/web_server", http.FileServer(http.Dir("./static/"))))

	http.Handle("/", r)

	panic(http.ListenAndServe(":8081", nil))
}
