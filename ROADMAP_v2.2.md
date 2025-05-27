# 🗺️ Campus Locker System v2.2 - Development Roadmap

## 🎯 Overview
Version 2.2 will introduce advanced multi-locker workflows, enhanced user experience, admin dashboard, and production-grade data persistence features.

---

## 📋 Feature List

### 🏢 **Feature 1: Multi-Locker Workflow**
**Priority**: High | **Complexity**: High

#### Description
Implement a two-stage locker system where parcels are first deposited in intermediate lockers, then transferred to recipient-specific lockers.

#### User Story
1. **Depositor** deposits parcel in any available locker (intermediate stage)
2. **System** assigns parcel to recipient's designated locker
3. **Admin/System** physically moves parcel to recipient locker
4. **Email** is sent to recipient with pickup instructions
5. **Recipient** picks up from their designated locker

#### Technical Implementation
- **Configuration**: `RECIPIENT_LOCKERS` in config file
- **Database Schema**: 
  - Add `recipient_locker_id` field to Parcel model
  - Add `locker_type` field to Locker model (`intermediate`, `recipient`, `general`)
- **Business Logic**: 
  - Modify `assign_locker_and_create_parcel()` to use intermediate lockers
  - Add `transfer_to_recipient_locker()` function
  - Update notification system for two-stage process
- **API Endpoints**:
  - `POST /admin/transfer-parcel/{parcel_id}`
  - `GET /admin/pending-transfers`

#### Tests Required
- Unit tests for multi-locker assignment logic
- Integration tests for workflow
- Admin transfer functionality tests
- Configuration validation tests

---

### 🔐 **Feature 2: Email-Based PIN Generation**
**Priority**: High | **Complexity**: Medium

#### Description
Replace immediate PIN delivery with a "Generate PIN" button in emails that creates a fresh PIN when clicked.

#### User Story
1. **Recipient** receives email: "Parcel ready for pickup"
2. **Email** contains: "Click here to generate your pickup PIN"
3. **Recipient** clicks button → new PIN generated & sent via email
4. **Old PINs** become invalid when new PIN is generated

#### Technical Implementation
- **Database Schema**: Add `pin_generation_token` to Parcel model
- **Email Templates**: 
  - Remove PIN from initial notification
  - Add "Generate PIN" button with unique URL
- **API Endpoints**:
  - `GET /generate-pin/{token}` - Generate new PIN for parcel
  - `POST /regenerate-pin` - Admin function to regenerate PIN
- **Security**: Unique tokens, rate limiting, expiry times

#### Tests Required
- PIN generation endpoint tests
- Email template validation
- Token security tests
- PIN invalidation tests

---

### 🛠️ **Feature 3: Admin Dashboard**
**Priority**: High | **Complexity**: Medium

#### Description
Comprehensive admin interface for managing lockers, parcels, and system operations.

#### Features
- **Locker Management**: Status overview, maintenance mode, location assignment
- **Parcel Tracking**: Search, status updates, transfer operations
- **User Management**: View recipient activity, PIN reissue
- **System Monitoring**: Health checks, email logs, error tracking
- **Reports**: Usage statistics, pickup rates, locker utilization

#### Technical Implementation
- **Frontend**: Enhanced HTML/CSS interface with responsive design
- **Routes**: Admin-only protected routes with role validation
- **Database Views**: Optimized queries for dashboard data
- **Real-time Updates**: AJAX for live status updates

#### Tests Required
- Admin authentication tests
- Dashboard functionality tests
- Role-based access tests
- UI/UX testing

---

### 💾 **Feature 4: Persistent Database Storage**
**Priority**: Critical | **Complexity**: Low

#### Description
Ensure database persistence across Docker container restarts and deployments.

#### Technical Implementation
- **Docker Volumes**: Properly configured named volumes
- **Backup Strategy**: Automated daily backups
- **Data Migration**: Version-safe database upgrades
- **Configuration**: Environment variables for database paths

#### Current Status Analysis
- ✅ Docker volumes already configured in `docker-compose.yml`
- ⚠️ Need to verify volume persistence during container rebuilds
- ❌ Backup strategy not implemented

#### Tests Required
- Database persistence tests across container restarts
- Backup/restore functionality tests
- Data integrity tests

---

### 🔄 **Feature 5: Automated Database Backups**
**Priority**: Medium | **Complexity**: Medium

#### Description
Daily automated backups with retention policy and restore capabilities.

#### Technical Implementation
- **Backup Service**: Separate container or cron job
- **Storage**: Local volumes + optional cloud storage
- **Retention**: 30 daily, 12 monthly backups
- **Monitoring**: Backup success/failure notifications

#### Tests Required
- Backup automation tests
- Restore functionality tests
- Retention policy tests

---

### 🚪 **Feature 6: Locker Closure Confirmation**
**Priority**: Medium | **Complexity**: Low

#### Description
Post-pickup confirmation system to ensure locker is properly closed and empty.

#### User Story
1. **User** enters PIN and locker opens
2. **System** prompts: "Have you taken everything and closed the locker securely?"
3. **User** confirms before locker is marked as free
4. **Optional**: Physical sensor integration for actual closure detection

#### Technical Implementation
- **UI Flow**: Post-pickup confirmation page
- **Database**: Add `closure_confirmed` field to pickup tracking
- **Future**: IoT sensor integration capabilities

#### Tests Required
- Pickup confirmation flow tests
- UI validation tests

---

## 🏗️ Implementation Strategy

### Phase 1: Core Infrastructure (Week 1-2)
1. **Database Persistence** - Critical foundation
2. **Multi-Locker Schema** - Database changes first
3. **Admin Dashboard Framework** - Basic structure

### Phase 2: Core Features (Week 3-4)
1. **Multi-Locker Workflow** - Business logic implementation
2. **Email PIN Generation** - Security enhancement
3. **Admin Dashboard** - Full functionality

### Phase 3: Enhancement & Polish (Week 5-6)
1. **Automated Backups** - Production readiness
2. **Locker Closure Confirmation** - UX improvement
3. **Frontend Enhancement** - UI/UX polish
4. **Comprehensive Testing** - Full test coverage

---

## 🧪 Testing Strategy

### Test Categories
1. **Unit Tests**: Business logic for each feature
2. **Integration Tests**: Multi-component workflows
3. **End-to-End Tests**: Complete user journeys
4. **Security Tests**: Authentication, authorization, token validation
5. **Performance Tests**: Database operations, email delivery
6. **Persistence Tests**: Docker volume and backup functionality

### Test Coverage Goal
- **Maintain 100% test pass rate**
- **Minimum 90% code coverage**
- **All new features must include tests**

---

## 📚 Documentation Requirements

### Update Required
1. **API Documentation**: New endpoints and workflows
2. **Admin Guide**: Dashboard usage and workflows
3. **Deployment Guide**: Database persistence and backup setup
4. **User Manual**: Multi-locker process and PIN generation
5. **Architecture Document**: Updated system design

---

## 🔧 Configuration Changes

### New Environment Variables
```bash
# Multi-Locker Configuration
ENABLE_MULTI_LOCKER_WORKFLOW=true
RECIPIENT_LOCKERS=user1:locker_101,user2:locker_102
INTERMEDIATE_LOCKER_COUNT=10

# Backup Configuration
BACKUP_ENABLED=true
BACKUP_SCHEDULE=0 2 * * *  # Daily at 2 AM
BACKUP_RETENTION_DAYS=30
BACKUP_STORAGE_PATH=/app/backups

# Security
PIN_GENERATION_TOKEN_EXPIRY=24  # hours
MAX_PIN_GENERATIONS_PER_DAY=3
```

---

## 🚀 Success Criteria

### v2.2 Release Checklist
- [ ] All multi-locker workflows functional
- [ ] Email PIN generation working securely
- [ ] Admin dashboard fully operational
- [ ] Database persistence verified across container restarts
- [ ] Daily backups running automatically
- [ ] Locker closure confirmation implemented
- [ ] All tests passing (target: 100+ tests)
- [ ] Documentation updated
- [ ] Performance benchmarks met
- [ ] Security audit completed

### Performance Targets
- **Response Time**: < 500ms for all API endpoints
- **Email Delivery**: < 30 seconds to MailHog
- **Database Backup**: Complete within 5 minutes
- **Container Restart**: < 60 seconds downtime

---

## 🤝 Development Workflow

### Branch Strategy
- **main**: Stable v2.1 release
- **develop**: Active v2.2 development
- **feature/***: Individual feature branches

### Code Review Process
1. Feature branch → Pull Request to develop
2. All tests must pass
3. Code review required
4. Integration testing in develop branch
5. Release candidate → main branch

---

*This roadmap is a living document and will be updated as development progresses.* 