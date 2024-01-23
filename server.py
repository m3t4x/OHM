import datetime
import io
import os

from bs4 import BeautifulSoup
from flask import Flask, render_template, redirect, Response, session, request
from main import Scraper
from flask_socketio import SocketIO, emit
import requests


app = Flask(__name__,
            template_folder="Pages")
app.secret_key = 'myKeys'
socketio = SocketIO(app)
bg_threads = []
scraper = None

def ScrapeLinks(soup):
    table = soup.find("table").find("tbody")
    trs = table.find_all("tr")
    links = []
    for tr in trs:
        link = tr.find_all("a")[1]["href"]
        links.append(link)
    return links

def ScrapeEntry(soup):
    try:
        dl = soup.find("dl", {"class": "datalist"})
        divs = dl.find_all("div")
        dataList = []
        for div in divs:
            data = div.find("dd").text
            data = data.strip().replace(","," ")
            dataList.append(data)
        return dataList
    except:
        return False

def StartScraping(startDate, endDate, item):
    startDate = startDate + "T00:00"
    endDate = endDate + "T23:59"
    session : requests.session = scraper.GetSession()
    url = "https://souscription.ohm-energie.com/admin"
    admin = session.get(url)
    soup = BeautifulSoup(admin.text, "html.parser")
    baseLink = soup.find("ul", {"class": "submenu"}).find("a")["href"]
    signature = baseLink.split("signature=")[-1].split("&")[0]
    baseLink = baseLink.replace("https://souscription.ohm-energie.com", "")
    pageNum = 1
    if startDate and endDate:
        reqUrl = "https://souscription.ohm-energie.com/admin?referrer=%s&crudAction=index&crudControllerFqcn=App\Controller\EasyAdmin\ContractDraftColdController&entityFqcn=App\Entity\ContractualDataCold&menuIndex=0&signature=%s&submenuIndex=0&filters[createdAt][comparison]=between&filters[createdAt][value]=%s&filters[createdAt][value2]=%s&filters[contractStatus][comparison]==&filters[contractStatus][value]=%s&page=%s"%(baseLink, signature, startDate, endDate, item, pageNum)
    else:
        reqUrl = "https://souscription.ohm-energie.com/admin?referrer=%s&crudAction=index&crudControllerFqcn=App\Controller\EasyAdmin\ContractDraftColdController&entityFqcn=App\Entity\ContractualDataCold&menuIndex=0&signature=%s&submenuIndex=0&filters[contractStatus][comparison]==&filters[contractStatus][value]=%s&page=%s" % (baseLink, signature, item,pageNum)
    builtReq = session.get(reqUrl)
    if "Aucun résultat trouvé" in builtReq.text:
        socketio.emit('initialize', {'pages': "RESULTS", "id": item, "current": "NO"})
    else:
        soup = BeautifulSoup(builtReq.text, "html.parser")
        count = int(soup.find("div", {"class": "list-pagination-counter"}).find("strong").text.strip())
        pages = 1
        if count % 20 == 0:
            pages = count // 20
        else:
            pages = (count // 20) + 1
        socketio.emit('initialize', {'pages': pages, "id": item, "current": 0})
        entriesLinks = []
        for pg in range(1, pages+1):
            url = reqUrl.replace("page=%s"%pageNum, "page=%s"%pg)
            req = session.get(url)
            soup = BeautifulSoup(req.text, "html.parser")
            links = ScrapeLinks(soup)
            for link in links:
                entriesLinks.append(link)
            pageNum = pg
            socketio.emit('initialize', {'pages': pages, "id": item, "current": pg})
        dateName = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M")
        fileName = "%s_%s.csv"%(dateName, item)
        instancePath = app.instance_path.replace("/instance","")
        outputFile = os.path.join(instancePath, "static", fileName)
        i = 0
        for link in entriesLinks:
            url = session.get(link)
            soup = BeautifulSoup(url.text, 'html.parser')
            entryData = ScrapeEntry(soup)
            i = i + 1
            if entryData:
                with io.open(outputFile, "a+", encoding="utf-8") as op:
                    op.write("%s\n"%(",".join(entryData)))
                socketio.emit('entry', {'total': len(entriesLinks), "id": item, "current": i})
            else:
                socketio.emit('entry', {'total': len(entriesLinks), "id": item, "current": i})

@app.route("/history", methods= ["GET"])
def history():
    instancePath = app.instance_path.replace("/instance", "")
    abs_path = os.path.join(instancePath, "static")
    files = os.listdir(abs_path)
    return render_template('history.html', files=files)

@app.route('/start', methods = ['POST'])
def StartScrape():
    global bg_threads
    startDate = request.form["startDate"]
    endDate = request.form["endDate"]
    selected = request.form.getlist("status")
    firstPartHtml = """
    <!DOCTYPE html>
        <html lang="en">
        <head>
            <style>
        fieldset span, fieldset h3 {
            display: inline; /* Makes span and h3 inline elements */
            margin-right: 10px; /* Adds spacing between the elements */
        }
        </style>
        </head>
        <body>
              <fieldset>
                    <legend>Scraping</legend>
    """
    sndPartHtml = """
                  </fieldset>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.0/socket.io.js"></script>
            <script type="text/javascript" charset="utf-8">
            var socket = io();
    
            socket.on('initialize', function(data) {
                console.log(data);
                var node = document.getElementById(data["id"]);
                node.innerText = "Scraping Links "+data["current"]+"/"+data["pages"];
            });

            socket.on('entry', function(data) {
                console.log(data);
                var node = document.getElementById(data["id"]+"_entries");
                node.innerText = "Scraping Links "+data["current"]+"/"+data["total"];
            });

            </script>
        </body>
        </html>
    """
    dataDict = scraper.GetDataDict()
    for item in selected:
        value = dataDict[item]
        firstPartHtml = firstPartHtml + "<span> Scraping Filter (%s) ... <h3 id='%s'></h3></span><br>"%(item, value) + "<span>     Scraping Client Entries (%s) ... <h3 id='%s_entries'></h3></span><br>"%(item, value)
    fullHtml = firstPartHtml + sndPartHtml
    for item in selected:
        background_thread = socketio.start_background_task(StartScraping, startDate, endDate, dataDict[item])
        bg_threads.append(background_thread)
    return fullHtml

@app.route('/', methods = ['GET'])
def BarrierPage():
    return render_template("security.html")


@app.route('/login', methods=['POST'])
def login():
    correct_password = 'cherif888'
    password = request.form['password']
    if password == correct_password:
        session['connected'] = True
        return redirect("/scrape")
    else:
        session['connected'] = False
        return redirect("/")

@app.route('/checkLogin', methods=["POST"])
def check_login():
    global scraper
    if session.get('connected'):
        data = request.get_json()
        scraper = Scraper()
        username = data['username']
        password = data['password']
        status = scraper.CheckLogin(username, password)
        if status:
            return Response('{"status":"success"}', status=200, mimetype='application/json')
        else:
            return Response(status=403)

@app.route('/scrape')
def secret_page():
    if session.get('connected'):
        return render_template("scrape.html")
    else:
        return redirect("/")

if __name__ == '__main__':
    app.run(debug=True)
