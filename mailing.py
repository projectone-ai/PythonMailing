import smtplib
import imaplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from os.path import basename
from decorators import check_server_connection
import email


class PyMailing:
    """
    This class has the main objective of organazing and sending emails of a single specific email provider
    e.g. (gmail, yahoo, outlook...)

    How it works:
    Firstly you have to instance the class by initializing it with the required parameters in the __init__ method.
    Try to perform Log In using the method start_connection_auth()
    Being logged on, you can call functions to perform actions like sending, listing emails and so on.

    If Log In failure:
        - Check the server configuration and credentials entered in the class initialization.
        - Check if your email provider accepts connection from a less secure source.

    After finishing using the object, you may want to close open connections by calling the close_connection() method.
    """
    def __init__(self, imap_server_address: str, smtp_server_address: str, smtp_port: str, email_address: str,
                 email_password: str):
        """
        Initializes the class by entering the essential Log In parameters.

        :param imap_server_address: The IMAP server address, should be available at your email provider website.
        :param smtp_server_address: The SMTP server address, should be available at your email provider website.
        :param smtp_port: The PORT of the SMTP server address, should be available at your email provider website.
        :param email_address: The email address you want to handle, e.g. example@gmail.com
        :param email_password: The password of the email address.
        """
        # Set IMAP, SMTP Configuration and credentials.
        self.__imap_server_address = imap_server_address
        self.__smtp_server_address = smtp_server_address
        self.__smtp_port = smtp_port
        self.__email_address = email_address
        self.__email_password = email_password
        self.domain = self.email_provider

        # Instancing the servers communication
        self._smtp_server = smtplib.SMTP(host=self.__smtp_server_address, port=self.__smtp_port)
        self._imap_server = imaplib.IMAP4_SSL(self.__imap_server_address)

    @staticmethod
    def __get_text(msg):
        """
        A recursive and internal static method for message extracting.

        :param msg: the raw message format that needs to be handled.
        :return: Returns a extracted message.
        """
        if msg.is_multipart():
            return PyMailing.__get_text(msg.get_payload(0))
        else:
            return msg.get_payload(None, True)

    @property
    def email_provider(self):
        """
        It will extract the email provider name from the email address.

        :return: Returns the email provider name.
        """
        domain = self.__email_address.split('@')[1]
        domain = domain.split('.')[0].lower()
        return domain

    def start_connection_auth(self):
        """ Perform authentication into your email service, trying to log in using SMTP and IMAP protocols. """
        self._smtp_server.starttls()
        self._smtp_server.login(user=self.__email_address, password=self.__email_password)
        self._imap_server.login(user=self.__email_address, password=self.__email_password)

    @check_server_connection
    def close_connection(self):
        """ Close the SMTP and IMAP server connection """
        self._smtp_server.close()
        self._imap_server.logout()

    @check_server_connection
    def list_boxes(self):
        """
        This method has the purpose of listing the boxes of an email account.

        :return: Returns a list of email boxes.
        """
        return [mailbox.decode().split(' "/" ')[1].replace('"', "") for mailbox in (self._imap_server.list()[1])]

    @check_server_connection
    def send_email(self, to_addr: list, subject: str, message: str, attachment=None,
                   to_cc: list = None, to_bcc: list = None):
        """
        This method sends an email to N emails addresses.

        :param to_addr: A list of N emails addresses.
        :param subject: An email subject.
        :param message: The message that will be sent via email, raw text or HTML are accepted.
        :param attachment: Optional for attaching a file to the email.
        :param to_cc: Optional list of email addresses for carbon copy.
        :param to_bcc: Optional list of email addresses for blind carbon copy.
        """
        msg = MIMEMultipart()
        msg['From'] = self.__email_address
        msg['To'] = ", ".join(to_addr)
        msg['CC'] = ", ".join(to_cc) if to_cc else ""
        msg['Subject'] = subject

        # Multipurpose Internet Mail Extensions (MIME) is an Internet standard that extends the format of email
        # messages to support text in character sets other than ASCII
        msg_text = MIMEText('%s' % message, 'html')
        msg.attach(msg_text)

        if attachment:
            part = MIMEApplication(
                attachment.read(),
                Name=basename(attachment.name)
            )
            part['Content-Disposition'] = 'attachment; filename="%s"' % basename(attachment.name)
            msg.attach(part)

        text = msg.as_string()
        to_bcc = to_bcc if to_bcc else []
        self._smtp_server.sendmail(self.__email_address, to_addr + to_bcc, text)

    @check_server_connection
    def list_emails(self, box: str, n_emails: int = 5):
        """
        This method has the purpose of listing email messages.

        :param box: The Email box name you want to list messages. If you are not sure about the box name,
        consult it through list_boxes() method.
        :param n_emails: Optional for listing the last number of messages.
        If a value is not entered, five will be a default parameter.
        :return: Returns a list of N last messages, being N the n_emails parameter.
        """
        list_emails = list()
        # Selecting a specific box of your email.
        self._imap_server.select('"{}"'.format(box))
        status, emails_ids = self._imap_server.search(None, 'ALL')
        # Formating and resorting all email ids by descending order
        emails_ids = sorted([int(id) for id in emails_ids[0].split()], reverse=True)
        for email_id in emails_ids[:n_emails]:
            attachments = list()
            email_dict = dict()
            # the content data at the '(RFC822)' format comes on
            # a list with a tuple with header, content, and the closing
            # byte b')'
            typ, data = self._imap_server.fetch(str(email_id), '(RFC822)')
            # rearranging the data into a new dictionary for organizational  purposes
            message = email.message_from_bytes(data[0][1])
            email_dict['from'] = message['from']
            email_dict['to'] = message['to']
            email_dict['cc'] = message['cc']
            email_dict['subject'] = [subject[0].decode('utf-8') if subject[1] == 'utf-8'
                                     else subject[0] for subject in email.header.decode_header(message['Subject'])][0]
            email_dict['datetime'] = email.utils.parsedate_tz(message['Date'])
            for part in message.walk():
                if part.get('Content-Disposition'):
                    attachments.append({'file_name': part.get_filename(),
                                        'file_content': part.get_payload(decode=True)})
            email_dict['attachments'] = attachments
            try:
                email_dict['message'] = PyMailing.__get_text(message).decode('utf-8')
            except UnicodeError:
                email_dict['message'] = PyMailing.__get_text(message).decode('latin-1')
            # Appending the email info (from, to, subject, cc and datetime) into the mailing list
            list_emails.append(email_dict)
        return list_emails


# Basic usage example
# Initialize the PyMailing
mailing = PyMailing(imap_server_address='', smtp_server_address='', smtp_port='',
                    email_address='', email_password='')

# Authenticate to the email service
mailing.start_connection_auth()

# Choose a file to attach to the email you want to send
file = open(r'', mode='rb')

# Send an email with a file attached to it
mailing.send_email(to_addr=[''], subject='',
                   attachment=file, message='<html></html>')

# Check all available mailboxes
print(mailing.list_boxes())

# Check email provider property
print(mailing.email_provider)

# Retrieve the last n emails inside Inbox
last_five_emails = mailing.list_emails(box='Inbox', n_emails=5)
for email in last_five_emails:
    print(email)

# Close any opened connections
mailing.close_connection()
