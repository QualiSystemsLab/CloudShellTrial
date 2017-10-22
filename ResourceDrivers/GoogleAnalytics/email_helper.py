import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from os.path import basename

class SMTPClient:
	def __init__(self, smtp_user, smtp_pass, smtp_address, smtp_port, send_as = None):
		self.smtp_user = smtp_user
		self.smtp_pass = smtp_pass
		self.smtp_address = smtp_address
		self.smtp_port = smtp_port
		self.send_as = send_as

	def send_email(self, recipients, message_title, message_body, is_html, files=None):
#		try:
		recipient_list = recipients.split(',')

		# Create message container - the correct MIME type is multipart/alternative.
		msg = MIMEMultipart('alternative')
		msg['Subject'] = message_title
		msg['From'] = self.smtp_user 
		if self.send_as: msg['From'] = self.send_as
		msg['To'] = recipient_list[0]
		if len(recipient_list) > 1:
			msg['Cc'] = ', '.join(recipient_list[1:])

		# Create the body of the message (a plain-text and an HTML version).
		text = message_body
		if is_html:
			html = message_body

		# Record the MIME types of both parts - text/plain and text/html.
		part1 = MIMEText(text, 'plain')
		if is_html:
			part2 = MIMEText(html, 'html')

		# the HTML message, is best and preferred.
		msg.attach(part1)
		if is_html:
			msg.attach(part2)
		if files:
			for filename in files:
				with open(filename, "rb") as file:
					part = MIMEApplication(file.read(), Name=basename(filename))

				part["Content-Disposition"] = 'attachment; filename="{}"'.format(basename(filename))
				msg.attach(part)

		# Send the message via local SMTP server.
		smtp_session = smtplib.SMTP(self.smtp_address, self.smtp_port)
		smtp_session.ehlo()
		smtp_session.starttls()
		smtp_session.login(self.smtp_user, self.smtp_pass)

		# sendmail function takes 3 arguments: sender's address, recipient's address
		# and message to send - here it is sent as one string.
		smtp_session.sendmail(msg['From'], recipient_list, msg.as_string())
		smtp_session.quit()
		return True
#		except Exception as ex:
#			return ex.message
