import { test, expect } from '@playwright/test';

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should display dashboard summary cards', async ({ page }) => {
    await expect(page.getByText('Total Trades')).toBeVisible();
    await expect(page.getByText('Net Profit')).toBeVisible();
    await expect(page.getByText('Win Rate')).toBeVisible();
    await expect(page.getByText('Avg Daily Profit')).toBeVisible();
  });

  test('should show open positions table', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /open positions/i })).toBeVisible();
  });

  test('should allow changing time period', async ({ page }) => {
    const periodSelect = page.locator('select').first();
    await periodSelect.selectOption('7');
    
    // Wait for data to refresh
    await page.waitForTimeout(1000);
  });

  test('should open quick trade modal', async ({ page }) => {
    await page.getByRole('button', { name: /quick trade/i }).click();
    await expect(page.getByRole('dialog')).toBeVisible();
    await expect(page.getByText(/place a quick trade/i)).toBeVisible();
  });

  test('should show confirmation before closing all positions', async ({ page }) => {
    const closeAllBtn = page.getByRole('button', { name: /close all/i });
    if (await closeAllBtn.isVisible()) {
      await closeAllBtn.click();
      await expect(page.getByText(/close all positions/i)).toBeVisible();
      await page.getByRole('button', { name: /cancel/i }).click();
    }
  });
});

test.describe('Accounts Page', () => {
  test('should navigate to accounts page', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('link', { name: /accounts/i }).click();
    await expect(page).toHaveURL('/accounts');
    await expect(page.getByRole('heading', { name: /trading accounts/i })).toBeVisible();
  });

  test('should open add account modal', async ({ page }) => {
    await page.goto('/accounts');
    await page.getByRole('button', { name: /add account/i }).click();
    await expect(page.getByRole('dialog')).toBeVisible();
  });
});

test.describe('Strategies Page', () => {
  test('should display strategies', async ({ page }) => {
    await page.goto('/strategies');
    await expect(page.getByRole('heading', { name: /trading strategies/i })).toBeVisible();
  });

  test('should filter strategies', async ({ page }) => {
    await page.goto('/strategies');
    const searchInput = page.getByPlaceholder(/search strategies/i);
    if (await searchInput.isVisible()) {
      await searchInput.fill('MA');
    }
  });
});
