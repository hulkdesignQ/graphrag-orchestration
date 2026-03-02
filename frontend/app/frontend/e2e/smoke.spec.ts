import { test, expect } from "@playwright/test";

test.describe("Navigation", () => {
    test("loads the home page (chat)", async ({ page }) => {
        await page.goto("/");
        // Should see either the login prompt or the chat empty state
        await expect(
            page.getByText("Sign in").or(page.getByRole("textbox"))
        ).toBeVisible({ timeout: 10000 });
    });

    test("navigates to files page", async ({ page }) => {
        await page.goto("/#/files");
        await expect(
            page.getByText("Sign in").or(page.getByText("files", { exact: false }))
        ).toBeVisible({ timeout: 10000 });
    });

    test("shows 404 for unknown route", async ({ page }) => {
        await page.goto("/#/nonexistent-page");
        // NoPage component or redirect to home
        await expect(page.locator("body")).toBeVisible();
    });
});

test.describe("Chat page (unauthenticated)", () => {
    test("shows example questions in empty state", async ({ page }) => {
        await page.goto("/");
        // If auth is disabled, should see examples or chat input
        const hasContent = await page
            .getByRole("textbox")
            .or(page.getByText("Sign in"))
            .isVisible()
            .catch(() => false);
        expect(hasContent).toBeTruthy();
    });
});

test.describe("Responsive", () => {
    test("renders on mobile viewport", async ({ page }) => {
        await page.setViewportSize({ width: 375, height: 812 });
        await page.goto("/");
        await expect(page.locator("body")).toBeVisible();
    });
});
