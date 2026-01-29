__doc__="""This is the SMSClass to send SMS via SNPP Gateway.
i.e. a Mail is sent to an Gateway/Emailserver and dependig on the
address, subject and body this gateway will trigger the sending of the SMS.

The code is tested in tests/test_lib_smsprovider
"""
from privacyidea.lib.smsprovider.SMSProvider import ISMSProvider, SMSError

try:
    from snpplib import SNPP
    SNPP_SUPPORT = True
except ImportError as exx:
    SNPP_SUPPORT = False

from privacyidea.lib import _


import logging
log = logging.getLogger(__name__)


class SnppSMSProvider(ISMSProvider):
    def __init__(self, db_smsprovider_object=None, smsgateway=None):
        if not SNPP_SUPPORT:
            raise SMSError(-1, "SNPP Error: no snpp library installed")

    def submit_message(self, phone, message):
        """
        send a message to a phone via a snpp protocol to smsc

        :param phone: the phone number
        :param message: the message to submit to the phone
        :return:
        """
        if not self.smsgateway:
            # this should not happen. We now always use sms gateway definitions.
            log.warning("Missing smsgateway definition!")
            raise SMSError(-1, "Missing smsgateway definition!")

        phone = self._mangle_phone(phone, self.smsgateway.option_dict)
        log.debug("submitting message {0!r} to {1!s}".format(message, phone))

        smsc_host = self.smsgateway.option_dict.get("SMSC_HOST")
        smsc_port = self.smsgateway.option_dict.get("SMSC_PORT")
        username = self.smsgateway.option_dict.get("USERNAME")
        passwd = self.smsgateway.option_dict.get("PASSWORD")
        subject = self.smsgateway.option_dict.get("SUBJECT", "{phone}").format(otp=message, phone=phone)
        body = self.smsgateway.option_dict.get("BODY", "{otp}").format(otp=message, phone=phone)

        if not smsc_host:
            log.warning("Can not submit message. SMSC_HOST is missing.")
            raise SMSError(-1, "No SMSC_HOST specified in the provider config.")

        if not smsc_port:
            log.warning("Can not submit message. SMSC_PORT is missing.")
            raise SMSError(-1, "No SMSC_PORT specified in the provider config.")

        subject = subject.replace(PHONE_TAG, phone)
        subject = subject.replace(MSG_TAG, message)
        body = body.replace(PHONE_TAG, phone)
        body = body.replace(MSG_TAG, message)

        # Initialize the SNPP Client
        client = None
        error_message = None 
        try:
            client = SNPP(None, None, 1)
            log.debug("connecting to %r:%r", smsc_host, smsc_port)
            client.connect(smsc_host, smsc_port)
            log.debug("connected!")

            log.debug("login with %s %s", username, passwd)
            if username != None:
                client.login(username, passwd)

            client.pager(phone)

            if subject != None:
                client.subject(subject)

            client.message(body)
            client.send()

        except Exception as exx:
            error_message = "{0!r}".format(err)
            log.warning("Failed to send message: {0!r}".format(error_message))
            log.debug("{0!s}".format(traceback.format_exc()))

        finally:
            if client:
                try:
                    client.quit()
                except Exception as exx:
                    log.exception(exx)

                client.close()

        if error_message:
            raise SMSError(error_message, "SMS could not be "
                                          "sent: {0!r}".format(error_message))
        return True

    @classmethod
    def parameters(cls):
        """
        Return a dictionary, that describes the parameters and options for the
        SMS provider.
        Parameters are required keys to values.

        :return: dict
        """
        params = {"options_allowed": False,
                  "headers_allowed": False,
                    "parameters": {
                        "SMSC_HOST": {
                            "required": True,
                            "description": _("SMSC Host IP")},
                        "SMSC_PORT": {
                            "required": True,
                            "description": _("SMSC Port")},
                        "USERNAME": {
                            "description": _("Username for authentication on SMSC")},
                        "PASSWORD": {
                            "description": _("Password for authentication on SMSC")},
                        "SUBJECT": {
                          "description": "The optional subject of the email. "
                                         "Use tags {phone} and {otp}."},
                        "BODY": {
                          "description": "The optional body of the email. "
                                         "Use tags {phone} and {otp}.",
                          "type": "text"},
                        "REGEXP": {
                            "description": cls.regexp_description
                        }
                    }
                }
        return params