"use client";

import { useEffect, useMemo, useState } from "react";
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  closestCorners,
  type DragEndEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import { KanbanColumn } from "@/components/KanbanColumn";
import { KanbanCardPreview } from "@/components/KanbanCardPreview";
import { initialData, moveCard, type BoardData } from "@/lib/kanban";
import {
  fetchBoard,
  createCardApi,
  deleteCardApi,
  moveCardApi,
  renameColumnApi,
} from "@/lib/api";

export const KanbanBoard = () => {
  const [board, setBoard] = useState<BoardData>(() => initialData);
  const [activeCardId, setActiveCardId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 6 },
    })
  );

  const cardsById = useMemo(() => board.cards, [board.cards]);

  useEffect(() => {
    const loadBoard = async () => {
      try {
        const remoteBoard = await fetchBoard();
        if (remoteBoard) {
          setBoard(remoteBoard);
        }
      } catch (err) {
        console.error("Unable to load board", err);
        setError("Unable to load board data.");
      } finally {
        setLoading(false);
      }
    };

    loadBoard();
  }, []);

  const handleDragStart = (event: DragStartEvent) => {
    setActiveCardId(event.active.id as string);
  };

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveCardId(null);

    if (!over || active.id === over.id) {
      return;
    }

    const sourceId = active.id as string;
    const targetId = over.id as string;
    const sourceColumn = board.columns.find((column) =>
      column.cardIds.includes(sourceId)
    );
    const targetColumn = board.columns.find(
      (column) => column.id === targetId || column.cardIds.includes(targetId)
    );

    if (!sourceColumn || !targetColumn) {
      return;
    }

    const destinationColumnId =
      targetColumn.id === targetId ? targetColumn.id : targetColumn.id;
    const targetCardIndex = targetColumn.cardIds.indexOf(targetId);
    const position = targetCardIndex === -1 ? targetColumn.cardIds.length : targetCardIndex;

    try {
      await moveCardApi(sourceId, destinationColumnId, position);
      setBoard((prev) => ({
        ...prev,
        columns: moveCard(prev.columns, sourceId, targetId),
      }));
    } catch (err) {
      console.error("Unable to move card", err);
      setError("Unable to move card.");
    }
  };

  const handleRenameColumn = async (columnId: string, title: string) => {
    setBoard((prev) => ({
      ...prev,
      columns: prev.columns.map((column) =>
        column.id === columnId ? { ...column, title } : column
      ),
    }));

    try {
      await renameColumnApi(columnId, title);
    } catch (err) {
      console.error("Unable to rename column", err);
      setError("Unable to rename column.");
    }
  };

  const handleAddCard = async (columnId: string, title: string, details: string) => {
    try {
      const card = await createCardApi(columnId, title, details || "No details yet.");
      setBoard((prev) => ({
        ...prev,
        cards: {
          ...prev.cards,
          [card.id]: { id: card.id, title: card.title, details: card.details },
        },
        columns: prev.columns.map((column) =>
          column.id === columnId
            ? { ...column, cardIds: [...column.cardIds, card.id] }
            : column
        ),
      }));
    } catch (err) {
      console.error("Unable to create card", err);
      setError("Unable to create card.");
    }
  };

  const handleDeleteCard = async (columnId: string, cardId: string) => {
    try {
      await deleteCardApi(cardId);
      setBoard((prev) => ({
        ...prev,
        cards: Object.fromEntries(
          Object.entries(prev.cards).filter(([id]) => id !== cardId)
        ),
        columns: prev.columns.map((column) =>
          column.id === columnId
            ? {
                ...column,
                cardIds: column.cardIds.filter((id) => id !== cardId),
              }
            : column
        ),
      }));
    } catch (err) {
      console.error("Unable to delete card", err);
      setError("Unable to delete card.");
    }
  };

  const activeCard = activeCardId ? cardsById[activeCardId] : null;

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[var(--surface)] p-6 text-[var(--navy-dark)]">
        {error}
      </div>
    );
  }

  return (
    <div className="relative overflow-hidden">
      <div className="pointer-events-none absolute left-0 top-0 h-[420px] w-[420px] -translate-x-1/3 -translate-y-1/3 rounded-full bg-[radial-gradient(circle,_rgba(32,157,215,0.25)_0%,_rgba(32,157,215,0.05)_55%,_transparent_70%)]" />
      <div className="pointer-events-none absolute bottom-0 right-0 h-[520px] w-[520px] translate-x-1/4 translate-y-1/4 rounded-full bg-[radial-gradient(circle,_rgba(117,57,145,0.18)_0%,_rgba(117,57,145,0.05)_55%,_transparent_75%)]" />

      <main className="relative mx-auto flex min-h-screen max-w-[1500px] flex-col gap-10 px-6 pb-16 pt-12">
        <header className="flex flex-col gap-6 rounded-[32px] border border-[var(--stroke)] bg-white/80 p-8 shadow-[var(--shadow)] backdrop-blur">
          <div className="flex flex-wrap items-start justify-between gap-6">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.35em] text-[var(--gray-text)]">
                Single Board Kanban
              </p>
              <h1 className="mt-3 font-display text-4xl font-semibold text-[var(--navy-dark)]">
                Kanban Studio
              </h1>
              <p className="mt-3 max-w-xl text-sm leading-6 text-[var(--gray-text)]">
                Keep momentum visible. Rename columns, drag cards between stages,
                and capture quick notes without getting buried in settings.
              </p>
            </div>
            <div className="rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] px-5 py-4">
              <p className="text-xs font-semibold uppercase tracking-[0.25em] text-[var(--gray-text)]">
                Focus
              </p>
              <p className="mt-2 text-lg font-semibold text-[var(--primary-blue)]">
                One board. Five columns. Zero clutter.
              </p>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-4">
            {board.columns.map((column) => (
              <div
                key={column.id}
                className="flex items-center gap-2 rounded-full border border-[var(--stroke)] px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-[var(--navy-dark)]"
              >
                <span className="h-2 w-2 rounded-full bg-[var(--accent-yellow)]" />
                {column.title}
              </div>
            ))}
          </div>
        </header>

        <DndContext
          sensors={sensors}
          collisionDetection={closestCorners}
          onDragStart={handleDragStart}
          onDragEnd={handleDragEnd}
        >
          <section className="grid gap-6 lg:grid-cols-5">
            {board.columns.map((column) => (
              <KanbanColumn
                key={column.id}
                column={column}
                cards={column.cardIds.map((cardId) => board.cards[cardId])}
                onRename={handleRenameColumn}
                onAddCard={handleAddCard}
                onDeleteCard={handleDeleteCard}
              />
            ))}
          </section>
          <DragOverlay>
            {activeCard ? (
              <div className="w-[260px]">
                <KanbanCardPreview card={activeCard} />
              </div>
            ) : null}
          </DragOverlay>
        </DndContext>
      </main>
    </div>
  );
};
