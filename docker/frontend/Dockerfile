# Frontend (React + Vite) - Build Stage
FROM node:20-alpine AS builder

WORKDIR /app

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./

# Build arguments für API URLs
ARG VITE_API_BASE_URL=http://localhost:8000
ARG VITE_TICKETS_UI_URL=http://localhost:5174

ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
ENV VITE_TICKETS_UI_URL=${VITE_TICKETS_UI_URL}

RUN npm run build

# Production Stage - Nginx
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY docker/frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 5173

CMD ["nginx", "-g", "daemon off;"]
