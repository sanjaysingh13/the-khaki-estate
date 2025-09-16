#!/usr/bin/env python
"""
Test runner script for the housing society web application.
Provides convenient commands to run different types of tests.
"""

import os
import sys

import django
from django.conf import settings
from django.test.utils import get_runner


def setup_django():
    """Set up Django environment for testing"""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.test")
    django.setup()


def run_tests(test_labels=None, verbosity=2, keepdb=False, parallel=None):
    """
    Run tests with specified parameters.

    Args:
        test_labels: List of test labels to run (e.g., ['backend.tests.test_models'])
        verbosity: Verbosity level (0=minimal, 1=normal, 2=verbose)
        keepdb: Keep test database after tests
        parallel: Number of parallel processes
    """
    setup_django()

    TestRunner = get_runner(settings)
    test_runner = TestRunner()

    failures = test_runner.run_tests(
        test_labels or ["the_khaki_estate.backend.tests"],
        verbosity=verbosity,
        keepdb=keepdb,
        parallel=parallel,
    )

    return failures


def run_model_tests():
    """Run only model tests"""
    return run_tests(["the_khaki_estate.backend.tests.test_models"])


def run_view_tests():
    """Run only view tests"""
    return run_tests(["the_khaki_estate.backend.tests.test_views"])


def run_task_tests():
    """Run only task tests"""
    return run_tests(["the_khaki_estate.backend.tests.test_tasks"])


def run_signal_tests():
    """Run only signal tests"""
    return run_tests(["the_khaki_estate.backend.tests.test_signals"])


def run_notification_service_tests():
    """Run only notification service tests"""
    return run_tests(["the_khaki_estate.backend.tests.test_notification_service"])


def run_integration_tests():
    """Run only integration tests"""
    return run_tests(["the_khaki_estate.backend.tests.test_integration"])


def run_fast_tests():
    """Run fast tests (exclude integration tests)"""
    return run_tests(
        [
            "the_khaki_estate.backend.tests.test_models",
            "the_khaki_estate.backend.tests.test_views",
            "the_khaki_estate.backend.tests.test_tasks",
            "the_khaki_estate.backend.tests.test_signals",
            "the_khaki_estate.backend.tests.test_notification_service",
        ]
    )


def run_all_tests():
    """Run all tests"""
    return run_tests()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Run tests for housing society application"
    )
    parser.add_argument(
        "--type",
        choices=[
            "all",
            "models",
            "views",
            "tasks",
            "signals",
            "notification-service",
            "integration",
            "fast",
        ],
        default="all",
        help="Type of tests to run",
    )
    parser.add_argument(
        "--verbosity", type=int, choices=[0, 1, 2], default=2, help="Verbosity level"
    )
    parser.add_argument(
        "--keepdb", action="store_true", help="Keep test database after tests"
    )
    parser.add_argument(
        "--parallel", type=int, default=None, help="Number of parallel processes"
    )

    args = parser.parse_args()

    # Map test types to functions
    test_functions = {
        "all": run_all_tests,
        "models": run_model_tests,
        "views": run_view_tests,
        "tasks": run_task_tests,
        "signals": run_signal_tests,
        "notification-service": run_notification_service_tests,
        "integration": run_integration_tests,
        "fast": run_fast_tests,
    }

    # Run selected tests
    failures = test_functions[args.type]()

    # Exit with appropriate code
    sys.exit(failures)
