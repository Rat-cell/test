# Campus Locker System - Team I

TO DO:

All html need to be updated
Think about how a admin is to be registered etc.
Sms push notification needs to be implemented (look for a service like mailbag in dockers

Move the databases to a database layer as well as the config file, as they need to be always safe for each client separately
Find out how to initialise and set up the entire thing

Generally move all vent thins to dockers

Basically make sure all tests and can be run in dockers not the vent

Also make sure the entire app is initialised set up and installed when opening the docker container
1. Initial Dockerization and Setup
* Helped you Dockerize the Flask-based campus locker system.
* Set up Docker Compose to run both the app and MailHog for email testing.
* Resolved port conflicts by changing port mappings in docker-compose.yml.
* Ensured the app and MailHog were accessible on their respective ports.
6. Initialization Automation
* Ensured all initialization (including admin creation) is handled automatically when Docker is spun up.
* Moved admin creation to run via the Dockerfile’s CMD.

## Version 1.81 (Changelog)

- **Log Management Improvements:**
  - Standardized all application logs to the root-level `logs/` folder.
    _Why/How:_ Prevents confusion and ensures all logs are in one place by updating the logging config and cleaning up duplicates.
  - Documented log rotation policy (10 KB per file, 10 backups, oldest deleted on rotation).
    _Why/How:_ Ensures logs don't grow indefinitely and are easy to manage; added clear documentation for maintainers.
  - Added best practices for log monitoring and configuration.
    _Why/How:_ Helps future developers/admins understand how to monitor and tune logging for their needs.
  - Removed duplicate/legacy log folders and files.
    _Why/How:_ Reduces clutter and risk of confusion or missed logs.
  - Clearly labeled that only main application logs are stored in `logs/`; audit logs are in the database.
    _Why/How:_ Clarifies log purpose and storage for maintainers and auditors.
- **Testing and Structure:**
  - Split and reorganized tests by user flow and edge cases for clarity and maintainability.
    _Why/How:_ Makes it easier to find, run, and extend tests for specific flows or features.
  - Added a dedicated admin log flow test to ensure audit logging of admin actions.
    _Why/How:_ Verifies that admin actions are properly recorded for security and traceability.
  - Confirmed all test files are connected and documented.
    _Why/How:_ Ensures no orphaned or untested flows remain after restructuring.
  - **Fixed all expired vs return_to_sender test issues:**
    _Why/How:_ Updated tests to expect the correct status (`return_to_sender` and `awaiting_collection`) for overdue parcels, matching the current application logic and ensuring all tests pass.
- **Documentation:**
  - Updated the main README to include all log and test documentation in one place.
    _Why/How:_ Centralizes project knowledge for easier onboarding and reference.
  - Removed the separate `logs/README.md` for simplicity and clarity.
    _Why/How:_ Avoids duplication and ensures all documentation is up to date.
  - Added detailed explanations of log types, rotation, and best practices.
    _Why/How:_ Helps maintainers understand and manage logs effectively.
- **Known Issues:**
  - Some tests expect a parcel status of `expired` after overdue, but the system now uses `return_to_sender`. This is a known mismatch between code and test expectations.

## Running with Docker vs. Local Setup

You can run the Campus Locker System in two ways:

### 1. **With Docker (Recommended for Quick Start & Consistency)**
- **All dependencies** (Python, packages, MailHog, etc.) are installed inside Docker containers.
- **You only need Docker and Docker Compose** installed on your computer.
- No need to install Python, pip, or any Python packages on your host machine.
- Use this approach if you want to avoid local setup or ensure a consistent environment.
- See the [Docker Setup](#docker-setup) section below for instructions.

### 2. **Local Setup (Recommended for Development & Debugging in VS Code)**
- **You must install Python, pip, and all dependencies** on your host machine.
- This allows you to use VS Code's Python features (linting, debugging, test discovery, etc.).
- Use this approach if you want to develop, debug, or run tests directly in your editor.
- See the [macOS Setup](#macos-setup) or [Windows Setup](#windows-setup) sections below for instructions.

**Summary:**
- **Docker:** Fastest way to get started, no local Python setup needed.
- **Local:** Best for development and using advanced editor features.

---

## Setup and Development Environment

**Recommended Workflow for All Users:**

1. **Clone the repository using Visual Studio Code.**
   - This ensures you have the latest code and can use all of VS Code's features.
2. **Run the application and services using Docker.**
   - This installs all dependencies inside containers, so you don't need to set up Python or packages on your computer.
3. **Use VS Code for editing, running, and testing code.**
   - You can open, edit, and manage the codebase in VS Code. You can also run tests inside the Docker container, or set up VS Code to use the container as a development environment (with the Remote - Containers extension, if desired).

**Unless you specifically want to develop or debug outside Docker, you do NOT need to install Python or dependencies locally.**

---

### macOS Setup

#### 1. Clone the Repository Using VS Code
- Open Visual Studio Code.
- Click on the **Source Control** icon in the Activity Bar on the left (or press `Cmd+Shift+G`).
- Click **"Clone Repository"** at the top, or open the Command Palette (`Cmd+Shift+P`) and type `Git: Clone`.
- Paste the repository URL (e.g., `https://github.com/your-org/campus_locker_system.git`) and press Enter.
- Choose a local folder to save the project.
- When prompted, click **"Open"** to open the cloned project in VS Code.

#### 2. Install Docker Desktop for Mac
- Download and install [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/).
- Start Docker Desktop.

#### 3. Build and Run the Application and Services with Docker
- In the project folder, open a terminal and run:
  ```bash
  docker-compose up --build
  ```
- This will build the application image, install all dependencies, and start the app and MailHog services.
- If you see a port conflict error, make sure nothing else is running on port 5000.

#### 4. Access the Application and MailHog
- The app will be available at [http://127.0.0.1:5000/](http://127.0.0.1:5000/)
- MailHog UI is at [http://localhost:8025](http://localhost:8025)

#### 5. Use VS Code for Editing and Testing
- Open the project folder in VS Code (`File > Open Folder...`).
- Edit code, run tests, and use all VS Code features as needed.
- To run tests inside the Docker container, you can use:
  ```bash
  docker-compose exec app pytest
  ```
- (Optional) For advanced development, use the Remote - Containers extension to develop directly inside the container.

---

### Windows Setup

#### 1. Clone the Repository Using VS Code
- Open Visual Studio Code.
- Click on the **Source Control** icon in the Activity Bar on the left (or press `Ctrl+Shift+G`).
- Click **"Clone Repository"** at the top, or open the Command Palette (`Ctrl+Shift+P`) and type `Git: Clone`.
- Paste the repository URL (e.g., `https://github.com/your-org/campus_locker_system.git`) and press Enter.
- Choose a local folder to save the project.
- When prompted, click **"Open"** to open the cloned project in VS Code.

#### 2. Install Docker Desktop for Windows
- Download and install [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/).
- Start Docker Desktop.

#### 3. Build and Run the Application and Services with Docker
- In the project folder, open a terminal (Command Prompt, PowerShell, or Git Bash) and run:
  ```cmd
  docker-compose up --build
  ```
- This will build the application image, install all dependencies, and start the app and MailHog services.
- If you see a port conflict error, make sure nothing else is running on port 5000.

#### 4. Access the Application and MailHog
- The app will be available at [http://127.0.0.1:5000/](http://127.0.0.1:5000/)
- MailHog UI is at [http://localhost:8025](http://localhost:8025)

#### 5. Use VS Code for Editing and Testing
- Open the project folder in VS Code (`File > Open Folder...`).
- Edit code, run tests, and use all VS Code features as needed.
- To run tests inside the Docker container, you can use:
  ```cmd
  docker-compose exec app pytest
  ```
- (Optional) For advanced development, use the Remote - Containers extension to develop directly inside the container.

---

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
        source venv/bin/activate
        ```
    *   You should see `(venv)` at the beginning of your terminal prompt.

4.  **Install Dependencies:**
    *   Install all the required Python packages:
        ```bash
        pip install -r requirements.txt
        ```
    *   This will install Flask, SQLAlchemy (for the database), Bcrypt (for password hashing), Flask-Mail, and Pytest (for testing).

5.  **Database Setup:**
    *   The application uses SQLite databases. The app will create `campus_locker.db` and `campus_locker_audit.db` in the `databases/` folder on first run.
    *   The necessary tables within these databases will also be created automatically.

6.  **Create an Admin User:**
    *   To access admin functionalities (though limited in this version), you need an admin user.
    *   Run the provided script from the `campus_locker_system` directory:
        ```bash
        python create_admin.py your_admin_username your_admin_password
        ```
        Replace `your_admin_username` and `your_admin_password` with your desired credentials. For example: `python create_admin.py admin adminpass123`.
        *   **Note:** The admin password must be at least 8 characters long.

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
*   **`databases/`: Contains all database files (`campus_locker.db`, `campus_locker_audit.db`).
*   **`logs/`**: Contains log files (e.g., `campus_locker.log`) that record application activity and errors. (This directory is created when the app runs).

## 4. Key Features Implemented

*   **Parcel Deposit:** Senders can specify parcel size and recipient email. The system assigns a locker and generates a unique 6-digit PIN.
*   **PIN Display & Email:** The PIN is shown on-screen to the sender and also emailed to the recipient (via MailHog for local viewing).
*   **Parcel Pickup:** Recipients use the 6-digit PIN to pick up their parcel. PINs expire after 24 hours.
*   **Secure PIN Storage:** PINs are not stored directly. Instead, a secure hash (salted SHA-256) of the PIN is stored, making it very difficult to reverse.
*   **Admin Login:** A basic login system for administrators. Admin passwords are also securely hashed (using bcrypt).
*   **Audit Trail:** Records key system events like parcel deposits, pickups (successful and failed attempts), admin logins/logouts, and email notification status. These logs are viewable by administrators.
*   **Locker Status Management (Admin):** Administrators can view all lockers and change their status (e.g., mark as 'out_of_service' or return to 'free' if empty). This helps manage faulty or reserved lockers.
*   **Parcel Interaction Confirmation (Backend Logic):** Supports backend logic for a locker client to allow senders to retract a mistaken deposit or recipients to dispute a pickup within a short window. This introduces new parcel statuses ('retracted_by_sender', 'pickup_disputed') and a locker status ('disputed_contents'). These new states currently require administrative follow-up for full resolution.
*   **Report Missing Item (FR-06):** Allows administrators to mark a parcel as 'missing'. Also provides an API endpoint for a locker client to signal a recipient reporting a parcel as missing immediately after a pickup attempt. This sets the parcel status to 'missing' and typically takes the associated locker out of service for investigation.
*   **Automated Tests:** Basic tests ensure core features are working as expected.

### 4.1. Viewing Audit Logs

Logged-in administrators can view a trail of system events to monitor activity. This includes records of:
*   Parcel deposits (initiated, successful, failed)
*   Parcel pickups (initiated, successful, failed due to invalid PIN or expiry)
*   Admin logins (successful, failed) and logouts
*   Email notification sending status

To view the audit logs, navigate to: `/admin/audit-logs`

The log displays the timestamp (UTC), the type of action, and a details field (in JSON format) providing more context about the event. The page shows the latest 100 entries.

### 4.2. Managing Locker Statuses (FR-08)

Administrators have the ability to manage the operational status of individual lockers. This is useful for handling maintenance, reservations, or other situations requiring a locker to be temporarily unavailable.

*   **Access:** Logged-in administrators can navigate to `/admin/lockers` to view a list of all lockers, their sizes, and their current operational statuses (e.g., 'free', 'occupied', 'out_of_service').
*   **Actions Available:**
    *   **Mark as 'Out of Service':** Any locker can be marked as 'out_of_service'. If it was 'free', it will no longer be assigned for new parcel deposits. If it was 'occupied', it remains 'out_of_service' (and the parcel can still be picked up; the locker will then be 'out_of_service' and empty).
    *   **Mark as 'Free':** A locker currently marked 'out_of_service' can be returned to 'free' status, making it available for new deposits. This action is only permitted if the locker does not contain an active ('deposited') parcel.
*   **Auditing:** All changes to locker statuses made by administrators are recorded in the audit log.

### 4.3. API Endpoints for Locker Client Interaction

The system now includes a set of API endpoints under the `/api/v1/` prefix, intended for use by a separate locker hardware client system:

*   **`POST /api/v1/deposit/<parcel_id>/retract`**: Called by the locker client if a sender indicates they made a mistake immediately after depositing a parcel. This marks the parcel as 'retracted_by_sender' and frees the locker (if it was not 'out_of_service').
*   **`POST /api/v1/pickup/<parcel_id>/dispute`**: Called by the locker client if a recipient indicates an issue (e.g., wrong item, empty locker) immediately after a pickup attempt. This marks the parcel as 'pickup_disputed' and the locker as 'disputed_contents', requiring admin attention.
*   **`POST /api/v1/parcel/<int:parcel_id>/report-missing`**: Called by the locker client if a recipient, immediately after opening a locker with a valid PIN, reports that the parcel is not there or is incorrect. This sets the parcel status to 'missing' and may take the locker out of service.

These endpoints are designed for machine-to-machine communication and do not have a direct user interface in this web application. Authentication for these endpoints would be required in a production system.

### 4.4. Managing and Reporting Missing Parcels (FR-06)

Administrators can manage parcels that are reported or suspected to be missing. This complements the API endpoint that allows a locker client to report a missing parcel on behalf of a recipient.

*   **Viewing Parcel Details:** Admins can view detailed information for any parcel by navigating to `/admin/parcel/<parcel_id>/view`. This page can be accessed via links from the main `/admin/lockers` page if a parcel is associated with a locker.
*   **Marking a Parcel as Missing:** From the parcel detail page, if a parcel is in a state like 'deposited' or 'pickup_disputed', an admin can mark it as 'missing'. 
    *   This action changes the parcel's status to 'missing'.
    *   If the parcel was 'deposited' in a locker, or its pickup was disputed, the associated locker will typically be set to 'out_of_service' to allow for inspection.
    *   This administrative action is recorded in the audit log.

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

## 6.1. Test Overview

The `tests/edge_cases/` directory contains edge case tests for the most critical user and API flows. Each test is commented for clarity:

### test_retract_edge_cases.py
- **test_api_retract_deposit_parcel_not_found**: API should return 404 or 400 when trying to retract a non-existent parcel.
- **test_api_retract_deposit_not_deposited**: API should return 400 or 409 when trying to retract a parcel that is not in 'deposited' state (already picked up).
- **test_api_retract_deposit_locker_was_oos**: Retracting a deposit when the locker is out_of_service should succeed, but locker remains out_of_service.

### test_dispute_edge_cases.py
- **test_dispute_pickup_parcel_not_found**: Disputing pickup for a non-existent parcel should return an error.
- **test_dispute_pickup_parcel_not_picked_up**: Disputing pickup for a parcel that has not been picked up should return an error.

### test_pickup_edge_cases.py
- **test_process_pickup_fails_for_retracted_parcel**: Picking up a parcel that has already been retracted should fail with 'Invalid PIN'.
- **test_process_pickup_fails_for_disputed_parcel**: Picking up a parcel that has been disputed should fail with 'Invalid PIN'.

### test_missing_edge_cases.py
- **test_report_missing_by_recipient_fail_not_found**: Reporting a missing parcel with a non-existent ID should return an error.
- **test_report_missing_by_recipient_fail_wrong_state**: Reporting a missing parcel in the wrong state (picked_up or expired) should return an error.

### test_sensor_edge_cases.py
- **test_sensor_data_missing_has_contents**: Submitting sensor data with missing 'has_contents' field should return 400.
- **test_sensor_data_invalid_type**: Submitting sensor data with non-boolean 'has_contents' should return 400.
- **test_sensor_data_nonexistent_locker**: Submitting sensor data for a non-existent locker should return 404 or 400.

### test_pin_reissue_edge_cases.py
- **test_old_pin_invalid_after_regeneration**: After PIN regeneration, the old PIN should be invalid and only the new PIN works.

**Edge Case Coverage vs. Requirements**

The following edge case requirements are **not yet directly covered** by the current tests and should be considered for future test development:
- Configurable system behaviors (e.g., changing pickup time limit, locker dimensions, notification preferences via config)
- Direct locker status updates via API or sensor integration
- Email/mobile confirmation before sending PINs/codes
- PIN reissue logic (ensuring new PIN invalidates old, only within pickup window)
- Return-to-sender process after pickup window expiry
- Explicit test that new PIN expires old PINs

The current edge case tests focus on invalid state transitions and error handling for the main user and API flows.

See the comments in each test file for more details on the scenarios covered.

## 7. Potential Next Steps & Future Improvements

This initial version covers the core requirements. Based on the original project charter, future enhancements could include:

*   **Full Audit Trail (FR-07):** Logging every deposit, pickup, and admin action (currently partially implemented).
*   **Advanced Admin Functions:**
    *   Re-issuing PINs (FR-05).
    *   Flagging lockers as "out_of_service" (FR-08 - basic version implemented).
    *   Reporting missing items (FR-06).
    *   Admin resolution workflows for new parcel/locker states (e.g., 'retracted_by_sender', 'pickup_disputed', 'disputed_contents').
*   **Web-Push Notifications (FR-03):** Real-time notifications in the browser, in addition to email.
*   **Reminder Notifications (FR-04):** Automatic reminders after 24 hours of occupancy.
*   **Nightly Backups:** Regular backups of the SQLite database.
*   **Enhanced UI/UX:** Improving the user interface and experience, including keyboard-only navigation.
*   **More Comprehensive Testing:** Adding more unit and end-to-end tests.
*   **Dockerization:** Packaging the entire application with Docker Compose for easy one-command deployment (`docker-compose up`).

## Appendix: Changelog

### Recent Changes

- Refactored tests for robustness and best practices:
  - Split admin/anonymous access tests for session isolation.
  - Used substring assertions for flashed messages and sensor data to avoid issues with HTML formatting/escaping.
  - Matched error codes and messages to actual Flask/API behavior.
  - Ensured all tests pass with the current codebase and configuration.
- Improved test coverage and reliability for admin locker management, sensor data display, and error handling.
- Updated test and code comments for clarity and maintainability.
- Added MailHog Docker Compose configuration for local email testing.
- Cleaned up impossible code paths and tests (e.g., `deposited_at is None` for parcels).

For a detailed commit history, see the project's git log.

## Application Logs

All application logs are stored in the root-level `logs/` folder. This includes:
- `campus_locker.log` and its rotated versions: Main application logs (info, warnings, errors) from the Flask app and its services.
- **Log rotation policy:**
    - Each log file is capped at 10 KB (10,240 bytes).
    - Up to 10 backup log files are kept (`campus_locker.log.1` through `.10`).
    - When the main log exceeds 10 KB, it is rotated and the oldest log is deleted.
- **Best practices:**
    - Monitor log file sizes and adjust `maxBytes` and `backupCount` in the logging configuration as needed for your deployment (e.g., increase for production).
    - Regularly review logs for errors and warnings.
    - Only main application logs are stored here. **Audit logs** are stored in the database table `audit_log` and are not written to files.

---
This README provides a starting point for understanding and running the Campus Locker System.
```
