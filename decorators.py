def check_server_connection(function):
    """
    A decorator with the objective of checking if the email service is connected before calling any email function.

    :param function: The function to be checked.
    :return It should return the function in case of positive for still logged on, else it should display a warning
    message that the service is not connected:
    """
    def inner(self, *args, **kwargs):
        smtp_status = self._smtp_server.noop()[0]
        imap_status = self._imap_server.noop()[0]

        """Checking gmail smtp and imap connection status"""
        if self.domain == 'gmail' and smtp_status == 250 and imap_status == 'OK':
            return function(self, *args, **kwargs)
        else:
            print('You are not logged in. Please try log in before calling a method or property')
            return False
    return inner
