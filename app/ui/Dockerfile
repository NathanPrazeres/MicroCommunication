# Use an official Node.js image as the base
FROM node:20-alpine

# Set working directory
WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the source code
COPY . .

# Build the frontend
RUN npm run build

# Expose the port the app runs on
EXPOSE 4173

# Start the frontend
CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0"]
