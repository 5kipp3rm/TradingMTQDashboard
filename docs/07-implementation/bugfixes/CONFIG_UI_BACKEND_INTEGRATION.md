# Config UI Backend Integration

## Summary

Updated the Settings/Config page to integrate with the backend API for per-account risk management configuration. Risk settings are now loaded from and saved to the database instead of using hardcoded values.

## Changes Made

### 1. Updated Config.tsx Component

**File**: `dashboard/src/pages/Config.tsx`

#### Added Imports
- `useEffect` from React for loading data on mount
- `accountsApi` from the API client

#### Added State Management
```typescript
const [settingsPerAccount, setSettingsPerAccount] = useState<AccountSettings>({});
const [isLoading, setIsLoading] = useState(false);
const [isSaving, setIsSaving] = useState(false);
```

**Note**: Removed hardcoded initial state with account IDs "1", "2", "3" - now starts with empty object and loads from API.

#### Added useEffect Hook for Loading Config
```typescript
useEffect(() => {
  const loadAccountConfig = async () => {
    if (!currentAccountId || currentAccountId === "all") return;

    setIsLoading(true);
    try {
      const response = await accountsApi.getConfig(parseInt(currentAccountId, 10));

      if (response.data) {
        const config = response.data as any;

        // Extract risk settings from the trading_config
        if (config.trading_config?.risk) {
          const riskConfig = config.trading_config.risk;
          setSettingsPerAccount((prev) => ({
            ...prev,
            [currentAccountId]: {
              risk_percent: riskConfig.risk_percent || defaultRiskSettings.risk_percent,
              max_positions: riskConfig.max_positions || defaultRiskSettings.max_positions,
              max_concurrent_trades: riskConfig.max_concurrent_trades || defaultRiskSettings.max_concurrent_trades,
              portfolio_risk_percent: riskConfig.portfolio_risk_percent || defaultRiskSettings.portfolio_risk_percent,
              stop_loss_pips: riskConfig.stop_loss_pips || defaultRiskSettings.stop_loss_pips,
              take_profit_pips: riskConfig.take_profit_pips || defaultRiskSettings.take_profit_pips,
            },
          }));
        } else {
          // No risk config found, use defaults
          setSettingsPerAccount((prev) => ({
            ...prev,
            [currentAccountId]: { ...defaultRiskSettings },
          }));
        }
      }
    } catch (error) {
      console.error("Error loading account config:", error);
      toast({
        title: "Error",
        description: "Failed to load account configuration",
        variant: "destructive",
      });
      // Use defaults on error
      setSettingsPerAccount((prev) => ({
        ...prev,
        [currentAccountId]: { ...defaultRiskSettings },
      }));
    } finally {
      setIsLoading(false);
    }
  };

  loadAccountConfig();
}, [currentAccountId, toast]);
```

**Behavior**:
- Loads configuration when component mounts or when selected account changes
- Extracts risk settings from `trading_config.risk` in API response
- Falls back to default values if config doesn't exist or on error
- Shows error toast if API call fails

#### Updated handleSave Function
```typescript
const handleSave = async () => {
  if (!currentAccountId || currentAccountId === "all") {
    toast({
      title: "Error",
      description: "Please select a specific account to save settings",
      variant: "destructive",
    });
    return;
  }

  setIsSaving(true);
  try {
    // Prepare the configuration update payload
    const configUpdate = {
      trading_config: {
        risk: {
          risk_percent: currentSettings.risk_percent,
          max_positions: currentSettings.max_positions,
          max_concurrent_trades: currentSettings.max_concurrent_trades,
          portfolio_risk_percent: currentSettings.portfolio_risk_percent,
          stop_loss_pips: currentSettings.stop_loss_pips,
          take_profit_pips: currentSettings.take_profit_pips,
        },
      },
    };

    const response = await accountsApi.updateConfig(
      parseInt(currentAccountId, 10),
      configUpdate
    );

    if (response.data) {
      toast({
        title: "Settings Saved",
        description: "Your risk management settings have been saved successfully.",
      });
    } else if (response.error) {
      throw new Error(response.error);
    }
  } catch (error) {
    console.error("Error saving account config:", error);
    toast({
      title: "Error",
      description: error instanceof Error ? error.message : "Failed to save settings",
      variant: "destructive",
    });
  } finally {
    setIsSaving(false);
  }
};
```

**Behavior**:
- Validates that a specific account is selected (not "all")
- Sends PUT request to `/api/accounts/{id}/config` with nested risk settings
- Shows success toast on save
- Shows error toast if save fails
- Updates button state during save operation

#### Updated UI Components

**Save Button** - Now shows loading state:
```tsx
<Button onClick={handleSave} disabled={isSaving || isLoading}>
  {isSaving ? "Saving..." : "Save Changes"}
</Button>
```

**Risk Management Card Header** - Shows loading indicator:
```tsx
<CardTitle className="flex items-center gap-2">
  <span>⚠️</span> Risk Management
  {isLoading && <span className="text-sm text-muted-foreground">(Loading...)</span>}
</CardTitle>
```

**Account Name Display** - Fixed to use correct field:
```tsx
<p className="text-sm text-muted-foreground">
  Configuring: {selectedAccount.account_name || selectedAccount.name}
</p>
```

## API Integration

### API Endpoints Used

#### GET `/api/accounts/{account_id}/config`
**Purpose**: Load current configuration for an account

**Response Structure**:
```json
{
  "account_id": 1,
  "account_number": 23423423423,
  "account_name": "datameir",
  "config_source": "hybrid",
  "config_path": "config/accounts/account-23423423423.yml",
  "portable": true,
  "trading_config": {
    "risk": {
      "risk_percent": 2.0,
      "max_positions": 3,
      "max_concurrent_trades": 10,
      "portfolio_risk_percent": 15.0,
      "stop_loss_pips": 40,
      "take_profit_pips": 80
    },
    "currencies": [...],
    "strategy": {...},
    "position_management": {...}
  }
}
```

#### PUT `/api/accounts/{account_id}/config`
**Purpose**: Update account configuration

**Request Body**:
```json
{
  "trading_config": {
    "risk": {
      "risk_percent": 2.5,
      "max_positions": 3,
      "max_concurrent_trades": 10,
      "portfolio_risk_percent": 15.0,
      "stop_loss_pips": 40,
      "take_profit_pips": 80
    }
  }
}
```

**Note**: The PUT endpoint accepts partial updates. You can send only the `trading_config.risk` section without sending the entire configuration.

## User Experience Flow

### Loading Configuration
1. User navigates to Settings page
2. Component loads configuration from API for selected account
3. Loading indicator appears in card header
4. Form fields populate with current values
5. If no config exists, defaults are used
6. Loading indicator disappears when complete

### Editing Settings
1. User modifies any risk management field
2. Changes are stored in local state
3. Save button remains enabled
4. No API calls are made until user clicks "Save Changes"

### Saving Changes
1. User clicks "Save Changes" button
2. Button text changes to "Saving..." and becomes disabled
3. API PUT request sent with updated risk settings
4. Success toast shows "Settings Saved" message
5. Button returns to normal state
6. If error occurs, error toast with details is shown

### Error Handling
- **Load Error**: Shows error toast, uses default values, allows user to edit and save
- **Save Error**: Shows error toast with specific error message, allows retry
- **No Account Selected**: Prevents save with informative error message
- **Network Error**: Caught and displayed to user with option to retry

## Testing

### Manual Testing Performed

#### Test 1: Load Configuration
```bash
curl http://localhost:8000/api/accounts/1/config
```
✅ Returns configuration with risk settings

#### Test 2: Update Configuration
```bash
curl -X PUT http://localhost:8000/api/accounts/1/config \
  -H "Content-Type: application/json" \
  -d '{"trading_config": {"risk": {"risk_percent": 2.5, ...}}}'
```
✅ Updates and returns new configuration

#### Test 3: Verify Persistence
```bash
curl http://localhost:8000/api/accounts/1/config
```
✅ Shows updated values persisted to database

### UI Testing Checklist

- [x] Config page loads without errors
- [x] Loading indicator appears when fetching config
- [x] Form fields populate with API data
- [x] Changes are reflected in real-time as user types
- [x] Save button disabled during load/save operations
- [x] Save button shows "Saving..." text during save
- [x] Success toast appears on successful save
- [x] Error toast appears on save failure
- [x] Default values used when account has no config
- [x] Switching accounts loads new configuration

## Benefits

### Before
- Risk settings were hardcoded in the component
- Changes were not persisted
- Each account had static test values
- No synchronization with backend
- No validation or error handling

### After
- Risk settings loaded from database
- Changes persist across sessions
- Each account has unique, editable configuration
- Full integration with backend API
- Comprehensive error handling
- Loading states for better UX
- Toast notifications for user feedback

## Future Enhancements

1. **Real-time Validation**: Add client-side validation before save
2. **Undo/Reset**: Add button to reset to last saved values
3. **Configuration History**: Show history of configuration changes
4. **Bulk Operations**: Allow applying same config to multiple accounts
5. **Import/Export**: Allow exporting config as JSON/YAML for backup
6. **Configuration Templates**: Create and apply templates for common setups
7. **Field-level Help**: Add tooltips explaining each setting
8. **Advanced Mode**: Show/hide advanced settings based on user preference

## Related Documentation

- [UI Enhancement Summary](./UI_ENHANCEMENT_SUMMARY.md) - Overview of account configuration UI
- [Hybrid Configuration Design](./HYBRID_CONFIGURATION_DESIGN.md) - Backend configuration architecture
- [API Documentation](./API.md) - Complete API reference

## Files Modified

- `dashboard/src/pages/Config.tsx` - Main configuration page component
- `docs/CONFIG_UI_BACKEND_INTEGRATION.md` - This documentation file

## Dependencies

- Existing `accountsApi.getConfig()` method in `dashboard/src/lib/api.ts`
- Existing `accountsApi.updateConfig()` method in `dashboard/src/lib/api.ts`
- Backend endpoints: `GET /api/accounts/{id}/config` and `PUT /api/accounts/{id}/config`
- `useAccounts()` context hook for selected account
- `useToast()` hook for notifications
