#! /usr/bin/env python3
import os

if os.path.exists("/run/riego3") == False:
	os.mkdir("/run/riego3")

#**** cancelado porque se crea un file de solo lectura
#if os.path.isfile("/run/riego3/riego3Out.txt") == False:
#	with open('/run/riego3/riego3Out.txt','a') as f:
#		f.write('..')
#		f.close()
#Un ultima linea para Git
