import sys
from app import create_app

recipient = None
if len(sys.argv) > 1:
    recipient = sys.argv[1]
else:
    import os
    recipient = os.environ.get('TEST_EMAIL')

if not recipient:
    print('Usage: python test_send_email.py recipient@example.com')
    raise SystemExit(1)

app = create_app()
with app.app_context():
    from services.email_service import EmailService
    svc = EmailService()
    ok = svc.send_test_email(recipient)
    print('send_test_email ->', ok)
