# CV Finder

## 🌟 Overview
CV Finder is a platform designed to streamline the job search and hiring process by allowing job seekers to upload their resumes and employers to search for candidates based on specific criteria. The project leverages modern web development technologies to provide a robust, scalable, and user-friendly application.

## 🚀 Features
- **For Job Seekers**: 
  - 📄 Upload and manage resumes.
  - ✅ Update profile information periodically.
  - 📧 Receive email notifications to update data.

- **For Employers**: 
  - 🔍 Search for candidates using filters such as years of experience.
  - 📃 View detailed candidate profiles.

- **Admin**: 
  - 🔧 Manage the database and ensure data integrity.

## 🛠️ Technologies Used

### ✨ Frontend
- ✨ **React**: Handles the user interface and client-side logic.
- 🔬 **Argon Design System React**: A UI library providing pre-built components and styles.
- 🌐 **Bootstrap**: Ensures responsive design and consistency.

### 📝 Backend
- 📝 **Django**: A Python web framework for managing backend logic.
- 🔒 **Django REST Framework**: Provides APIs to communicate with the frontend.
- 🌐 **PostgreSQL**: Database for storing user data and resumes.

### 🧰 Development Tools
- 🛠️ **Docker**: Containerizes the application for consistent development and deployment.
- 🔁 **Docker Compose**: Manages multi-container setups for frontend, backend, and database.
- 🔧 **Git**: Version control for project collaboration.

### 📂 File Structure
- **`backend/`**: Contains the Django application with models, views, serializers, and API endpoints.
- **`frontend/`**: Houses the React application and static assets.
- **`docker-compose.yml`**: Defines and orchestrates the services (frontend, backend, database).

## 🖥️ Local Development Setup

### 📋 Prerequisites
- 📅 **Node.js**: Ensure the LTS version is installed.
- 🛠️ **Docker**: Ensure Docker and Docker Compose are installed.

### 🛠️ Steps
1. 🔧 Clone the repository:
   ```bash
   git clone <repository-url>
   cd cv-finder
   ```

2. ⚙️ Build and run the application using Docker Compose:
   ```bash
   docker-compose up --build
   ```

3. 🔗 Access the application:
   - Frontend: [http://localhost:3000](http://localhost:3000)
   - Backend: [http://localhost:1234](http://localhost:1234)

4. 🔢 To debug or check logs:
   ```bash
   docker logs <container-id>
   ```

## 🌐 Deployment
The project is containerized using Docker, making it suitable for deployment on cloud platforms like AWS, Azure, or GCP. Database and service scalability can be achieved by orchestrating containers using Kubernetes or similar tools.

## 👥 Contributors
This project is maintained and developed by the CV Finder team.

## ⚙️ Environment Setup
To set up the environment variables, create a `.env` file based on the provided `.env.example`:
1. Request the `.env.example` file from the project maintainer.
2. Rename it to `.env`:
   ```bash
   mv .env.example .env
   ```
3. Fill in the required values for the following variables:
   ```env
   # Database Configuration
   POSTGRES_DB=
   POSTGRES_USER=
   POSTGRES_PASSWORD=

   # Django Settings
   DJANGO_SUPERUSER_USERNAME=
   DJANGO_SUPERUSER_PASSWORD=
   DJANGO_SUPERUSER_EMAIL=
   ```
