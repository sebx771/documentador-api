import os
import time

nombre= input("1)Sebastian o 2)Santiago: ")
correo= ""
if nombre != "1" and nombre != "2":
    print("Opción no válida para el nombre. Por favor, elige 1 o 2.")
    exit(1)
if nombre == "1":
    nombre= "Sebastian"
    correo= "sebascova18@gmail.com"

if nombre == "2":
    nombre= "Santiago"
    correo= "santicova18@gmail.com"



print("Actualizando usuario git...")
os.system(f'git config --global user.name "{nombre}"')
print("Usuario git actualizado a:", nombre)
print("Actualizando correo git...")
time.sleep(2)
os.system(f'git config --global user.email "{correo}"')
print("Correo git actualizado a:", correo)
