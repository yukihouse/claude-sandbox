import { test, expect } from '@playwright/test'

test.describe('カウンターデモ (Vite/React版) E2E', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('初期表示でカウントが0になっている', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'カウンターデモ' })).toBeVisible()
    await expect(page.getByTestId('count')).toHaveText('0')
  })

  test('+1ボタンを押すとカウントが増える', async ({ page }) => {
    const plusButton = page.getByRole('button', { name: '+1' })

    await plusButton.click()
    await expect(page.getByTestId('count')).toHaveText('1')

    await plusButton.click()
    await expect(page.getByTestId('count')).toHaveText('2')
  })

  test('リセットボタンを押すとカウントが0に戻る', async ({ page }) => {
    const plusButton = page.getByRole('button', { name: '+1' })
    const resetButton = page.getByRole('button', { name: 'リセット' })

    await plusButton.click()
    await plusButton.click()
    await expect(page.getByTestId('count')).toHaveText('2')

    await resetButton.click()
    await expect(page.getByTestId('count')).toHaveText('0')
  })

  test('ホームへ戻るリンクがホーム画面を指している', async ({ page }) => {
    await expect(page.getByRole('link', { name: 'ホームへ戻る' })).toHaveAttribute(
      'href',
      'http://localhost:8080/',
    )
  })
})
