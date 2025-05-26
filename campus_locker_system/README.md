# Campus Locker System - Team I

## 1. Project Overview

*   **Purpose:** This project is a browser-based campus locker system. It allows senders (like students or couriers) to deposit parcels and recipients to pick them up 24/7 using a one-time PIN.
*   **Technology Stack:** The core system is built with Python and the Flask web framework. It uses an SQLite database for storage and MailHog for local email testing (to simulate sending PINs).
*   **Team:** Developed by Team I (Pauline Feldhoﬀ, Paul von Franqué, Asma Mzee, Samuel Neo, Gublan Dag) as part of the Digital Literacy IV: Software Architecture course.
*   **Note:** This is an initial implementation focusing on core deposit and pickup functionalities. All locker hardware is simulated.

## 2. Getting Started: Setup & Running the Application

Follow these steps to get the application running on your local machine (macOS is the primary demo environment, but it should work on other systems with Python).

### Prerequisites:
*   **Python 3.7+:** Ensure you have Python installed. You can check by opening a terminal and typing `python --version` or `python3 --version`.
*   **pip:** Python's package installer, usually comes with Python.
*   **MailHog (for email testing):**
    *   MailHog is a tool that catches emails sent by the application locally, so you don't need a real email server for development.
    *   The easiest way to run MailHog is using Docker:
        ```bash
        docker run -d -p 1025:1025 -p 8025:8025 mailhog/mailhog
        ```
    *   After running this, you can view received emails by opening your web browser and going to `http://localhost:8025`.
    *   If you don't have Docker, you can download MailHog directly from its GitHub releases page.

### Setup Steps:

1.  **Clone/Download the Code:**
    *   If you have git, clone the repository. Otherwise, download the source code files and place them in a directory, let's call it `campus_locker_system`.

2.  **Navigate to Project Directory:**
    *   Open your terminal and change to the project directory:
        ```bash
        cd path/to/campus_locker_system
        ```

3.  **Create a Virtual Environment (Recommended):**
    *   It's good practice to keep project dependencies separate.
        ```bash
        python3 -m venv venv
        source venv/bin/activate  # On Windows: venv\Scripts\activate
        ```
    *   You should see `(venv)` at the beginning of your terminal prompt.

4.  **Install Dependencies:**
    *   Install all the required Python packages:
        ```bash
        pip install -r requirements.txt
        ```
    *   This will install Flask, SQLAlchemy (for the database), Bcrypt (for password hashing), Flask-Mail, and Pytest (for testing).

5.  **Database Setup:**
    *   The application uses an SQLite database file (`campus_locker.db`). This file will be automatically created in the main `campus_locker_system` directory the first time you run the application. The necessary tables inside it will also be created automatically.

6.  **Create an Admin User:**
    *   To access admin functionalities (though limited in this version), you need an admin user.
    *   Run the provided script from the `campus_locker_system` directory:
        ```bash
        python create_admin.py your_admin_username your_admin_password
        ```
        Replace `your_admin_username` and `your_admin_password` with your desired credentials. For example: `python create_admin.py admin adminpass123`

7.  **Run the Application:**
    *   Start the Flask development server:
        ```bash
        python run.py
        ```
    *   You should see output indicating the server is running, usually on `http://127.0.0.1:5000/`.

8.  **Access the Application:**
    *   Open your web browser and go to `http://127.0.0.1:5000/deposit` to deposit a parcel.
    *   Go to `http://127.0.0.1:5000/pickup` to pick up a parcel.
    *   Go to `http://127.0.0.1:5000/admin/login` to log in as an admin.

## 3. Project Structure Explained

The project code is organized into several main parts within the `campus_locker_system` directory:

*   **`app/`**: This is the heart of the Flask application.
    *   **`__init__.py`**: Initializes the Flask application, database, mail system, and ties different parts together.
    *   **`config.py`**: Contains configuration settings (like database location, mail server settings).
    *   **`application/`**: Contains the "business logic" or "brains" of the system.
        *   `services.py`: Functions that perform core tasks like assigning a locker, generating PINs, processing pickups, and verifying admin users.
    *   **`persistence/`**: Manages data storage.
        *   `models.py`: Defines the structure of the database tables (Lockers, Parcels, Admin Users, Audit Logs) using SQLAlchemy.
    *   **`presentation/`**: Handles what the user sees and interacts with (the user interface).
        *   `routes.py`: Defines the web page URLs (like `/deposit`, `/pickup`) and connects them to Python functions that decide what to do and what HTML to show.
        *   `templates/`: Contains HTML files that structure the web pages.
            *   `admin/`: HTML files specific to admin pages.
*   **`tests/`**: Contains automated tests written using Pytest to check if different parts of the application work correctly.
*   **`create_admin.py`**: The script mentioned earlier to create an admin user.
*   **`run.py`**: A simple script to start the Flask development server.
*   **`requirements.txt`**: Lists all the Python packages the project depends on.
*   **`campus_locker.db`**: The SQLite database file (created when the app runs).
*   **`logs/`**: Contains log files (e.g., `campus_locker.log`) that record application activity and errors. (This directory is created when the app runs).

## 4. Key Features Implemented

*   **Parcel Deposit:** Senders can specify parcel size and recipient email. The system assigns a locker and generates a unique 6-digit PIN.
*   **PIN Display & Email:** The PIN is shown on-screen to the sender and also emailed to the recipient (via MailHog for local viewing).
*   **Parcel Pickup:** Recipients use the 6-digit PIN to pick up their parcel. PINs expire after 24 hours.
*   **Secure PIN Storage:** PINs are not stored directly. Instead, a secure hash (salted SHA-256) of the PIN is stored, making it very difficult to reverse.
*   **Admin Login:** A basic login system for administrators. Admin passwords are also securely hashed (using bcrypt).
*   **Automated Tests:** Basic tests ensure core features are working as expected.

## 5. Architectural Choices (Why things are built this way)

*   **Flask Framework:** A lightweight and flexible Python web framework, good for building web applications quickly.
*   **Layered Architecture:** The code is divided into layers (Presentation, Application, Persistence). This helps keep things organized:
    *   *Presentation* handles user interaction.
    *   *Application* handles the main logic and tasks.
    *   *Persistence* handles database interactions.
    This separation makes the code easier to understand, test, and modify.
*   **SQLAlchemy ORM:** Used for interacting with the SQLite database. It allows developers to work with database records as Python objects, simplifying database operations.
*   **SQLite Database:** A simple file-based database, easy to set up and use for local development and small applications.
*   **MailHog:** For testing email functionality locally without needing a real email server. This is very convenient for development.
*   **Security:** PINs and admin passwords are not stored as plain text. They are "hashed" using strong algorithms (SHA-256 for PINs, bcrypt for admin passwords) to protect them even if the database file is compromised.

## 6. How to Run Tests

1.  Make sure you have activated your virtual environment (`source venv/bin/activate`).
2.  Navigate to the project root directory (`campus_locker_system`).
3.  Run pytest from the terminal:
    ```bash
    python -m pytest
    ```
    Or simply:
    ```bash
    pytest
    ```
    You should see output indicating the number of tests passed.

## 7. Potential Next Steps & Future Improvements

This initial version covers the core requirements. Based on the original project charter, future enhancements could include:

*   **Full Audit Trail (FR-07):** Logging every deposit, pickup, and admin action.
*   **Advanced Admin Functions:**
    *   Re-issuing PINs (FR-05).
    *   Flagging lockers as "out of service" (FR-08).
    *   Reporting missing items (FR-06).
*   **Web-Push Notifications (FR-03):** Real-time notifications in the browser, in addition to email.
*   **Reminder Notifications (FR-04):** Automatic reminders after 24 hours of occupancy.
*   **Nightly Backups:** Regular backups of the SQLite database.
*   **Enhanced UI/UX:** Improving the user interface and experience, including keyboard-only navigation.
*   **More Comprehensive Testing:** Adding more unit and end-to-end tests.
*   **Dockerization:** Packaging the entire application with Docker Compose for easy one-command deployment (`docker-compose up`).

---
This README provides a starting point for understanding and running the Campus Locker System.
```
