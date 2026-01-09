from flask import Blueprint, jsonify

main = Blueprint("main", __name__)

@main.route("/")
def index():
    return jsonify({
        "status": "aman",
        "keterangan": "Sistem UAS Praktikum Pemrograman berjalan dengan baik"
    })
