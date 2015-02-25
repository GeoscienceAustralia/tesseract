package main

import (
    "log"
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

	out, err := exec.Command("python", "../core/datacube_esteroids.py", "1985-08-01T00:00:00.000Z", "2000-09-01T00:00:00.000Z", "147.542", "-30.6234").Output()
	if err != nil {
		log.Fatal(err)
	}
	w.Write(out)
}


func projectAll1(w http.ResponseWriter, r *http.Request) {

    x := make([]interface{}, 0)
    geomap1 := make(map[string]interface{})
    geomap1["date"] = "11-Oct-13"
    geomap1["IE"] = 41.62
    geomap1["Chrome"] = 22.36
    geomap1["Firefox"] = 25.58
    geomap1["Safari"] = 9.13
    geomap1["Opera"] = 1.22
    x = append(x, geomap1)
    geomap2 := make(map[string]interface{})
    geomap2["date"] = "11-Oct-14"
    geomap2["IE"] = 41.95
    geomap2["Chrome"] = 22.15
    geomap2["Firefox"] = 25.78
    geomap2["Safari"] = 8.79
    geomap2["Opera"] = 1.25
    x = append(x, geomap2)
    geomap3 := make(map[string]interface{})
    geomap3["date"] = "11-Oct-15"
    geomap3["IE"] = 37.64
    geomap3["Chrome"] = 24.77
    geomap3["Firefox"] = 25.96
    geomap3["Safari"] = 10.16
    geomap3["Opera"] = 1.39
    x = append(x, geomap3)
    geomap4 := make(map[string]interface{})
    geomap4["date"] = "11-Oct-16"
    geomap4["IE"] = 37.64
    geomap4["Chrome"] = 24.65
    geomap4["Firefox"] = 25.98
    geomap4["Safari"] = 10.59
    geomap4["Opera"] = 1.44
    x = append(x, geomap4)

    //x1 := []int{3, 6, 3}

    jsonBytes, _ := json.Marshal(x)

	w.Write([]byte(jsonBytes))
}

func projectAll2(w http.ResponseWriter, r *http.Request) {

    x := []int{3, 6, 3}

	jsonBytes, _ := json.Marshal(x)

	w.Write([]byte(jsonBytes))
}

func main() {
	r := mux.NewRouter()

	r.Handle("/", http.RedirectHandler("/web_server/index.html", 302))
	r.HandleFunc("/pixel_drill/{year:[0-9]+}/{exp_name:[A-Za-z0-9._ %-]+}/{source:[A-Za-z0-9._ %-]+}/{date:[0-9]+}/", projectAll2).Methods("GET")
	r.HandleFunc("/pixel_drull/{year:[0-9]+}/{exp_name:[A-Za-z0-9._ %-]+}/{source:[A-Za-z0-9._ %-]+}/{date:[0-9]+}/", projectAll1).Methods("GET")

	r.PathPrefix("/web_server/").Handler(http.StripPrefix("/web_server", http.FileServer(http.Dir("./static/"))))

	http.Handle("/", r)

	panic(http.ListenAndServe("127.0.0.1:8081", nil))
}