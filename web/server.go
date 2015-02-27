package main

import (
    "fmt"
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

    params := mux.Vars(r)
	start_date := params["start_date"]
	end_date := params["end_date"]
	lon := params["lon"]
	lat := params["lat"]

	//cmd := exec.Command("python", "../core/datacube_esteroids.py", start_date, end_date, lon, lat)

	fmt.Printf("python", "../core/datacube_esteroids.py", start_date, end_date, lon, lat)

    x := make([]interface{}, 0)
    item1 := make(map[string]interface{})
    item1["timestamp"] = "2011-02-13T23:43:41.000Z"
    item1["fc_0"] = 250.0
    item1["fc_1"] = 500.0
    item1["fc_2"] = 250.0
    //item1["fc_3"] = 0.0
    //item1["wofs_0"] = 100.0
    x = append(x, item1)
    item2 := make(map[string]interface{})
    item2["timestamp"] = "2011-02-16T13:23:04.000Z"
    item2["fc_0"] = 200.0
    item2["fc_1"] = 500.0
    item2["fc_2"] = 300.0
    //item2["fc_3"] = 0.0
    //item2["wofs_0"] = 150.0
    x = append(x, item2)
    item3 := make(map[string]interface{})
    item3["timestamp"] = "2011-02-26T17:23:31.000Z"
    item3["fc_0"] = 180.0
    item3["fc_1"] = 520.0
    item3["fc_2"] = 300.0
    //item3["fc_3"] = 0.0
    //item3["wofs_0"] = 150.0
    x = append(x, item3)
    item4 := make(map[string]interface{})
    item4["timestamp"] = "2011-03-01T09:51:34.000Z"
    item4["fc_0"] = 160.0
    item4["fc_1"] = 530.0
    item4["fc_2"] = 310.0
    //item4["fc_3"] = 0.0
    //item4["wofs_0"] = 150.0
    x = append(x, item4)
    item5 := make(map[string]interface{})
    item5["timestamp"] = "2011-03-08T11:04:23.000Z"
    item5["fc_0"] = 130.0
    item5["fc_1"] = 540.0
    item5["fc_2"] = 330.0
    //item5["fc_3"] = 0.0
    //item5["wofs_0"] = 150.0
    x = append(x, item5)

    jsonBytes, _ := json.Marshal(x)

	w.Write([]byte(jsonBytes))
}

func main() {
	r := mux.NewRouter()

	r.Handle("/", http.RedirectHandler("/web_server/index.html", 302))
	r.HandleFunc("/pixel_drill/{start_date:[A-Z0-9.:-]+}/{end_date:[A-Z0-9.:-]+}/{lon:[0-9.-]+}/{lat:[0-9.-]+}/", projectAll1).Methods("GET")
	r.PathPrefix("/web_server/").Handler(http.StripPrefix("/web_server", http.FileServer(http.Dir("./static/"))))

	http.Handle("/", r)

	panic(http.ListenAndServe("127.0.0.1:8081", nil))
}