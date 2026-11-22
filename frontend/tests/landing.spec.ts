import { expect, test } from '@playwright/test'

for (const width of [1440, 1024, 390]) {
  test(`landing navigation, languages and demo at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 })
    await page.emulateMedia({ reducedMotion: 'reduce' })
    await page.goto('/')
    await expect(page.getByRole('heading', { level: 1 })).toContainText('Your language.')
    await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth)).toBe(width)

    if (width === 390) await page.getByRole('button', { name: 'Menu' }).click()
    await page.getByRole('navigation').getByRole('link', { name: 'Try a demo' }).click()
    await expect(page).toHaveURL(/#demo$/)
    await page.getByRole('button', { name: 'Read a sample call' }).click()
    const dialog = page.getByRole('dialog')
    await expect(dialog.getByText('No call is placed', { exact: false })).toBeVisible()
    await dialog.getByRole('button', { name: 'Hospital appointments' }).click()
    await expect(dialog.getByText('general physician', { exact: false })).toBeVisible()
    await page.keyboard.press('Escape')
    await expect(dialog).toBeHidden()

    await page.locator('select').selectOption('te')
    await expect(page.locator('html')).toHaveAttribute('lang', 'te')
    await expect(page.getByRole('heading', { level: 1 })).toContainText('మీ భాషలో.')
    await page.locator('select').selectOption('hi')
    await expect(page.locator('html')).toHaveAttribute('lang', 'hi')
    await expect(page.getByRole('heading', { level: 1 })).toContainText('आपकी भाषा।')
    await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth)).toBe(width)
  })
}
