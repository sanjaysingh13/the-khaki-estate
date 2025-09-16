# Housing Society Web Application - Test Suite Documentation

## Overview

This document provides comprehensive documentation for the test suite of the housing society web application. The test suite covers all major functionality including models, views, tasks, signals, and integration workflows.

## Test Structure

The test suite is organized into the following modules:

```
the_khaki_estate/backend/tests/
├── __init__.py
├── factories.py              # Factory classes for test data generation
├── test_models.py           # Model tests
├── test_views.py           # View and API endpoint tests
├── test_tasks.py           # Celery task tests
├── test_signals.py         # Django signal tests
├── test_notification_service.py  # NotificationService tests
└── test_integration.py     # Integration and workflow tests
```

## Test Categories

### 1. Model Tests (`test_models.py`)

Tests all Django models including:

- **Resident Model**: User creation, validation, notification preferences
- **Announcement Models**: Announcement creation, categories, ordering
- **Maintenance Request Models**: Request creation, ticket generation, status tracking
- **Common Area Models**: Area creation, booking rules, availability
- **Booking Models**: Booking creation, number generation, status management
- **Event Models**: Event creation, RSVP handling, type management
- **Marketplace Models**: Item creation, status management, type handling
- **Notification Models**: Notification creation, status tracking, read functionality
- **Comment Models**: Comment creation, threading, relationship management
- **Emergency Contact Models**: Contact creation, type handling, ordering
- **Document Models**: Document creation, access control, type management

**Key Test Features:**
- Model validation and constraints
- String representations
- Default values and choices
- Ordering and relationships
- Data integrity

### 2. View Tests (`test_views.py`)

Tests all view functionality including:

- **Authentication Requirements**: Login requirements for protected endpoints
- **API Endpoints**: JSON response structure and data
- **Pagination**: Page handling and navigation
- **Error Handling**: 404, 405, and other error responses
- **Data Filtering**: Status and parameter filtering
- **Permission Checks**: User access control
- **Response Performance**: Response time validation

**Key Test Features:**
- HTTP method validation
- Authentication and authorization
- Response structure validation
- Error handling
- Performance testing

### 3. Task Tests (`test_tasks.py`)

Tests Celery task functionality including:

- **Email Delivery**: SMTP integration and error handling
- **SMS Delivery**: SMS service integration (placeholder)
- **Delivery Methods**: Email-only, SMS-only, both, in-app-only
- **Error Handling**: Task failure and retry mechanisms
- **Status Updates**: Notification status transitions
- **Template Rendering**: Email template processing
- **Concurrent Execution**: Task safety and data integrity

**Key Test Features:**
- Task execution and completion
- Error handling and recovery
- Delivery method validation
- Status tracking
- Performance testing

### 4. Signal Tests (`test_signals.py`)

Tests Django signal functionality including:

- **Announcement Signals**: Auto-notification on announcement creation
- **Maintenance Request Signals**: Notifications for request updates
- **Signal Timing**: Proper signal firing timing
- **Error Handling**: Signal error handling
- **Signal Disconnection**: Signal management
- **Integration**: Signal interaction with other components

**Key Test Features:**
- Signal triggering
- Notification creation
- Error handling
- Signal management
- Integration testing

### 5. NotificationService Tests (`test_notification_service.py`)

Tests the NotificationService class including:

- **Notification Creation**: Single and bulk notification creation
- **User Preferences**: Email, SMS, and urgent-only preferences
- **Delivery Methods**: Method selection and override
- **Bulk Operations**: Multiple resident notifications
- **Data Handling**: Complex data structures
- **Error Handling**: Service error handling
- **Performance**: Bulk operation efficiency

**Key Test Features:**
- Service method functionality
- User preference handling
- Bulk operations
- Data consistency
- Performance testing

### 6. Integration Tests (`test_integration.py`)

Tests complete workflows including:

- **Announcement Workflow**: Creation → Notification → Comments → Read Tracking
- **Maintenance Request Workflow**: Submission → Assignment → Updates → Resolution
- **Booking Workflow**: Request → Confirmation → Payment → Completion
- **Event Workflow**: Creation → RSVP → Management
- **Marketplace Workflow**: Listing → Status Changes → Completion
- **Notification Workflow**: Creation → Delivery → Read Tracking
- **Complete Society Workflow**: Multi-model interactions

**Key Test Features:**
- End-to-end workflows
- Model interactions
- Data consistency
- Complex scenarios
- Performance testing

## Factory Classes (`factories.py`)

The factory classes provide realistic test data generation using Factory Boy:

- **ResidentFactory**: Creates residents with various types and preferences
- **AnnouncementFactory**: Creates announcements with realistic content
- **MaintenanceRequestFactory**: Creates maintenance requests with proper ticket numbers
- **CommonAreaFactory**: Creates common areas with booking rules
- **BookingFactory**: Creates bookings with realistic dates and times
- **EventFactory**: Creates events with proper scheduling
- **MarketplaceItemFactory**: Creates marketplace items with various types
- **NotificationFactory**: Creates notifications with proper status tracking
- **And many more...**

## Running Tests

### Using Django Test Runner

```bash
# Run all backend tests
python manage.py test the_khaki_estate.backend.tests

# Run specific test module
python manage.py test the_khaki_estate.backend.tests.test_models

# Run specific test class
python manage.py test the_khaki_estate.backend.tests.test_models.ResidentModelTest

# Run specific test method
python manage.py test the_khaki_estate.backend.tests.test_models.ResidentModelTest.test_resident_creation

# Run with verbose output
python manage.py test the_khaki_estate.backend.tests --verbosity=2

# Keep test database
python manage.py test the_khaki_estate.backend.tests --keepdb

# Run in parallel
python manage.py test the_khaki_estate.backend.tests --parallel=4
```

### Using Custom Test Runner

```bash
# Run all tests
python run_tests.py --type all

# Run specific test types
python run_tests.py --type models
python run_tests.py --type views
python run_tests.py --type tasks
python run_tests.py --type signals
python run_tests.py --type notification-service
python run_tests.py --type integration
python run_tests.py --type fast

# Run with custom options
python run_tests.py --type all --verbosity=2 --keepdb --parallel=4
```

## Test Configuration

### Test Settings

The test configuration is defined in `config/settings/test.py`:

- **Database**: Uses in-memory SQLite for fast test execution
- **Email Backend**: Uses local memory backend for email testing
- **Password Hashing**: Uses MD5 for faster test execution
- **Media Storage**: Uses temporary directory for file uploads
- **Debug**: Enabled for template debugging

### Test Dependencies

Required packages for testing:

```python
# In requirements-test.txt or pyproject.toml
factory-boy>=3.2.0
pytest>=7.0.0
pytest-django>=4.5.0
coverage>=7.0.0
```

## Test Coverage

The test suite provides comprehensive coverage for:

- **Model Validation**: All model fields, constraints, and relationships
- **Business Logic**: All custom methods and properties
- **API Endpoints**: All view functions and their responses
- **Background Tasks**: All Celery tasks and their execution
- **Signals**: All Django signals and their handlers
- **Services**: All service classes and their methods
- **Workflows**: Complete end-to-end user workflows
- **Error Handling**: All error conditions and edge cases
- **Performance**: Critical performance scenarios

## Best Practices

### Test Organization

1. **Group Related Tests**: Tests are grouped by functionality and model
2. **Use Descriptive Names**: Test method names clearly describe what is being tested
3. **One Assertion Per Test**: Each test focuses on a single behavior
4. **Independent Tests**: Tests don't depend on each other
5. **Clean Setup**: Each test starts with a clean state

### Test Data

1. **Use Factories**: All test data is created using factory classes
2. **Realistic Data**: Test data reflects real-world scenarios
3. **Minimal Data**: Use only necessary data for each test
4. **Isolated Data**: Each test uses its own data instances

### Mocking and Patching

1. **External Services**: Mock external API calls and services
2. **Email/SMS**: Mock email and SMS sending
3. **File Operations**: Mock file uploads and downloads
4. **Time-dependent**: Mock time-dependent operations

### Assertions

1. **Specific Assertions**: Use specific assertion methods
2. **Clear Messages**: Provide clear failure messages
3. **Multiple Checks**: Verify multiple aspects when relevant
4. **Edge Cases**: Test boundary conditions and edge cases

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-test.txt

    - name: Run tests
      run: |
        python manage.py test the_khaki_estate.backend.tests --verbosity=2

    - name: Generate coverage report
      run: |
        coverage run --source='.' manage.py test the_khaki_estate.backend.tests
        coverage report
        coverage xml
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed
2. **Database Issues**: Use `--keepdb` flag for debugging
3. **Mock Issues**: Check mock setup and teardown
4. **Signal Issues**: Ensure signals are properly connected
5. **Task Issues**: Check Celery configuration

### Debug Tips

1. **Verbose Output**: Use `--verbosity=2` for detailed output
2. **Single Test**: Run individual tests for debugging
3. **Print Statements**: Add print statements for debugging
4. **Database Inspection**: Use Django shell to inspect test data
5. **Mock Verification**: Verify mock calls and arguments

## Contributing

When adding new tests:

1. **Follow Naming Conventions**: Use descriptive test method names
2. **Add Documentation**: Include docstrings explaining test purpose
3. **Use Factories**: Create new factories for new models
4. **Test Edge Cases**: Include tests for error conditions
5. **Update Coverage**: Ensure new code is covered by tests

## Conclusion

This comprehensive test suite ensures the reliability and quality of the housing society web application. The tests cover all major functionality and provide confidence in the application's behavior across various scenarios.

For questions or issues with the test suite, please refer to the Django testing documentation or contact the development team.
