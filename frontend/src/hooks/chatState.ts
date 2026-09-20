import type { ChatMessage, SavedConversation, StreamEvent } from "../types";

export interface ChatState {
  conversationId: string | null;
  messages: ChatMessage[];
  activeId: string | null;
  restoring: boolean;
  restoreError: string;
  notice: string;
}

export function initialChat(conversationId: string | null = null): ChatState {
  return {
    conversationId,
    messages: [],
    activeId: null,
    restoring: !!conversationId,
    restoreError: "",
    notice: "",
  };
}

export function savedMessages(conversation: SavedConversation): ChatMessage[] {
  return conversation.messages.map((message) => ({
    key: `saved-${message.message_id}`,
    messageId: message.message_id,
    role: message.role,
    text: message.content,
    status: "complete",
    sources: message.sources,
    citationCheck: message.citation_check,
    retrievalQuestion: message.retrieval_question,
  }));
}

type Action =
  | { type: "reset" }
  | { type: "restoring" }
  | { type: "restoreError"; error: string }
  | { type: "loaded"; conversation: SavedConversation; notice?: string }
  | { type: "begin"; id: string; question: string; messages: ChatMessage[] }
  | { type: "event"; event: StreamEvent }
  | { type: "failed"; id: string; interrupted: boolean; error: string };

export function chatReducer(state: ChatState, action: Action): ChatState {
  switch (action.type) {
    case "reset":
      return initialChat();
    case "restoring":
      return { ...state, restoring: true, restoreError: "", notice: "" };
    case "restoreError":
      return { ...state, restoring: false, restoreError: action.error };
    case "loaded":
      return {
        ...initialChat(),
        conversationId: action.conversation.conversation_id,
        messages: savedMessages(action.conversation),
        notice: action.notice || "",
      };
    case "begin":
      return {
        ...state,
        restoring: false,
        restoreError: "",
        notice: "",
        activeId: action.id,
        messages: [
          ...action.messages,
          {
            key: `${action.id}-user`,
            role: "user",
            text: action.question,
            status: "complete",
            sources: null,
            citationCheck: null,
            retrievalQuestion: null,
          },
          {
            key: action.id,
            role: "assistant",
            text: "",
            question: action.question,
            status: "pending",
            sources: null,
            citationCheck: null,
            retrievalQuestion: null,
          },
        ],
      };
    case "failed":
      if (state.activeId !== action.id) return state;
      return {
        ...state,
        activeId: null,
        messages: state.messages.map((message) =>
          message.key === action.id
            ? {
                ...message,
                status: action.interrupted ? "interrupted" : "failed",
                error: action.error,
              }
            : message,
        ),
      };
    case "event": {
      const event = action.event;
      if (event.request_id !== state.activeId) return state;
      return {
        ...state,
        conversationId:
          event.event === "complete"
            ? event.conversation_id
            : state.conversationId,
        activeId: event.event === "complete" ? null : state.activeId,
        messages: state.messages.map((message) => {
          if (message.key !== event.request_id) return message;
          switch (event.event) {
            case "sources":
              return { ...message, sources: event.sources };
            case "answer_delta":
              return {
                ...message,
                status: "streaming",
                text: message.text + event.delta,
              };
            case "debug":
              return {
                ...message,
                debug: event,
                retrievalQuestion: event.retrieval_question,
              };
            case "complete":
              return {
                ...message,
                status: "complete",
                messageId: event.message_id,
                text: event.answer,
                sources: event.sources,
                citationCheck: event.citation_check,
                retrievalQuestion: event.retrieval_question,
              };
            default:
              return message;
          }
        }),
      };
    }
  }
}
