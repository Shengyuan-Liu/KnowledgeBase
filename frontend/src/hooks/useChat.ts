import { useCallback, useEffect, useReducer, useRef, useState } from "react";
import {
  loadConversation,
  streamAnswer,
  StreamInterruptedError,
} from "../api/chat";
import { chatReducer, initialChat, savedMessages } from "./chatState";

export const CONVERSATION_KEY = "knowledgebase.conversationId";

export function useChat() {
  const [state, dispatch] = useReducer(chatReducer, undefined, () =>
    initialChat(localStorage.getItem(CONVERSATION_KEY)),
  );
  const [draft, setDraft] = useState("");
  const [planSearch, setPlanSearch] = useState(false);
  const work = useRef<{ id: string; controller: AbortController } | null>(null);

  const restore = useCallback(async (id: string) => {
    work.current?.controller.abort();
    const task = { id: crypto.randomUUID(), controller: new AbortController() };
    work.current = task;
    dispatch({ type: "restoring" });
    try {
      const conversation = await loadConversation(id, task.controller.signal);
      if (work.current !== task) return;
      dispatch({ type: "loaded", conversation });
    } catch (error) {
      if (work.current === task && !task.controller.signal.aborted)
        dispatch({ type: "restoreError", error: (error as Error).message });
    } finally {
      if (work.current === task) work.current = null;
    }
  }, []);

  useEffect(() => {
    const id = localStorage.getItem(CONVERSATION_KEY);
    if (id) void restore(id);
    return () => {
      work.current?.controller.abort();
      work.current = null;
    };
  }, [restore]);

  function reset() {
    work.current?.controller.abort();
    work.current = null;
    localStorage.removeItem(CONVERSATION_KEY);
    setDraft("");
    dispatch({ type: "reset" });
  }

  async function send(question = draft) {
    question = question.trim();
    if (!question || work.current || state.restoreError) return;
    const task = { id: crypto.randomUUID(), controller: new AbortController() };
    work.current = task;
    let messages = state.messages;
    const unfinished = messages.at(-1);
    // A lost completion event can hide a committed answer. Read before retrying.
    if (unfinished && ["failed", "interrupted"].includes(unfinished.status)) {
      if (state.conversationId) {
        dispatch({ type: "restoring" });
        try {
          const conversation = await loadConversation(
            state.conversationId,
            task.controller.signal,
          );
          if (work.current !== task) return;
          const lastSavedId = Math.max(
            0,
            ...messages.map((message) => message.messageId || 0),
          );
          const recovered = conversation.messages.some(
            (message) => message.message_id > lastSavedId,
          );
          if (recovered) {
            dispatch({
              type: "loaded",
              conversation,
              notice:
                "Recovered the saved conversation. Review it before sending another question.",
            });
            work.current = null;
            return;
          }
          messages = savedMessages(conversation);
        } catch (error) {
          if (work.current === task) {
            dispatch({ type: "restoreError", error: (error as Error).message });
            work.current = null;
          }
          return;
        }
      } else {
        messages = messages.slice(0, -2);
      }
    }
    setDraft(question);
    dispatch({ type: "begin", id: task.id, question, messages });
    try {
      await streamAnswer(
        question,
        state.conversationId,
        task.id,
        task.controller.signal,
        (event) => {
          if (work.current !== task || task.controller.signal.aborted) return;
          dispatch({ type: "event", event });
          if (event.event === "complete") {
            localStorage.setItem(CONVERSATION_KEY, event.conversation_id);
            setDraft("");
          }
        },
        planSearch ? "planned" : "single",
      );
    } catch (error) {
      if (work.current === task)
        dispatch({
          type: "failed",
          id: task.id,
          interrupted:
            task.controller.signal.aborted ||
            error instanceof StreamInterruptedError,
          error: task.controller.signal.aborted
            ? "Generation stopped. Partial text is not a completed answer."
            : (error as Error).message,
        });
    } finally {
      if (work.current === task) work.current = null;
    }
  }

  function stop() {
    const task = work.current;
    if (!task || !state.activeId) return;
    task.controller.abort();
    work.current = null;
    dispatch({
      type: "failed",
      id: task.id,
      interrupted: true,
      error: "Generation stopped. Partial text is not a completed answer.",
    });
  }

  return { ...state, draft, setDraft, planSearch, setPlanSearch, send, stop, reset, restore };
}
