import type { BoardData, Column, Card } from "./kanban";

export const TOKEN_KEY = "pm-demo-token";

export const getAuthToken = () => {
  if (typeof window === "undefined") {
    return null;
  }
  return window.localStorage.getItem(TOKEN_KEY);
};

export const getAuthHeaders = (): Record<string, string> => {
  const token = getAuthToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
};

const getFetchUrl = (path: string) => {
  if (typeof window !== "undefined" && window.location?.origin) {
    return new URL(path, window.location.origin).toString();
  }
  return new URL(path, "http://localhost").toString();
};

const parseId = (id: number | string) => String(id);

const normalizeCard = (card: {
  id: number;
  columnId: number;
  title: string;
  description: string;
  position: number;
  metadata: unknown;
  updatedAt: string;
}) => ({
  id: parseId(card.id),
  columnId: parseId(card.columnId),
  title: card.title,
  details: card.description,
  position: card.position,
  metadata: card.metadata,
  updatedAt: card.updatedAt,
});

const normalizeColumn = (column: {
  id: number;
  title: string;
  position: number;
  cardIds: number[];
}): Column => ({
  id: parseId(column.id),
  title: column.title,
  cardIds: column.cardIds.map(parseId),
});

const normalizeBoard = (board: {
  id: number;
  title: string;
  columns: Array<{
    id: number;
    title: string;
    position: number;
    cardIds: number[];
  }>;
  cards: Array<{
    id: number;
    columnId: number;
    title: string;
    description: string;
    position: number;
    metadata: unknown;
    updatedAt: string;
  }>;
}): BoardData => {
  const columns = board.columns.map(normalizeColumn);
  const cards = Object.fromEntries(
    board.cards.map((card) => [parseId(card.id), normalizeCard(card)])
  );
  return {
    id: parseId(board.id),
    title: board.title,
    columns,
    cards,
  };
};

export const fetchBoard = async (): Promise<BoardData | null> => {
  const response = await fetch(getFetchUrl("/api/board"), {
    headers: { "Content-Type": "application/json", ...getAuthHeaders() },
  });
  if (!response.ok) {
    return null;
  }
  const data = await response.json();
  return normalizeBoard(data);
};

export const createCardApi = async (
  columnId: string,
  title: string,
  description: string
) => {
  const response = await fetch(getFetchUrl("/api/cards"), {
    method: "POST",
    headers: { "Content-Type": "application/json", ...getAuthHeaders() },
    body: JSON.stringify({
      columnId: Number(columnId),
      title,
      description,
    }),
  });
  if (!response.ok) {
    throw new Error("Unable to create card");
  }
  return normalizeCard(await response.json());
};

export const deleteCardApi = async (cardId: string) => {
  const response = await fetch(getFetchUrl(`/api/cards/${Number(cardId)}`), {
    method: "DELETE",
    headers: { ...getAuthHeaders() },
  });
  if (!response.ok) {
    throw new Error("Unable to delete card");
  }
};

export const moveCardApi = async (
  cardId: string,
  targetColumnId: string,
  position: number
) => {
  const response = await fetch(getFetchUrl(`/api/cards/${Number(cardId)}/move`), {
    method: "POST",
    headers: { "Content-Type": "application/json", ...getAuthHeaders() },
    body: JSON.stringify({
      targetColumnId: Number(targetColumnId),
      position,
    }),
  });
  if (!response.ok) {
    throw new Error("Unable to move card");
  }
  return normalizeCard(await response.json());
};

export const renameColumnApi = async (columnId: string, title: string) => {
  const response = await fetch(getFetchUrl(`/api/columns/${Number(columnId)}`), {
    method: "PATCH",
    headers: { "Content-Type": "application/json", ...getAuthHeaders() },
    body: JSON.stringify({ title }),
  });
  if (!response.ok) {
    throw new Error("Unable to rename column");
  }
};

export type AiPromptResponse = {
  response_text: string;
  actions?: Array<{ action_type: string; card_id: number }>;
};

export const promptAiApi = async (message: string): Promise<AiPromptResponse> => {
  const response = await fetch(getFetchUrl("/api/ai/prompt"), {
    method: "POST",
    headers: { "Content-Type": "application/json", ...getAuthHeaders() },
    body: JSON.stringify({ message }),
  });
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`Unable to send AI prompt: ${body}`);
  }
  return response.json();
};
