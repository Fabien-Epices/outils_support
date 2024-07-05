# coding: utf-8
################################################################################################################################
# écriuture d'un fichier txt
################################
from pathlib import Path
#import json

class cls_TextFileWriter:
### écriuture d'un fichier txt

	def version(self):
		return "Text File Writer v1.0"

	def __init__(self, outputDir = "./zzz/"):		# 
		# outputDir :	dossier de dépôts des données (au format matlab-like)
		# fileName : 	nom du fichier
		self.outputDir			= outputDir
		self.outputPath = Path(outputDir)
		if not self.outputPath.exists() :   # test de la présence du répertoire
			print(">>> création du répertoire '" + outputDir + "'\n")
			self.outputPath.mkdir(parents=False, exist_ok=False) # création du réperoire manquant


	def wr(self, txt=[], fileName="zzzz.txt", verbose = False):		# 
		outputFullName = self.outputDir + fileName  
		if verbose : 
			print(" --- fichier " + str(outputFullName) + " ...  ---- ")
		with open(outputFullName, "w+") as f :
			if type(txt) == list : 
				for t in txt :
					f.write(str(t))		# texte de la ligne
					f.write("\n")		# ajout de la fin de ligne
					if verbose :
						print(str(t))
			else : 
				f.write(txt)
				if verbose :
					print(str(txt))
	
		print(" --- fichier " + str(outputFullName) + " créé ---- ")

###########	tests ##############@
if __name__ == "__main__":
	cls_TextFileWriter(outputDir= "./zzz/").wr(
		txt			=["fichier de test...", "", "fini !"], 
		fileName	="test.txt", 
		verbose 	= True
	)
	############
	print("\n====  done ====\n")