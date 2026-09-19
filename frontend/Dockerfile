FROM node:24.21.0-alpine3.24

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

COPY index.html tsconfig.json vite.config.ts ./
COPY src ./src
COPY tests ./tests

RUN chown -R node:node /app
USER node

EXPOSE 5173
CMD ["npm", "run", "dev"]
