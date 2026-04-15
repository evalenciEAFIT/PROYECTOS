#!/bin/bash

echo "==============================="
echo "Iniciando SAMA_DATA Dashboard..."
echo "==============================="

cd /home/edi/PROYECTOS/SAMA_DATA/DASHBOARD || exit
go run main.go
