from extensions import db
from datetime import datetime

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    deadline = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<Task {self.id} - {self.content} ({"Done" if self.completed else "Pending"})>'

    def time_remaining(self):
        if self.deadline:
            now = datetime.now()
            remaining_time = self.deadline - now
            return remaining_time
        return None
