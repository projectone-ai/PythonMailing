def check_server_connection(function):
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