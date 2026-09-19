import { expect, test } from '@playwright/test'

test('replays fixture data and acknowledges the high-price alert', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('heading', { name: 'NEMWatch' })).toBeVisible()
  await expect(page.getByText('Educational use only.')).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Regional overview' })).toBeVisible()

  const start = page.getByRole('button', { name: 'Start replay' })
  await expect(start).toBeEnabled()
  await start.click()
  await expect(page.locator('.replay-progress')).toContainText(/running|completed/i, { timeout: 20_000 })

  const alert = page.locator('.alert-card').filter({ hasText: 'high price' }).first()
  await expect(alert).toBeVisible({ timeout: 30_000 })
  await alert.getByLabel('Acknowledgement note').fill('Reviewed in browser smoke test')
  await alert.getByRole('button', { name: 'Acknowledge' }).click()
  await expect(alert).toContainText('Reviewed in browser smoke test')
  await expect(alert).toContainText('Acknowledged')
})
