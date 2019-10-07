from flask import Flask, render_template, request, send_file
from dcorepackager import DCOREPackager
from urllib.parse import urlparse

app = Flask(__name__)

def parseURL(fullURL):
    o = urlparse(fullURL)
    baseURL = "://".join([o.scheme,o.netloc])
    handle = o.path.rsplit("/handle/").pop()
    return {"base":baseURL, "handle":handle}

@app.route("/")
def homepage():
    return render_template('home.html')

@app.route("/get")
def get_package():
    fullURL = request.args.get("fullurl")
    url = parseURL(fullURL)
    pkg = DCOREPackager(url['base'], url['handle'])
    return send_file(   
        pkg.getPackage(),
        as_attachment=True,
        mimetype="application/zip",
        attachment_filename="item.zip")

if __name__ == "__main__":
    app.run()
