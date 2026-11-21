import os, csv, io, secrets
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, Response, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint
from werkzeug.security import check_password_hash

app=Flask(__name__)
app.config['SECRET_KEY']=os.getenv('SECRET_KEY') or secrets.token_hex(32)
db_url=os.getenv('DATABASE_URL','sqlite:///neet.db')
if db_url.startswith('postgres://'): db_url='postgresql://'+db_url[len('postgres://'):]
app.config['SQLALCHEMY_DATABASE_URI']=db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
app.config['SESSION_COOKIE_HTTPONLY']=True
app.config['SESSION_COOKIE_SAMESITE']='Lax'
app.config['SESSION_COOKIE_SECURE']=os.getenv('COOKIE_SECURE','0')=='1'
db=SQLAlchemy(app)
SUBJECTS=[('Physics',45),('Chemistry',45),('Botany',45),('Zoology',45)]
TOTAL=180

class Student(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    reg=db.Column(db.String(30),unique=True,nullable=False)
    name=db.Column(db.String(160),nullable=False)
    started_at=db.Column(db.DateTime(timezone=True),nullable=False)
    submitted_at=db.Column(db.DateTime(timezone=True))
    answers=db.relationship('Answer',backref='student',cascade='all, delete-orphan',lazy=True)
class Answer(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    student_id=db.Column(db.Integer,db.ForeignKey('student.id'),nullable=False)
    q=db.Column(db.Integer,nullable=False)
    option=db.Column(db.String(1),nullable=False)
    __table_args__=(UniqueConstraint('student_id','q'),)
with app.app_context(): db.create_all()

def utcnow(): return datetime.now(timezone.utc)
def aware(dt): return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt
def expired(s): return utcnow()>=aware(s.started_at)+timedelta(minutes=180)
def finish_if_expired(s):
    if not s.submitted_at and expired(s):
        s.submitted_at=utcnow();db.session.commit()
def admin_required(fn):
    @wraps(fn)
    def wrapper(*args,**kwargs):
        if not session.get('admin'):return redirect(url_for('admin_login'))
        return fn(*args,**kwargs)
    return wrapper
@app.route('/')
def home():return render_template('home.html')
@app.route('/register',methods=['POST'])
def register():
    name=' '.join(request.form.get('name','').split())
    if not 2<=len(name)<=160:flash('Enter a valid full name.');return redirect(url_for('home'))
    student=Student(reg='SCI-NEET-'+secrets.token_hex(5).upper(),name=name,started_at=utcnow())
    db.session.add(student);db.session.commit();session['student_id']=student.id
    return redirect(url_for('exam'))
@app.route('/exam')
def exam():
    s=db.session.get(Student,session.get('student_id')) if session.get('student_id') else None
    if not s:return redirect(url_for('home'))
    finish_if_expired(s)
    if s.submitted_at:return render_template('submitted.html',student=s)
    return render_template('exam.html',student=s,subjects=SUBJECTS,answers={a.q:a.option for a in s.answers},deadline=(aware(s.started_at)+timedelta(minutes=180)).isoformat())
@app.post('/api/answer')
def save_answer():
    s=db.session.get(Student,session.get('student_id')) if session.get('student_id') else None
    if not s:return jsonify(error='Please register again'),401
    finish_if_expired(s)
    if s.submitted_at:return jsonify(error='Exam has ended'),403
    payload=request.get_json(silent=True) or {}
    try:q=int(payload.get('q'))
    except (TypeError,ValueError):return jsonify(error='Invalid question'),400
    option=payload.get('option')
    if q<1 or q>TOTAL or option not in ('A','B','C','D',None):return jsonify(error='Invalid answer'),400
    a=Answer.query.filter_by(student_id=s.id,q=q).first()
    if option is None:
        if a:db.session.delete(a)
    elif a:a.option=option
    else:db.session.add(Answer(student_id=s.id,q=q,option=option))
    db.session.commit();return jsonify(ok=True)
@app.post('/submit')
def submit():
    s=db.session.get(Student,session.get('student_id')) if session.get('student_id') else None
    if not s:return redirect(url_for('home'))
    if not s.submitted_at:s.submitted_at=utcnow();db.session.commit()
    return redirect(url_for('exam'))
@app.route('/admin/login',methods=['GET','POST'])
def admin_login():
    if request.method=='POST':
        password=os.getenv('ADMIN_PASSWORD','')
        candidate=request.form.get('password','')
        valid=(password.startswith('pbkdf2:') or password.startswith('scrypt:')) and check_password_hash(password,candidate) if password else False
        if not valid and password:valid=secrets.compare_digest(candidate,password)
        if valid:session.clear();session['admin']=True;return redirect(url_for('admin'))
        flash('Incorrect password')
    return render_template('login.html')
@app.route('/admin/logout',methods=['POST'])
@admin_required
def logout():session.clear();return redirect(url_for('home'))
@app.route('/admin')
@admin_required
def admin():
    students=Student.query.order_by(Student.id.desc()).all()
    for s in students:finish_if_expired(s)
    return render_template('admin.html',students=students)
@app.route('/admin/student/<int:sid>')
@admin_required
def student_result(sid):
    s=db.get_or_404(Student,sid);finish_if_expired(s)
    return render_template('result.html',student=s,subjects=SUBJECTS,answers={a.q:a.option for a in s.answers})
@app.route('/admin/export.csv')
@admin_required
def export():
    out=io.StringIO();w=csv.writer(out)
    w.writerow(['Registration','Name','Started UTC','Submitted UTC']+[f'Q{i}' for i in range(1,181)])
    for s in Student.query.order_by(Student.id).all():
        finish_if_expired(s);ans={a.q:a.option for a in s.answers}
        w.writerow([s.reg,s.name,s.started_at.isoformat(),s.submitted_at.isoformat() if s.submitted_at else '']+[ans.get(i,'') for i in range(1,181)])
    return Response(out.getvalue(),mimetype='text/csv',headers={'Content-Disposition':'attachment; filename=scientia_neet_responses.csv'})
if __name__=='__main__':app.run(debug=os.getenv('FLASK_DEBUG')=='1')
