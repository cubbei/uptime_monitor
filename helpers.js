function httpGet(theUrl)
{
    var xmlHttp = new XMLHttpRequest();
    xmlHttp.open( "GET", theUrl, false ); // false for synchronous request
    xmlHttp.send( null );
    return xmlHttp.responseText;
}

function get_id(uri)
{
    return uri.replace("https://","").replace("http://","").replaceAll(".","-")
}

function process_charts(data)
{
    
    for (const uri in data) {
        if (Object.hasOwnProperty.call(data, uri)) {
            console.log("processing: ", uri);
            const id = get_id(uri);
            const dataset = data[uri];
            console.log("dataset: ", dataset);
            const ctx = document.getElementById(id);
            ctx.innerHTML = "";
            var chart = null;
            try {
                chart = Chart.getChart(id);
                chart.data = dataset;
                chart.update();
            } catch (error) {
                chart = new Chart(ctx, {
                    type: 'bar', 
                    data: dataset,
                    options: {
                        scales: {
                            yAxis: {
                                max: 100,
                                min: 0
                            }
                        }
                    }
                })
            }
        }
    }
}


function get_data() {
    console.log("Updating chart data...")
    var data = httpGet("/stats");
    process_charts(JSON.parse(data));
    console.log("done.")
}

function main() {
    get_data();
    setInterval(() => {
        get_data();
    }, 30000);
}