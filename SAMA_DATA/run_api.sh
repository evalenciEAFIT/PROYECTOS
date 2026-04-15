#!/bin/bash

echo "==============================="
echo "Iniciando SAMA_DATA API..."
echo "==============================="

cd /home/edi/PROYECTOS/SAMA_DATA/API || exit
go run main.go
