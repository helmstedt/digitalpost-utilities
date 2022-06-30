Download all messages from post.borger.dk
=========================================

This utility lets you log in to https://post.borger.dk and download all messages to the same folder as the program.

The program will try to keep the authorization for https://post.borger.dk alive, but is currently not able to work for more than approximately an hour. If your mailbox takes more than an hour to download, you will need to modify the API queries for subsequent runs to be able to download everything.

Requirements
============
* A Danish NemID or MitID login for access to post.borger.dk.
* `digitalpost_fetch_all.py` from this repository.
* Python and the packages `seleniumwire`, `requests`, `python-slugify` and `beautifulsoup4`.
* A computer with a desktop browser. The program is set up for Chrome, but can be modified to work with e.g. Firefox.
* A webdriver to run and monitor your browser from a Python script. If running Chrome, get `chromedriver.exe` from https://chromedriver.chromium.org/ and put it in your PATH or at the same location as `digitalpost_fetch_all.py`.

Steps to run
============

* Run `python digitalpost_fetch_all.py` from your terminal
* The script will open a browser window where you'll need to log on to post.borger.dk with your NemID or MitID.
* After completing your browser login, press ENTER in your terminal
* Wait for the script to download your messages

Questions?
==========

Feel free to get in touch. My contact information is available on https://helmstedt.dk.