from flask import Flask, render_template, request, redirect, session
import sqlite3
import urllib.parse
from datetime import datetime

app = Flask(__name__)
app.secret_key = "rentmanager"

def get_db():
    conn = sqlite3.connect("rent.db")
    conn.row_factory = sqlite3.Row
    return conn
@app.route("/")
def home():
    return redirect("/login")


@app.route("/dashboard")
def dashboard():

    if "admin" not in session:
        return redirect("/login")

    conn = get_db()

    rooms = conn.execute("SELECT * FROM rooms").fetchall()

    data = []

    for room in rooms:

        last = conn.execute(
        "SELECT * FROM bills WHERE room_id=? ORDER BY id DESC LIMIT 1",
        (room["id"],)
        ).fetchone()

        data.append((room,last))

    conn.close()

    return render_template("index.html", data=data)


@app.route("/generate", methods=["POST"])
def generate():

    room_id = request.form["room_id"]
    curr = int(request.form["current"])
    water = int(request.form["water"])
    balance = int(request.form["balance"])

    conn = get_db()

    room = conn.execute(
    "SELECT * FROM rooms WHERE id=?",
    (room_id,)
    ).fetchone()

    last = conn.execute(
    "SELECT * FROM bills WHERE room_id=? ORDER BY id DESC LIMIT 1",
    (room_id,)
    ).fetchone()

    prev = 0
    if last:
        prev = last["curr_reading"]

    units = curr - prev
    electricity = units * 12

    total = room["rent"] + electricity + water + balance

    month = datetime.now().strftime("%B %Y")

    conn.execute("""
    INSERT INTO bills
    (room_id,prev_reading,curr_reading,units,electricity,water,balance,total,month)
    VALUES(?,?,?,?,?,?,?,?,?)
    """,
    (room_id,prev,curr,units,electricity,water,balance,total,month)
    )

    conn.commit()
    conn.close()

    return f"""
    <h2>Bill Generated</h2>
    Previous Reading: {prev}<br>
    Units Used: {units}<br>
    Electricity: {electricity}<br>
    Total Bill: {total}<br><br>
    <a href="/">Back</a>
    """


@app.route("/history/<room_id>")
def history(room_id):

    conn = get_db()

    room = conn.execute(
    "SELECT * FROM rooms WHERE id=?",
    (room_id,)
    ).fetchone()

    bills = conn.execute(
    "SELECT * FROM bills WHERE room_id=?",
    (room_id,)
    ).fetchall()

    conn.close()

    return render_template("history.html", room=room, bills=bills)
@app.route("/send/<int:room_id>")
def send(room_id):

    conn = get_db()

    room = conn.execute(
    "SELECT * FROM rooms WHERE id=?",
    (room_id,)
    ).fetchone()

    last = conn.execute(
    "SELECT * FROM bills WHERE room_id=? ORDER BY id DESC LIMIT 1",
    (room_id,)
    ).fetchone()

    if not last:
        return "No bill yet"

    message = f"""
⚡ Electricity Bill

Room: {room['room_number']}
Rent: ₹{room['rent']}

Units Used: {last['units']}
Total Bill: ₹{last['total']}

Please pay your bill Via Phone Pay Or Cash
For Phone Pay use:chhayasalunkhe1977@axl
Phone No: 7972722366(Chhaya Salunkhe)
"""

    phone = room["phone"]

    text = urllib.parse.quote(message)

    url = f"https://wa.me/91{phone}?text={text}"

    conn.close()

    return redirect(url)

@app.route("/delete/<int:bill_id>")
def delete(bill_id):

    conn = get_db()

    conn.execute("DELETE FROM bills WHERE id=?", (bill_id,))

    conn.commit()
    conn.close()

    return redirect("/")

@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if username == "salunkhe_corner" and password == "sc5737":
            session["admin"] = True
            return redirect("/dashboard")

        return "Invalid Login"

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect("/login")

@app.route("/summary")
def summary():

    conn = get_db()

    rooms = conn.execute("SELECT * FROM rooms").fetchall()

    room_names=[]
    room_units=[]
    room_bills=[]

    total_rent=0
    total_units=0
    total_bills=0

    for r in rooms:

        total_rent += r["rent"]
        room_names.append(r["room_number"])

        last = conn.execute(
        "SELECT units,total FROM bills WHERE room_id=? ORDER BY id DESC LIMIT 1",
        (r["id"],)
        ).fetchone()

        if last:
            room_units.append(last["units"])
            room_bills.append(last["total"])
            total_units += last["units"]
            total_bills += last["total"]
        else:
            room_units.append(0)
            room_bills.append(0)

    return render_template(
        "summary.html",
        rooms=len(rooms),
        total_rent=total_rent,
        total_units=total_units,
        total_bills=total_bills,
        room_names=room_names,
        room_units=room_units,
        room_bills=room_bills
    )

@app.route("/tenants")
def tenants():

    if "admin" not in session:
        return redirect("/login")

    conn = get_db()

    tenants = conn.execute(
    "SELECT * FROM tenants"
    ).fetchall()

    conn.close()

    return render_template("tenants.html", tenants=tenants)

@app.route("/add_tenant", methods=["POST"])
def add_tenant():

    name = request.form["name"]
    room = request.form["room"]
    profession = request.form["profession"]
    phone = request.form["phone"]
    joining = request.form["joining"]
    leaving = request.form["leaving"]
    rent = request.form["rent"]
    deposit = request.form["deposit"]

    conn = get_db()

    conn.execute("""
    INSERT INTO tenants
    (name,room_number,profession,phone,joining_date,leaving_date,rent,deposit)
    VALUES(?,?,?,?,?,?,?,?)
    """,(name,room,profession,phone,joining,leaving,rent,deposit))

    conn.commit()
    conn.close()

    return redirect("/tenants")

@app.route("/delete_tenant/<int:id>")
def delete_tenant(id):

    conn = get_db()

    conn.execute(
    "DELETE FROM tenants WHERE id=?",
    (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/tenants")




if __name__ == "__main__":
    app.run(debug=True)