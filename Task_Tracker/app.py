from flask import Flask, render_template, request, redirect, url_for
from extensions import db
from models import Task
from datetime import datetime
import os

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)


@app.route('/')
@app.route('/<filter>')
def index(filter='all'):
    if filter == 'completed':
        tasks = Task.query.filter_by(completed=True).all()
    elif filter == 'pending':
        tasks = Task.query.filter_by(completed=False).all()
    else:
        tasks = Task.query.all()

    return render_template('index.html', tasks=tasks)


@app.route('/add', methods=['POST'])
def add_task():
    task_content = request.form['content']
    date_str = request.form.get('date')
    time_str = request.form.get('time')

    deadline_str = f"{date_str} {time_str}" if date_str and time_str else None
    deadline = datetime.strptime(deadline_str, '%d.%m.%Y %H:%M') if deadline_str else None

    new_task = Task(content=task_content, deadline=deadline)
    db.session.add(new_task)
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/delete/<int:id>')
def delete_task(id):
    task = Task.query.get_or_404(id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/complete/<int:id>')
def complete_task(id):
    task = Task.query.get_or_404(id)
    task.completed = not task.completed
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update_task(id):
    task = Task.query.get_or_404(id)
    if request.method == 'POST':
        task.content = request.form['content']
        date_str = request.form.get('date')
        time_str = request.form.get('time')

        deadline_str = f"{date_str} {time_str}" if date_str and time_str else None
        task.deadline = datetime.strptime(deadline_str, '%d.%m.%Y %H:%M') if deadline_str else None
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('update.html', task=task)


if __name__ == "__main__":
    with app.app_context():
        if not os.path.exists('tasks.db'):
            db.create_all()
    app.run(debug=True)
