FROM node:20

# Set the working directory
WORKDIR /app

# Copy package.json and package-lock.json for dependency installation
COPY package.json ./

# Install all dependencies
RUN npm install --legacy-peer-deps

# Copy the application source code
COPY . .

# Expose the port React runs on
EXPOSE 3000

# Start the React application
CMD ["npm", "start"]
