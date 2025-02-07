import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

class MailSender:

    def __init__(self, config):
        """ Constructor of the class

        The constructor takes a dictionary detailing:
            mail_address:   Mail address of the account that will send the mails
            password:       Password of the account that will send the mails
            smtp_address:   Smtp Address of the server where the account belongs
            smtp_port:      Port to communicate with the Smtp server

        If no dictionary is entered, default values are set for account no-reply@ciberisciii.es
        """
        self.username = config['mail_address']
        self.password = config['password']
        self.smtp_address = config['smtp_address']
        self.smpt_port = config['smpt_port']

    def send_massive_emails(self, list_mails, send_name = None):
        """ Method that sends a list of massive mails

        The method accepts arguments:
            list_mails: It is actually a list, where each position contains a dictionary with the next structure
                        {   'subject': ..., 
                            'body': ..., 
                            'destination_emails': [...],
                            'cc_emails': [...],             # Optional field
                            'files': [...]                  # Optional field
                        }
            
            send_name: String containing the name to send the mails as (if the mails must be sent from a shared
            mailbox the account belongs to)

        The method returns:
            A tuple containing:
                A boolean indicating True if succesfully connected to the server, False otherwise
                A list containing all the dictionary objects that failed when sending the mail.
        """
        # If send_name is not specified, we send as the account username
        if send_name is None:
            send_name = self.username
        
        try:
            # Try to connect to the SMTP server
            with smtplib.SMTP(self.smtp_address, self.smpt_port) as server:
                server.starttls()                           # Start TLS encryption
                server.login(self.username, self.password)  # Log in to the SMTP server

                failed_mails = []                           # Initialize list of failed mails

                # Iterate over all the emails
                for mail in list_mails:

                    error = False

                    # Mail creation
                    msg = MIMEMultipart()
                    msg['From'] = send_name
                    msg['To'] = ",".join(mail['destination_emails'])
                    msg['Subject'] = mail['subject']
                    if 'cc_emails' in mail:
                        msg['Cc'] = ",".join(mail['cc_emails'])
                    else:
                        mail['cc_emails'] = []                      # If cc_emails is not a key, initialize it as an empty list
                    msg.attach(MIMEText(mail['body'], 'html'))

                    # Check if the files specified exist in the directory
                    if 'files' in mail:
                        for file in mail['files']:
                            try:
                                # Attach the file
                                attachment_path = file['path']
                                file_name = file['name']

                                with open(attachment_path, 'rb') as attachment:
                                    part = MIMEBase('application', 'octet-stream')
                                    part.set_payload(attachment.read())

                                encoders.encode_base64(part)
                                part.add_header(
                                    'Content-Disposition',
                                    f'attachment; filename="{file_name}"'
                                )
                                msg.attach(part)

                            # If any error occurs, error = True so the mail is processed as an error
                            except Exception as e:
                                error = True

                    # If mail construction OK, send the mail
                    if not error:
                        try:
                            # Try to send the mail
                            server.sendmail(send_name, mail['destination_emails'] + mail['cc_emails'], msg.as_string())
                        # If not possible add it to failed mail list
                        except Exception as e:
                            failed_mails.append({'subject': mail['subject'], 'body': mail['body'], 'destination_emails': mail['destination_emails']})
                    else:
                        failed_mails.append({'subject': mail['subject'], 'body': mail['body'], 'destination_emails': mail['destination_emails']})
                
                # Return True as connection was succesful and list of failed_mails
                return True, failed_mails


        # If connection is not possible return False and the whole list of mails
        except Exception as e:
            return False, list_mails