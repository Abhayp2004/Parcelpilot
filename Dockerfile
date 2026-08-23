FROM python:3.11-slim AS backend

WORKDIR /app
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt
COPY backend /app/backend
COPY data /app/data
EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package.json .
COPY frontend/tsconfig.json .
COPY frontend/tsconfig.app.json .
COPY frontend/tsconfig.node.json .
COPY frontend/tailwind.config.ts .
COPY frontend/postcss.config.js .
COPY frontend/vite.config.ts .
RUN npm install
COPY frontend /app/frontend
RUN npm run build

FROM nginx:1.27-alpine AS frontend

COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=frontend-builder /app/frontend/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
