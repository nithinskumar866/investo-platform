import { test, expect } from '@playwright/test';
import fs from 'fs';
import path from 'path';

const BASE_URL = 'http://localhost:3000';
const ARTIFACT_DIR = 'C:\\Users\\nithi\\.gemini\\antigravity-ide\\brain\\fd444762-25ce-4671-ac6b-7e9ab7e0e2fd\\scratch';

if (!fs.existsSync(ARTIFACT_DIR)) {
  fs.mkdirSync(ARTIFACT_DIR, { recursive: true });
}

const RESULTS: any[] = [];

test.describe.serial('Comprehensive Platform Audit', () => {
  let errors: string[] = [];
  let apiFailures: string[] = [];

  test.beforeEach(async ({ page }) => {
    errors = [];
    apiFailures = [];
    page.on('pageerror', err => errors.push(`[Exception] ${err.message}`));
    page.on('console', msg => {
      if (msg.type() === 'error' && !msg.text().includes('favicon') && !msg.text().includes('Warning:')) {
        errors.push(`[Console] ${msg.text()}`);
      }
    });
    page.on('response', response => {
      if (!response.ok() && response.url().includes('/api/') && response.request().method() === 'GET') {
        apiFailures.push(`[API ${response.status()}] ${response.url()}`);
      }
    });
  });

  async function checkPage(page: any, routePath: string, name: string) {
    let emptyScreen = false;
    try {
      await page.goto(`${BASE_URL}${routePath}`, { waitUntil: 'domcontentloaded', timeout: 20000 });
      await page.waitForTimeout(2000); // let hydration and queries finish
      const content = await page.content();
      emptyScreen = content.includes('Application Error') || content.includes('An unexpected error has occurred');

      const screenshotName = `audit_${name.replace(/[:\/ ]/g, '_')}.png`;
      await page.screenshot({ path: path.join(ARTIFACT_DIR, screenshotName) });

      RESULTS.push({
        Flow: name,
        Path: routePath,
        Pass: errors.length === 0 && apiFailures.length === 0 && !emptyScreen ? 'PASS' : 'FAIL',
        Screenshot: screenshotName,
        Errors: [...errors, ...apiFailures].join(' | ') || (emptyScreen ? '[Screen] Application Error' : '')
      });
    } catch (e: any) {
      RESULTS.push({ Flow: name, Path: routePath, Pass: 'FAIL', Screenshot: null, Errors: `[Timeout/Crash] ${e.message}` });
    }
    errors = [];
    apiFailures = [];
  }

  test('Admin Full Flow', async ({ page, context }) => {
    test.setTimeout(240000);
    await context.clearCookies();
    await page.goto(`${BASE_URL}/auth/login`);
    await page.evaluate(() => localStorage.clear()).catch(()=>{});
    await page.goto(`${BASE_URL}/auth/login`);
    await page.waitForLoadState('domcontentloaded');
    await page.fill('input[type="email"]', 'admin@investo.com');
    await page.fill('input[type="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForURL('**/admin', { timeout: 15000 }).catch(() => {});
    
    const adminRoutes = [
      '/admin', '/admin/audit', '/admin/ops', '/admin/revenue'
    ];
    for (const route of adminRoutes) {
      await checkPage(page, route, `Admin: ${route}`);
    }
  });

  test('Founder Full Flow', async ({ page, context }) => {
    test.setTimeout(300000);
    await context.clearCookies();
    await page.goto(`${BASE_URL}/auth/login`);
    await page.evaluate(() => localStorage.clear()).catch(()=>{});
    await page.goto(`${BASE_URL}/auth/login`);
    await page.waitForLoadState('domcontentloaded');
    await page.fill('input[type="email"]', 'founder@test.com');
    await page.fill('input[type="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForURL('**/founder', { timeout: 15000 }).catch(() => {});
    
    const founderRoutes = [
      '/founder/analytics', '/founder/data-room', '/founder/discover', '/founder/insights'
    ];
    for (const route of founderRoutes) {
      await checkPage(page, route, `Founder: ${route}`);
    }

    // Run Shared Routes under Founder context
    const sharedRoutes = [
      '/search', '/trending', '/notifications'
    ];
    for (const route of sharedRoutes) {
      await checkPage(page, route, `Shared: ${route}`);
    }
  });

  test('Investor Full Flow', async ({ page, context }) => {
    test.setTimeout(240000);
    await context.clearCookies();
    await page.goto(`${BASE_URL}/auth/login`);
    await page.evaluate(() => localStorage.clear()).catch(()=>{});
    await page.goto(`${BASE_URL}/auth/login`);
    await page.waitForLoadState('domcontentloaded');
    await page.fill('input[type="email"]', 'investor@test.com');
    await page.fill('input[type="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForURL('**/investor', { timeout: 15000 }).catch(() => {});
    
    const investorRoutes = [
      '/investor/analytics', '/investor/deals', '/investor/discover',
      '/investor/insights', '/investor/matches', '/investor/saved'
    ];
    for (const route of investorRoutes) {
      await checkPage(page, route, `Investor: ${route}`);
    }
  });

  test.afterAll(() => {
    fs.writeFileSync(path.join(ARTIFACT_DIR, 'comprehensive_audit_prod.json'), JSON.stringify(RESULTS, null, 2));
  });
});
