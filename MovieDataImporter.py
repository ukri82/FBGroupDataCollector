from selenium import webdriver
import os, errno
import time
import datetime
import selenium.webdriver.support.ui as ui
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions    import NoSuchWindowException
import shutil
import logging
import base64
import ConfigParser
from Crypto.Cipher import AES
from Crypto.Hash import SHA256, HMAC
import bcrypt


class MovieDataImporter:

	def __init__(self):

		self.myConfig = ConfigParser.ConfigParser()
		self.myConfig.read("./MovieConfig.ini")

		self.logger = logging.getLogger("MovieDataLog")
		chrome_options = webdriver.ChromeOptions()
		chrome_options.add_argument('--disable-application-cache')
		prefs = {"download.default_directory" : "./data"}
		chrome_options.add_experimental_option("prefs",prefs)
		self.myDriver = webdriver.Chrome('/usr/bin/chromedriver', service_args=['--verbose'], chrome_options=chrome_options, service_log_path="./log/chromedriver.log")
		self.myDriver.get(self.myConfig.get("FB", "AppURL"))

		

	def __del__(self):
		self.myDriver.quit()


	def WaitForDataCollectionFinished(self):

		aDataStatusElement = self.myDriver.find_element_by_id("final_status")
		time.sleep( 2 )
		
	    	aTotalWaitTime = 0
		while aDataStatusElement.text != "All the posts downloaded":
			time.sleep( 5 )
			aTotalWaitTime = aTotalWaitTime + 5
			if aTotalWaitTime > 60:
				break

		if aDataStatusElement.text == "All the posts downloaded":
			self.logger.info( "Data collection finished")

	def SilentRemove(self, filename):
		try:
			os.remove(filename)
	    	except OSError as e: # this would be "except OSError, e:" before Python 2.6
			if e.errno != errno.ENOENT: # errno.ENOENT = no such file or directory
		    		raise # re-raise exception if a different error occured

	def DownLoadFile(self):

		aSrcFileName = "./data/moviedata.txt"
		self.SilentRemove(aSrcFileName)

		anImportLinkElement = ui.WebDriverWait(self.myDriver, 10).until(EC.presence_of_element_located((By.ID, "tfa_src_data")))
		time.sleep( 2 )
	
		anImportLinkElement.click()

		aTotalWait = 0
		while not os.path.exists(aSrcFileName):
			time.sleep( 2 )
			aTotalWait = aTotalWait + 2
			if aTotalWait > 60:
				self.logger.error( "Download wait timed out")
				break;

		self.logger.info( "File download finished")

		aDestFileName = ""
		if os.path.exists(aSrcFileName):
			aDestFileName = "./data/moviedata_" + datetime.datetime.now().strftime("%d%m%Y_%H%M%S") + ".txt"
			self.logger.info( "The data file is stored at : " + aDestFileName)
			shutil.move(aSrcFileName, aDestFileName)
		else:
			self.logger.error("The downloaded file [%s] doesn't exist", aSrcFileName)

		return aDestFileName

	def GetPass(self):
		salt = self.myConfig.get("FB", "Salt")
		key = self.myConfig.get("FB", "Key")
		hashed = bcrypt.hashpw(key, salt)
		
		cipher = AES.new(hashed[0:32])
		
		BLOCK_SIZE = 32
		PADDING = '{'

		pad = lambda s: s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * PADDING

		DecodeAES = lambda c, e: c.decrypt(base64.b64decode(e)).rstrip(PADDING)
		
		return DecodeAES(cipher, self.myConfig.get("FB", "Pass"))

	def Login(self):

		aGetDataElement = ui.WebDriverWait(self.myDriver, 10).until(EC.presence_of_element_located((By.ID, "login_button")))

		time.sleep( 2 )

		aGetDataElement.click()

		time.sleep( 5 )

		self.logger.info('Login button is clicked')

		self.myDriver.switch_to_window(self.myDriver.window_handles[-1])

		anEmailElement = ui.WebDriverWait(self.myDriver, 10).until(EC.presence_of_element_located((By.ID, "email")))
		aPasswordElement = ui.WebDriverWait(self.myDriver, 10).until(EC.presence_of_element_located((By.ID, "pass")))
		aLoginButtonElement = ui.WebDriverWait(self.myDriver, 10).until(EC.presence_of_element_located((By.ID, "u_0_1")))
		anEmailElement.send_keys(self.myConfig.get("FB", "User"))
		time.sleep( 2 )
		aPasswordElement.send_keys(self.GetPass())
		time.sleep( 2 )
		self.logger.info('Login data is entered')

		aLoginButtonElement.click()

		self.logger.info('Login data is submitted')

		self.myDriver.switch_to_window(self.myDriver.window_handles[-1])

	def Import(self):

		aPostsFile = ""
		try:
			self.Login()

			self.WaitForDataCollectionFinished()

			self.logger.info('Page has collected the data. Importing it now...')
			
			aPostsFile = self.DownLoadFile()

			self.logger.info('Data is imported')
	
		finally:
			self.logger.info("Download finished")
			return aPostsFile


