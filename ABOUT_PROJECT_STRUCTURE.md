# 📂 Project Structure Guide - Campus Locker System

This document explains what each file and folder in our project does and why we need it. It's written for people who are new to coding or want to understand how our project is organized.

## 🎯 What is this project?

The Campus Locker System is a web application that helps manage package deliveries on campus. Think of it like a smart mailbox system where people can drop off and pick up packages using special codes.

---

## 📁 Main Project Structure

### 🏠 Root Directory (`/`)
This is the main folder that contains everything for our project.

```
📦 Campus Locker System
├── 📁 campus_locker_system/     # Main application code
├── 📁 docs/                     # Documentation and diagrams
├── 📁 scripts/                  # Helper scripts for setup
├── 📁 ssl/                      # Security certificates
├── 📁 venv/                     # Python virtual environment
├── 📄 README.md                 # Main project information
├── 📄 docker-compose.yml        # How to run the app in containers
└── 📄 other configuration files...
```

---

## 📋 File-by-File Breakdown

### 🔧 Configuration Files (Root Level)

#### `README.md`
- **What it is**: The main instruction manual for the project
- **Why we need it**: Tells new developers how to set up and use the project
- **What it contains**: Installation instructions, features, and how to get started

#### `docker-compose.yml` & `docker-compose.dev.yml`
- **What they are**: Instructions for running our app in "containers" (isolated environments)
- **Why we need them**: Makes it easy to run the app on any computer without setup hassles
- **Difference**: 
  - `docker-compose.yml` = Production version (for real use)
  - `docker-compose.dev.yml` = Development version (for coding/testing)

#### `.gitignore`
- **What it is**: A list of files that Git should ignore
- **Why we need it**: Prevents unnecessary files (like temporary files) from being saved to the project history
- **Examples**: Virtual environments, cache files, personal settings

#### `Makefile`
- **What it is**: A collection of shortcuts for common commands
- **Why we need it**: Instead of typing long commands, you can just type `make up` or `make test`
- **Example**: `make up` starts the entire application

#### `nginx.conf`
- **What it is**: Configuration for Nginx (a web server)
- **Why we need it**: Acts like a traffic director, sending web requests to the right place
- **Think of it as**: A receptionist at a hotel directing guests to the right rooms

### 📚 Documentation Files

#### `QUICK_START.md`
- **What it is**: Step-by-step guide to get the app running quickly
- **Why we need it**: New team members can start working in minutes, not hours
- **Perfect for**: People who just want to see the app work

#### `COLLABORATION_GUIDE.md`
- **What it is**: Rules and guidelines for working together on the project
- **Why we need it**: Keeps everyone on the same page about how to contribute
- **Contains**: Git workflow, code standards, communication guidelines

#### `DOCKER_DEPLOYMENT.md`
- **What it is**: Detailed instructions for deploying the app using Docker
- **Why we need it**: Step-by-step guide for putting the app on a real server
- **Perfect for**: When you want to make the app available to real users

---

## 📁 Main Application Directory (`campus_locker_system/`)

This folder contains all the actual code that makes our app work.

### 🐍 Python Files

#### `run.py`
- **What it is**: The "start button" for our application
- **Why we need it**: This file actually starts the web server
- **Think of it as**: The ignition key of a car

#### `requirements.txt`
- **What it is**: A shopping list of all the Python libraries our app needs
- **Why we need it**: Tells Python what extra tools to download
- **Example**: Like needing specific ingredients to bake a cake

#### `create_admin.py`
- **What it is**: A helper script to create administrator accounts
- **Why we need it**: Someone needs to be the "boss" who can manage everything
- **When to use**: When setting up the app for the first time

#### `config.py`
- **What it is**: All the settings and configurations for our app
- **Why we need it**: Like the settings menu on your phone - controls how everything works
- **Contains**: Database connections, email settings, security keys

### 🏗️ Application Structure (`app/` folder)

Our app follows a special pattern called "Hexagonal Architecture." Think of it like organizing a house into different rooms for different purposes.

#### `📁 presentation/`
- **What it is**: The "face" of our application - what users see and interact with
- **Why we need it**: Contains web pages, forms, and user interfaces
- **Think of it as**: The storefront of a shop - where customers interact

#### `📁 business/`
- **What it is**: The "brain" of our application - where all the important decisions happen
- **Why we need it**: Contains the core logic and rules of our locker system
- **Think of it as**: The manager's office - where business decisions are made

#### `📁 adapters/`
- **What it is**: Translators that help different parts of our app talk to each other
- **Why we need it**: Converts information between different formats
- **Think of it as**: Interpreters at the United Nations - help different systems communicate

#### `📁 persistence/`
- **What it is**: Where we save and retrieve data from the database
- **Why we need it**: Remembers information even when the app is turned off
- **Think of it as**: The filing cabinet - where all records are stored

#### `📁 services/`
- **What it is**: Helper functions that do specific jobs
- **Why we need it**: Breaks down complex tasks into smaller, manageable pieces
- **Think of it as**: Specialized departments in a company (HR, Accounting, etc.)

### 🗄️ Data Storage

#### `📁 databases/`
- **What it is**: Where all our data is stored (user accounts, locker information, etc.)
- **Why we need it**: The app needs to remember things between sessions
- **Think of it as**: A digital filing cabinet that never forgets

#### `📁 logs/`
- **What it is**: A diary of everything that happens in the app
- **Why we need it**: Helps us debug problems and understand how the app is being used
- **Think of it as**: Security camera footage - helps investigate issues

### 🧪 Testing

#### `📁 tests/`
- **What it is**: Code that tests our main code to make sure it works correctly
- **Why we need it**: Catches bugs before users find them
- **Think of it as**: Quality control in a factory

#### `pytest.ini`
- **What it is**: Configuration file for our testing system
- **Why we need it**: Tells the testing system how to run our tests
- **Contains**: Test settings and preferences

### 🐳 Containerization

#### `Dockerfile` & `Dockerfile.dev`
- **What they are**: Instructions for building a "container" (isolated environment) for our app
- **Why we need them**: Ensures the app runs the same way on every computer
- **Difference**:
  - `Dockerfile` = Production version (optimized for real use)
  - `Dockerfile.dev` = Development version (optimized for coding)

---

## 📁 Supporting Directories

### `📁 docs/`
Contains detailed documentation and diagrams

#### `C4_DIAGRAMS_README.md`
- **What it is**: Explains the visual diagrams of our app's architecture
- **Why we need it**: Helps developers understand how different parts connect
- **Think of it as**: Blueprints for a building

#### `c4-diagrams.puml`
- **What it is**: The actual diagram code that creates visual representations
- **Why we need it**: Creates pictures that are easier to understand than text

### `📁 scripts/`
Contains helpful automation scripts

#### `setup.sh`
- **What it is**: Automatic setup script for new developers
- **Why we need it**: Sets up everything needed to start coding
- **Think of it as**: An automatic installer

#### `test-deployment.sh`
- **What it is**: Script that tests if our deployment is working correctly
- **Why we need it**: Ensures everything is working before users see it
- **Think of it as**: A final inspection before opening a restaurant

### `📁 venv/`
- **What it is**: A separate Python environment just for this project
- **Why we need it**: Keeps our project's dependencies separate from other projects
- **Think of it as**: A private workshop with only the tools you need for this project

### `📁 ssl/`
- **What it is**: Security certificates for encrypted connections
- **Why we need it**: Protects data traveling between users and our app
- **Think of it as**: The lock on your front door

---

## 🔄 How Everything Works Together

1. **User visits the website** → Nginx receives the request
2. **Nginx forwards the request** → To our Flask application
3. **Flask app processes the request** → Using business logic
4. **If data is needed** → Persistence layer talks to the database
5. **Response is sent back** → Through the same chain, but in reverse
6. **Everything is logged** → For debugging and monitoring

---

## 🚀 Getting Started

If you're new to the project:

1. Read `README.md` first for the big picture
2. Follow `QUICK_START.md` to get the app running
3. Check `COLLABORATION_GUIDE.md` to understand how we work together
4. Use this file to understand what each part does

Remember: You don't need to understand everything at once. Start with getting the app running, then gradually explore different parts as you work on the project!

---

## 🤔 Still Have Questions?

- Check the `README.md` for more technical details
- Look at the `docs/` folder for visual diagrams
- Ask team members - we're here to help!

This project is designed to be beginner-friendly, so don't hesitate to explore and learn! 