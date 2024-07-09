################################################################################################################################
# modbusDefinition :
# 	- Définition des registres modbus, pour la création d'un .ini
################################
from utils import TextFileWriter, Resize, slope_intercept
from pathlib import Path
import pandas as pd				# utiilsation de DataFrame() pour l'affichage sous forme de tableaux   
import re						# regex
import json
import csv
import warnings

pd.options.display.width 		= 600
pd.options.display.max_colwidth = 25
#pd.options.display.min_rows 	= 10

# mise à l’échelle de la variable (Ax +B)
def getVarCoeff(x1,y1,x2,y2):				
	### récupération des coefs A & B à appliquer à la valeur lue sur le modbus.  
	if (x1 or y1 or x2 or y2) :				# tous les coefs ne sont pas nuls
		x1 = float(str(x1).replace(',', '.'))	# abscisse point 1 pour la "mise à l’échelle"	
		y1 = float(str(y1).replace(',', '.'))	# abscisse point 2 pour la "mise à l’échelle"
		x2 = float(str(x2).replace(',', '.'))	# ordonnée point 1 pour la "mise à l’échelle"
		y2 = float(str(y2).replace(',', '.'))	# ordonnée point 2 pour la "mise à l’échelle"
		(a, b) = slope_intercept( x1, y1, x2, y2 )
	else :
		(a, b) = (1.0, 0.0)					# valeurs par défaut : gain à 1, offset à 0
	
	return a,b
class modbusDefinition:
### Définition des requêtes et variables modbus
### génération du fichier .ini 
	def version(self):
		return "modbusDefinition v1.0"


	def __init__(self, siteName = "<site?>"):	
		self.siteName	= siteName
		self.d			= {}
		self.reqIdx		= 0
		self.varIndex 	= 0

		self.parserDir()
		#self.iniData 	= {}

		self.RequestsTableColumns = {
			"id"				: '?'	, # Index de la requête de 1 à N								compteur de requêtes	-> calculé
			"Name"				: '?'	, # Désignation de la requête Modbus							nom de requête 			-> à renseigner 
			"ReadFctCode" 		: 3		, # Code fonction et sous code fonction en lecture				3 => “read holding registers” 
			#									1 => “read coils”
			#									2 => “read discrete inputs”
			#									3 => “read holding registers” 
			# 									4 => “read input registers”
			"WriteFctCode" 		: 0		, # Code fonction et sous code fonction en écriture				(inutilisé)
			"StartReg" 			: 0		, # Adresse du premier registre Modbus	/!\ en mots de 16b /!\	min(addrList)			-> calculé
			"NbReg"				: 0		, # Taille de la réponse sans en-tête et CRC (en mots)			len(addrList)			-> calculé
			"EnableReading"		: 1		, #	Activation de la requête en lecture 						1 => activé en mode polling (mesures)
			"EnableWritting"	: 2		, #	Activation de la requête en écriture						2 => désactivé
			"Option1"			: 0		, #	Réservé
			"Option2"			: 0		, #	Réservé
		}

		self.VariablesTableColumns = {
			"varIndex"			: '?'	, # Index de la variable de 1 à N								compteur				-> calculé
			"varReqIndex"		: '?'	, # Désignation requête Modbus (Modbus_RequestsTables)			index requête : reqIdx	-> calculé
			"varName"			: '?'	, # Désignation de la variable Modbus							nom de variable 		-> à renseigner 
			"varType"			: 8		, # Type de variable											8 => flottant inversé
			#									1 => bit
			#									2 => octet
			#									3 => mot
			#									4 => mot inversé
			#									5 => double mot
			#									6 => double mot inversé
			#									7 => flottant
			#									8 => flottant inversé
			#									9 => chaîne de caractères
			#									10 => Format spécifique afficheur Siebert
			"varSigned"			: 2		, # signed	: 1 => signé, 2 => non signé						1 => signé
			"varPosition"		: 1		, # Position de la variable dans la trame
			"varOption1"		: ''	, # Réservé
			"varOption2"		: ''	, # Réservé
			"varCoeffA"			: 1		, # Coefficient A de mise à l’échelle de la variable (Ax +B)
			"varCoeffB"			: 0		, # Coefficient B de mise à l’échelle de la variable (Ax +B)
			"varUnit"			: ''	, # Unité de la variable
			"varAction"			: 2		, # Méthode de traitement de la variable :						2 : récupération du minimum, maximum et calcul de la moyenne.
			#									0 : variable non relevé.
			#									1 : variable traitée comme paramètres
			#									2 : récupération du minimum, maximum et calcul de la moyenne. 
			# 									4 : valeur instantanée
			#									8 : déclencheur d’alarme sur changement d’état
		}
		
		self.varTypeDef = {		# les adresses sont en mots (de 16 bits)
			1  : { 'size':  1,	'littleEndian':True,	'signed': 2,	'fr' : "bit", 									}, 	
			2  : { 'size':  1,	'littleEndian':True,	'signed': 2,	'fr' : "octet", 								}, 
			3  : { 'size':  1,	'littleEndian':True,	'signed': 2,	'fr' : "mot", 									}, 
			4  : { 'size':  1,	'littleEndian':False,	'signed': 2,	'fr' : "mot inversé", 							}, 
			5  : { 'size':  2,	'littleEndian':True,	'signed': 2,	'fr' : "double mot", 							}, 
			6  : { 'size':  2,	'littleEndian':False,	'signed': 2,	'fr' : "double mot inversé", 					}, 
			7  : { 'size':  2,	'littleEndian':True,	'signed': 2,	'fr' : "flottant", 								}, 
			8  : { 'size':  2,	'littleEndian':False,	'signed': 2,	'fr' : "flottant inversé", 						}, 
			9  : { 'size':  1,	'littleEndian':True,	'signed': 2,	'fr' : "chaîne de caractères", 					}, 
		#	10 : { 'size':  1,	'littleEndian':Truee,	'signed': 2,	'fr' : "Format spécifique afficheur Siebert", 	}, 
		}


		# définition de lignes 'variables' vide (pour l'ajour de variables non-lues)
		self.emptyVariable = self.VariablesTableColumns.copy()
		self.emptyVariable["varName"] 	= "reserve"
		self.emptyVariable["varType"] 	= 2				# 2 => octet
		self.emptyVariable["varAction"] = 0 			# 0 : variable non relevé.
		
		#self.printReqColumns(True)
		#self.printVarColumns(True)


	def parserDir(self, inputDir= "./ZZZ/", outputDir= "./ZZZ/"):	
		# inputDir :	dossier de lecture des fihciers '.ini'
		# outputDir :	dossier de dépôts infos décodés en '.json' et/ou '.csv'
		self.inputDir	= inputDir
		self.inputPath = Path(inputDir)
		if not self.inputPath.exists() :   # test de la présence du répertoire
			print(">>> création du répertoire '" + inputDir + "'\n")
			self.inputPath.mkdir(parents=True, exist_ok=False) # création du réperoire manquant

		self.outputDir	= outputDir
		self.outputPath = Path(outputDir)
		if not self.outputPath.exists() :   # test de la présence du répertoire
			print(">>> création du répertoire '" + outputDir + "'\n")
			self.outputPath.mkdir(parents=True, exist_ok=False) # création du réperoire manquant

	def headerLine(self, D={}) :
		lst = list(D.keys()) 		# on prend les clés du dictionnaire D comme nom de colonnes
		return self.dictToLine(lst, lineStart="# ")
	
	def dictToLine(self, D={}, lineStart="#") :
		if type(D) is dict :		# si c'est un dictoinnaire, on prend les valeurs (si c'est une liste, les éléments)
			D = D.values()

		l = ""
		firstColumn=True
		for k in D : 
			if firstColumn : 	
				l += lineStart + str(k)
				firstColumn = False
			else :				
				l += ";"  + str(k)
		return l

	def printReqColumns(self, verbose = False) :
		print("RequestsTableColumns...")
		#print(self.RequestsTableColumns)	
		print(self.headerLine(self.RequestsTableColumns) )
		if verbose :
			for c in self.RequestsTableColumns :
				print("   " + Resize(c) + " ---> " + str(self.RequestsTableColumns[c])  )

	def printVarColumns(self, verbose = False) :
		print("VariablesTableColumns...")
		#print(self.VariablesTableColumns)
		print(self.headerLine(self.VariablesTableColumns) )
		if verbose :
			for c in self.VariablesTableColumns :
				print("   " + Resize(c) + " ---> " + str(self.VariablesTableColumns[c])  )

	def strValues(self, V={}, verbose = False) :
		# affichage des valeurs d'un dictionnaire définissant une variable 
		txt 	= ""
		start 	= ""
		for v in V :
			if v != 'debug' and V[v] != "" :						# on n'affiche pas le debug ni les champs vides
				txt += start + str(v) + "=" + str(V[v])
			elif verbose :											# sauf en verbose...
				txt += start + str(v) + "=" + str(V[v])
			start = ", "
		return txt
	
	def printValues(self, V={}, end="", verbose = False) :
		print( self.strValues(V) + end)

	################################	adr. requête + variables	################################
	def add_Request_And_Variables_with_adresses(self, R, V, verbose=False ):
	# création d'un nouvelle requête, avec ses variables associées
	#	- R est le dictionnaire définissant les Requêtes (ou simplement le nom de cette requête) --> voir "newRequestLine()""
	#	- V est un dictionnaire { adresse: { def. variable}, ...}
	#
	# ... À partir des adresses, on calcule :
	#	- pour la requête... 
	#		- 'StartReg'	: 	est le min des adresses des variables associées			-> en mots (de 16b)
	# 		- 'NbReg'		: 	est le nombre de registes à lire = (max - min)
	#	- pour les variables... 
	# 		- 'varPosition'	: 	est l'offset de la variable = adresse - StartReg + 1			(commence à 1)
		if type(R) is str : 
			#print("R est une chaine qui correspond au nom de la requête -> on en fait un dict.")
			R = { 'Name': R }	
		elif type(R) is not dict :
			raise TypeError("La requête doit être décrite par un dictionaire (ou par son nom)")

		addrList = []	# liste des adresses des variables 
		for addr in V :
			addrList.append(int(addr))

		# au cas où : trie par ordre croissant
		addrList.sort()
		if verbose :
			print("################################################################################")
			print(addrList)
			print("################################################################################")

		R['StartReg']	= min(addrList)						# min des adresses des variables associées
		R['NbReg'] 		= max(addrList) - R['StartReg']		# nombre de registes à lire = (max - min)

		nextAddr = R['StartReg']
		self.newRequestLine(R, verbose )					# création de la requête
		for a in addrList :
			if 		a < nextAddr :
				print("\n\n/!\\ next addr.: " + Resize(a, 4) + " != " + Resize(nextAddr, 4) + " -> overlap !"				) 	
				raise TypeError("Overlap dans les adresses des varables !")
			elif 	a > nextAddr :
				print(    "/!\\ next addr.: " + Resize(a, 4) + " != " + Resize(nextAddr, 4) + " -> " + str(a - nextAddr)  + " vairables manquantes !"	) 	
				for u in range(1, a-nextAddr+1) :						# /!\ "varPosition" commence à 1 /!\
					v = self.emptyVariable.copy()
					v['varPosition'] = nextAddr - R['StartReg'] + u		# offset de la pseudo-variable
					if verbose :
						print("@" + Resize(nextAddr, 4)  + "- " + Resize(R['StartReg'], 4) + "+ " + Resize(u, 4) + "... Pseudo-variable : " + Resize(v['varName'], 100) + "pos: " + Resize(v['varPosition']) )

					self.newVariableLine(v)								# ajout  de la pseudo-variable
					
				
			if a in V :
				V[a]['varPosition'] = int(a) - R['StartReg']+1			# offset de la variable						/!\ "varPosition" commence à 1 /!\
				if verbose :
					print("@" + Resize(a, 4) + "- " + Resize(R['StartReg'], 4+6) + "...        variable : " + Resize(V[a]['varName'], 100)  + "pos: " + Resize(V[a]['varPosition']) )
					#print("variable : " + self.strValues(V[a]) )
				
				self.newVariableLine(V[a])								# ajout  de la variable

				# taille des données attendues -> suivant la définiition de "self.varTypeDef"
				if 'varType' in V[a] :			
					t = V[a]['varType']									# type de la variable V[a]
				else : 
					t = self.VariablesTableColumns['varType']			# type par défaut


				if t in self.varTypeDef : 	
					nextAddr = a + int(self.varTypeDef[t]['size'])	
				else :
					print("/!\\ taille de variable type " + str(t) +": inconnue !")
					nextAddr = a + 1	# valeur par défaut !

			else :
				print(str(a) + " n'est pas dans " + str(V) )
			
			#print(Resize(a, 4) + " ---> next addr.: " + str(nextAddr) ) 						#TODO... à vérifier :  est-ce qu'il faut ajouter des variables "non-lues", et est-ce qu'il y a des overlaps ?



	################################	ajout de requêtes			################################
	def newRequestLine(self, R, verbose=False ):
	# création d'un nouvelle requête
	#	- les champs sont initialisés avec "RequestsTableColumns", puis
	#	- les champs fournis dans le dictionnaire "D" remplacent ceux initilalisés.
	#
	# Note : le champs 'id' est calculé automatiquement (c'est un compteur de requêtes).
	#
	# Méthode alternative : "R" est une chaine qui correspond au nom de la requête ; les autres champs restent ceux initialisés
	#
		newReq = {}

		if type(R) is str : 
			#print("R est une chaine qui correspond au nom de la requête -> on en fait un dict.")
			R = { 'Name': R }	
		elif type(R) is not dict :
			raise TypeError("La requête doit être décrite par un dictionaire (ou par son nom)")

		if 'Name' in R : 
			self.reqIdx += 1
			R['id'] = self.reqIdx	# forçage du N° de requête
	
			# MaJ du dictionnaire clé/valeut qui définit les variables
			newReq['ReqTable']	= self.RequestsTableColumns.copy()	# init

			print(" ====== "+str(R)+ " ====== ")
			for k in R :
				if k in newReq['ReqTable']: 
					newReq['ReqTable'][k] = R[k] 
				else :
					w = "\n   /!\\ Le champ '" + str(k) + "' n'est pas dans la liste des colonnes des requêtes. /!\\"
					#print(w)
					warnings.warn(w)
					print(newReq['ReqTable']) 


			# traduction du dictionnaire en chaine 
			newReq['Request' ]	= self.dictToLine( newReq['ReqTable'], lineStart="" )

			# init des listes pour les variables à ajouter
			newReq['VarTabList'] 	= []	# init: liste des structures contenant les champs des variables
			newReq['Variables' ] 	= []	# init: liste des chaines de description des variables

			self.d[self.reqIdx] = newReq

			if verbose :
				print("   ---- ReqTable -----> " + str(newReq['ReqTable']))
				print("   ---- Request  -----> " + str(newReq['Request' ]))
			return self.reqIdx
		else :
			raise ValueError("Erreur : pas de nom de requête !")
			#return 		 "Erreur : pas de nom de requête !"



	def printRequest(self, reqList=[], verbose=False):
		if reqList == 'all' :
			reqList	= list(range(0, self.reqIdx+1) )
			#print("Liste des requêtes : " + str(reqList) )
		elif type(reqList) is int :
				reqList = [reqList]
		elif not reqList :					# si non défini, on prend la requête en cours
			reqList	= [ self.reqIdx ]

		F =[]
		for reqIdx in reqList :
			if reqIdx in self.d :
				F.append( self.d[reqIdx]['ReqTable'] )
				req		= self.d[reqIdx]	# requête i
				rTable	= req['ReqTable']
				print("req" + Resize(reqIdx, 5) + " --- " + Resize(rTable['Name'], 35) + " ---> '" + str(req['Request']) + "'" )
				if verbose :
					for k in rTable : 
						print("   " + Resize(k) + ": " + str(rTable[k]) )

		if 1 :
			print(" ----------------------------------------- ")
			df = pd.DataFrame(F)
			print(df)


	################################	ajout de variable(s)		################################
	def newVariableLine(self, D={}, addLine=True ):
		self.varDict 	= self.VariablesTableColumns.copy()			# infos pour le MODUS
		self.varDebug 	= {}										# autres infos (pour debug & test)

		# forçage n° variable dans la def des variables
		self.setVariable(feild='varIndex', 		varValue= self.varIndex	)
		self.varIndex += 1
		
		# forçage n° requête dans la def des variables
		self.setVariable(feild='varReqIndex', 	varValue=self.reqIdx	)

		if len(D) : 
			# ajout d'un dictionnaire clé/valeut qui définit les variables
			for k in D :
				if k not in ['varIndex', 'varReqIndex'] : 							# le N° de requête a été mis automatiquement
					#print("set " + str(k) + " -> " + str(D[k]) )
					self.setVariable(feild=k, varValue=D[k])
			
			if addLine : # mémorisation de la ligne
				#print("add..." )
				self.addVarLine()

			
	def setVariable(self, feild="", varValue=""):
		# ajout d'un champs qui définissent les variables
		if feild in self.varDict :
			self.varDict[feild] = varValue
		elif feild == "debug" : 
			self.varDebug[feild] = varValue
		else :
			print("/!\\ la variable '" + str(feild) + "' n'est pas dans la liste /!\\")
			print(self.varDict)


	def addVarLine(self, verbose = False):
		reqIdx = self.reqIdx
		varDef=self.dictToLine(self.varDict, lineStart="")
		if reqIdx in self.d :
			self.d[reqIdx]['VarTabList'].append(self.varDict)	# liste des structures contenant les champs des variables
			self.d[reqIdx]['Variables' ].append(varDef)			# liste des chaines de description des variables

			if verbose : 
				self.printVariables()


	def printVariables(self, reqList=[], verbose=False):
		if reqList == 'all' :
			reqList	= list(range(0, self.reqIdx+1) )
			#print("Liste des requêtes : " + str(reqList) )
		elif type(reqList) is int :
				reqList = [reqList]
		elif not reqList :					# si non défini, on prend la requête en cours
			reqList	= [ self.reqIdx ]

		for reqIdx in reqList :
			if reqIdx in self.d :
				print("----------------------------------------------------------------------------------")
				print("req " + str(reqIdx) + " (" + str(self.d[reqIdx]['ReqTable']['Name']) + ") : variables... ")
				rVar = self.d[reqIdx]['Variables']
				for idx in  range(len(rVar)) : 
					print("   " + str(rVar[idx]) )

					if verbose :
						v = self.d[reqIdx]['VarTabList'][idx]		# parcours de la liste des structures contenant les champs des variables
						for k in v : 
							print("   " + Resize(k) + ": " + str(v[k]) )

				if 1 : 
					print("----------------------------------------------------------------------------------")
					F = self.d[reqIdx]['VarTabList']
					print(" --- " + str(self.d[reqIdx]['ReqTable']['Name'] ) + " --- ")
					#print(F)
					df = pd.DataFrame(F)
					print(df)


	################################	écriture du fichier			################################
	def modbusReqLines(self) :
		#### 	Modbus_RequestsTables 		---> dans d[reqIdx]['Request'] => chaine
		lines = []
		lines.append("Modbus_RequestsTables={")
		for reqIdx in self.d:
			data = self.d[reqIdx]
			if 'Request' in data :
				lines.append(data['Request'] )
		lines.append("}")
		lines.append("")
		lines.append("")
		return lines

	def modbusVarLines(self) :
		#### 	Modbus_VariablesTables 		----> dans d[reqIdx]['Variables'] => liste de chaines
		lines = []
		lines.append("Modbus_VariablesTables={")
		#for req in modbusData:
		for reqIdx in self.d:
			data = self.d[reqIdx]
			if 'Variables' in data :
				for l in data['Variables'] :			# parcours de la liste des chaines de description des variables
					lines.append(l)
				
		lines.append( "}")
		return lines

	def modbusDefLines(self, verbose = False) :
		### génération du fichier modbus
		lines = []
		lines.append("#Based on " + str(self.siteName) + " collected values")
		lines.append("")
		lines.append("# Description of fields")
		#lines.append("# Id;Name;ReadFctCode;WriteFctCode;StartReg;NbReg;EnableReading;EnableWritting;Option1;Option2")
		lines.append( self.headerLine(self.RequestsTableColumns) )

		for l in self.modbusReqLines() :	# Modbus_RequestsTables ...
			lines.append( l )				# ... lignes de définition des requêtes

		lines.append("")
		lines.append("# Description of fields")
		#lines.append("# varIndex;varReqIndex;varName;varType;varSigned;varPosition;varOption1;varOption2;varCoeffA;varCoeffB;varUnit;varAction")
		lines.append( self.headerLine(self.VariablesTableColumns) )


		lines.append("#")
		for l in self.modbusVarLines() :	# Modbus_VariablesTables ...
			lines.append( l )				# ... lignes de définition des variables

		if verbose : 
			for l in lines :
				print(l)

		return lines


	def jsonDebug(self, outputDir= "./out/ZZZ/", jsonFileName = "zzz.json") :
		txt= json.dumps(self.d, ensure_ascii=False)		# Les caractères non ASCII sont laissés sans modif
		out= TextFileWriter(outputDir= outputDir)		# définiton du répertoire
		out.wr(txt=txt, fileName= jsonFileName)			# ecriture des données json
		
	def modbusDefFile(self, outputDir= "./out/ZZZ/", fileName = "zzz.ini", verbose = False) :
		if 1 : 
			if ".ini" in fileName :		jsonFileName= fileName.replace(".ini", ".json")
			else :						jsonFileName= fileName + ".json"
			self.jsonDebug(outputDir, jsonFileName)

		# écriture du fichier text
		#print("Création du fichier " + str(outputDir) + str(fileName) + " ... ")
		lines = self.modbusDefLines(verbose)
		out= TextFileWriter(outputDir= outputDir)	#définiton du répertoire
		out.wr(txt=lines, fileName= fileName)		#ecriture des données de la list de lignes


	def iniLineParser(self, lineType="?", txtLine="", verbose= True, skipUnreadVal= True) :
		# lineType	= 'req' ou 'var'
		# txtLine	= ligne à analyser
		# verbose	= True / False
		if "\n" in txtLine :
			txtLine= txtLine.replace("\n","")						# suppression fin de chaine
		Lst = txtLine.split(";")									# découpe via les ";"

		if		lineType == "req" : 		
			tabCol	= self.RequestsTableColumns
			rPos	= Lst[0]								# index de la requête 			-> champs 0 des requêtes
			name	= Lst[1]								# nom de la requête 			-> champs 1
		elif	lineType == "var" : 		
			tabCol	= self.VariablesTableColumns
			rPos	= Lst[1]								# index de la requête 			-> champs 1 des variables
			name	= Lst[2]								# nom de la variable 			-> champs 2
		else :
			return False

		lineLength 	=  len(tabCol) 			
		if len(Lst) >= lineLength: 
			if verbose :
				print(Resize(rPos, 3) + ">>> " + lineType + ": '" + str(name) + "'")		# "1  >>> req: '<nom req>'"		ou    "1  >>> var: '<nom var>'"

			if 	't' not in self.iniData :		
				self.iniData['t'] = {}	# chaines du fichier .ini
				self.iniData['d'] = {} 	# dictionnaire <non colonne>/<valeur>

			if 	rPos not in self.iniData['t'] :		
				self.iniData['t'][rPos] = {'req':"" , 'var':[]	}	# chaines du fichier .ini
				self.iniData['d'][rPos] = {'req':{} , 'var':[]	} 	# dictionnaire <non colonne>/<valeur>
			
			Dct = {}								
			for idx, k in enumerate(tabCol) :
				Dct[k] = Lst[idx]

			if 		lineType == 'req' :								# on remplie la structure 'requête'	
				self.iniData['t'][rPos]['req'] = txtLine			# 	index de la requête -> champs 0 des requêtes
				self.iniData['d'][rPos]['req'] = Dct				#	index de la requête -> champs 0 des requêtes
			
			elif 	lineType == 'var' :								# on remplie la liste de structures 'variables' (associées à 1 requête)	
				self.iniData['t'][rPos]['var'].append(txtLine)		# 	index de la requête -> champs 1 des variables

				if not ((skipUnreadVal==True) and (Lst[11]=='0')) :	# ... avec ou sans les '0 : variable non relevé'
					self.iniData['d'][rPos]['var'].append(Dct)		# 	index de la requête -> champs 1 des variables

				#elif (Lst[2] != "reserve") :	print("??? reserve ---> " + str(Lst) )


		else :
			print()
			print("\n"+ lineType + " :"		)
			print("ligne : " + txtLine		)
			print(" ----> " + str(Lst)		)
			print("table : " + str(tabCol) 	) 
			print("\ntaille des données lues/attendues : " + str(len(Lst)) + " / " + str(lineLength) ) 
			print()
			raise ValueError("Erreur : pas assez de données pour la ligne.")

	def iniFilesParser(self, Files= [""], To='csv,debug', encoding='', skipUnreadVal= True, verbose= False) :
		# encoding : 		forçage du type de caractères ascii (ex: 'utf-16', 'utf-8', ... ou '')
		# skipUnreadVal :	pour ignorer les valeurs non-lues (varAction à 0)
		# verbose :			affichage de debug

		#import de tout le répetoire (si le nom de fichier n'est pas précié)		
		if type(Files) == list :
			#Files = Files
			print("import de la liste : " + str(Files) )
		elif Files == "all" :
			self.FileRegex = "*.ini"
			print("\nImport du repertoire " + self.inputDir + " (regex : " + self.FileRegex + " ) ...")
			importFilesList = list( self.inputPath.glob(self.FileRegex) )         	# liste des noms complets de fichiers ('chemin/*.init')
			Files = []
			for f in importFilesList :                                             	# recherche des id dans les noms de fichiers
				fName = re.split('/', str(f))[-1] 									# récupération du nom de fichiers
				Files.append(fName)													# ajout à la liste de noms de fichiers
		else :	# import d'un fichier particulier (jsonFile)
			Files = [ Files ]


		for f in Files : 
			print("  ...  import de " + self.inputDir + f )

		for f in Files : 
			print(" ==== analyse de " + self.inputDir + f + " ==== ")
			self.iniParser(	
				fileName= f, 
				encoding=encoding,	
				skipUnreadVal=skipUnreadVal, 	
				verbose=verbose)
			
			if "csv" in To :
				self.ini2CsvFile()
			if "json" in To :
				self.ini2JsonFile()
			if "debug" in To :
				self.print()

			print("\n\n")

	def iniParser(self, fileName = "", encoding='', skipUnreadVal= True, verbose= False) :
		# encoding : 		forçage du type de caractères ascii (ex: 'utf-16', 'utf-8', ... ou '')
		# skipUnreadVal :	pour ignorer les valeurs non-lues (varAction à 0)
		# verbose :			affichage de debug
		
		self.iniData 	= {}		# init

		self.inName  = fileName
		if ".ini" in fileName :		
			self.outName = fileName.replace('.ini', '')		# supression de l'extension (si elle existe)
		elif "." in fileName :		
			self.outName = fileName.replace('.'  , '-')		# supression de l'extension (si elle existe)
		else :
			self.outName = fileName							# nom sans extension
			self.inName  = fileName	+ '.ini'

		inFullName = self.inputDir + fileName		# nouveau fichier à parser

		if encoding != "" :		# encoding non précisé
			with open(inFullName, encoding=encoding	) as inifile:
				lines = inifile.readlines()		# on lit toutes les lignes du fichier '.ini'
		else :
			with open(inFullName					) as inifile:
				lines = inifile.readlines()		# on lit toutes les lignes du fichier '.ini'

		### décodage requêtes @ variables
		reqLine = False
		varLine = False

		# parcours des lignes du fichier		
		for txtLine in lines:
			#print(txtLine)
			if txtLine[0] != '#' :				# on ignore les lignes de commentaires ...

				### décodage des lignes de requêtes
				if		"modbus_requeststables" in txtLine.lower() :
					reqLine = True
					if	"Modbus_RequestsTables" not in txtLine :
						print("\n/!\\ case de 'Modbus_RequestsTables' non respectée: \n")
						print(txtLine) 	
						#raise ValueError("Erreur : case de 'Modbus_RequestsTables' non respectée.")

				elif reqLine and ("}" not in txtLine) :
					self.iniLineParser(lineType="req", txtLine=txtLine, skipUnreadVal= skipUnreadVal, verbose= verbose)
				else : 
					reqLine = False


				### décodage des lignes de variables
				#if		"Modbus_VariablesTables" in txtLine :
				if		"modbus_variablestables" in txtLine.lower() :
					varLine = True
					if	"Modbus_VariablesTables" not in txtLine :
						print("\n/!\\ case de 'Modbus_VariablesTables' non respectée: \n")
						print(txtLine) 	
						#raise ValueError("Erreur : case de 'Modbus_RequestsTables' non respectée.")

				elif varLine and ("}" not in txtLine) :
					self.iniLineParser(lineType="var", txtLine=txtLine, skipUnreadVal= skipUnreadVal, verbose= verbose)
				else : 
					varLine = False
			elif 1:#verbose:   								# ligne de commentaires ...
				print( str(txtLine).replace("\n",""))		# ligne de commentaires ...


		if verbose :
			#print(self.iniData)
			self.print()


	def print(self) :
		print()
		print(	"----------------\nparsing de "	+ self.inputDir + self.inName )
		#print(	"----------------\n" + str(self.iniData)	)
		print(	"----------------" )
		if 'd' in self.iniData :
			Rlist = []
			for idx in self.iniData['d'] :
				if 'req' in 	self.iniData['d'][idx] :
					Rlist.append(self.iniData['d'][idx]['req'])
					#reqLst = list(self.iniData['d'][idx]['req'].values() )
					#print("req " + str(idx) + " : " + str(reqLst) )
				#else : print(" 'red' n'est pas dans self.iniData[" + str(idx) + "]['d]")

			print(" --- liste des requêtes ---")
			pd.options.display.max_colwidth = 40
			df = pd.DataFrame( Rlist )
			print(df)
			print()

			print(" --- listes de variables ---")
			for idx in self.iniData['d'] :
				if 'var' in 	self.iniData['d'][idx] :
					df = pd.DataFrame( self.iniData['d'][idx]['var'])
					print(df)
					#varLst = 	self.iniData['d'][idx]['var']
					#for v in varLst :
					#	print("var --> " + str( list( v.values() ) ))
	
				print()
			#else : print(" 'd' n'est pas dans self.iniData[" + str(idx) + "]")
		print(	"----------------" )

	def ini2JsonFile(self) :
	### copie des données décodées dans un fichier Json
		txt= json.dumps(self.iniData, ensure_ascii=False)		# Les caractères non ASCII sont laissés sans modif
		out= TextFileWriter(outputDir= self.outputDir)			# définiton du répertoire
		out.wr(txt=txt, fileName= self.inName + ".json")		# ecriture des données json

	def ini2CsvFile(self, verbose = True) :
	### copie des données décodées dans un fichier Csv (en les mettant "à plat" ...)
	#... par recopie des noms/adr de requêtes en début de ligne "var"
		if 'd' in self.iniData :
			VList = []
			for idx in self.iniData['d'] :
				if 'req' in 	self.iniData['d'][idx] :
					Rinit = { 'ReqName' : "" }		# init
					lastReq = self.iniData['d'][idx]['req']
					if ('Name' in lastReq) and ('StartReg' in lastReq) :
						Rinit['ReqName'		] 	= 	lastReq['Name'	]											# colonne 1 -> nom requête
						Rinit['ReqStartReg'] 	=	lastReq['StartReg']											# colonne 2 -> adr. requête
						Rinit['ReqNbReg'] 		=	int(lastReq['NbReg']) 										# colonne 3 -> nbr de mots requête
						Rinit['|'] 				= "|"															# sépataratceur colonne de gauche

						if 'var' in 	self.iniData['d'][idx] :
							for Vidx, Vval in enumerate(self.iniData['d'][idx]['var']) :
								Vline = Rinit.copy()
								for v in Vval :
									Vline[v]	= self.iniData['d'][idx]['var'][Vidx][v]						#... puis toutes les colonnes des variables

								Vline['/']		= "/"															# sépataratceur colonnes de doite
								#Vline['ReqStartReg'] 	=	lastReq['StartReg']									# colonne de doite -> adr. requête
								if ('varPosition' in Vval) and ('varType' in Vval) :							
									Vline['adr']= int(lastReq['StartReg']) + int(Vval['varPosition'])-1			# colonnes de doite -> adr. variable		("varPosition" commence à 1 /!\)

									t = int(Vval['varType'])
									Vline['fin']= Vline['adr'] + int(self.varTypeDef[t]['size'])-1				# colonnes de doite -> adr. variable (fin)
									Vline['VarSize' ] 	=	int(self.varTypeDef[t]['size'])						# colonne de doite -> nbr de mots requête

								Vline['ReqEnd'	] 	=	int(lastReq['StartReg']) + int(lastReq['NbReg']) 		# colonne de doite -> adr. fin requête
									
								#print("   new var ---> " + str(R) )
								VList.append(Vline)

		if verbose :
			print(	"----------------" )
			df = pd.DataFrame( VList )
			print(df)

		fullName = self.outputDir + self.inName + ".csv"
		with open(fullName, "w", newline="") as f:
			w = csv.DictWriter(f, VList[0].keys(), delimiter= ";",  quotechar= '"' )
			w.writeheader()
			for v in VList :
				w.writerow(v)
		print(	'--- fichier ' + fullName + ' créé ----' )


###########	tests ##############@
if __name__ == "__main__":

	mb = modbusDefinition("Ze Zite")
	f = "z-test.ini"

	if 1 : 	### étape 1 :    création d'un fichier de défintion ".ini"  ###
		# ... à partir de données sur les "requêtes" et les "variables" à inclure
		
		# saisie des index de variables et de sa position
		mb.newRequestLine(	{ "Name": "XXXX", "StartReg": 10}							, True)
		mb.newVariableLine( {"varIndex":1, "varName":"Ze 1st Var", "varPosition":1} )	
		mb.newVariableLine( {"varIndex":2, "varName":"Ze 2nd Var", "varPosition":2} )	
		mb.newVariableLine( {"varIndex":3, "varName":"Ze 3rd Var", "varPosition":3} )	

		# saisie via l'adresse de la variable, 
		# ... et de sa def. 
		mb.VariablesTableColumns["varType"] = 3			# forçage du type 3 par défaut (pour le variables suivantes)
		V = {	# adr:{ <def. variable> }
			20: {"varName":"Ze 4st Var" 				},
			22: {"varName":"Ze Var V" 					},
			24: {"varName":"Ze Var VI" 					},
			26: {"varName":"ZeLatsVar"	, "varType":4 	},
		}
		mb.add_Request_And_Variables_with_adresses("YYYY", V, False)

		
		### création d'un fichier de défintion "".ini" (et de debug .json) 	###
		print("\n\n---------------------------")
		print(''' étape 1 :    création d'un fichier de défintion ".ini" ''')
		mb.modbusDefFile(	outputDir= "./ZZZ/",	fileName = f)


	if 1 : 	### étape 2 :    décodage d'un fichier de déf ".ini"  existant ###
		# ... et créatoin des fichiers de debug ".json", ".csv", etc.

		print("\n\n---------------------------")
		print(''' étape 2 :    décodage d'un fichier de déf ".ini"  existant ''')
		#mb.parserDir(inputDir= "???", outputDir= "???")	 # optionnel : configuration des répertoires 
		mb.iniParser(fileName = f, encoding="utf-16", verbose=True)
		mb.ini2JsonFile()
		mb.ini2CsvFile()
	
	print("\n\n---------------------------")
	print("\n====  done ====\n")