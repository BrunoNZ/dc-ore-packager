from flask import Flask, render_template, request, send_file
from dcorepackager import DCOREPackager
from pathlib import Path

app = Flask(__name__)

@app.route("/")
def homepage():
    return render_template('home.html')

@app.route("/get")
def get_package():
    baseURL = request.args.get("baseurl")
    handle = request.args.get("handle")
    pkg = DCOREPackager(baseURL, handle)
    return send_file(   
        pkg.getPackage(),
        as_attachment=True,
        mimetype="application/zip",
        attachment_filename="item.zip")

if __name__ == "__main__":
    app.run()
