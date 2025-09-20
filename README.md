# The Khaki Estate - Housing Complex Management System

A comprehensive Django-based web application designed to serve as a **digital community hub** for housing complex management, addressing the core concern that "no one looks at WhatsApp messages" by providing structured, trackable, and actionable communication.

## 🏗️ System Overview

The Khaki Estate Management System is a full-featured housing complex management platform that transforms traditional community communication from informal WhatsApp groups into a structured, professional, and efficient digital ecosystem.

### 🎯 Core Philosophy

**From Messaging Platform → Digital Community Hub**

Instead of relying on informal communication channels where messages get lost and important announcements are missed, this system provides:
- **Structured Communication** with read receipts and tracking
- **Actionable Workflows** for maintenance, bookings, and community engagement
- **Professional Management** tools for committee members
- **Community Engagement** features that foster interaction

## 🚀 Key Features & Workflows

### 📢 **Communication Workflow**
**Management → Residents & Resident → Management**

- **Announcements System**
  - Categorized announcements (General, Maintenance, Events, Emergency)
  - Email/SMS notifications with delivery tracking
  - In-app notifications with read receipts
  - Threaded comments for community discussion
  - Advanced filtering and search capabilities
  - Pinning system for important announcements

- **Maintenance Requests**
  - Unique ticket number generation (MNT-2025-0001)
  - Automatic notifications to committee members
  - Real-time status updates with timeline tracking
  - Photo attachments for issue documentation
  - Assignment system for staff/contractors
  - Resident notifications on status changes

### 🔧 **Maintenance Management Workflow**

- **Issue Reporting**
  - Location-based issue reporting
  - Priority classification (Low, Medium, High, Urgent)
  - Photo documentation system
  - Auto-triage based on category and priority

- **Progress Tracking**
  - Real-time status updates
  - Staff assignment and tracking
  - Resident confirmation system
  - Ticket closure with resolution details
  - Analytics and reporting dashboard

### 📅 **Facility Booking Workflow**

- **Smart Booking System**
  - Interactive availability calendar
  - Date/time validation with conflict prevention
  - Booking rules and policies enforcement
  - Waiting list management
  - Cancellation policies with fee calculation

- **Management Features**
  - Unique booking number generation
  - Fee calculation and payment tracking
  - Confirmation and reminder notifications
  - Calendar integration for easy viewing

### 👥 **Community Engagement Workflow**

- **Event Management**
  - Event creation with RSVP system
  - Guest count tracking and capacity management
  - Attendance tracking and analytics
  - Reminder notifications
  - Post-event photo sharing and feedback

- **Marketplace**
  - Item posting for sale/services
  - Interest management and contact facilitation
  - Expiry date tracking
  - Status updates and moderation
  - Lost & found functionality

### 📊 **Dashboard & Analytics**

- **Resident Dashboard**
  - Recent announcements with read status
  - Personal maintenance requests
  - Upcoming bookings and events
  - Marketplace items of interest
  - Notification center

- **Committee Dashboard**
  - Pending maintenance requests
  - Upcoming events and RSVPs
  - Recent bookings and conflicts
  - Communication analytics
  - System health monitoring

### 🔔 **Notification System**

- **Multi-Channel Notifications**
  - In-app notifications
  - Email notifications
  - SMS notifications (future integration)
  - Push notifications (future integration)

- **Smart Notification Management**
  - Preference-based delivery
  - Urgency-based prioritization
  - Read receipt tracking
  - Notification history and analytics

## 🛠️ Technical Architecture

### **Backend Technologies**
- **Django 4.2+** - Web framework
- **PostgreSQL** - Primary database
- **Celery** - Asynchronous task processing
- **Redis** - Caching and message broker
- **Neo4j** - Graph database for analytics (optional)

### **Frontend Technologies**
- **Bootstrap 5** - Responsive UI framework
- **Font Awesome** - Icon library
- **JavaScript** - Interactive functionality
- **AJAX** - Real-time updates

### **Key Django Components**

#### **Models**
- `Resident` - User profiles with role management
- `Announcement` - Communication system
- `MaintenanceRequest` - Issue tracking
- `Booking` - Facility reservations
- `Event` - Community events
- `MarketplaceItem` - Community marketplace
- `Notification` - Multi-channel notifications

#### **Views & Templates**
- **Dashboard Views** - Role-based dashboards
- **Communication Views** - Announcements and comments
- **Maintenance Views** - Request management
- **Booking Views** - Facility reservation system
- **Event Views** - Community event management
- **Marketplace Views** - Community marketplace
- **Notification Views** - Notification management

#### **Celery Tasks**
- `send_announcement_notifications` - Automated notifications
- `send_maintenance_notifications` - Maintenance alerts
- `send_booking_reminders` - Booking confirmations
- `send_event_reminders` - Event notifications

## 🎯 Success Metrics & KPIs

### **Communication Effectiveness**
- **Target**: 90% announcement read rate within 48 hours
- **Target**: 95% maintenance request acknowledgment within 24 hours
- **Target**: 80% resident engagement in community events

### **System Usage**
- **Target**: 85% daily active users
- **Target**: 95% maintenance requests submitted through system
- **Target**: 70% facility bookings made through system

## 🚀 Getting Started

**IMPORTANT: This project uses `uv` as the Python package manager for all dependency management and virtual environment operations.**

### **Prerequisites**
- Python 3.11+
- PostgreSQL 13+
- Redis 6+
- uv (modern Python package manager)

### **Installation**

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd the_khaki_estate
   ```

2. **Install dependencies**
   ```bash
   uv sync
   ```

3. **Setup database**
   ```bash
   uv run python manage.py migrate
   ```

4. **Create superuser**
   ```bash
   uv run python manage.py createsuperuser
   ```

5. **Start development server**
   ```bash
   uv run python manage.py runserver 8001
   ```

6. **Start Celery worker** (in separate terminal)
   ```bash
   uv run celery -A config.celery_app worker -l info
   ```

### **Configuration**

1. **Environment Variables**
   - Set up `.env` file with database credentials
   - Configure email settings for notifications
   - Set up Redis connection details

2. **Initial Setup**
   - Create announcement categories
   - Set up common areas for booking
   - Configure notification templates
   - Set up emergency contacts

## 📱 User Roles & Permissions

### **Residents**
- View announcements and mark as read
- Submit maintenance requests
- Book common facilities
- RSVP to events
- Post marketplace items
- View personal dashboard

### **Committee Members**
- Create and manage announcements
- Manage maintenance requests
- Oversee facility bookings
- Create and manage events
- Moderate marketplace content
- Access analytics dashboard

### **Administrators**
- Full system access
- User management
- System configuration
- Analytics and reporting
- Backup and maintenance

## 🔮 Future Enhancements

### **Phase 2 Features**
- **Payment Integration** - Online payment for bookings and fees
- **Mobile App** - Native mobile application
- **SMS Integration** - Twilio integration for SMS notifications
- **Calendar Sync** - Google Calendar integration
- **File Storage** - Cloud storage for documents and photos

### **Phase 3 Features**
- **AI-Powered Analytics** - Predictive maintenance
- **Voice Notifications** - Alexa/Google Home integration
- **IoT Integration** - Smart building sensors
- **Advanced Reporting** - Business intelligence dashboard

## 📚 Documentation

This project maintains comprehensive documentation in two main files:

### **Technical Documentation**
- **[TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md)**: Complete technical reference for developers, system architects, and technical teams
- **Covers**: Architecture, models, workflows, API design, deployment, testing, and development tools
- **Includes**: Latest tech stack information, code examples, and implementation patterns

### **User Guide**
- **[USER_GUIDE.md](USER_GUIDE.md)**: Comprehensive guide for all users (residents, committee members, maintenance staff)
- **Covers**: Getting started, user roles, features, workflows, troubleshooting, and best practices
- **Includes**: Step-by-step instructions, screenshots, and role-specific guidance

### **Documentation Servers**
- **MkDocs**: http://localhost:8000 (primary documentation)
- **Django Application**: http://localhost:8001 (main application)
- **Sphinx Documentation**: http://localhost:8080 (static) / http://localhost:9000 (live reload)

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTORS.txt) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Team

- **Sanjay Singh** - Lead Developer
- **The Khaki Estate Community** - Beta Testers and Feedback

---

**Built with ❤️ for The Khaki Estate Community**

*Transforming housing complex management from chaotic messaging to structured community engagement.*
