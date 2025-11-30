import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
from utils.notifications import send_email_reminder

class TestSendEmailReminder(unittest.TestCase):

    @patch("utils.notifications.smtplib.SMTP_SSL")  
    @patch("utils.notifications.ssl.create_default_context") 
    def test_send_email_success(self, mock_ssl, mock_smtp):

        mock_ssl.return_value = MagicMock()

        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        due = datetime(2025, 1, 1, 12, 0)
        success, message = send_email_reminder(
            "test@example.com",
            "Walk Dog",
            due)

        self.assertTrue(success)
        self.assertIn("Reminder sent to test@example.com", message)

        mock_server.login.assert_called_once()
        mock_server.send_message.assert_called_once()

    @patch("utils.notifications.smtplib.SMTP_SSL")
    @patch("utils.notifications.ssl.create_default_context")
    def testSendEmailFailure(self, mock_ssl, mock_smtp):

        mock_smtp.side_effect = Exception("SMTP error")

        due = datetime(2025, 1, 1, 12, 0)
        success, message = send_email_reminder(
            "test@example.com",
            "Walk Dog",
            due)

        self.assertFalse(success)
        self.assertIn("SMTP error", message)  