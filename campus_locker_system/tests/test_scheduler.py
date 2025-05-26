import pytest
from flask import Flask
from flask_apscheduler import APScheduler
from app import create_app, scheduler as global_scheduler # Import the global scheduler instance
from app.application.services import send_scheduled_reminder_notifications, process_overdue_parcels
from app.config import Config
from datetime import timedelta

# Fixture for an app instance configured for testing scheduler startup (TESTING=False)
@pytest.fixture(scope="function") # Function scope to ensure clean state for each test
def app_for_scheduler_test():
    # Create a new app instance with a config that has TESTING = False
    # to allow the scheduler to start.
    app = Flask(__name__)
    
    # Use a custom config for this specific app instance
    class SchedulerTestConfig(Config):
        TESTING = False
        # Use in-memory SQLite for tests to avoid file conflicts and ensure clean state
        SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:' 
        # Ensure other relevant configs are set if needed for app creation,
        # e.g., default job intervals if not set by create_app's default config object.
        REMINDER_JOB_INTERVAL_HOURS = Config.REMINDER_JOB_INTERVAL_HOURS
        OVERDUE_PROCESSING_JOB_INTERVAL_HOURS = Config.OVERDUE_PROCESSING_JOB_INTERVAL_HOURS


    app.config.from_object(SchedulerTestConfig())

    # Manually re-initialize extensions for this app instance
    from app import db, mail # Import extensions
    db.init_app(app)
    mail.init_app(app)
    
    # Critical: Re-initialize the global scheduler instance with this app
    # or use a new local scheduler instance if the global one causes issues.
    # For this test, we'll test the behavior of the global scheduler instance
    # when associated with an app where TESTING is False.
    
    # Simulate the parts of create_app relevant to scheduler initialization
    # This is a bit tricky because create_app uses a global scheduler instance.
    # We need to ensure that the global scheduler is 'reset' or tested carefully.
    # The existing create_app() will be called by app fixture, which sets TESTING=True.
    # Here, we are creating a specific app for non-testing mode.
    
    # Let's use a local scheduler for this app to avoid state issues with the global one.
    # However, the goal is to test the app's create_app behavior.
    # The `create_app` function in __init__ is what initializes and starts the global scheduler.
    # So, we should call THAT create_app but with a config that has TESTING=False.

    # Re-creating the app with TESTING=False using the actual create_app
    # This will use and potentially start the global_scheduler.
    # We need to ensure we can shut it down.
    
    # Create a test app with TESTING = False
    # This is a simplified app creation, focusing on config for scheduler
    # The real create_app in __init__ handles blueprint registration, db creation etc.
    # For testing the scheduler part of create_app, we call create_app and then modify its config for testing.
    # Or, pass a specific config to create_app if it supports it. (Current create_app doesn't directly take config object as param)

    # Let's create the app using the main factory but override the config for TESTING
    # then ensure scheduler is stopped.
    
    # This approach might be problematic if create_app() is not designed for re-entry with different configs
    # or if it has global side effects not cleaned up by fixtures.
    # A cleaner way might be to parameterize the app fixture in conftest.py,
    # but for a single test file, creating a custom app instance is okay.

    # Create app using the factory to ensure all initializations are done
    app_instance = create_app() 
    
    # Override TESTING to False for this specific instance AFTER initial create_app from fixture (if any)
    # or if this is the primary app for the test
    app_instance.config['TESTING'] = False
    app_instance.config['REMINDER_JOB_INTERVAL_HOURS'] = 1 # for predictable testing
    app_instance.config['OVERDUE_PROCESSING_JOB_INTERVAL_HOURS'] = 2 # for predictable testing
    
    # The scheduler is initialized within create_app.
    # We need to make sure we are testing the scheduler associated with *this* app_instance.
    # The global `scheduler` instance from app.__init__ is used.
    
    # Ensure the scheduler is started for this app context if it wasn't
    # This mimics the logic in create_app, but we control TESTING config.
    if not global_scheduler.running: # Check the global scheduler
        global_scheduler.init_app(app_instance) # Init with this app
        global_scheduler.start()

    yield app_instance # Provide this specially configured app to the test

    # Teardown: ensure scheduler is shut down after test to prevent interference
    if global_scheduler.running:
        global_scheduler.shutdown(wait=False)
    # Clear jobs for this scheduler instance if necessary, to avoid state leakage
    # This is important as we're dealing with a potentially global scheduler state.
    # If jobs persist, they might affect subsequent tests.
    for job in global_scheduler.get_jobs():
        global_scheduler.remove_job(job.id)


def test_scheduler_initialization_modes(app, app_for_scheduler_test): # app fixture from conftest (TESTING=True)
    # 1. Test with app configured for TESTING = True (using 'app' fixture from conftest)
    assert app.scheduler is not None
    assert isinstance(app.scheduler, APScheduler)
    # In TESTING=True mode, the scheduler should not be started by create_app
    assert app.scheduler.running is False, "Scheduler should not be running when app.config['TESTING'] is True"

    # 2. Test with app_for_scheduler_test configured for TESTING = False
    # This fixture (app_for_scheduler_test) is designed to run create_app in a way
    # that TESTING is false, so scheduler should start.
    scheduler_for_normal_mode = app_for_scheduler_test.scheduler 
    assert scheduler_for_normal_mode is not None
    assert isinstance(scheduler_for_normal_mode, APScheduler)
    assert scheduler_for_normal_mode.running is True, "Scheduler should be running when app.config['TESTING'] is False"


def test_scheduler_jobs_registered_in_normal_mode(app_for_scheduler_test):
    # This test uses the app_for_scheduler_test fixture which creates an app
    # with TESTING=False, thus triggering the job registration logic in create_app.
    
    # The global_scheduler instance is used by create_app
    scheduler = global_scheduler 
    assert scheduler.running is True, "Scheduler should be running for this test."

    # Verify 'send_reminders_job'
    reminder_job = scheduler.get_job('send_reminders_job')
    assert reminder_job is not None, "send_reminders_job not found in scheduler"
    # To compare functions, it's often best to compare their __name__ or fully qualified name
    # if direct object comparison is unreliable due to proxying or decoration.
    assert reminder_job.func.__name__ == send_scheduled_reminder_notifications.__name__
    assert reminder_job.trigger is not None
    # For Flask-APScheduler, the interval is stored in seconds on the trigger
    # The config REMINDER_JOB_INTERVAL_HOURS is set to 1 in app_for_scheduler_test
    expected_reminder_interval_seconds = timedelta(hours=app_for_scheduler_test.config['REMINDER_JOB_INTERVAL_HOURS']).total_seconds()
    assert hasattr(reminder_job.trigger, 'interval_length'), "Trigger does not have interval_length (APScheduler 3.x)"
    assert reminder_job.trigger.interval_length == expected_reminder_interval_seconds


    # Verify 'process_overdue_job'
    overdue_job = scheduler.get_job('process_overdue_job')
    assert overdue_job is not None, "process_overdue_job not found in scheduler"
    assert overdue_job.func.__name__ == process_overdue_parcels.__name__
    assert overdue_job.trigger is not None
    # The config OVERDUE_PROCESSING_JOB_INTERVAL_HOURS is set to 2 in app_for_scheduler_test
    expected_overdue_interval_seconds = timedelta(hours=app_for_scheduler_test.config['OVERDUE_PROCESSING_JOB_INTERVAL_HOURS']).total_seconds()
    assert hasattr(overdue_job.trigger, 'interval_length'), "Trigger does not have interval_length (APScheduler 3.x)"
    assert overdue_job.trigger.interval_length == expected_overdue_interval_seconds
    
    # Note: Accessing trigger.interval might vary slightly depending on APScheduler version
    # and the specific trigger type. For IntervalTrigger, it's usually `trigger.interval`.
    # Flask-APScheduler (which wraps APScheduler) might have its own way or directly expose APScheduler's trigger.
    # The example used `job.trigger.interval`, let's adjust if needed based on Flask-APScheduler's API.
    # APScheduler 3.x uses `trigger.interval_length` for interval in seconds.
    # APScheduler 4.x might use `trigger.interval.total_seconds()`.
    # Assuming Flask-APScheduler uses APScheduler 3.x style for now.
    # If these assertions fail, it means the way to get interval seconds from the trigger needs adjustment.
    # For `IntervalTrigger`, `interval_length` is typically in seconds.

def test_no_jobs_registered_in_testing_mode(app): # Uses the standard 'app' fixture (TESTING=True)
    scheduler = app.scheduler 
    assert scheduler.running is False # Scheduler should not be running

    # In TESTING mode, jobs should not be added by create_app's logic
    assert scheduler.get_job('send_reminders_job') is None
    assert scheduler.get_job('process_overdue_job') is None

# Additional check: Ensure scheduler is really off after tests using the normal app fixture
def test_scheduler_remains_off_for_standard_app_fixture(app):
    assert app.scheduler.running is False
    assert global_scheduler.running is False # Check global instance too if it's the same
    # This helps catch if a previous test using app_for_scheduler_test didn't clean up properly.
    # However, pytest fixtures should isolate test runs. The main check is app.scheduler.running.
    # If global_scheduler is indeed global and modified by app_for_scheduler_test,
    # then its state *could* leak if not managed in app_for_scheduler_test's teardown.
    # The app_for_scheduler_test fixture includes a teardown to shut down and clear jobs
    # from the global_scheduler instance.
