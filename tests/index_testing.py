import unittest
from unittest.mock import patch
from datetime import datetime, timedelta
from flask import Flask
from utils.notifications import notifications_bp

class test_index(unittest.TestCase):

    def setUp(self):
        self.app = Flask(__name__)
        self.app.secret_key = "test-secret"
        self.app.register_blueprint(notifications_bp)
        self.client = self.app.test_client()

    @patch("utils.notifications.render_template")
    def test_index_get(self, mock_render):
        mock_render.return_value = b"html content"
        response = self.client.get("/notifications")
        self.assertEqual(response.data, b"html content")

    @patch("utils.notifications.scheduler.add_job")
    @patch("utils.notifications.render_template")
    def test_index_post_valid(self, mock_render, mock_add_job):
        mock_render.return_value = b"html content"
        future_time = (datetime.now() + timedelta(minutes = 15)).strftime("%Y-%m-%dT%H:%M")
        response = self.client.post("/notifications", data = {
            "email" : "test@example.com",
            "task_name" : "test task",
            "due_time" : future_time}, follow_redirects = True)
        self.assertTrue(mock_add_job.called)
        args, kwargs = mock_add_job.call_args
        self.assertEqual(kwargs["args"][0], "test@example.com")
        self.assertEqual(kwargs["args"][1], "test task")

    @patch("utils.notifications.render_template")
    def test_index_post_invalid_date(self, mock_render):
        mock_render.return_value = b"html content"
        response = self.client.post("/notifications", data = {
            "email" : "test@example.com",
            "task_name" : "test task",
            "due_time" : "invalid-date"}, follow_redirects = True)
        self.assertIn(b"html content", response.data)

    @patch("utils.notifications.scheduler.add_job")
    @patch("utils.notifications.render_template")
    def test_index_post_past_reminder(self, mock_render, mock_add_job):
        mock_render.return_value = b"html content"
        past_time = (datetime.now() - timedelta(minutes = 5)).strftime("%Y-%m-%dT%H:%M")
        response = self.client.post("/notifications", data = {
            "email" : "test@example.com",
            "task_name" : "past task",
            "due_time" : past_time}, follow_redirects = True)
        self.assertTrue(mock_add_job.called)
        reminder_time = mock_add_job.call_args.kwargs["run_date"]
        from datetime import datetime as dt
        self.assertLessEqual((reminder_time - dt.now()).total_seconds(), 10)