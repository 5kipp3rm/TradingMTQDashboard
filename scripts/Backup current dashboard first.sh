# Backup current dashboard first
cp -r dashboard dashboard-backup

# Remove dashboard from git tracking but keep files
git rm -r --cached dashboard
git commit -m "Prepare for dashboard submodule conversion"

# Remove the directory
rm -rf dashboard

# Add as submodule pointing to trading-dashboard branch
git submodule add -b trading-dashboard https://github.com/5kipp3rm/TradingMTQDashboard dashboard

# Commit the submodule
git add .gitmodules dashboard
git commit -m "Add dashboard as submodule (trading-dashboard branch)"

# Update dashboard to latest from remote
cd dashboard
git pull origin trading-dashboard
cd ..

# Commit the submodule update in main repo
git add dashboard
git commit -m "Update dashboard submodule"
git push
Temp@1234