#!/usr/bin/env python3

import email
from email.mime.text import MIMEText
import smtplib
import asyncio
import server
from config import Config
from quamash import QEventLoop
from PySide import QtSql, QtCore
from passwords import DB_SERVER, DB_PORT, DB_LOGIN, DB_PASSWORD, DB_TABLE
import sys

MAIL_ADDRESS = "admin@forever.com"

def send_email(text, to_name, to_email, subject):
    pass
    # print(text)
    # print("To: %s" % to_email)
    # msg = MIMEText(text)
    #
    # msg['Subject'] = subject
    # msg['From'] = email.utils.formataddr(('Forged Alliance Forever', MAIL_ADDRESS))
    # msg['To'] = email.utils.formataddr((to_name, to_email))
    #
    # s = smtplib.SMTP_SSL(Config['smtp_server'], 465, Config['smtp_server'],
    #                      timeout=5)
    # s.login(Config['smtp_username'], Config['smtp_password'])
    #
    # s.sendmail(MAIL_ADDRESS, [to_email], msg.as_string())
    # s.quit()

@asyncio.coroutine
def do_the_thing():

    with (yield from db_pool) as conn:
        cursor = yield from conn.cursor()

        candidates = dict()
        cases = dict()

        # Duplicate usernames
        yield from cursor.execute("SELECT login, email FROM login WHERE LOWER(login) IN (SELECT LOWER(login) FROM login GROUP BY LOWER(login) HAVING COUNT(*) > 1) ORDER BY LOWER(login);")

        # Each pair of usernames is adjacent. Let's gather up the set of emails associated with each
        # login name.
        login = None
        last_login = ""
        collected_emails = []
        collected_cases = []
        for i in range(0, cursor.rowcount):
            login, email = yield from cursor.fetchone()

            if login.lower() != last_login:
                candidates[login.lower()] = collected_emails
                cases[login.lower()] = collected_cases
                collected_emails = []
                collected_cases = []

            collected_emails.append(email)
            collected_cases.append(login)

        candidates[login.lower()] = collected_emails
        cases[login.lower()] = collected_cases

        for key, list in candidates.items():
            print(key)
            print(", ".join(list))


        for name, emails in candidates.items():
            for email in emails:
                send_email(
"""Hello %s

Due technical fault a few years ago, it was for a time possible to create FAF accounts with usernames
that differed from one another only in the case of some symbols. There could be an account called
'Sheeo' and an account called 'SHEEO': as you can imagine, this is fairly bad.

While that problem was fixed, accounts of this sort still exist in our database (but it's unlikely
they are able to log in. The new development team recently discovered this fault, and in order to
properly correct it (and make usernames fully case-insensitive, we need to purge the database of
accounts which don't have properly unique names.

You're receiving this one-off automated email to let you know that this email address is associated
with one of those problematic accounts. We have accounts in our database with these names:
%s
At least one of which is associated with this email address.

Please let us know:
- Do you control the other email addresses associated with those other accounts? (If so, you'll have
  emails like this one sent there, too.)
- Which, if any, of these accounts do you wish to keep? (we can merge the statistics and history of
  them into one unified account)

If you don't reply to this email, we'll merge the accounts into the one that appears
to most recently have been active.
""" % (name, ", ".join(cases[name.lower()])), name, email, "Forged Alliance Forever: Account query from the admins (username)")

        # Duplicate emails
        yield from cursor.execute("SELECT login, email FROM login WHERE LOWER(email) IN (SELECT LOWER(email) FROM login GROUP BY LOWER(email) HAVING COUNT(*) > 1) ORDER BY LOWER(email);")

        # Gather up the usernames associated with each email.
        candidates = dict()

        last_email = ""
        email = None
        usernames = []
        for i in range(0, cursor.rowcount):
            login, email = yield from cursor.fetchone()

            if email.lower() != last_email:
                candidates[last_email] = usernames
                last_email = email.lower()
                usernames = []

            usernames.append(login)

        candidates[email.lower()] = usernames

        for key, list in candidates.items():
            print(key)
            print(",".join(list))


        for email, usernames in candidates.items():
            send_email(
"""Hello %s

Due to a technical fault a few years ago, this email address has ended up associated with several
FAF accounts:
%s

While it is no longer possible for this to happen, we need to eliminate this duplication from the
database before we can finish repairing the fault. Could you please reply to this email and let us
know:
- Which, if any, of those user accounts do you use to log in and play?
- What should we do with the others? We can merge their stats, games, and history with the account
  you want, so you end up with one account that reflects all your FAF play over the years, or we can
  delete them. Let us know.

If you don't reply to this email, we'll merge the accounts into the one that appears
to most recently have been active.
""" % (usernames[0], ", ".join(usernames)), usernames[0], email, "Forged Alliance Forever: Account query from the admins (email)")


if __name__ == "__main__":

    app = QtCore.QCoreApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    pool_fut = asyncio.async(server.db.connect(host=DB_SERVER,
                                               port=DB_PORT,
                                               user=DB_LOGIN,
                                               password=DB_PASSWORD,
                                               maxsize=10,
                                               db=DB_TABLE,
                                               loop=loop))
    db_pool = loop.run_until_complete(pool_fut)

    loop.run_until_complete(asyncio.async(do_the_thing()))
