import smtplib
from email.message import EmailMessage
def sendmail(to,subject,body):
    server = smtplib.SMTP_SSL('smtp.gmail.com',465)
    server.login('madambakamn@gmail.com','fikc nwvw mydg kywi')
    msg = EmailMessage()
    msg['From'] = 'madambakamn@gmail.com'
    msg['To'] = to
    msg['Subject'] = subject
    msg.set_content(body)
    server.send_message(msg)
    server.quit()