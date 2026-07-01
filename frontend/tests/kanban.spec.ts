import { expect, test } from "@playwright/test";

test("loads the kanban board", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
  await expect(page.locator('[data-testid^="column-"]')).toHaveCount(5);
});

test("adds a card to a column", async ({ page }) => {
  await page.goto("/");
  const firstColumn = page.locator('[data-testid^="column-"]').first();
  await firstColumn.getByRole("button", { name: /add a card/i }).click();
  await firstColumn.getByPlaceholder("Card title").fill("Playwright card");
  await firstColumn.getByPlaceholder("Details").fill("Added via e2e.");
  await firstColumn.getByRole("button", { name: /add card/i }).click();
  await expect(firstColumn.getByText("Playwright card")).toBeVisible();
});

test("moves a card between columns", async ({ page }) => {
  await page.goto("/");
  const card = page.getByTestId("card-card-1");
  const targetColumn = page.getByTestId("column-col-review");
  const cardBox = await card.boundingBox();
  const columnBox = await targetColumn.boundingBox();
  if (!cardBox || !columnBox) {
    throw new Error("Unable to resolve drag coordinates.");
  }

  await page.mouse.move(
    cardBox.x + cardBox.width / 2,
    cardBox.y + cardBox.height / 2
  );
  await page.mouse.down();
  await page.mouse.move(
    columnBox.x + columnBox.width / 2,
    columnBox.y + 120,
    { steps: 12 }
  );
  await page.mouse.up();
  await expect(targetColumn.getByTestId("card-card-1")).toBeVisible();
});

test("AI chat updates the board when actions are returned", async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem("pm-demo-token", "demo-token-user");
  });

  const initialBoard = {
    id: 1,
    title: "Kanban Studio",
    columns: [
      { id: 1, title: "Backlog", position: 0, cardIds: [1, 2] },
      { id: 2, title: "Discovery", position: 1, cardIds: [3] },
      { id: 3, title: "In Progress", position: 2, cardIds: [4, 5] },
      { id: 4, title: "Review", position: 3, cardIds: [6] },
      { id: 5, title: "Done", position: 4, cardIds: [7, 8] },
    ],
    cards: [
      {
        id: 1,
        columnId: 1,
        title: "Align roadmap themes",
        description: "Draft quarterly themes with impact statements and metrics.",
        position: 0,
        metadata: {},
        updatedAt: "2026-01-01T00:00:00Z",
      },
      {
        id: 2,
        columnId: 1,
        title: "Gather customer signals",
        description: "Review support tags, sales notes, and churn feedback.",
        position: 1,
        metadata: {},
        updatedAt: "2026-01-01T00:00:00Z",
      },
      {
        id: 3,
        columnId: 2,
        title: "Prototype analytics view",
        description: "Sketch initial dashboard layout and key drill-downs.",
        position: 0,
        metadata: {},
        updatedAt: "2026-01-01T00:00:00Z",
      },
      {
        id: 4,
        columnId: 3,
        title: "Build team sync ritual",
        description: "Create a weekly check-in for progress and blockers.",
        position: 0,
        metadata: {},
        updatedAt: "2026-01-01T00:00:00Z",
      },
      {
        id: 5,
        columnId: 3,
        title: "Review user onboarding flow",
        description: "Validate the first three steps of onboarding for friction.",
        position: 1,
        metadata: {},
        updatedAt: "2026-01-01T00:00:00Z",
      },
      {
        id: 6,
        columnId: 4,
        title: "Publish launch plan",
        description: "Share the rollout plan with the team and stakeholders.",
        position: 0,
        metadata: {},
        updatedAt: "2026-01-01T00:00:00Z",
      },
      {
        id: 7,
        columnId: 5,
        title: "Ship marketing page",
        description: "Final copy approved and asset pack delivered.",
        position: 0,
        metadata: {},
        updatedAt: "2026-01-01T00:00:00Z",
      },
      {
        id: 8,
        columnId: 5,
        title: "Close onboarding sprint",
        description: "Document release notes and share internally.",
        position: 1,
        metadata: {},
        updatedAt: "2026-01-01T00:00:00Z",
      },
    ],
  };

  const updatedBoard = {
    ...initialBoard,
    columns: initialBoard.columns.map((column) =>
      column.id === 1
        ? { ...column, cardIds: column.cardIds.filter((id) => id !== 1) }
        : column.id === 4
        ? { ...column, cardIds: [...column.cardIds, 1] }
        : column
    ),
    cards: initialBoard.cards.map((card) =>
      card.id === 1 ? { ...card, columnId: 4, position: 1 } : card
    ),
  };

  let boardRequestCount = 0;
  await page.route("**/api/me", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ user: "user" }),
    })
  );

  await page.route("**/api/board", (route) => {
    boardRequestCount += 1;
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(boardRequestCount === 1 ? initialBoard : updatedBoard),
    });
  });

  await page.route("**/api/ai/prompt", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        response_text: "Moved the first card to Review.",
        actions: [{ action_type: "move", card_id: 1 }],
      }),
    })
  );

  await page.goto("/");

  await expect(page.getByText("Kanban Studio")).toBeVisible();

  const promptInput = page.getByPlaceholder("Ask the AI to update the board...");
  await promptInput.fill("Move the first card to Review.");
  await page.getByRole("button", { name: /send/i }).click();

  await expect(page.getByText("Moved the first card to Review.")).toBeVisible();
  await expect(page.getByTestId("column-4").getByTestId("card-card-1")).toBeVisible();
});
