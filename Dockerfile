# Multi-stage build con Python y Node.js para la app React + API Express
FROM node:20-slim AS base

# Instalar Python 3 y SQLite para el pipeline de datos
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalar dependencias de Python
COPY requirements.txt pyproject.toml ./
RUN pip3 install --no-cache-dir -r requirements.txt --break-system-packages

# Instalar dependencias de Node.js
COPY package.json package-lock.json* bun.lock* ./
RUN npm install --legacy-peer-deps

# Copiar el código del proyecto
COPY . .

# Ejecutar el pipeline ETL inicial para poblar la base de datos SQLite
RUN python3 -m src.pipeline

# Compilar los estáticos de React (Vite)
RUN npm run build

# Variables de entorno de producción
ENV NODE_ENV=production
ENV PORT=3000

# Exponer el puerto de la aplicación web
EXPOSE 3000

# Iniciar el servidor Full-Stack Node/Express
CMD ["npm", "start"]