# syntax=docker/dockerfile:1
# ---- Build stage ----
FROM node:22-alpine AS build
WORKDIR /app

RUN apk add --no-cache libc6-compat
COPY package.json yarn.lock ./
RUN yarn install --frozen-lockfile --non-interactive

COPY prisma ./prisma
COPY src ./src
COPY nest-cli.json tsconfig.json tsconfig.build.json ./
RUN yarn prisma generate
RUN yarn build

# ---- Runtime stage ----
FROM node:22-alpine AS runtime
WORKDIR /app
ENV NODE_ENV=production

RUN apk add --no-cache wget openssl libc6-compat

COPY package.json yarn.lock ./
RUN yarn install --frozen-lockfile --non-interactive --production

COPY --from=build /app/dist ./dist
COPY --from=build /app/prisma ./prisma
RUN yarn prisma generate

EXPOSE 3000
USER node
CMD ["node", "dist/main.js"]
