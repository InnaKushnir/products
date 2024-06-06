import os

from celery_ import app
from datetime import datetime


@app.task
def track_order_status(order_id, new_status):
    try:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        project_root = os.path.abspath(os.path.dirname(__file__))
        file_path = os.path.join(project_root, 'order_events.txt')

        with open(file_path, "a") as file:
            file.write(f'Order {order_id} change status on {new_status["status"]} at {current_time}\n')
    except Exception as e:
        print(f"Error while writing to file: {e}")