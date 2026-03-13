# Ticket Frontend (React + Vite) - Build Stage
FROM node:20-alpine AS builder

WORKDIR /app

COPY ticket_frontend/package*.json ./
RUN npm ci

COPY ticket_frontend/ ./

# Build arguments für API URL
ARG VITE_TICKETS_API_BASE_URL=http://localhost:9000

ENV VITE_TICKETS_API_BASE_URL=${VITE_TICKETS_API_BASE_URL}

RUN npm run build

# Production Stage - Nginx
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY docker/ticket_frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 5174

CMD ["nginx", "-g", "daemon off;"]
