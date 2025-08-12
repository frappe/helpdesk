#!/bin/bash
set -e

# Exit immediately if any command fails
function error_exit() {
    echo "ERROR: $1" >&2
    exit 1
}

function log_info() {
    echo "INFO: $1"
}

function log_warning() {
    echo "WARNING: $1"
}

cd ~ || error_exit "Failed to change to home directory"

log_info "Setting Up Bench..."

# Install frappe-bench with timeout
timeout 300 pip install frappe-bench || error_exit "Failed to install frappe-bench within 5 minutes"

# Initialize bench with timeout and better error handling
log_info "Initializing Frappe Bench..."
timeout 900 bench -v init frappe-bench \
    --skip-assets \
    --skip-redis-config-generation \
    --python "$(which python)" \
    --frappe-branch "${BASE_BRANCH}" || error_exit "Failed to initialize frappe-bench within 15 minutes"

cd ./frappe-bench || error_exit "Failed to change to frappe-bench directory"

log_info "Get Helpdesk..."
timeout 300 bench get-app --skip-assets helpdesk "${GITHUB_WORKSPACE}" || error_exit "Failed to get helpdesk app within 5 minutes"

log_info "Generating POT file..."
timeout 120 bench generate-pot-file --app helpdesk || error_exit "Failed to generate POT file within 2 minutes"

# Verify POT file was created
POT_FILE="./apps/helpdesk/helpdesk/locale/main.pot"
if [ ! -f "$POT_FILE" ]; then
    error_exit "POT file was not created at $POT_FILE"
fi

log_info "POT file successfully created with $(wc -l < "$POT_FILE") lines"

cd ./apps/helpdesk || error_exit "Failed to change to helpdesk directory"

log_info "Configuring git user..."
git config user.email "developers@erpnext.com"
git config user.name "frappe-pr-bot"

log_info "Setting the correct git remote..."
# Here, the git remote is a local file path by default. Let's change it to the upstream repo.
git remote set-url upstream https://github.com/frappe/helpdesk.git

log_info "Creating a new branch..."
isodate=$(date -u +"%Y-%m-%d")
branch_name="pot_${BASE_BRANCH}_${isodate}"

# Check if branch already exists and use timestamp if it does
if git ls-remote --exit-code --heads upstream "$branch_name" >/dev/null 2>&1; then
    timestamp=$(date -u +"%Y%m%d-%H%M%S")
    branch_name="pot_${BASE_BRANCH}_${timestamp}"
    log_warning "Branch already existed, using timestamp: $branch_name"
fi

git checkout -b "${branch_name}" || error_exit "Failed to create branch $branch_name"

log_info "Checking for changes..."
if git diff --quiet HEAD helpdesk/locale/main.pot; then
    log_info "No changes to POT file, skipping commit and PR creation"
    exit 0
fi

log_info "Committing changes..."
git add helpdesk/locale/main.pot
git commit -m "chore: update POT file

- Generated on $(date -u)
- Contains $(grep -c 'msgid' helpdesk/locale/main.pot) translatable strings
- Automated update via GitHub Actions" || error_exit "Failed to commit changes"

log_info "Setting up GitHub CLI authentication..."
gh auth setup-git || error_exit "Failed to setup GitHub CLI authentication"

log_info "Pushing changes to upstream..."
git push -u upstream "${branch_name}" || error_exit "Failed to push branch to upstream"

log_info "Creating a PR..."
PR_BODY="🤖 **Automated POT File Update**

This PR updates the translation template file (\`main.pot\`) with the latest translatable strings from the Helpdesk application.

**Changes:**
- Updated \`helpdesk/locale/main.pot\`
- Contains $(grep -c 'msgid' helpdesk/locale/main.pot) translatable strings
- Generated automatically on $(date -u)

**What this enables:**
- Crowdin can now sync with the latest translatable strings
- Translators can work on new strings that have been added
- Ensures translation coverage for recent code changes

**Verification:**
- ✅ POT file generated successfully
- ✅ Contains valid translation strings
- ✅ Ready for Crowdin synchronization

This is an automated update. Please review and merge to enable translation sync."

gh pr create \
    --title "chore: update POT file - $(date -u +"%Y-%m-%d")" \
    --body "$PR_BODY" \
    --base "${BASE_BRANCH}" \
    --head "${branch_name}" \
    -R frappe/helpdesk || error_exit "Failed to create pull request"

log_info "✅ Successfully created PR for POT file update!"
