import { render, screen, within, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { KanbanBoard } from "@/components/KanbanBoard";

const mockBoard = {
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
      position: 0,
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

const getFirstColumn = () => screen.getAllByTestId(/column-/i)[0];

const waitForRemoteBoard = async () => {
  await waitFor(() => expect(screen.getByText("Build team sync ritual")).toBeInTheDocument());
};

const createFetchMock = () => {
  const mockedFetch = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);

    if (url.endsWith("/api/board")) {
      return Promise.resolve(
        new Response(JSON.stringify(mockBoard), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        })
      );
    }

    if (url.endsWith("/api/columns/1") && init?.method === "PATCH") {
      return Promise.resolve(new Response(JSON.stringify({ status: "ok" }), { status: 200 }));
    }

    if (url.endsWith("/api/cards") && init?.method === "POST") {
      const payload = init.body ? JSON.parse(String(init.body)) : {};
      return Promise.resolve(
        new Response(
          JSON.stringify({
            id: 99,
            columnId: payload.columnId,
            title: payload.title,
            description: payload.description,
            position: 2,
            metadata: {},
            updatedAt: "2026-01-01T00:00:00Z",
          }),
          { status: 200, headers: { "Content-Type": "application/json" } }
        )
      );
    }

    if (url.match(/\/api\/cards\/\d+$/) && init?.method === "DELETE") {
      return Promise.resolve(new Response(JSON.stringify({ status: "ok" }), { status: 200 }));
    }

    if (url.match(/\/api\/cards\/\d+\/move$/) && init?.method === "POST") {
      const payload = init.body ? JSON.parse(String(init.body)) : {};
      return Promise.resolve(
        new Response(
          JSON.stringify({
            id: 1,
            columnId: payload.targetColumnId,
            title: "Align roadmap themes",
            description: "Draft quarterly themes with impact statements and metrics.",
            position: payload.position,
            metadata: {},
            updatedAt: "2026-01-01T00:00:00Z",
          }),
          { status: 200, headers: { "Content-Type": "application/json" } }
        )
      );
    }

    if (url.endsWith("/api/ai/prompt") && init?.method === "POST") {
      return Promise.resolve(
        new Response(
          JSON.stringify({
            response_text: "Moved the card to the next phase.",
            actions: [{ action_type: "move", card_id: 1 }],
          }),
          { status: 200, headers: { "Content-Type": "application/json" } }
        )
      );
    }

    return Promise.resolve(new Response(null, { status: 404 }));
  });
  vi.stubGlobal("fetch", mockedFetch);
  return mockedFetch;
};

describe("KanbanBoard", () => {
  beforeEach(() => {
    createFetchMock();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders five columns", async () => {
    render(<KanbanBoard />);
    await waitFor(() => expect(screen.getAllByTestId(/column-/i)).toHaveLength(5));
  });

  it("renames a column", async () => {
    render(<KanbanBoard />);
    await waitForRemoteBoard();

    const column = getFirstColumn();
    const input = within(column).getByLabelText("Column title");
    await userEvent.clear(input);
    await userEvent.type(input, "New Name");
    expect(input).toHaveValue("New Name");
  });

  it("adds and removes a card", async () => {
    render(<KanbanBoard />);
    await waitForRemoteBoard();

    const column = getFirstColumn();
    const addButton = within(column).getByRole("button", {
      name: /add a card/i,
    });
    await userEvent.click(addButton);

    const titleInput = within(column).getByPlaceholderText(/card title/i);
    await userEvent.type(titleInput, "New card");
    const detailsInput = within(column).getByPlaceholderText(/details/i);
    await userEvent.type(detailsInput, "Notes");

    await userEvent.click(within(column).getByRole("button", { name: /add card/i }));
    await waitFor(() => expect(within(column).getByText("New card")).toBeInTheDocument());

    const deleteButton = within(column).getByRole("button", {
      name: /delete new card/i,
    });
    await userEvent.click(deleteButton);
    await waitFor(() => expect(within(column).queryByText("New card")).not.toBeInTheDocument());
  });

  it("sends an AI prompt and displays assistant response", async () => {
    render(<KanbanBoard />);
    await waitForRemoteBoard();

    const promptInput = screen.getByPlaceholderText(/Ask the AI to update the board/i);
    await userEvent.type(promptInput, "Move the first card to review.");

    const sendButton = screen.getByRole("button", { name: /send/i });
    await userEvent.click(sendButton);

    await waitFor(() => expect(screen.getByText("Moved the card to the next phase.")).toBeInTheDocument());
  });
});
