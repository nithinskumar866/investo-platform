import { test, expect } from '@playwright/test';
import * as path from 'path';

const BASE_URL = 'http://localhost:3000';
const API_URL = 'http://localhost:8000';
const ARTIFACT_DIR = path.join(process.cwd(), '..', '..', 'brain', process.env.CONVERSATION_ID || '', 'scratch');

test.describe('Final End-to-End Chat Validation', () => {
  test.beforeAll(() => {
    require('child_process').execSync('python manage.py flush --no-input', { cwd: '../' });
  });
  test.setTimeout(900000);

  test('Complete Entrepreneur to Investor Chat Workflow', async ({ browser }) => {
    test.setTimeout(900000); // 10 minutes timeout for slow backend
    
    // ---------------------------------------------------------
    // Phase 1: Entrepreneur (Nathan) Setup
    // ---------------------------------------------------------
    const contextN = await browser.newContext();
    const pageN = await contextN.newPage();
    const nathanEmail = `nathan_${Date.now()}@test.com`;
    const startupName = `Nathan Innovations ${Date.now()}`;
    
    // Register Nathan
    await pageN.goto(`${BASE_URL}/auth/register`);
    await pageN.getByText('I have a startup').click();
    await pageN.fill('input[name="first_name"]', 'Nathan');
    await pageN.fill('input[name="last_name"]', 'Founder');
    await pageN.fill('input[name="email"]', nathanEmail);
    await pageN.fill('input[name="password"]', 'StrongPass123!');
    await pageN.fill('input[name="confirm_password"]', 'StrongPass123!');
    await pageN.getByRole('button', { name: 'Create Account' }).click();
    
    // Wait for redirect to login
    await pageN.waitForURL('**/auth/login', { timeout: 180000 });
    await pageN.waitForTimeout(2000); // Give backend a sec
    
    // Login Nathan
    await pageN.fill('input[name="email"]', nathanEmail);
    await pageN.fill('input[name="password"]', 'StrongPass123!');
    await pageN.getByRole('button', { name: 'Sign In' }).click();
    await expect(pageN).toHaveURL(/.*founder/, { timeout: 180000 });
    
    // Fallback API call for onboarding
    const storeNStr = await pageN.evaluate(() => localStorage.getItem('access_token'));
    const tokenN = storeNStr ? storeNStr : null;
    await pageN.request.patch(`${API_URL}/api/v1/auth/profile/entrepreneur/`, {
      headers: { Authorization: `Bearer ${tokenN}` },
      data: {
        bio: 'I am a founder.',
        linkedin_url: 'https://linkedin.com/in/nathan',
        onboarding_completed: true
      }
    });
    
    // Create Startup via UI
    await pageN.goto(`${BASE_URL}/founder/startups/new`);
    await expect(pageN).toHaveURL(/.*founder\/startups\/new/, { timeout: 180000 });
    await pageN.fill('input[name="name"]', startupName);
    await pageN.fill('input[name="tagline"]', 'Changing the world');
    await pageN.fill('textarea[name="description"]', 'A great startup description here.');
    await pageN.selectOption('select[name="industry"]', 'ai_ml');
    await pageN.selectOption('select[name="stage"]', 'pre_seed');
    await pageN.selectOption('select[name="funding_status"]', 'raising');
    await pageN.getByRole('button', { name: 'Create Startup' }).click();
    await expect(pageN).toHaveURL(/.*founder\/startups/, { timeout: 180000 });

    // ---------------------------------------------------------
    // Phase 2: Investor (Sandhya) Setup
    // ---------------------------------------------------------
    const contextS = await browser.newContext();
    const pageS = await contextS.newPage();
    const sandhyaEmail = `sandhya_${Date.now()}@test.com`;
    
    // Register Sandhya
    await pageS.goto(`${BASE_URL}/auth/register`);
    await pageS.getByText('I want to invest').click();
    await pageS.fill('input[name="first_name"]', 'Sandhya');
    await pageS.fill('input[name="last_name"]', 'Investor');
    await pageS.fill('input[name="email"]', sandhyaEmail);
    await pageS.fill('input[name="password"]', 'StrongPass123!');
    await pageS.fill('input[name="confirm_password"]', 'StrongPass123!');
    await pageS.getByRole('button', { name: 'Create Account' }).click();
      // Wait for redirect to login
      await pageS.waitForURL('**/auth/login', { timeout: 180000 });
      await pageS.waitForTimeout(2000);
      
      // Login Sandhya
      await pageS.fill('input[name="email"]', sandhyaEmail);
      await pageS.fill('input[name="password"]', 'StrongPass123!');
      await pageS.click('button:has-text("Sign In")');
    await expect(pageS).toHaveURL(/.*investor/, { timeout: 180000 });
    
    // Fallback API call for onboarding/profile since UI doesn't exist
    const storeSStr = await pageS.evaluate(() => localStorage.getItem('access_token'));
    const tokenS = storeSStr ? storeSStr : null;
    await pageS.request.patch(`${API_URL}/api/v1/auth/profile/investor/`, {
      headers: { Authorization: `Bearer ${tokenS}` },
      data: {
        investor_type: 'vc',
        preferred_stages: ['pre_seed'],
        preferred_industries: ['ai_ml'],
        onboarding_completed: true
      }
    });
    
    // ---------------------------------------------------------
    // Phase 3 & 4: Matching
    // ---------------------------------------------------------
    // Trigger Match Generation asynchronously via API
    await pageS.request.get(`${API_URL}/api/v1/matching/investor/matches/?reload=true`, {
      headers: { Authorization: `Bearer ${tokenS}` }
    });
    await pageS.waitForTimeout(2000); // Give backend time to generate
    
    await pageS.goto(`${BASE_URL}/investor/matches`);
    await pageS.waitForTimeout(2000); // Wait for matches to load
    
    // Verify Nathan's startup appears
    await expect(pageS.getByText(startupName)).toBeVisible({ timeout: 30000 });
    
    // ---------------------------------------------------------
    // Phase 5: Complete Chat Validation
    // ---------------------------------------------------------
    // Sandhya clicks Message (using direct goto for reliability)
    await pageS.waitForTimeout(2000); // Wait for React hydration
    const startupCard = pageS.locator('.space-y-3 > div').filter({ hasText: startupName });
    const msgBtn = startupCard.locator('.message-startup-btn');
    const chatUrl = await msgBtn.getAttribute('href');
    if (!chatUrl) throw new Error("Message link has no href");
    await pageS.goto(`${BASE_URL}${chatUrl}`);
    await expect(pageS).toHaveURL(/.*chat/);
    await pageS.waitForTimeout(2000); // Wait for chat WS connect

    // Sandhya sends message
    await pageS.fill('input[placeholder="Type a message..."]', 'Hi Nathan, I am interested in your startup!');
    await pageS.keyboard.press('Enter');
    await expect(pageS.getByText('Hi Nathan, I am interested in your startup!')).toBeVisible();

    // Nathan opens chat
    await pageN.goto(`${BASE_URL}/chat`);
    await pageN.waitForTimeout(2000); // Wait for chat WS connect
    
    // Nathan clicks on the conversation with Sandhya
    await pageN.locator('.min-w-0').first().click();
    await pageN.waitForTimeout(1000);
    
    // Nathan sees message and replies
    await expect(pageN.getByText('Hi Nathan, I am interested in your startup!').first()).toBeVisible();
    await pageN.fill('input[placeholder="Type a message..."]', 'Hi Sandhya, let us talk!');
    await pageN.keyboard.press('Enter');
    await expect(pageN.getByText('Hi Sandhya, let us talk!')).toBeVisible();

    // Sandhya receives reply
    await expect(pageS.getByText('Hi Sandhya, let us talk!').first()).toBeVisible();

    // Persistence: Refresh both browsers
    await pageS.reload();
    await pageN.reload();
    await pageS.waitForTimeout(2000);
    await pageN.waitForTimeout(2000);
    
    await expect(pageS.getByText('Hi Sandhya, let us talk!').first()).toBeVisible();
    await expect(pageN.getByText('Hi Nathan, I am interested in your startup!').first()).toBeVisible();

    console.log("Chat validation completed successfully.");
  });

});
