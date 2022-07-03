Utilities for post.borger.dk
============================

These utilities let you log in to Danish Digital Post (mail from public authorities) https://post.borger.dk and either:

* Set up a task to send unread messages to an e-mail address of your choosing, or:
* Download all messages to the same folder as the program.

Requirements
============
* A Danish NemID or MitID login for access to post.borger.dk.
* Python and the packages `seleniumwire`, `requests`, `python-slugify` and `beautifulsoup4`.
* A modern graphical browser with JavaScript enabled. The program is set up for Chrome, but can be modified to work with e.g. Firefox.
* A webdriver to run and monitor your browser from a Python script. If running Chrome, get `chromedriver.exe` from https://chromedriver.chromium.org/ and put it in your PATH or at the same location as `digitalpost_fetch_all.py`.
* For checking new messages and sending them to e-mail, a server, service or PC that's on 24/7 to monitor for new mails and keep your login active.
* For checking new messages and sending them to e-mail, an e-mail address and the ability to send e-mails using SMTP.

Steps to download all messages
==============================

* Run `post_borger_dk_fetch_and_save_all.py` from your terminal
* The script will open a browser window where you'll need to log on to post.borger.dk with your NemID or MitID.
* After completing your browser login, press ENTER in your terminal
* Wait for the script to download your messages

Set up a task to send unread messages to an e-mail address of your choosing
===========================================================================

Step one
--------

* Enter your e-mail and e-mail server details in `post_borger_dk_configuration_example.py` and save the file as `post_borger_dk_configuration.py`

Step two
--------

* Run `post_borger_dk_first_login.py` on a computer with a desktop browser. The program is set up to work with Chrome and `chromedriver.exe`.
* The program will open a browser window where you'll need to log on to post.borger.dk with your NemID or MitID.
* If your login is successfull, the program will save access tokens for post.borger.dk to `post_borger_dk_cookies`

Step three
----------

* Immediately after completing step two, copy the files from the program directory (including `post_borger_dk_cookies`) to a computer or server that is on 24/7 (if this is your computer from step two, no need to copy anything.)
* If necessary edit the `cookies_filename` variable in `post_borger_dk_configuration.py` to the full path of your `post_borger_dk_cookies` file
* Run `post_borger_dk_send_new_by_email.py` at specific intervals to fetch messages from mit.dk and send them to your e-mail. I recommend somewhere between 1 and 3 minutes between each run. You can also try around 20 minutes as this is the usual interval for renewing authorization at post.borger.dk. The program refreshes cookies on each run if necessary.
* If running `post_borger_dk_send_new_by_email.py` on Linux, set up a CRON job to automate running the program. If running the program on Windows, use Task Scheduler.

A note on security
==================

Keep your cookie file (default filename is `post_borger_dk_cookies`) somewhere only you can access as the file can be used to access your Digital Post messages and possibly also other services with NemID/MitID authorization.

Questions?
==========

Feel free to get in touch. My contact information is available on https://helmstedt.dk.