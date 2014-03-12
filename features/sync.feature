Feature: Sync
	As a user
	In order to keep my files secure
	I want to synchronize them accross multiple storage providers

	Scenario: Initialize folder
		Given I have a folder with files
		| name				| 	size 		| 
		| backup-2014-03-03	|	1400000000	|
		| backup-2014-03-04	|	1700000000	|
		| backup-2014-03-05	|	2200000000	|
		When I execute "cuckoodrive init"
		Then the folder is indexed 
		And a json index file is created
		And the index file contains all the files in the folder


	Scenario: Adding dropbox cloud storage
		When I add a provider with following settings
		| name 		| appkey 	| appsecret 	|
		| dropbox 	| APP_KEY	| APP_SECRET	|
		Then the storage provider "dropbox" is added to the index file
		And I can see the used and free space of the storage provider
		And I can see all the files of cuckoodrive on it

	Scenario: Adding google drive cloud storage
		When I add a provider with following settings
		| name 			| appkey 	| appsecret 	|
		| googledrive 	| APP_KEY	| APP_SECRET	|
		Then the storage provider "googledrive" is added to the index file
		And I can see the used and free space of the storage provider
		And I can see all the files of cuckoodrive on it

	Scenario: Synchronize folder initially
		Given I have a folder with files
		| name				| 	size 		| 
		| backup-2014-03-03	|	1400000000	|
		| backup-2014-03-04	|	1700000000	|
		| backup-2014-03-05	|	2200000000	|
		When I synchronize initially
		Then the files in the folder are synchronized with all the cloud storage providers

	Scenario: Synchronize folder after something was removed
		Given I have provider "googledrive" with files
		| name				| 	size 		| 
		| backup-2014-03-03	|	1400000000	|
		| backup-2014-03-05	|	2200000000	|
		And I have provider "dropbox" with files
		| name				| 	size 		| 
		| backup-2014-03-03	|	1400000000	|
		| backup-2014-03-04	|	1700000000	|
		When I synchronize an empty folder with the files
		Then the missing files in the folder are pulled from the cloud storage providers and added again so that I have files
		| name				| 	size 		| 
		| backup-2014-03-03	|	1400000000	|
		| backup-2014-03-04	|	1700000000	|
		| backup-2014-03-05	|	2200000000	|
