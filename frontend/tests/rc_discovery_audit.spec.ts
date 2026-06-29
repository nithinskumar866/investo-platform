import { test, expect } from '@playwright/test';
import fs from 'fs';
import path from 'path';

const BASE_URL = 'http://localhost:3000';
const RESULTS: any[] = [];
// Save into brain artifact directory
const ARTIFACT_DIR = 'C:\\Users\\nithi\\.gemini\\antigravity-ide\\brain\\ff67cf83-3db9-4c63-98f5-e6d4f1924146\\scratch';

if (!fs.existsSync(ARTIFACT_DIR)) {
  fs.mkdirSync(ARTIFACT_DIR, { recursive: true });
}

test.describe.serial('RC Discovery Audit', () => {
  let errors: string[] = [];
  let apiFailures: string[] = [];
  let apiCount = 0;

  test.beforeEach(async ({ page }) => {
    errors = [];
    apiFailures = [];
    page.on('pageerror', err => errors.push(`[Runtime] ${err.message}`));
    page.on('console', msg => {
      if (msg.type() === 'error' && !msg.text().includes('favicon') && !msg.text().includes('Warning:')) {
        errors.push(`[Console] ${msg.text()}`);
      }
    });
    page.on('response', response => {
      if (response.url().includes('/api/')) {
        apiCount++;
        if (!response.ok()) {
          apiFailures.push(`[API ${response.status()}] ${response.url()}`);
        }
      }
    });
  });

  async function checkPage(page: import('@playwright/test').Page, role: string, routePath: string, name: string) {
    let emptyScreen = false;
    let screenshotFile = '';
    let pass = 'PASS';
    let rootCause = 'None';
    let severity = 'None';
    
    try {
      const response = await page.goto(`${BASE_URL}${routePath}`, { waitUntil: 'domcontentloaded', timeout: 30000 });
      await page.waitForTimeout(2000); // let hydration and queries finish
      const content = await page.content();
      const is404 = response?.status() === 404 || await page.locator('.next-error-h1').isVisible();
      emptyScreen = content.includes('Application Error') || content.includes('An unexpected error has occurred');
      
      const safeName = role.toLowerCase() + '_' + name.replace(/[^a-z0-9]/gi, '_').toLowerCase();
      screenshotFile = `${ARTIFACT_DIR}\\${safeName}.png`;
      await page.screenshot({ path: screenshotFile, fullPage: true });

      if (is404) {
          pass = 'FAIL';
          rootCause = 'Page not found (404)';
          severity = 'P0';
      } else if (emptyScreen) {
          pass = 'FAIL';
          rootCause = 'Application Error / Hydration crash';
          severity = 'P0';
      } else if (errors.length > 0 || apiFailures.length > 0) {
          pass = 'FAIL';
          rootCause = 'Console or API Error';
          severity = 'P1';
      }

      RESULTS.push({
        Role: role,
        Flow: name,
        Path: routePath,
        Pass: pass,
        Severity: severity,
        RootCause: rootCause,
        Errors: [...errors, ...apiFailures].slice(0, 5).join(' | ') || (emptyScreen ? '[Screen] Application Error' : ''),
        Screenshot: screenshotFile,
        APICount: apiCount
      });
    } catch (e: any) {
      RESULTS.push({ 
          Role: role, Flow: name, Path: routePath, Pass: 'FAIL', Severity: 'P0', 
          RootCause: 'Timeout or Crash', Errors: `[Timeout/Crash] ${e.message}`, Screenshot: '', APICount: apiCount 
      });
    }
    errors = [];
    apiFailures = [];
  }

  test('Unauthenticated Flow', async ({ page }) => {
    test.setTimeout(180000);
    await checkPage(page, 'Guest', '/', 'Landing Page');
    await checkPage(page, 'Guest', '/auth/login', 'Login');
    await checkPage(page, 'Guest', '/auth/register', 'Register');
    await checkPage(page, 'Guest', '/auth/forgot-password', 'Forgot Password');
  });

  test('Founder Flow', async ({ page }) => {
    test.setTimeout(600000);
    await page.goto(`${BASE_URL}/auth/login`);
    await page.fill('input[type="email"]', 'founder@investo.com');
    await page.fill('input[type="password"]', 'founder123');
    await page.click('button[type="submit"]');
    await page.waitForURL('**/founder', { timeout: 30000 }).catch(() => {});
    
    const routes = [
        { path: '/founder', name: 'Dashboard' },
        { path: '/founder/analytics', name: 'Analytics' },
        { path: '/founder/data-room', name: 'Data Room' },
        { path: '/founder/deals', name: 'Deals' },
        { path: '/founder/discover', name: 'Discover' },
        { path: '/founder/insights', name: 'Insights' },
        { path: '/founder/matches', name: 'Matches' },
        { path: '/founder/startups', name: 'Startups' },
        { path: '/founder/startups/new', name: 'New Startup' },
        { path: '/chat', name: 'Chat List' },
        { path: '/billing', name: 'Billing' },
        { path: '/feed', name: 'Feed' },
        { path: '/meetings', name: 'Meetings' },
        { path: '/notifications', name: 'Notifications' },
        { path: '/search', name: 'Search' },
        { path: '/trending', name: 'Trending' }
    ];
    for (const r of routes) {
        await checkPage(page, 'Founder', r.path, r.name);
    }
  });

  test('Investor Flow', async ({ page }) => {
    test.setTimeout(600000);
    await page.goto(`${BASE_URL}/auth/login`);
    await page.fill('input[type="email"]', 'investor@investo.com');
    await page.fill('input[type="password"]', 'investor123');
    await page.click('button[type="submit"]');
    await page.waitForURL('**/investor', { timeout: 30000 }).catch(() => {});
    
    const routes = [
        { path: '/investor', name: 'Dashboard' },
        { path: '/investor/analytics', name: 'Analytics' },
        { path: '/investor/deals', name: 'Deals' },
        { path: '/investor/discover', name: 'Discover' },
        { path: '/investor/insights', name: 'Insights' },
        { path: '/investor/matches', name: 'Matches' },
        { path: '/investor/saved', name: 'Saved' },
        { path: '/chat', name: 'Chat List' },
        { path: '/billing', name: 'Billing' },
        { path: '/feed', name: 'Feed' },
        { path: '/meetings', name: 'Meetings' },
        { path: '/notifications', name: 'Notifications' },
        { path: '/search', name: 'Search' },
        { path: '/trending', name: 'Trending' }
    ];
    for (const r of routes) {
        await checkPage(page, 'Investor', r.path, r.name);
    }
  });

  test('Admin Flow', async ({ page }) => {
    test.setTimeout(600000);
    await page.goto(`${BASE_URL}/auth/login`);
    await page.fill('input[type="email"]', 'admin@investo.com');
    await page.fill('input[type="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForURL('**/admin', { timeout: 30000 }).catch(() => {});
    
    const routes = [
        { path: '/admin', name: 'Dashboard' },
        { path: '/admin/audit', name: 'Audit' },
        { path: '/admin/ops', name: 'Ops' },
        { path: '/admin/revenue', name: 'Revenue' },
        { path: '/admin/risk', name: 'Risk' },
        { path: '/admin/startups', name: 'Startups' },
        { path: '/admin/tickets', name: 'Tickets' },
        { path: '/admin/users', name: 'Users' }
    ];
    for (const r of routes) {
        await checkPage(page, 'Admin', r.path, r.name);
    }
  });

  test.afterAll(() => {
    fs.writeFileSync(path.join(ARTIFACT_DIR, 'rc_discovery_audit.json'), JSON.stringify(RESULTS, null, 2));
    console.log("\\n=== RC DISCOVERY AUDIT RESULTS ===");
    console.table(RESULTS.map(r => ({ Role: r.Role, Path: r.Path, Pass: r.Pass, Severity: r.Severity })));
  });
});
