#!/bin/bash

# Documentation Reorganization Script
# Purpose: Reorganize TradingMTQ documentation into logical structure
# Date: January 1, 2026

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOCS_DIR="."
BACKUP_DIR="../docs-backup-$(date +%Y%m%d-%H%M%S)"
DRY_RUN=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help)
            echo "Usage: $0 [--dry-run] [--help]"
            echo ""
            echo "Options:"
            echo "  --dry-run    Show what would be done without making changes"
            echo "  --help       Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Create directory if it doesn't exist
create_dir() {
    local dir=$1
    if [ "$DRY_RUN" = true ]; then
        echo "Would create: $dir"
    else
        mkdir -p "$dir"
        log_success "Created directory: $dir"
    fi
}

# Move file using git mv to preserve history
move_file() {
    local src=$1
    local dest=$2

    if [ ! -f "$src" ]; then
        log_warning "File not found, skipping: $src"
        return
    fi

    if [ "$DRY_RUN" = true ]; then
        echo "Would move: $src -> $dest"
    else
        git mv "$src" "$dest" 2>/dev/null || mv "$src" "$dest"
        log_success "Moved: $(basename $src)"
    fi
}

# Main script
main() {
    log_info "Starting documentation reorganization..."

    if [ "$DRY_RUN" = true ]; then
        log_warning "DRY RUN MODE - No changes will be made"
    fi

    # Step 1: Create backup
    if [ "$DRY_RUN" = false ]; then
        log_info "Creating backup..."
        mkdir -p "$BACKUP_DIR"
        cp -r "$DOCS_DIR"/* "$BACKUP_DIR/" 2>/dev/null || true
        log_success "Backup created at: $BACKUP_DIR"
    else
        echo "Would create backup at: $BACKUP_DIR"
    fi

    # Step 2: Create new directory structure
    log_info "Creating new directory structure..."

    create_dir "$DOCS_DIR/01-setup"
    create_dir "$DOCS_DIR/05-status"
    create_dir "$DOCS_DIR/06-phases/completed"
    create_dir "$DOCS_DIR/06-phases/current"
    create_dir "$DOCS_DIR/06-phases/planning"
    create_dir "$DOCS_DIR/07-implementation/features"
    create_dir "$DOCS_DIR/07-implementation/workers"
    create_dir "$DOCS_DIR/07-implementation/bugfixes"
    create_dir "$DOCS_DIR/07-implementation/analysis"
    create_dir "$DOCS_DIR/08-testing"
    create_dir "$DOCS_DIR/09-ml-ai"
    create_dir "$DOCS_DIR/10-strategies"
    create_dir "$DOCS_DIR/11-cli"
    create_dir "$DOCS_DIR/12-configuration"
    create_dir "$DOCS_DIR/13-reports"

    # Step 3: Move files by category

    # Setup documents
    log_info "Moving setup documents..."
    move_file "$DOCS_DIR/COMPLETE_SETUP_AND_RUN_GUIDE.md" "$DOCS_DIR/01-setup/"
    move_file "$DOCS_DIR/SETUP_FROM_SCRATCH.md" "$DOCS_DIR/01-setup/"
    move_file "$DOCS_DIR/DEPLOYMENT_GUIDE.md" "$DOCS_DIR/01-setup/"
    move_file "$DOCS_DIR/MACOS_SETUP_VALIDATED.md" "$DOCS_DIR/01-setup/"
    move_file "$DOCS_DIR/DIRECT_PACKAGES_SETUP.md" "$DOCS_DIR/01-setup/"
    move_file "$DOCS_DIR/DEPLOYMENT_PACKAGE_COMPLETE.md" "$DOCS_DIR/01-setup/"
    move_file "$DOCS_DIR/PHASE4_UI_SETUP_GUIDE.md" "$DOCS_DIR/01-setup/"
    move_file "$DOCS_DIR/SUBMODULE_PUSH_GUIDE.md" "$DOCS_DIR/01-setup/"

    # Status documents
    log_info "Moving status documents..."
    move_file "$DOCS_DIR/EXECUTIVE_SUMMARY.md" "$DOCS_DIR/05-status/"
    move_file "$DOCS_DIR/COMPLETE_PROJECT_STATUS.md" "$DOCS_DIR/05-status/"
    move_file "$DOCS_DIR/CURRENT_STATUS.md" "$DOCS_DIR/05-status/"
    move_file "$DOCS_DIR/FEATURE_PROGRESS.md" "$DOCS_DIR/05-status/"
    move_file "$DOCS_DIR/FEATURE_PROGRESS_TABLE.md" "$DOCS_DIR/05-status/"
    move_file "$DOCS_DIR/FEATURE_2_PLAN.md" "$DOCS_DIR/05-status/"
    move_file "$DOCS_DIR/FEATURE_3_PLAN.md" "$DOCS_DIR/05-status/"
    move_file "$DOCS_DIR/QUICK_TRADE_POPUP_PROGRESS.md" "$DOCS_DIR/05-status/"
    move_file "$DOCS_DIR/PHASE1_TASK3_PORTFOLIO_POSITION_LIMITS.md" "$DOCS_DIR/05-status/"

    # Phase documents - Completed
    log_info "Moving completed phase documents..."
    move_file "$DOCS_DIR/PHASE_0_COMPLETION.md" "$DOCS_DIR/06-phases/completed/"
    move_file "$DOCS_DIR/PHASE_4.5_COMPLETE.md" "$DOCS_DIR/06-phases/completed/"
    move_file "$DOCS_DIR/PHASE_5.1_COMPLETE.md" "$DOCS_DIR/06-phases/completed/"
    move_file "$DOCS_DIR/PHASE_4.5_PROGRESS.md" "$DOCS_DIR/06-phases/completed/"
    move_file "$DOCS_DIR/PHASE_4.5_REFACTORING_EXAMPLE.md" "$DOCS_DIR/06-phases/completed/"

    # Phase documents - Current
    log_info "Moving current phase documents..."
    move_file "$DOCS_DIR/PHASE_5.2_ANALYTICS_PLAN.md" "$DOCS_DIR/06-phases/current/"

    # Phase documents - Planning
    log_info "Moving planning documents..."
    move_file "$DOCS_DIR/ENHANCEMENT_ROADMAP.md" "$DOCS_DIR/06-phases/planning/"
    move_file "$DOCS_DIR/PRIORITIZED_IMPLEMENTATION_PHASES.md" "$DOCS_DIR/06-phases/planning/"
    move_file "$DOCS_DIR/PRODUCTION_DEPLOYMENT_CHECKLIST.md" "$DOCS_DIR/06-phases/planning/"

    # Implementation - Features
    log_info "Moving feature implementation documents..."
    move_file "$DOCS_DIR/MULTI_ACCOUNT_FIX_SUMMARY.md" "$DOCS_DIR/07-implementation/features/"
    move_file "$DOCS_DIR/UNIFIED_LOGGER_IMPLEMENTATION_SUMMARY.md" "$DOCS_DIR/07-implementation/features/"
    move_file "$DOCS_DIR/UNIFIED_LOGGER_MIGRATION.md" "$DOCS_DIR/07-implementation/features/"
    move_file "$DOCS_DIR/CONFIG_MANAGER_IMPLEMENTATION.md" "$DOCS_DIR/07-implementation/features/"
    move_file "$DOCS_DIR/ADD_CURRENCY_FEATURE.md" "$DOCS_DIR/07-implementation/features/"
    move_file "$DOCS_DIR/CORRELATION_ID_IMPLEMENTATION.md" "$DOCS_DIR/07-implementation/features/"
    move_file "$DOCS_DIR/SOFT_DELETE_DESIGN.md" "$DOCS_DIR/07-implementation/features/"
    move_file "$DOCS_DIR/DEFAULT_CURRENCIES_IMPLEMENTATION.md" "$DOCS_DIR/07-implementation/features/"
    move_file "$DOCS_DIR/CONFIGURATION_IMPLEMENTATION_STATUS.md" "$DOCS_DIR/07-implementation/features/"
    move_file "$DOCS_DIR/ACCOUNT_BROKER_VALIDATION_FIX.md" "$DOCS_DIR/07-implementation/features/"
    move_file "$DOCS_DIR/ACCOUNT_FIELDS_GUIDE.md" "$DOCS_DIR/07-implementation/features/"

    # Implementation - Workers
    log_info "Moving worker implementation documents..."
    move_file "$DOCS_DIR/PHASE4_WORKER_MANAGER_SUMMARY.md" "$DOCS_DIR/07-implementation/workers/"
    move_file "$DOCS_DIR/PHASE5_WORKER_API_SUMMARY.md" "$DOCS_DIR/07-implementation/workers/"

    # Implementation - Bug fixes
    log_info "Moving bug fix documents..."
    move_file "$DOCS_DIR/ACCOUNTS_UI_BUG_FIXES_2025-12-28.md" "$DOCS_DIR/07-implementation/bugfixes/"
    move_file "$DOCS_DIR/DASHBOARD_API_FIXES_2025-12-28.md" "$DOCS_DIR/07-implementation/bugfixes/"
    move_file "$DOCS_DIR/CORS_BROWSER_CACHE_FIX.md" "$DOCS_DIR/07-implementation/bugfixes/"
    move_file "$DOCS_DIR/MARKET_HOURS_FIX.md" "$DOCS_DIR/07-implementation/bugfixes/"
    move_file "$DOCS_DIR/POSITION_SERVICE_IMPORT_FIX.md" "$DOCS_DIR/07-implementation/bugfixes/"
    move_file "$DOCS_DIR/CONFIG_UI_BACKEND_INTEGRATION.md" "$DOCS_DIR/07-implementation/bugfixes/"

    # Implementation - Analysis
    log_info "Moving analysis documents..."
    move_file "$DOCS_DIR/CODEBASE_ANALYSIS_AND_IMPLEMENTATION_PLAN.md" "$DOCS_DIR/07-implementation/analysis/"
    move_file "$DOCS_DIR/POSITION_OPENING_ANALYSIS.md" "$DOCS_DIR/07-implementation/analysis/"
    move_file "$DOCS_DIR/LOGGER_COMPARISON.md" "$DOCS_DIR/07-implementation/analysis/"

    # Testing documents
    log_info "Moving testing documents..."
    move_file "$DOCS_DIR/TEST_SUMMARY.md" "$DOCS_DIR/08-testing/"
    move_file "$DOCS_DIR/TEST_RESULTS.md" "$DOCS_DIR/08-testing/"
    move_file "$DOCS_DIR/TESTING_COMPLETE.md" "$DOCS_DIR/08-testing/"
    move_file "$DOCS_DIR/SOFT_DELETE_TESTING.md" "$DOCS_DIR/08-testing/"

    # ML/AI documents
    log_info "Moving ML/AI documents..."
    move_file "$DOCS_DIR/AI_ENHANCED_TRADING.md" "$DOCS_DIR/09-ml-ai/"
    move_file "$DOCS_DIR/ML_TRAINING_PHASES.md" "$DOCS_DIR/09-ml-ai/"
    move_file "$DOCS_DIR/ML_INTEGRATION.md" "$DOCS_DIR/09-ml-ai/"
    move_file "$DOCS_DIR/ML_QUICK_START.md" "$DOCS_DIR/09-ml-ai/"
    move_file "$DOCS_DIR/ML_COMPLETE.md" "$DOCS_DIR/09-ml-ai/"
    move_file "$DOCS_DIR/HOW_ML_MODEL_WAS_CREATED.md" "$DOCS_DIR/09-ml-ai/"
    move_file "$DOCS_DIR/MODELS_MIGRATION.md" "$DOCS_DIR/09-ml-ai/"

    # Strategy documents
    log_info "Moving strategy documents..."
    move_file "$DOCS_DIR/AGGRESSIVE_TRADING_GUIDE.md" "$DOCS_DIR/10-strategies/"
    move_file "$DOCS_DIR/PROFIT_MAXIMIZATION_STRATEGY.md" "$DOCS_DIR/10-strategies/"
    move_file "$DOCS_DIR/QUICK_START_INTERVAL_TRADING.md" "$DOCS_DIR/10-strategies/"

    # CLI documents
    log_info "Moving CLI documents..."
    move_file "$DOCS_DIR/CLI_USAGE.md" "$DOCS_DIR/11-cli/"
    move_file "$DOCS_DIR/CLI_IMPLEMENTATION.md" "$DOCS_DIR/11-cli/"
    move_file "$DOCS_DIR/CLI_ML_LLM_FLAGS.md" "$DOCS_DIR/11-cli/"
    move_file "$DOCS_DIR/CLI_ENHANCEMENT_SUMMARY.md" "$DOCS_DIR/11-cli/"

    # Configuration documents
    log_info "Moving configuration documents..."
    move_file "$DOCS_DIR/HYBRID_CONFIGURATION_DESIGN.md" "$DOCS_DIR/12-configuration/"

    # Reports
    log_info "Moving report documents..."
    move_file "$DOCS_DIR/REPORTS.md" "$DOCS_DIR/13-reports/"
    move_file "$DOCS_DIR/IMPLEMENTATION_SUMMARY.md" "$DOCS_DIR/13-reports/"
    move_file "$DOCS_DIR/PRIORITY_CHECKLIST.md" "$DOCS_DIR/13-reports/"

    # Architecture and API
    log_info "Moving architecture and API documents..."
    move_file "$DOCS_DIR/COMPLETE_SYSTEM_FLOW.md" "$DOCS_DIR/03-architecture/"
    move_file "$DOCS_DIR/API.md" "$DOCS_DIR/04-api/"

    # Archive old documents
    log_info "Moving documents to archive..."
    move_file "$DOCS_DIR/UI_ENHANCEMENT_SUMMARY.md" "$DOCS_DIR/99-archive/"
    move_file "$DOCS_DIR/ISSUE_RESOLUTION_SUMMARY.md" "$DOCS_DIR/99-archive/"
    move_file "$DOCS_DIR/ALERTS.md" "$DOCS_DIR/99-archive/"

    # Step 4: Replace README
    log_info "Updating main README..."
    if [ "$DRY_RUN" = false ]; then
        if [ -f "$DOCS_DIR/NEW_README.md" ]; then
            mv "$DOCS_DIR/README.md" "$DOCS_DIR/README.md.old"
            mv "$DOCS_DIR/NEW_README.md" "$DOCS_DIR/README.md"
            log_success "README updated (old version saved as README.md.old)"
        else
            log_warning "NEW_README.md not found, skipping README update"
        fi
    else
        echo "Would replace README.md with NEW_README.md"
    fi

    # Step 5: Summary
    log_info "Reorganization complete!"
    echo ""
    echo "Summary:"
    echo "  - New directory structure created"
    echo "  - Files organized by category"
    echo "  - Backup available at: $BACKUP_DIR"
    echo "  - Old README saved as: README.md.old"
    echo ""
    echo "Next steps:"
    echo "  1. Review the new structure"
    echo "  2. Test documentation navigation"
    echo "  3. Commit changes with git"
    echo "  4. Update any external links"
    echo ""
    log_success "All done! 🎉"
}

# Run main function
main
