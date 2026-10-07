import os
from flask import Flask, render_template, redirect, url_for, request
from models import db, Task
from forms import TaskForm
from datetime import datetime, timedelta

app = Flask(__name__)
app.config["SECRET_KEY"] = "super_secret_key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///todo.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

@app.route("/", methods=["GET", "POST"])
def index():
    form = TaskForm()
    if form.validate_on_submit():
        task = Task(
            title=form.title.data,
            description=form.description.data,
            deadline=form.deadline.data,
            priority=form.priority.data
        )
        db.session.add(task)
        db.session.commit()
        return redirect(url_for("index"))

    tasks = Task.query.order_by(Task.deadline).all()
    total = len(tasks)
    done_count = sum(1 for t in tasks if t.is_done)

    now = datetime.now()
    today_date = now.date()
    start_of_week = today_date - timedelta(days=today_date.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    grouped = {"overdue": [], "today": [], "this_week": [], "later": [], "completed": []}

    for t in tasks:
        if t.is_done:
            grouped["completed"].append(t)
        elif t.deadline < now:
            grouped["overdue"].append(t)
        elif t.deadline.date() == today_date:
            grouped["today"].append(t)
        elif start_of_week <= t.deadline.date() <= end_of_week:
            grouped["this_week"].append(t)
        else:
            grouped["later"].append(t)

    return render_template("index.html", form=form, grouped=grouped, total=total, done_count=done_count)

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    task = Task.query.get_or_404(id)
    form = TaskForm(obj=task)
    if form.validate_on_submit():
        task.title = form.title.data
        task.description = form.description.data
        task.deadline = form.deadline.data
        task.priority = form.priority.data
        db.session.commit()
        return redirect(url_for("index"))
    return render_template("edit.html", form=form, task=task)

@app.route("/toggle/<int:id>", methods=["POST"])
def toggle(id):
    task = Task.query.get_or_404(id)
    task.is_done = not task.is_done
    db.session.commit()
    return redirect(url_for("index"))

@app.route("/delete/<int:id>", methods=["POST"])
def delete(id):
    task = Task.query.get_or_404(id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for("index"))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
