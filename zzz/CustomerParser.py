# coding: utf-8
from pathlib import Path
import unicodedata			# Unicode Character Database (UCD) which defines character properties for all Unicode characters
import csv
from CustomerUpdate import clsCustomerUpdate #, clsCustomersFilesWriter, Resize

def Resize(S="", size=20):
	# redimentionne une chaine en ajoutant des espces à la fin
	myStr = str(S)
	for idx in range( size - len(myStr) ) :
		myStr = myStr + " "
	return myStr

def simplifyStr(str1) :
	S1 = str(str1).replace(' ', '').replace(',', '').replace('-', '').replace("'", "")	# supression des " " et "," et "-" etc.
	S1 =str(S1).lower() 
	S1 =unicodedata.normalize('NFKD', S1).encode('ASCII', 'ignore')
	return str(S1)

def strDiff(str1, str2) :
	# comparaison de 2 chaines (sans tenir compte des majuscues, minuscules, sans accents, etc.)
	#S1 =str(str1).replace(' ', '').replace(',', '').replace('-', '').replace("'", "")	# supression des " " et "," et "-" etc.
	#S2 =str(str2).replace(' ', '').replace(',', '').replace('-', '').replace("'", "")
	#
	#S1 =str(S1).lower() 
	#S2 =str(S2).lower()
	#
	#S1 =unicodedata.normalize('NFKD', S1).encode('ASCII', 'ignore')
	#S2 =unicodedata.normalize('NFKD', S2).encode('ASCII', 'ignore')
	#
	#if S1 != S2:	print(" ... " + Resize(S1, 50) + " / " + Resize(S2, 50) )
	#return S1 != S2	

	return simplifyStr(str1) != simplifyStr(str2)
########################################################################################################################
class clsEpicesCustomerReader:
### Récupération des infos dans la base client Epices

	def version(self):
		return "EpicesCustomerReader v1.0"

	def __init__(self, EpicesFile  = "./0-Epices/clients.csv", delimiter=';', outputDir = "./out/", fixCsvShift=True, verbose=False):
	### données de la base Epices 
		self.delimiter 	= delimiter
		self.outputDir	= outputDir
		self.outputPath = Path(outputDir)
		if not self.outputPath.exists() :   # test de la présence du répertoire
			print(">>> création du répertoire '" + outputDir + "'\n")
			self.outputPath.mkdir(parents=False, exist_ok=False) # création du réperoire manquant     

		self.CustomerBase = {}
		self.unactiveCustomer = {}
		self.EpicesActiveConsumers = {}
		try :
			with open(EpicesFile) as csvfile:
				reader = csv.DictReader(csvfile, delimiter=delimiter)
				#{'Id': '28', 'Name': 'CRER', 'Address': 'Zone de Baussais - 8 rue Jacques Cartier', 'City': 'La Crèche', 'Postal code': '79260', 'Country': 'FRANCE', 
				# 'Created at': '2016-07-13 13:35:15 UTC', 'Updated at': '2018-03-14 08:36:04 UTC', 'Logo': '/uploads/client/28/logo/28.', 'Company registration number': '', 
				# 'Vat number': '', 'Deactivated at': '', 'IO Active': 'true', 'IO Epices identifier': '411CRER', 'IO frequency': '12', 'IO trial duration days': '0', 'IO invoicing per main group': 'false', 'IO number of main groups': '1', 'IO contract reference date': '2017-05-19', 'IO order number': '', 'IO Chorus': 'false', 'IO unique mandate reference': '', 'IO service invoice code': '706200', 'IO installation fee invoice code': '704100', 'IO fixed discount': 'true', 'IO degressive discount mode': '', 'IO default invoice mentions': 'false', 'IO third party company invoicing': 'Isabelle CLEMENT', 'IO Contact 0 Name': 'isabelle.clement@crer.info', 'IO Contact 0 Email': '05 49 08 24 24', 'IO Contact 0 Phone': None, 'IO Contact 1 Name': None, 'IO Contact 1 Email': None, 'IO Contact 1 Phone': None, 'IO Contact 2 Name': None, 'IO Contact 2 Email': None, 'IO Contact 2 Phone': None, 'IO Contact 3 Name': None, 'IO Contact 3 Email': None, 'IO Contact 3 Phone': None}


				for row in reader:
					#print(row)
					# !!! "Id" n'est pas l'identifiant à utiliser, c'est : "IO Epices identifier" !!!
					if 'IO Epices identifier' in row.keys() :
						id = row['IO Epices identifier']

						# on récupère les infos utiles (nom, adresse du client, etc.)
						d = {}
						d["id"] = id

						self.CustomerBase[id] = row

						#################################################################
						# /!\ il faut utiliser les noms 'cogilog' pour le décodage /!\	#
						if 'IO Epices identifier' in row.keys() :
							d['Code'] = row['IO Epices identifier']		# c'est le 'code client', donc la clé Cogilog !
						
						if 'Name' in row.keys() :
							d['Nom du client'] = row['Name']

						if 'Address' in row.keys() :
							d['Voie (adresse)'] = row['Address']

						if 'Postal code' in row.keys() :
							d['Code postal'] = row['Postal code']

						if 'City' in row.keys() :
							d['Ville'] = row['City']

						if 'Vat number' in row.keys() :
							d['intracom'] = row['Vat number']	#  /!\ ce n'est pas un champs 'cogilog' (qui ne prend que le 'Préfixe intracom') /!\	#

						if 'Company registration number' in row.keys() :
							d['SIRET'] = row['Company registration number']	
					
						if 'IO Active' in row.keys() :
							d['actif'] = row['IO Active']
							
						if d['actif'] == 'true' :
							self.EpicesActiveConsumers[id] = d
						else :
							self.unactiveCustomer[id] = d
						# /!\ il faut utiliser les noms 'cogilog' pour le décodage /!\	#
						#################################################################

		except Exception:
			print('\n       !!! fichier non trouvé : ' + EpicesFile + " !!!\n")

		if fixCsvShift :
			self.fixColumnShift(fileName=EpicesFile, verbose=verbose)
		
		if verbose == True :
			self.listPrint()	

	def fixColumnShift(self, fileName="epices.csv", verbose = True) :
		#### /!\ **attention** : le fichier "clients.csv" exporté par Epices est buggée :  
		#	=> il y a un décalage au niveau de la colonne **"IO third party company invoicing"** (qui devrait-être vide ?)  
		#	... elle contient les données de la colonne suivante "IO Contact 0 Name", et le déclage se poursuit jusqu'à la dernière colonne du fichier.  
		#
		#### Fix du pb de décalalge de colonne ("IO third party company invoicing" / "IO Contact 0 Name") :		
		# si il y a des '@' dans la colonne "IO Contact 0 Name", c'est que c'est décalé !
		columnShift = False
		for id in self.CustomerBase : 
			if "IO third party company invoicing" in self.CustomerBase[id] :
				if "IO Contact 0 Name" in self.CustomerBase[id] :
					k = self.CustomerBase[id]["IO Contact 0 Name"]
					if '@' in str(k) : 
						print("/!\\  dans '" + str(fileName) + "', 'IO Contact 0 Name' ---> " + str(k) + " /!\\")
						if verbose :
							print(" --> il faut décaler les dernières colonnes dans l'export '" + str(fileName) + "'...")
						columnShift = True
						break

		lastColumnList = [
			'IO third party company invoicing', 
			'IO Contact 0 Name', 			'IO Contact 0 Email', 			'IO Contact 0 Phone', 
			'IO Contact 1 Name', 			'IO Contact 1 Email', 			'IO Contact 1 Phone', 
			'IO Contact 2 Name', 			'IO Contact 2 Email', 			'IO Contact 2 Phone', 
			'IO Contact 3 Name', 			'IO Contact 3 Email', 			'IO Contact 3 Phone'
			]


		# si il y a un décalalage, on décale les dernières colonnes
		if columnShift :
			self.newCustomerBase = {}
			for id in self.CustomerBase : 
				self.newCustomerBase[id] = {}
				extraColumnFound = False
				for k in self.CustomerBase[id] :
					if k == "IO third party company invoicing" :
						extraColumnFound = True
						old_k = k
					elif extraColumnFound :
						self.newCustomerBase[id][k] = self.CustomerBase[id][old_k]
						old_k = k
					else :
						self.newCustomerBase[id][k] = self.CustomerBase[id][k]
						old_k = k
				
				if 0 : #verbose :
					print(Resize(id) + " --old--> " + str(self.CustomerBase[id]		))
					print(Resize(id) + " -modif-> " + str(self.newCustomerBase[id]	))
					print()

			self.CustomerBase = self.newCustomerBase.copy()
			if verbose :
				print('**** Fix du pb de décalalge de colonne ("IO third party company invoicing" / "IO Contact 0 Name") ****')
				for id in self.CustomerBase : 
					print(Resize(id) + "--> " , end="")
					for k in self.CustomerBase[id] : 
						if k in lastColumnList :
							print(Resize(k, 18) + ": " + Resize(self.CustomerBase[id][k], 50) , end=", ") 
					print()
				print('****    ****    ****    ****')
			
			print("... décalage des dernières colonnes de l'export '" + str(fileName) + "' : fait !")
			print()


	def listPrint(self): 
		idx = 1
		for id in self.EpicesActiveConsumers:
			print(Resize(idx, 3) + ") Epices -> client " + Resize(id) + " --> " + str( self.EpicesActiveConsumers[id]) )
			idx += 1

	def recordUnactiveCustomer(self, encoding="utf-16", delimiter='\t'): 
		csvFullname 	= self.outputDir + "ClientsInactifs.csv"
		print("Mémorisation des clients inactifs dans '" + csvFullname + "'")
		
		l = []	# création d'une liste de dictionnaires : 1 dictionnaire par ligne à écrire dans le CSV
		for id in self.unactiveCustomer :
			l.append(self.unactiveCustomer[id])
		
		with open(csvFullname, 'w', encoding = encoding) as csvFile:  # You will need 'wb' mode in Python 2.x
			w = csv.DictWriter(csvFile, l[1].keys(), delimiter=delimiter)
			w.writeheader()
			w.writerows(l)

		print("----> " + str(len(l)) +" clients inactifs.")
		#for k in l :
		#	print(Resize(k['id']) + " -> " + str(k['Nom du client']) )





########################################################################################################################
class clsCogilogCustomerReader:
### Récupération des infos dans la base client Cogilog 

	def version(self):
		return "CogilogCustomerReader v1.0"

	def __init__(self, CogilogFile = "./0-Cogilog-Clients/Export clients.txt", delimiter='\t', outputDir = "./out/", verbose=False):
	### données de la base Cogilog 
		self.outputPath = Path(outputDir)
		if not self.outputPath.exists() :   # test de la présence du répertoire
			print(">>> création du répertoire '" + outputDir + "'\n")
			self.outputPath.mkdir(parents=False, exist_ok=False) # création du réperoire manquant     


		try :
			if verbose :
				print("old file  : '" + CogilogFile 	+ "'")								# "./0-Cogilog-Clients/Export clients.txt
				print("old file  : '" + CogilogFile.replace(".txt", ".csv") 	+ "'")		# "./0-Cogilog-Clients/Export clients.csv
			CogilogCsvName = CogilogFile.replace(".txt", ".csv")
			
			#csvWrFile = open(CogilogCsvName, "w", encoding = self.encoding)
			with open(CogilogCsvName, "w", encoding = "utf-16") 	as csvWrFile :
				if verbose :
					print("ouverture : '" + CogilogCsvName 	+ "'")				# "./0-Cogilog-Clients/Export clients.txt
					
				with open(CogilogFile, encoding = "utf-16") 			as txtRdfile:
					# recopie du ficher texte dans un fichier csv, en enlevant la première ligne : "**Gestion	Clients"
					if verbose :
						print("ouverture : '" + CogilogFile 	+ "'")			# "./0-Cogilog-Clients/Export clients.txt
		
					lines = txtRdfile.readlines()

					lineNumber 	= 0
					for l in lines :
						if lineNumber == 1:
							# bug de l'export Cogilog : on a 2 fois 'Complément (adresse)'...
							if 'Complément (adresse)\tComplément (adresse)\t' in l :
								l = l.replace(	'Complément (adresse)\tComplément (adresse)\t', \
				  									'Complément 1 (adresse)\tComplément 2 (adresse)\t')
								print("dans " + str(CogilogCsvName) + ", on renomme les colonnes 'Complément (adresse)'\t'Complément (adresse)' ---> 'Complément 1 (adresse)'\t'Complément 2 (adresse)'" )

						if lineNumber > 0:
							csvWrFile.write(l)		# on ne prend pas la première ligne : "**Gestion	Clients"
						
						lineNumber += 1		

			if verbose : 
				print("fermeture de '" + CogilogCsvName 	+ "'")			
				print("Fichier '" + CogilogCsvName 	+ "' ... créé.")				
			

			self.CogilogDataComp = {}
			try :
				with open(CogilogCsvName, encoding = "utf-16") as csvlikefile:
					reader = csv.DictReader(csvlikefile, delimiter="\t")
					#{'Code': '411RGE', 'Nom du client': 'Région Gävleborg Ekonomiservice', 'CP': '826 82', 'Ville': 'Söderhamn', 'Pays': 'Suede',
					# 'E-mail': '', 'N° intracom.': 'SE232100019801', 'Siret': '232100019801', 'Compte': '411RGE'}

				
					for row in reader:
						#print(row)
						# !!! "Id" n'est pas l'identifiant à utiliser, c'est : "Code" !!!
						if 'Code' in row.keys() :
							id = row['Code']

							# on récupère les infos utiles (nom, adresse du client, etc.)
							d = {}
							d["id"] = id
							
							if 'Nom du client' in row.keys() :
								d['Nom du client'] = row['Nom du client']

						########################
						####	Adresse		####
						#print(row.keys())
						fieldList = [					# liste des champs dans l'ordre dans lesquels on les veux
							'Complément 1 (adresse)'	, 	# pré-complément : batiment, lieu-dit, etc.
							'Complément (adresse)'		, 	# au cas où...
							'Numéro (adresse)'			, 	# N°
							'Voie (adresse)'			,	# voie
							'Complément 2 (adresse)'	, 	# post-complémant
							]
						if 			'Voie (adresse)' in row.keys() :
							if row[ 'Voie (adresse)'] :
								#if 			'Numéro (adresse)' in row.keys() :
								#	if row[	'Numéro (adresse)'] :
								#		d['Voie (adresse)'] = row['Numéro (adresse)'] + " " +	row['Voie (adresse)']	# !!! pour le test, il ne faut pas (toujours) prendre en compte les "," ni les " " ...
								#	else :
								#		d['Voie (adresse)'] = 									row['Voie (adresse)'] 
								#	
								#if 			'Complément 1 (adresse)' in row.keys() :											# !!! il y a 2 compléments d'adresse -> comment on gère ???
								#	if row[	'Complément 1 (adresse)'] :
								#		d['Voie (adresse)'] = d['Voie (adresse)'] + " " 	+ 	row['Complément 1 (adresse)']	# !!! pour le test, il ne faut pas (toujours) prendre en compte les "," ni les " " ...								
								Addr = ""
								addrDetails = {}
								for f in fieldList : 
									if f in  row.keys() :
										if len(row[f]) : 
											Addr += str(row[f]) + ", "
											addrDetails[f]= row[f]
								#print(Resize(id) + " : adresse-> " + str(Addr) + ".")		
								
								if len(Addr) :
									d['Voie (adresse)'] = Addr[0:-2]	# on s'arrête avant le dernier ', '
									d['adr. détails']   = addrDetails					
								else :
									d['Voie (adresse)'] = ""

								if verbose : 
									print(Resize(id) + " : adresse = <" + d['Voie (adresse)'] + ">")		


							if 'Code postal' in row.keys() :
								d['Code postal'] = row['Code postal']

							if 'Ville' in row.keys() :
								d['Ville'] = row['Ville']
						########################



						self.CogilogDataComp[id] = d           
			except Exception:
				print('\n       !!! problème parsing : ' + CogilogFile + " !!!\n")

		except Exception:
			print('\n       !!! fichier non trouvé : ' + CogilogFile + " !!!\n")

		if verbose == True :
			self.listPrint()	

	def check(self, customer): 
		#customer.['piece'] : {'date': '30/09/2023', 'code client': '411GRPFAU-AGVO', 'mode de facturation': '*DEFAULT', 'mode de paiement proposé': '*DEFAULT', 'date échéance': '30/10/2023', 'acompte': '*DEFAULT', 'taux de remise générale': '*DEFAULT', "taux d'escompte": '*DEFAULT', 'commercial (nom prénom)': '*DEFAULT', 'compte comptable': '*DEFAULT', 'civilité': '', 'nom': '*DEFAULT', 'numéro': '', 'voie': '', 'complément 1': '', 'complément 2': '', 'code postal': '', 'Ville': '', 'cedex': '', 'pays': '', 'tél': '*DEFAULT', 'fax': '*DEFAULT', 'email': '*DEFAULT', 'intracom': '', 'siret': '', 'nom livraison': '', 'numéro livraison': '', 'voie livraison': '', 'complément livraison': '', 'complément 2 livraison': '', 'code postal livraison': '', 'ville livraison': '', 'cedex livraison': '', 'pays livraison': '', 'nom de la remise type': '*DEFAULT', 'banque': '*DEFAULT', 'RIB code banque': '', 'RIB code guichet': '', 'RIB numéro du compte': '', 'RIB clé': '', 'Message': '', 'Référence': '', 'Contact': '', 'Commentaires': '', 'Notes': '', 'Texte 1': "Paiement à l'ordre de Épices Énergie par chèque ou virement", 'Texte 2': 'virement', 'Texte 3': '', 'Texte 4': '', 'Texte 5': '', 'Texte 6': '', 'Texte 7': '', 'Texte 8': '', 'Texte 9': '411GRPFAU-AGVO/5034/FA23900564', 'Nombre 1': '', 'Nombre 2': '0.0', 'Nombre 3': '', 'Nombre 4': '', 'Nombre 5': '', 'Nombre 6': '', 'Nombre 7': '', 'Nombre 8': '', 'Nombre 9': '', 'Date 1': '', 'Date 2': '', 'Date 3': '', 'Date 4': '', 'Date 5': '', 'Date 6': '', 'Date 7': '', 'Date 8': '', 'Date 9': '', 'IBAN': '*DEFAULT', 'BIC': '*DEFAULT', 'Contact livraison': '', 'Code affaire': '', 'Retenue': '', 'Service livraison': '', 'Téléphone livraison': '', 'Imprimée': '', 'Verrouillée': '', 'Archivée': '', 'Date heure transfert en comptabilité': '', 'Relance1': '', 'Relance2': '', 'Relance3': '', 'Relance4': '', 'Préfixe (adresse facturation)': '', 'Nom (adresse facturation)': 'AGV FLOTTES ONET', 'Complément 1 (adresse facturation)': '', 'Numéro (adresse facturation)': '', 'Voie (adresse facturation)': 'Avenue du causse - Z.A. de Bel Air, 12850 ONET LE CHATEAU', 'Complément 2 (adresse facturation)': '', 'Code Postal (adresse facturation)': '', 'Ville (adresse facturation)': '', 'Cedex (adresse facturation)': '', 'Pays (adresse facturation)': '', 'Téléphone 2': '', 'Fonction Contact': '', 'Numéro de la pièce': '', 'importer totaux': '*DEFAULT', 'Net ht': '', 'Montant TVA': '', 'Marge': '', 'Montant Taxe ad1': '', 'Montant taxe ad2': '', 'mouvementer stock': '', 'importer solde': '', 'Solde': '', 'Réservé : Numéro de commande sur le site marchand': '', 'Réservé : Nom du site marchand': '', 'Réservé : État de la commande sur le site marchand': '', 'Réservé : Timestamp de la commande sur le site marchand': '', "Compte d'acompte": '', 'Adresse e-mail livraison': '', 'Réservé : ID de la commande sur le site marchand': '', 'Libre': '', "Réservé : nature de la pièce d'origine (voir les noms en  ligne 3)": '', "Réservé : numéro de la pièce d'origine": '', "Réservé : année de la pièce d'origine (facultatif)": ''}
		custumer_ID = customer['piece']['code client']
		invoiceCheckedOK = True
		if custumer_ID not in self.CogilogDataComp :
			print("!!! le code client '" + str(custumer_ID) + "' n'est pas connu sous Cogilog => on ignore la facture !" )
			invoiceCheckedOK = False

		return invoiceCheckedOK


	def listPrint(self): 
		idx = 1
		for id in self.CogilogDataComp : 
			print(Resize(idx, 3) + ") Cogilog -> client " + Resize(id) + " --> " + str( self.CogilogDataComp[id]) )
			idx +=1
	

########################################################################################################################
class clsBaseCompare:
### écriture de tableur qui synthétise les différence de base client Epices / Cogilog 

	def version(self):
		return "BaseCompare v1.0"

	def __init__(self, EpicesFile  = "./0-Epices/clients.csv", CogilogFile = "./0-Cogilog-Clients/Export clients.txt", outputDir = "./out/", fixCsvShift=True, verbose=False):
		self.outputDir	= outputDir
		self.outputPath = Path(outputDir)
		self.verbose	= verbose

		self.addrCmpCnt = 0		# Nombre d'adresse testées
		self.addrCmpOk	= 0		# Nombre d'adresse testées OK
		self.addrCmpKo	= 0		# Nombre d'adresse testées KO
		self.updt = clsCustomerUpdate()

		if not self.outputPath.exists() :   # test de la présence du répertoire
			print(">>> création du répertoire '" + outputDir + "'\n")
			self.outputPath.mkdir(parents=False, exist_ok=False) # création du réperoire manquant     

		#################################
		# récupération de la base Cogilog
		print("====			import de la base client Cogilog 		====")
		self.Cogilog 			= clsCogilogCustomerReader(	CogilogFile = CogilogFile, outputDir = outputDir)
		self.CogilogDataComp	= self.Cogilog.CogilogDataComp
		print("... " + str(len(self.CogilogDataComp)) + " clients Cogoilog")
		
		#################################
		# récupération de la base Epcies
		print("====			import de la base client Epices 		====")
		self.Epices 			= clsEpicesCustomerReader(	EpicesFile  = EpicesFile, outputDir = outputDir, fixCsvShift=fixCsvShift )
		self.Epices.recordUnactiveCustomer(delimiter="\t")
		self.EpicesActiveConsumers 	= self.Epices.EpicesActiveConsumers		# dictionnaire au format 'import Cogilog' 
		#self.unactiveCustomer  = self.Epices.unactiveCustomer		# dictionnaire au format 'import Cogilog' 
		print("... " + str(len(self.EpicesActiveConsumers)) + " clients Epices")


		print("=========================================================")
		print("====  Comparaison des bases clients Epices/Cogilog   ====")
		self.addressDiffOnly	= {}
		self.addressDiffAll		= {}
		self.matchingCustomersCode 	= []
		self.matchingCustomersName	= []
		self.unknownCustomersCode 	= []
		self.invalidCustomerNames 	= []
		self.invalidCustomerAddr	= []


		for id in self.EpicesActiveConsumers : 
			if id not in self.CogilogDataComp :
				self.EpicesActiveConsumers[id]["statut"] 			= "ID inconnu"
				self.EpicesActiveConsumers[id]["correction"]		= "ID: " + str(id)
				self.unknownCustomersCode.append(id)
				#print("client " + str(id) + " pas Cogilog --> " + str( slef.EpicesCustomer[id]['Nom du client']) )
			
			else :
				self.EpicesActiveConsumers[id]["statut"] 			= "dans Cogilog..."
				self.EpicesActiveConsumers[id]["correction"]		= "-"
				self.matchingCustomersCode.append(id)
				
				if not self.nameCmp(	id,approxName=True) :
					self.EpicesActiveConsumers[id]["statut"] 		= "nom KO"
					self.EpicesActiveConsumers[id]["correction"]	= "nom: " + str(self.CogilogDataComp[id]['Nom du client'])
					self.invalidCustomerNames.append(id)

				else : #if self.nameCmp(	id,approxName=True) :
					self.matchingCustomersName.append(id)

					if self.nameCmp(	id, approxName=False) :
						self.EpicesActiveConsumers[id]["statut"]	= "nom ok"
						self.EpicesActiveConsumers[id]["correction"]= ""
					else : 
						self.invalidCustomerAddr.append(id)
						self.EpicesActiveConsumers[id]["statut"] 	= "nom ~~"
						self.EpicesActiveConsumers[id]["correction"]= "nom: " + str(self.CogilogDataComp[id]['Nom du client'])

					cogAdr 	= ""
					if 'Voie (adresse)' in self.CogilogDataComp[id] :		cogAdr += self.CogilogDataComp[id]['Voie (adresse)'] 	+ ", "
					if 'Code postal' in self.CogilogDataComp[id] :			cogAdr += self.CogilogDataComp[id]['Code postal'] 		+ ", "
					if 'Ville' in self.CogilogDataComp[id] :				cogAdr += self.CogilogDataComp[id]['Ville'] 			+ ", "
					
					if self.addrCmp(id) :	# pour le client "id" : comparaison des adresses Cogilog/Epices
						self.EpicesActiveConsumers[id]["statut"] 	+= ", adr KO"	
						self.EpicesActiveConsumers[id]["correction"]+= " adr: " + cogAdr

					else :
						self.EpicesActiveConsumers[id]["statut"] 	+= ", adr ok"
						#self.EpicesActiveConsumers[id]["correction"]= " adr: " + cogAdr

					if self.mailCmp(id) : 
						print("****************\n")

		if verbose : 
			print("... " + Resize(len(self.unknownCustomersCode) , 3) + " codes clients inconnus")
			print("  + " + Resize(len(self.matchingCustomersCode), 3) + " codes clients communs ok")
			print("dont :")	
			print("    ... " + Resize(len(self.invalidCustomerNames) , 3) + " clients avec nom incohérent")
			print("      + " + Resize(len(self.matchingCustomersName), 3) + " clients avec nom ok")
			print()	

		# Liste des erreurs d'adresses :
		print("-------- Diff. adresses (sur " + str(self.addrCmpCnt) + " clients avec N° et nom OK)-------")
		print("... soit : " + str(self.addrCmpOk) + " adr OK, " + str(self.addrCmpKo) + " adr KO")
		if verbose : 
			print(self.addressDiffOnly)
			#print(str(len(self.addressDiffOnly)))
			print(self.addressDiffAll)
			#print(str(len(self.addressDiffAll)))
			print("--------")
		
		if len(self.addressDiffOnly) :
			self.fileRecord(L=sorted(self.addressDiffOnly.keys()), D=self.addressDiffOnly, filename="ProblemesAdresses.csv", delimiter="\t")

		if len(self.addressDiffAll) :
			self.fileRecord(L=sorted(self.addressDiffAll.keys()),  D=self.addressDiffAll,  filename="Adresses.csv", delimiter="\t")
		
		if verbose :
			print("-------- Diff. adresses    -------")
		
	def nameCmp(self, id, approxName= True):
		if approxName :
			return not strDiff(	self.EpicesActiveConsumers[id]['Nom du client'],	self.CogilogDataComp[id]['Nom du client'])
		else :
			return 			(	self.EpicesActiveConsumers[id]['Nom du client'] ==	self.CogilogDataComp[id]['Nom du client'])
			 

	def addrCmp(self, id):
		self.addrCmpCnt += 1		# Nombre d'adresse testées

		# comparaison des adresses Clients/Cogilog 
		if 'Voie (adresse)' in self.EpicesActiveConsumers[id] :	epicesAddr 	= self.EpicesActiveConsumers[id]['Voie (adresse)']
		else :													epicesAddr 	= None
		if 'Code postal' in self.EpicesActiveConsumers[id] :	epicesCP 	= self.EpicesActiveConsumers[id]['Code postal']
		else :													epicesCP 	= None
		if 'Ville' in self.EpicesActiveConsumers[id] :			epicesTown 	= self.EpicesActiveConsumers[id]['Ville']
		else :													epicesTown 	= None

		if 'Voie (adresse)' in self.CogilogDataComp[id] :		cogilogAddr	= self.CogilogDataComp[id]['Voie (adresse)']
		else :													cogilogAddr	= None
		if 'Code postal' in self.CogilogDataComp[id] :			cogilogCP 	= self.CogilogDataComp[id]['Code postal']
		else :													cogilogCP 	= None
		if 'Ville' in self.CogilogDataComp[id] :				cogilogTown	= self.CogilogDataComp[id]['Ville']
		else :													cogilogTown	= None

		err = ""
		if strDiff(epicesAddr,	cogilogAddr	) :					err += "adr. "
		if strDiff(epicesCP,	epicesCP	) :					err += "CP "
		if strDiff(epicesTown,	cogilogTown	) :					err += "Ville "

		if err != "" :
			self.addrCmpKo += 1		# Nombre d'adresse testées KO
			# on met tous les champs
			self.addressDiffAll[id] = { 
					"id"			: id,
					"client"		: self.EpicesActiveConsumers[id]['Nom du client'],
					"erreur"		: err			,
					"Epices_Adr" 	: epicesAddr	, 
					"Epices_CP" 	: epicesCP		, 
					"Epices_Ville" 	: epicesTown 	,
					"Cogilog_Adr" 	: cogilogAddr	, 
					"Cogilog_CP" 	: cogilogCP		, 
					"Cogilog_Ville" : cogilogTown	,
					}
			
			# on ne mets que les champs en erreur
			self.addressDiffOnly[id] = { 
					"id"			: id,
					"client"		: self.EpicesActiveConsumers[id]['Nom du client'],
					"erreur"		: err			,
					}
			if strDiff(epicesAddr,	cogilogAddr	) :
				self.addressDiffOnly[id]["Epices_Adr"]		= epicesAddr
				self.addressDiffOnly[id]["Cogilog_Adr"]		= cogilogAddr
			else :
				self.addressDiffOnly[id]["Epices_Adr"]		= ""
				self.addressDiffOnly[id]["Cogilog_Adr"]		= ""

			if strDiff(epicesCP,	epicesCP	) :
				self.addressDiffOnly[id]["Epices_CP"]		= epicesCP
				self.addressDiffOnly[id]["Cogilog_CP"]		= cogilogCP
			else:
				self.addressDiffOnly[id]["Epices_CP"]		= ""
				self.addressDiffOnly[id]["Cogilog_CP"]		= ""

			if strDiff(epicesTown,	cogilogTown	) :
				self.addressDiffOnly[id]["Epices_Ville"]	= epicesTown
				self.addressDiffOnly[id]["Cogilog_Ville"]	= cogilogTown
			else :
				self.addressDiffOnly[id]["Epices_Ville"]	= ""
				self.addressDiffOnly[id]["Cogilog_Ville"]	= ""


			if self.verbose :
				print("Epices  = " + Resize(epicesAddr , 30) + ", " + Resize(epicesCP , 10) + " " + Resize(epicesTown )	)
				print("Cogolog = " + Resize(cogilogAddr, 30) + ", " + Resize(cogilogCP, 10) + " " + Resize(cogilogTown)	)
				print()
		else : 
			self.addrCmpOk += 1		# Nombre d'adresse testées OK

		return (err != "")

	def mailCmp(self, id):
		#comparaison des adresses mails
		mailDiff = False
		"""
		"        Epices -> "
		id
		Code
		Nom du client
		Voie (adresse)
		Code postal
		Ville
		intracom
		SIRET
		actif
		statut
		correction	

        "Cgilog -> "
		id
		Nom du client
		Voie (adresse)
		Code postal
		Ville
		"""
		#if strDiff(	self.EpicesActiveConsumers[id]['E-mail'],	self.CogilogDataComp[id]['E-mail']) :
		#	print("E-mails différents ...")
		#	print("        Epices -> " + str(self.EpicesActiveConsumers[id]['E-mail']))
		#	print("        Cgilog -> " + str(self.CogilogDataComp[id]['E-mail']))
		#	
		#	mailDiff = True

		return mailDiff
		
	def diffRecord(self, verbose = False): 
		print("\n ---- Synthèse des " + str(len(self.EpicesActiveConsumers)) + " clients Epices --- ")
		print("> À créer: " + Resize(len(self.unknownCustomersCode) , 3) + " codes clients inconnus                           /!\\")
		print("> communs: " + Resize(len(self.matchingCustomersCode), 3) + " clients avec un 'code client' connu sous Cogilog "   )
		print(">>> dont   " + Resize(len(self.invalidCustomerNames) , 3) + " clients avec noms incohérents                    /!\\")
		print(">>>  et    " + Resize(len(self.matchingCustomersName), 3) + " clients avec un code client connu et le même nom "    )
		print(">>>>> dont " + Resize(self.addrCmpKo 				, 3) + " clients avec adr. incohérentes                   /!\\")
		#print(str(len(self.unknownCustomersCode )) + " 'codes client' inconnu par Cogilog"   )

		if verbose :
			print()
			print("-----------------------------")
			print("liste des " + str(len(self.unknownCustomersCode)) + " clients inconnus : ")
			for id in self.unknownCustomersCode :
				print("client " + Resize(id) + ": pas dans Cogilog --> " + str( self.EpicesActiveConsumers[id]['Nom du client']) )

		if len(					self.unknownCustomersCode	) :	
			self.fileRecord(L=	self.unknownCustomersCode, D=self.EpicesActiveConsumers, filename="ClientsInconnusDansCogilog.csv", delimiter="\t")

		if verbose :
			print()
			print("-----------------------------")
			print("liste des " + str(len(self.invalidCustomerNames)) + " clients avec nom incohérent : ")
			for id in self.invalidCustomerNames :
				print("client " + Resize(id, 16) + ": " \
					+	" E= "	+ Resize( self.EpicesActiveConsumers[ id]['Nom du client'], 32) \
					+	" C= "	+ Resize( self.CogilogDataComp[id]['Nom du client'], 32) )

		if len(					self.invalidCustomerNames	) :	
			self.fileRecord(L=	self.invalidCustomerNames, D=self.EpicesActiveConsumers, filename="ClientsNomsIncoherentDansCogilog.csv", delimiter="\t")

		if verbose :
			print()
			print("-----------------------------")
			#print("liste des " + str(self.addrCmpKo) 			+ " clients avec nom incohérent : ")
			print("liste des " + str(len(self.addressDiffAll)) 	+ " clients avec nom incohérent : ")
			for id in self.addressDiffAll :
				d = self.addressDiffAll[id]
				Eadr = str(d["Epices_Adr" ]) + ", " + str(d["Epices_CP" ]) + ", " + str(d["Epices_Ville" ])
				Cadr = str(d["Cogilog_Adr"]) + ", " + str(d["Cogilog_CP"]) + ", " + str(d["Cogilog_Ville"])
				print("client " + Resize(id, 16) + ": " + Resize(Eadr, 50) + " / "+ Resize(Cadr, 50) 		)
				

	def logRecord(self, T = "", filename = "log.txt"): 
		if len(T) :
			logFullname 	= self.outputDir + filename
			print("Mémorisation dans " + Resize(logFullname, 40))
			with open(logFullname, 'w') as logFile:  
				logFile.write(T)

	def fileRecord(self, L = [], D = {}, filename = "void.csv", encoding="utf-16", delimiter=';'): 
		# L 		: liste des ID à utiliser
		# D			: dictionnaire avec les données à recopier
		# filename 	: nom CSV généré
		csvFullname 	= self.outputDir + filename
		print("Mémorisation dans " + Resize(csvFullname, 40), end = "")
		
		if len(L) > 0 :
			lines = []	# création d'une liste de dictionnaires : 1 dictionnaire par ligne à écrire dans le CSV
			for id in L : 			
				lines.append(D[id])
		else : 
			lines = []	# création d'une liste de dictionnaires : 1 dictionnaire par ligne à écrire dans le CSV
			for id in D : 			
				lines.append(D[id])
		
		with open(csvFullname, 'w', encoding = encoding) as csvFile:  # You will need 'wb' mode in Python 2.x
			w = csv.DictWriter(csvFile, lines[1].keys(), delimiter=delimiter)
			w.writeheader()
			w.writerows(lines)

		print(" ----> " + str(len(lines)) +" lignes.")

	def sortDict(self, d={}, sortKey= "statut") :
		# trie par la clé "statut" des données
		def select_status(item):
		    return item[1][sortKey]
		
		dictItems = sorted(d.items(), key=select_status)
		#L=[]		# liste des clées après trie
		D={}		# dictionnaire trié par "statut"
		for k in dictItems :
			#L.append(k[0])	# liste des clées après trie
			D[k[0]] = k[1]	# dictionnaire trié par "statut"
		return D
	
	def synthesis(self, verbose = False) :
		print("\n------------------------------\nsynthèse :")
		D = self.sortDict(d=self.EpicesActiveConsumers, sortKey= "statut")
		cnt = 0
		self.AddrLog = ""	
		for id in D :
			print(			  Resize(id, 12) 						\
		 		+ " : " 	+ Resize(D[id]["statut"]		, 20) 	\
		 		+ "... " 	+ Resize(D[id]["Nom du client"]	, 32) 	\
				+ " -> " 	+ Resize(D[id]["correction"]	, 60)	)
			
			if 'adr. détails' in self.CogilogDataComp[id] : 
				if "adr KO" in D[id]["statut"] :
					cnt += 1
					self.AddrLog += "------------------------------------------------------------------------------------\n"
					self.AddrLog += Resize(cnt, 4) + Resize(">>>>", 8) + Resize(id, 16) + Resize(D[id]["Nom du client"]	, 70) + "\n\n"
					
					AddrLine = 	"Epices ---> " 															+	\
								Resize(self.EpicesActiveConsumers[id]['Voie (adresse)']	, 60) 	+ ", "	+	\
		   						Resize(self.EpicesActiveConsumers[id]['Code postal']	, 10)	+ ", "	+	\
		   						Resize(self.EpicesActiveConsumers[id]['Ville']) 							
					self.AddrLog += AddrLine + "\n"
					print(Resize("", 70) +  AddrLine)

					AddrLine = 	"Cogilog --> " 															+ 	\
								Resize(self.CogilogDataComp[id]['Voie (adresse)']	, 60) 		+ ", "	+	\
		   						Resize(self.CogilogDataComp[id]['Code postal']		, 10) 		+ ", "	+	\
		   						Resize(self.CogilogDataComp[id]['Ville']) 													
					self.AddrLog += AddrLine + "\n"
					print(Resize("", 70) +  AddrLine)

					for k in self.CogilogDataComp[id]['adr. détails'] : 
						AddrLine = 	Resize(k, 24) +  ": " + str(self.CogilogDataComp[id]['adr. détails'][k])
						self.AddrLog += Resize(" ...", 12) +  AddrLine + "\n"
						print(Resize("", 70) +  AddrLine)

					if verbose :	####  détails = chaines comparées	####
						print(Resize("", 70) +  "Epices --> " + 										\
									simplifyStr(self.EpicesActiveConsumers[id]['Voie (adresse)']) 	+ ", "	+	\
									simplifyStr(self.EpicesActiveConsumers[id]['Code postal']) 		+ ", "	+	\
									simplifyStr(self.EpicesActiveConsumers[id]['Ville']) 			)
						print(Resize("", 70) +  "Cogilog -> " + 										\
									simplifyStr(self.CogilogDataComp[id]['Voie (adresse)']) 	+ ", "	+	\
									simplifyStr(self.CogilogDataComp[id]['Code postal']) 		+ ", "	+	\
									simplifyStr(self.CogilogDataComp[id]['Ville']) 			)
					###				####  détails = chaines comparées	####

					self.AddrLog += "\n"

			
			
		self.fileRecord(D=D, filename="SyntheseClientsActifs.csv", delimiter="\t")

		#print("\n\n\nself.AddrLog...\n\n\n")
		#print(self.AddrLog)
		self.logRecord(T=self.AddrLog, filename="log_adr_diff.txt")
		
	def listToEpicesCustomersDict(self, L=[], verbose=False) :
		# conversion d'une liste de clients (Epices) en un dictionnaire portant sur la même liste... mais avec les données en plus
		d = {}
		IDs = []
		idx = 0
		for k in L : 
			if k in 	self.Epices.CustomerBase :
				idx+=1
				IDs.append(k)
				d[k] = 	self.Epices.CustomerBase[k]
				if verbose :
					print( Resize(idx, 4) + ": " + Resize(k, 15) + "---> " + str(d[k]))
		
		if not verbose :
			print("... " + Resize(idx, 4) + " clients avec données cogilog incohérentes")
			print( IDs )
			print()
		
		return d

	# génération des fichiers d'imports
	def newCusomerFiles(self, verbose=False) :
		D = self.listToEpicesCustomersDict(L = sorted(self.unknownCustomersCode) , verbose=verbose)		# création du dictionnaire (avec les données Epices à partir de la liste fournie
		self.updt.wrCogilogFiles(epicesCustomer= D,	outputDir= "./2d-import-clients/",	outName= "import_clients",		noChangeList = []			, modify = False, noteLog=True)

	def nameUpdateFiles(self, noChangeList = ['id', 'adr', 'mail', 'paiement'], verbose=False) :
		D = self.listToEpicesCustomersDict(L = sorted(self.invalidCustomerNames) , verbose=verbose)		# création du dictionnaire (avec les données Epices à partir de la liste fournie
		self.updt.wrCogilogFiles(epicesCustomer= D,	outputDir= "./2e-modif-clients/",	outName= "noms_clients",		noChangeList = noChangeList, modify = True	)

	def addrUpdateFiles(self, noChangeList = ['id', 'paiement'], verbose=False) :
		D = self.listToEpicesCustomersDict(L = sorted(self.invalidCustomerAddr) , verbose=verbose)		# création du dictionnaire (avec les données Epices à partir de la liste fournie
		self.updt.wrCogilogFiles(epicesCustomer= D,	outputDir= "./2e-modif-clients/",	outName= "adresses_clients",	noChangeList = noChangeList, modify = True	)

		
########################################################################################################################			
if __name__ == "__main__":
	outputDir = "./2c-clients/"

	if 0 : 
		print("\n====  Base client Cogilog ====\n")
		Cogilog 			= clsCogilogCustomerReader(	outputDir = outputDir)
		CogilogDataComp     = Cogilog.CogilogDataComp
		print("\n... détails de la Base client Cogilog...\n")
		Cogilog.listPrint()

	if 0 :
		print("\n====  Base client Epices ====\n")
		Epices 				= clsEpicesCustomerReader(	outputDir = outputDir)
		Epices.recordUnactiveCustomer(delimiter="\t")
		EpicesActiveConsumers		= Epices.EpicesActiveConsumers
		unactiveCustomer    = Epices.unactiveCustomer
		print("\n... détails de la Base client Epices...\n")
		Epices.listPrint()
		print("\n" + str(len(EpicesActiveConsumers	  )) + " clients   actifs sous Epices"         )
		print("\n" + str(len(unactiveCustomer )) + " clients inactifs sous Epices"         )

	############
	###		Comparaison des bases		###
	print("\n====  Comparaison des bases clients Epices/Cogilog ====\n")
	cmp = clsBaseCompare(outputDir = outputDir, verbose=False)
	cmp.diffRecord(True)
	cmp.synthesis()

	############
	###		Génération des fichiers d'import		###
	print("\n====  Génération des fichiers d'import Cogilog ====\n")
	print("\nCréation des clients inconnus...")
	#cmp.wrCogilogFiles( cmp.invalidCustomerNames, "./2e-modif-clients/"	, outName= "noms_clients", modify = True)
	cmp.newCusomerFiles()

	print("\nMise à jour des noms ...")
	#cmp.wrCogilogFiles( cmp.invalidCustomerNames, "./2e-modif-clients/"	, outName= "noms_clients", modify = True)
	cmp.nameUpdateFiles()

	print("\nMise à jour des adresses (seules)...")
	#cmp.wrCogilogFiles( cmp.invalidCustomerAddr, "./2e-modif-clients/"	, outName= "adresses_clients", modify = True)
	cmp.addrUpdateFiles()
	
	############
	print("\n====  done ====\n")
