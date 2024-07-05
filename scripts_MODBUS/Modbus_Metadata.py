# coding: utf-8
################################################################################################################################
# metadata pou rla génération des fichiers MODBUS
################################
#from pathlib import Path
#import json

def Resize(S="", size=20):
	# redimentionne une chaine en ajoutant des espces à la fin
	myStr = str(S)
	for idx in range( size - len(myStr) ) :
		myStr = myStr + " "
	return myStr

class cls_Modbus_Metadata:
	def __init__(self):
		self.RequestsTableColumns = {
			"ReadFctCode" 		: 4		,
			"WriteFctCode" 		: 0		,
			"StartReg" 			: 0		, # min(addrList)
			"NbReg"				: 0		, # len(addrList)
			"EnableReading"		: 1		,
			"EnableWritting"	: 2		,
			"Option1"			: 0		,
			"Option2"			: 0		,
		}

		self.VariablesTableColiumns = {
			"varIndex"			: 1		, # compteur
			"varReqIndex"		: 1		, # index du groupe (requête)
			"varName"			: "?"	,
			"varType"			: 8		,
			"varSigned"			: 1		,
			"varPosition"		: 1		,
			"varOption1"		: ""	,
			"varOption2"		: ""	,
			"varCoeffA"			: 1		,
			"varCoeffB"			: 0		,
			"varUnit"			: "?"	,
			"varAction"			: 2		,
		}


###########	tests ##############@
if __name__ == "__main__":
	mb = cls_Modbus_Metadata()
	print(mb.RequestsTableColumns)
	print(mb.VariablesTableColiumns)
	
	############
	print("\n====  done ====\n")