from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'rahasia_saya'

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:hiroo19mi2006@localhost/flask_login_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    password = db.Column(db.String(100))
    role = db.Column(db.String(20))

class Penelitian(db.Model):
    __tablename__ = 'penelitian'
    id = db.Column(db.Integer, primary_key=True)
    judul = db.Column(db.String(200))
    tahun = db.Column(db.Integer)
    kategori = db.Column(db.String(100))
    status = db.Column(db.String(20), default='menunggu')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    user = db.relationship('User', backref='penelitian')


@app.route("/")
def home():
    return render_template('index.html')

@app.route("/login", methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username, password=password).first()

        if user:
            session['username'] = user.username
            session['user_id'] = user.id
            session['role'] = user.role

            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('dashboard_dosen'))
                
        else:
            msg = "Username atau password salah."
            
    return render_template('login.html', msg=msg)

@app.route("/dashboard_dosen")
def dashboard_dosen():
    if 'username' not in session:
        return redirect(url_for('login'))

    # Hanya dosen yang boleh masuk
    if session.get('role') != 'dosen':
        return redirect(url_for('admin_dashboard'))

    # Ambil data penelitian dosen
    data = Penelitian.query.filter_by(user_id=session['user_id']).all()

    # Hitung statistik
    total = len(data)
    menunggu = len([d for d in data if d.status == 'menunggu'])
    disetujui = len([d for d in data if d.status == 'disetujui'])
    ditolak = len([d for d in data if d.status == 'ditolak'])

    return render_template(
        'dashboard_dosen.html',
        username=session['username'],
        data=data,
        total=total,
        menunggu=menunggu,
        disetujui=disetujui,
        ditolak=ditolak
    )

@app.route("/admin_dashboard")
def admin_dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))

    if session.get('role') != 'admin':
        return redirect(url_for('dashboard_dosen'))

    data = Penelitian.query.all()

    return render_template(
        'admin_dashboard.html',
        username=session['username'],
        data=data
    )

    
@app.route("/logout")
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

@app.route("/data")
def data():
    if "username" not in session:
        return redirect(url_for('login'))

    semua_penelitian = Penelitian.query.all()
    return render_template("data.html", data=semua_penelitian)

@app.route("/tambah", methods=['GET', 'POST'])
def tambah():
    if "username" not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        judul = request.form['judul']
        tahun = request.form['tahun']
        kategori = request.form['kategori']

        baru = Penelitian(judul=judul, tahun=tahun, kategori=kategori, status='menunggu', user_id=session['user_id'])
        db.session.add(baru)
        db.session.commit()

        return redirect(url_for('dashboard_dosen'))

    return render_template("tambah.html")

@app.route("/edit/<int:id>", methods=['GET', 'POST'])
def edit(id):
    if "username" not in session:
        return redirect(url_for('login'))

    penelitian = Penelitian.query.get(id)

    if request.method == 'POST':
        penelitian.judul = request.form['judul']
        penelitian.tahun = request.form['tahun']
        penelitian.kategori = request.form['kategori']

        db.session.commit()
        return redirect(url_for('dashboard_dosen'))

    return render_template("edit.html", penelitian=penelitian)

@app.route("/hapus/<int:id>")
def hapus(id):
    if "username" not in session:
        return redirect(url_for('login'))

    penelitian = Penelitian.query.get(id)
    db.session.delete(penelitian)
    db.session.commit()

    return redirect(url_for('dashboard_dosen'))

@app.route("/admin/verifikasi")
def admin_verifikasi():
    if 'role' in session and session['role'] == 'admin':
        data = Penelitian.query.filter_by(status='menunggu').all()
        return render_template("admin_verifikasi.html", data=data)
    else:
        return redirect(url_for('login'))
    
@app.route("/admin/setujui/<int:id>")
def setujui_penelitian(id):
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    p = Penelitian.query.get(id)
    if p:
        p.status = "disetujui"
        db.session.commit()

    return redirect(url_for('admin_verifikasi'))

@app.route("/admin/tolak/<int:id>")
def tolak_penelitian(id):
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    p = Penelitian.query.get(id)
    if p:
        p.status = "ditolak"
        db.session.commit()

    return redirect(url_for('admin_verifikasi'))

@app.route("/admin/penelitian")
def admin_penelitian():
    if 'role' in session and session['role'] == 'admin':
        data = Penelitian.query.all()
        return render_template("admin_penelitian.html", data=data)
    else:
        return redirect(url_for('login'))
    
@app.route("/admin/users")
def admin_users():
    if 'role' in session and session['role'] == 'admin':
        users = User.query.all()
        return render_template("admin_users.html", users=users)
    else:
        return redirect(url_for('login'))

@app.route("/admin/users/tambah", methods=['GET', 'POST'])
def tambah_user():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        new_user = User(username=username, password=password, role=role)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('admin_users'))

    return render_template("admin_tambah_user.html")

@app.route("/admin/users/edit/<int:id>", methods=['GET', 'POST'])
def edit_user(id):
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    user = User.query.get(id)

    if request.method == 'POST':
        user.username = request.form['username']
        user.password = request.form['password']
        user.role = request.form['role']
        db.session.commit()
        return redirect(url_for('admin_users'))

    return render_template("admin_edit_user.html", user=user)

@app.route("/admin/users/hapus/<int:id>")
def hapus_user(id):
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    user = User.query.get(id)
    if user:
        db.session.delete(user)
        db.session.commit()

    return redirect(url_for('admin_users'))











