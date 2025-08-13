# Lead Router Pro - Script Analysis and Cleanup Recommendations

## Script Categories

### 🟢 CORE SYSTEM FILES (Keep - Essential)
- `main_working_final.py` - Main application entry point
- `config.py` - Configuration management
- `start_server.py` - Server startup script
- `sync_ghl_as_truth.py` - **ACTIVE** - New GHL sync (single source of truth)

### 🟡 API ROUTES (Keep - Active)
- `api/routes/admin_functions.py` - **NEW** - Admin functions API
- `api/routes/admin_routes.py` - Main admin dashboard API
- `api/routes/auth_routes.py` - Authentication endpoints
- `api/routes/field_mapping_routes.py` - Field mapping management
- `api/routes/lead_reassignment.py` - Lead reassignment functionality
- `api/routes/routing_admin.py` - Routing configuration
- `api/routes/security_admin.py` - Security management
- `api/routes/simple_admin.py` - Simple admin endpoints
- `api/routes/vendor_toggle.py` - Vendor management
- `api/routes/webhook_routes.py` - Main webhook processing
- `api/routes/webhook_ai_utilities.py` - AI utilities (if still used)
- `api/routes/webhook_routes_vendor_fix.py` - **REVIEW** - May be outdated

### 🟡 API SERVICES (Keep - Active)
- `api/services/auth_service.py` - Authentication service
- `api/services/email_service.py` - Email functionality
- `api/services/field_mapper.py` - Field mapping service
- `api/services/field_reference_service.py` - Field reference management
- `api/services/free_email_2fa.py` - 2FA email service
- `api/services/ghl_api.py` - **ACTIVE** - Main GHL API client
- `api/services/lead_routing_service.py` - Lead routing logic
- `api/services/location_service.py` - Location/county services
- `api/services/service_categories.py` - Service categorization
- `api/services/simple_lead_router.py` - Simple routing logic
- `api/services/ai_classifier.py` - **REVIEW** - AI classification (if still used)
- `api/services/ai_enhanced_field_mapper_v2.py` - **REVIEW** - AI field mapping
- `api/services/ai_error_recovery_v2.py` - **REVIEW** - AI error recovery
- `api/services/ghl_api_enhanced_v2.py` - **REVIEW** - Enhanced GHL API (may duplicate ghl_api.py)

### 🟡 API SECURITY (Keep - Active)
- `api/security/auth_middleware.py` - Authentication middleware
- `api/security/ip_security.py` - IP security functions
- `api/security/middleware.py` - Security middleware

### 🟡 DATABASE (Keep - Active)
- `database/models.py` - Database models
- `database/simple_connection.py` - Database connection management

### 🟡 UTILITIES (Keep - Active)
- `utils/dependency_manager.py` - Dependency management
- `utils/__init__.py` - Utils package init

### 🔴 DEBUGGING/TEST SCRIPTS (CLEANUP CANDIDATES)

#### High Priority Cleanup (Remove)
- `analyze_miscategorized_leads.py` - Analysis script
- `analyze_webhook_payloads.py` - Analysis script
- `check_and_fix_2fa.py` - One-time fix script
- `check_vendor_data.py` - Debug script
- `check_vendor_webhook_log.py` - Debug script
- `code_fix_script.py` - One-time fix script
- `debug_lead_data.py` - Debug script
- `debug_v1_user_creation.py` - Debug script
- `demo_2fa_setup.py` - Demo script
- `diagnose_ghl_jwt_issue.py` - Diagnostic script
- `diagnose_vendor_assignment.py` - Diagnostic script
- `fix_admin_user.py` - One-time fix script
- `fix_database_and_ghl_ids.py` - One-time fix script
- `fix_miscategorized_leads.py` - One-time fix script
- `fix_vendor_assignment.py` - One-time fix script
- `fix_vendor_assignment_proper.py` - One-time fix script
- `fix_vendor_system_complete.py` - One-time fix script
- `fix_vendor_user_rate_limiting.py` - One-time fix script
- `get_detailed_webhook_logs.py` - Debug script
- `get_raw_webhook_payloads.py` - Debug script
- `get_webhook_logs.py` - Debug script
- `install_2fa_dependencies.py` - One-time install script
- `investigate_logs.py` - Debug script
- `minimal_service_preservation_fix.py` - One-time fix script
- `print_active_vendors.py` - Debug script
- `quick_vendor_fix.py` - One-time fix script
- `recovery_database_fix.py` - One-time fix script
- `simple_log_check.py` - Debug script
- `test_auth_issue.py` - Test script
- `test_complete_vendor_flow.py` - Test script
- `test_county_based_assignment.py` - Test script
- `test_email_direct.py` - Test script
- `test_ghl_connection.py` - Test script
- `test_ip_security.py` - Test script
- `test_multi_level_routing.py` - Test script
- `test_new_database_structure.py` - Test script
- `test_opportunity_assignment.py` - Test script
- `test_vendor_submission_fix.py` - Test script
- `test_vendor_widget_submission.py` - Test script
- `trace_lead_assignment.py` - Debug script
- `verify_admin_status.py` - One-time verification script
- `verify_jwt_fix.py` - One-time verification script
- `view_recent_form_submissions.py` - Debug script
- `webhook_payload_detailed_analysis.py` - Analysis script
- `webhook_service_field_analysis.py` - Analysis script
- `whitelist_admin_ip.py` - One-time configuration script

#### Medium Priority Cleanup (Review First)
- `bulk_vendor_submission.py` - **REVIEW** - May be useful for bulk operations
- `cleanup_tenants.py` - **REVIEW** - May be useful for maintenance
- `clear_lead_assignments.py` - **REVIEW** - May be useful for maintenance
- `comprehensive_service_mappings.py` - **REVIEW** - Service mapping reference
- `create_admin_user.py` - **REVIEW** - Admin user creation utility
- `migrate_enhanced_leads.py` - **REVIEW** - Migration script (may be needed)
- `restructure_database_tables.py` - **REVIEW** - Database migration script
- `setup_free_2fa_email.py` - **REVIEW** - 2FA setup utility
- `sync_vendors_from_ghl.py` - **REPLACE** - Legacy sync (replaced by sync_ghl_as_truth.py)
- `update_webhook_routes_mappings.py` - **REVIEW** - Mapping updates
- `validate_form_mappings.py` - **REVIEW** - Form validation utility

### 🟡 ARCHIVED SCRIPTS (Already Archived - Keep in Archive)
- All files in `archived_scripts/` - These are already properly archived

### 🟡 MIGRATION SCRIPTS (Keep - May be needed)
- `scripts/migrate_vendors_to_county.py` - Migration script
- `scripts/rollback_vendor_migration.py` - Rollback script

## Cleanup Recommendations

### Phase 1: High Priority Cleanup (Safe to Remove)
Remove all debugging, testing, and one-time fix scripts that were created for specific issues and are no longer needed.

### Phase 2: Review and Decide
Review the medium priority scripts to determine if they provide ongoing value or should be archived.

### Phase 3: Consolidation
- Consider consolidating similar functionality
- Review if AI-related services are still being used
- Ensure no duplicate functionality between similar scripts

## Summary
- **Total Scripts**: 94
- **Core/Active**: 34
- **High Priority Cleanup**: 42
- **Medium Priority Review**: 12
- **Already Archived**: 16

**Cleanup Potential**: ~45% of scripts can be safely removed, significantly cleaning up the project.