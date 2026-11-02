import { test, expect, type Browser, type Page } from '@playwright/test';

/**
 * Core journey against the real Django API (seeded database, port 8000).
 * Creates its own startup with a unique name and deletes it in the last step.
 */
const run = Date.now();
const STARTUP = `Journey Labs ${run}`;
const ROOM = `Diligence Room ${run}`;
const DOC = `Traction Report ${run}`;

const FOUNDER = { email: 'founder@investo.com', password: 'founder123', home: '/founder' };
const INVESTOR = { email: 'investor@investo.com', password: 'investor123', home: '/investor' };
const ADMIN = { email: 'admin@investo.com', password: 'admin123', home: '/admin' };

async function signIn(page: Page, who: { email: string; password: string; home: string }) {
  await page.goto('/auth/login');
  await page.getByRole('textbox', { name: 'Email' }).fill(who.email);
  await page.getByLabel('Password', { exact: true }).fill(who.password);
  await page.getByRole('button', { name: 'Sign In' }).click();
  await expect(page).toHaveURL(new RegExp(`${who.home}$`));
}

async function session(browser: Browser, who: typeof FOUNDER) {
  const context = await browser.newContext();
  const page = await context.newPage();
  page.on('dialog', (d) => d.accept());
  await signIn(page, who);
  return page;
}

test.describe.serial('core journey', () => {
  test.setTimeout(90_000);

  let founder: Page;
  let investor: Page;
  let startupPath = '';

  const dealCard = (page: Page) => page.locator(`[data-startup="${STARTUP}"]`);

  test('signed-out visitors see the landing page and are kept out of the app', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('heading', { name: 'How it works' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'For founders' })).toBeVisible();
    await page.goto('/founder');
    await expect(page).toHaveURL(/\/auth\/login\?next=%2Ffounder/);
  });

  test('a wrong password shows the real error, not "session expired"', async ({ page }) => {
    await page.goto('/auth/login');
    await page.getByRole('textbox', { name: 'Email' }).fill(FOUNDER.email);
    await page.getByLabel('Password', { exact: true }).fill('definitely-wrong');
    await page.getByRole('button', { name: 'Sign In' }).click();
    await expect(page.getByRole('alert').filter({ hasText: 'Invalid email or password' })).toBeVisible();
    await expect(page.getByText(/session expired/i)).toHaveCount(0);
    await expect(page).toHaveURL(/\/auth\/login/);
  });

  test('founder creates and publishes a startup, and refresh keeps the session', async ({ browser }) => {
    founder = await session(browser, FOUNDER);
    await founder.goto('/founder/startups/new');
    await founder.getByLabel('Startup name *').fill(STARTUP);
    await founder.getByLabel('Tagline *').fill('Proving the whole journey works');
    await founder.getByLabel('Industry *').selectOption('saas');
    await founder.getByLabel('Stage *').selectOption('seed');
    await founder.getByLabel('Funding goal ($)').fill('200000');
    await founder.getByRole('button', { name: 'Add member' }).click();
    await founder.getByLabel('Team member 1 name').fill('Ada Tester');
    await founder.getByLabel('Team member 1 role').fill('CTO');
    await founder.getByRole('button', { name: 'Save and publish' }).click();
    await expect(founder).toHaveURL(/\/founder\/startups$/);

    const card = founder.locator('[data-testid^="startup-card-"]').filter({ hasText: STARTUP });
    await expect(card.getByText('active', { exact: true })).toBeVisible();
    const testId = await card.getAttribute('data-testid');
    startupPath = `/startup/${testId!.replace('startup-card-', '')}`;

    // F5: identity must survive, so the role navigation and page stay put.
    await founder.reload();
    await expect(founder).toHaveURL(/\/founder\/startups$/);
    await expect(founder.getByRole('link', { name: 'Deal Pipeline' })).toBeVisible();
    await expect(card).toBeVisible();
    // The startup page shows what was entered.
    await founder.goto(startupPath);
    await expect(founder.getByRole('heading', { name: STARTUP })).toBeVisible();
    await expect(founder.getByText('Ada Tester')).toBeVisible();
  });

  test('founder creates a data room and uploads a file', async () => {
    await founder.goto('/founder/data-room');
    const startupSelect = founder.getByLabel('Startup', { exact: true });
    await expect(startupSelect.locator('option', { hasText: STARTUP })).toHaveCount(1);
    await startupSelect.selectOption({ label: STARTUP });
    await founder.getByRole('button', { name: 'New room' }).click();
    await founder.getByLabel('Room title').fill(ROOM);
    await founder.getByRole('button', { name: 'Create room' }).click();
    await expect(founder.getByRole('heading', { name: ROOM })).toBeVisible();

    await founder.getByLabel('Document title').fill(DOC);
    await founder.getByLabel('File').setInputFiles({ name: 'traction.txt', mimeType: 'text/plain', buffer: Buffer.from('dummy traction report') });
    await founder.getByRole('button', { name: 'Upload document' }).click();
    await expect(founder.getByRole('list', { name: 'Room documents' }).getByText(DOC)).toBeVisible();
  });

  test('investor discovers the startup, requests the data room and expresses interest', async ({ browser }) => {
    investor = await session(browser, INVESTOR);
    await investor.goto('/investor/discover');
    await investor.getByLabel('Search startups').fill(STARTUP);
    await investor.getByRole('heading', { name: STARTUP }).click();
    await expect(investor).toHaveURL(new RegExp(`${startupPath}$`));
    await expect(investor.getByTestId('funding-raised')).toHaveText('$0 raised');

    const access = investor.getByTestId('data-room-access');
    await expect(access.getByText(ROOM)).toBeVisible();
    await access.getByRole('button', { name: 'Request access' }).click();
    await expect(access.getByText('awaiting founder')).toBeVisible();

    // Not approved yet, so the document must not be reachable.
    await investor.goto('/investor/data-room');
    await expect(investor.getByText(/Your access requests/)).toBeVisible();
    await expect(investor.getByText(DOC)).toHaveCount(0);

    await investor.goto(startupPath);
    await investor.getByRole('button', { name: 'Express interest' }).click();
    await investor.getByRole('dialog').getByRole('button', { name: 'Send interest' }).click();
    await expect(investor.getByRole('link', { name: 'In pipeline: Interested' })).toBeVisible();
  });

  test('founder approves access and the investor can then see the document', async () => {
    await founder.goto('/founder/data-room');
    const request = founder.locator(`[data-room="${ROOM}"]`);
    await request.getByRole('button', { name: 'Approve' }).click();
    await expect(request.getByText('approved')).toBeVisible();

    await investor.goto('/investor/data-room');
    await expect(investor.getByRole('list', { name: 'Accessible documents' }).getByText(DOC)).toBeVisible();
  });

  test('investor moves the deal through the stages and sends a term sheet', async () => {
    await investor.goto('/investor/deals');
    for (const [button, column] of [
      ['Move to Meeting Scheduled', 'meeting_scheduled'],
      ['Move to Due Diligence', 'due_diligence'],
      ['Move to Negotiating', 'negotiating'],
    ]) {
      await dealCard(investor).getByRole('button', { name: button }).click();
      await expect(investor.locator(`[data-stage="${column}"]`).locator(`[data-startup="${STARTUP}"]`)).toBeVisible();
    }
    await dealCard(investor).getByRole('button', { name: 'Send term sheet' }).click();
    const dialog = investor.getByRole('dialog');
    await dialog.getByLabel('Amount offered ($)').fill('50000');
    await dialog.getByLabel('Equity (%)').fill('5');
    await dialog.getByRole('button', { name: 'Send term sheet' }).click();
    await expect(investor.locator('[data-stage="term_sheet_sent"]').locator(`[data-startup="${STARTUP}"]`)).toBeVisible();
    // The founder has not accepted, so closing must be blocked.
    await expect(dealCard(investor).getByText('Awaiting founder acceptance')).toBeVisible();
    await expect(dealCard(investor).getByRole('button', { name: 'Close deal' })).toBeDisabled();
  });

  test('founder accepts the term sheet', async () => {
    await founder.goto('/founder/deals');
    await dealCard(founder).getByRole('button', { name: 'Accept term sheet' }).click();
    await expect(dealCard(founder).getByText('Founder accepted the term sheet')).toBeVisible();
  });

  test('investor closes the deal and funding progress updates', async () => {
    await investor.goto('/investor/deals');
    await expect(dealCard(investor).getByText('Founder accepted the term sheet')).toBeVisible();
    await dealCard(investor).getByRole('button', { name: 'Close deal' }).click();
    const dialog = investor.getByRole('dialog');
    await dialog.getByLabel('Final amount ($)').fill('50000');
    await dialog.getByRole('button', { name: 'Close deal' }).click();
    await expect(investor.locator('[data-stage="invested"]').locator(`[data-startup="${STARTUP}"]`)).toBeVisible();

    await investor.goto(startupPath);
    await expect(investor.getByTestId('funding-raised')).toHaveText('$50,000 raised');
    await expect(investor.getByTestId('funding-progress')).toContainText('25% raised');
    await expect(investor.getByText('funded', { exact: true })).toBeVisible();
  });

  test('role guards redirect, and sign out revokes the session', async () => {
    await investor.goto('/admin');
    await expect(investor).toHaveURL(/\/investor$/);
    const refresh = await investor.evaluate(() => localStorage.getItem('refresh_token'));
    await investor.getByRole('button', { name: 'Sign out' }).click();
    await expect(investor).toHaveURL(/\/auth\/login/);
    // The server must have blacklisted the token, not just the browser forgetting it.
    const replay = await investor.request.post('http://localhost:8000/api/v1/auth/refresh/', { data: { refresh } });
    expect(replay.status()).toBe(401);
    await investor.goto('/investor');
    await expect(investor).toHaveURL(/\/auth\/login/);
    await investor.context().close();
  });

  test('admin pages load real data', async ({ browser }) => {
    const admin = await session(browser, ADMIN);
    await expect(admin.getByRole('heading', { name: 'Admin Dashboard' })).toBeVisible();
    await expect(admin.getByTestId('metric-total_users')).not.toHaveText('0');
    await expect(admin.getByTestId('metric-total_startups')).not.toHaveText('0');

    await admin.goto('/admin/users');
    await expect(admin.getByTestId(`user-${FOUNDER.email}`)).toBeVisible();

    await admin.goto('/admin/startups');
    await expect(admin.getByRole('link', { name: STARTUP }).first()).toBeVisible();

    await admin.goto('/admin/risk');
    await expect(admin.getByTestId('recent-bans')).toHaveText(/^\d+$/);
    await expect(admin.getByText('Mike Ross')).toHaveCount(0);

    await admin.goto('/admin/ops');
    await expect(admin.getByTestId('service-database')).toContainText('healthy');
    await expect(admin.getByText('Chart placeholder')).toHaveCount(0);

    await admin.goto('/admin/revenue');
    await expect(admin.getByText('no real payments')).toBeVisible();
    await expect(admin.getByText('Chart placeholder')).toHaveCount(0);

    await admin.goto('/admin/audit');
    await expect(admin.getByRole('heading', { name: 'Audit Logs' })).toBeVisible();
    await admin.goto('/admin/tickets');
    await expect(admin.getByRole('heading', { name: 'Support Tickets' })).toBeVisible();
    await admin.context().close();
  });

  test('founder deletes the test startup', async () => {
    await founder.goto('/founder/startups');
    const card = founder.locator('[data-testid^="startup-card-"]').filter({ hasText: STARTUP });
    await card.getByRole('button', { name: 'Delete' }).click();
    await expect(card).toHaveCount(0);
    await founder.context().close();
  });
});
