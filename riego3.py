#! /usr/bin/env python3
import os
import RPi.GPIO as GPIO
import time
import pymysql

alertaTanqueSuperior = 32 #pin de entrada 0/1 que indica que hay agua en el tanque superior
alertaTanqueInferior = 36
bomba = 40

GPIO.setmode(GPIO.BOARD)

conexion = pymysql.connect(host="localhost",
	user="raul",
	password="riego1",
	database="riego")
cursor = conexion.cursor()

flipFlop = 0
fechaActual = ""
horaActual = ""
estadoActual = "Inactivo" #Los estados pueden ser inactivo, apagando, activo
carrusel = 0 #Carrusel es una variable que durante el riego cicla indicando la accion en curso


fMin = 0
fSec = 0
fDiaDeSemana = 0

#algo mas para hacerlo diferente

#class accionPendiente:
#	def __init__(self, tiempo, accion):
#		self.tiempoRestante = tiempo
#		self.accion = accion
#	def reducirUnMinuto(self):
#		if (self.tiempoRestante > 0):
#			self.tiempoRestante = self.tiempoRestante -1
#class colaDeAcciones:
#	def __init__(self):
#		self.items=[]
#	def encolar(self,x):
#		self.items.append(x)
#	def desencolar(self):
#		try:
#			return self.items.pop(0)
#		except:
#			raise ValueError("La cola esta vacía")
#	def esVacia(self):
#		return self.items == []
#	def actual(self):
#		return self.items[0]

def faltaAgua():
	if not(GPIO.input(alertaTanqueInferior)):
		return 1
	else:
		return 0

def actualizarHora():
	global fMin
	global fechaActual
	global horaActual	
	#global fSec
	global fDiaDeSemana
	seconds = time.time()
	fMin = time.localtime(seconds).tm_min
	fechaActual= "'" + str(time.localtime(seconds).tm_year) + "-" + str(time.localtime(seconds).tm_mon) + "-" + str(time.localtime(seconds).tm_mday) + "'"
	horaActual="'" + str(time.localtime(seconds).tm_hour) + ":" + str(time.localtime(seconds).tm_min) + ":" + str(time.localtime(seconds).tm_sec) + "'"
	#fSec = time.localtime(seconds).tm_sec
	fDiaDeSemana = time.localtime(seconds).tm_wday	

def registrarClima():
	#Esta rutina intenta agregar una linea de clima a la base de datos
	temperatura = 24
	humedad = 49
	lluvia = 0
	try:
		f = open("/run/riego3/weather3.txt","r")
		for linea in f.readlines():
			palabras = linea.split(' ')
			#for palabra in linea.split(' '):
			#	reportar(palabra)
			if "Temp" in palabras[0]:
				try:
					temperatura = int((palabras[3].replace("(","")))
				except:
					pass
			if "Hum" in palabras[1]:
				try:
					humedad = int((palabras[2].replace("%","")))					
				except:
					pass
			if "ain" in linea:
				lluvia = 2
			if "izzle" in linea:						
				lluvia = 1
				
				f.close()
	except:
		pass
	registros = "INSERT into registroClimatico (fecha, hora, lluvia, temperatura, humedad) "\
		"values (" + fechaActual + "," + horaActual + "," + str(lluvia) + "," + str(temperatura) + "," + str(humedad) + ");"
	#print(registros)
	cursor.execute(registros)
	conexion.commit()

	
#def evaluarProgramas()
#	pass

def accionPorMinuto():
	#Esta rutina se ejecuta una vez por minuto
	actualizarHora()
	if (fMin in [13,43]):
		try:
			os.system('weather -v SAZN > /run/riego3/weather3.txt&')
		except:
			pass		
	if (fMin in [15,45]): #Permite dos minutos para que llegue la información climática
		
		if (horaActual == 0 and fMin == 15): #Se ejecuta una vez por día, pasada la medianoche
			#comandoSql = "SELECT @var := MAX(fecha) from registroClimatico; DELETE FROM registroClimatico WHERE fecha < DATE_ADD(@var, INTERVAL -30 DAY)"
			comandoSql = " DELETE FROM registroClimatico WHERE fecha < DATE_ADD(CURRENT_DATE, INTERVAL -30 DAY)"
			cursor.execute(comandoSql)
			conexion.commit()
			registrarClima() #Llama a la rutina que inserta una linea de información climatica, previo consultar al aeropuerto
 
	if (estadoActual == 0):
		#evaluarProgramas()
		pass



GPIO.setmode(GPIO.BOARD)

if os.path.exists("/run/riego3") == False:
	os.mkdir("/run/riego3")

#ca = colaDeAcciones()
#ap = accionPendiente(5, "regarZona1")
#ca.encolar(ap)
#ap = accionPendiente(3, "espera")
#ca.encolar(ap)

#while not (ca.esVacia()):
#	i= (ca.actual().tiempoRestante)
#	if (i>0):
#		ca.actual().reducirUnMinuto()
#		print (str(i) + ": " + ca.actual().accion)
#	else:
#		ap=ca.desencolar()


try:
	GPIO.setup(alertaTanqueSuperior, GPIO.IN)
	GPIO.setup(alertaTanqueInferior, GPIO.IN)
	aguaEnTanqueAnterior = -1
	aguaEnTanque = 0
	time.sleep(30)  #Pausa inicial al arrancar la computadora
	#Ciclo principal del programa
	while True:
		# **** Actualizar variables de la hora del sistema
		seconds = time.time()	
		fSec = time.localtime(seconds).tm_sec

	#**** Rutina que publica el estado a MQTT
		aguaEnTanque = faltaAgua()
		if (aguaEnTanque != aguaEnTanqueAnterior):
			aguaEnTanqueAnterior = aguaEnTanque
			os.system('mosquitto_pub -h localhost -t riego/aguaEnTanque -m ' + ["OK","Falta_agua"][aguaEnTanque])
	
	#**** Rutina que evalúa si pasó un minuto desde la ultima vez	
		
		if (fSec > 2): 
			flipFlop = 0						
		else:		
			if (flipFlop == 0):
				flipFlop=1
				accionPorMinuto()
				



		time.sleep(.5)
finally:
        #cleanup
        GPIO.cleanup()

#******************************************



