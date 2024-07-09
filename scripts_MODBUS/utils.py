# coding: utf-8
################################################################################################################################
# Utilitaires :
# 	- écriuture d'un fichier txt
#	- calcul des coefs d'une droite y = a*x + b
#	etc.
################################
from pathlib import Path
#import json



def Resize(S="", size=20):
	# redimentionne une chaine en ajoutant des espces à la fin
	myStr = str(S)
	for idx in range( size - len(myStr) ) :
		myStr = myStr + " "
	return myStr

def slope_intercept(x1,y1,x2,y2):
	# repris de "https://fr.moonbooks.org/Articles/Calculer-le-coefficient-directeur-et--dune-droite-avec-python-/"
    a = (y2 - y1) / (x2 - x1)
    b = y1 - a * x1     
    return a,b
#print(slope_intercept(x1,y1,x2,y2))







class TextFileWriter:
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
			self.outputPath.mkdir(parents=True, exist_ok=False) # création du réperoire manquant


	def wr(self, txt=[], fileName="zzzz.txt", encoding="utf-16", verbose = False):		# 
		outputFullName = self.outputDir + fileName  
		if verbose : 
			print(" --- fichier " + str(outputFullName) + " ...  ---- ")
		with open(outputFullName, "w+", encoding=encoding) as f :
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
	TextFileWriter(outputDir= "./zzz/").wr(
		txt			=["fichier de test...", "", "fini !"], 
		fileName	="test.txt", 
		verbose 	= True
	)

	print()
	# calcul des coefs d'une droite
	x1 = 2.0
	y1 = 3.0
	x2 = 6.0
	y2 = 5.0
	(a, b) = slope_intercept(x1,y1,x2,y2)
	print("----------\ntests des calcul des coef de la droite\n(repris de : https://fr.moonbooks.org/Articles/Calculer-le-coefficient-directeur-et--dune-droite-avec-python-/ )")
	print("----------\ndroite trouvée : " + str(a) + " * x + " + str(b) + "\n... vérif ... " )
	print("y("+ str(x1) + ") = " + str( y1) + " = " + str( a*x1 + b)  )
	print("y("+ str(x2) + ") = " + str( y2) + " = " + str( a*x2 + b)  )

	############
	print("\n====  done ====\n")