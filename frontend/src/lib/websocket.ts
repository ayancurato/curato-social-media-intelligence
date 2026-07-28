/**
 * Curato AI — WebSocket Client
 *
 * Manages WebSocket connections for real-time workflow updates.
 */

import { siteConfig } from "@/config/site";
import type { WebSocketEvent } from "@/types/workflow";

type EventHandler = (event: WebSocketEvent) => void;

export class CuratoWebSocket {
  private ws: WebSocket | null = null;
  private sessionId: string;
  private handlers: EventHandler[] = [];
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  constructor(sessionId: string) {
    this.sessionId = sessionId;
  }

  connect(): void {
    const url = `${siteConfig.api.wsUrl}/api/v1/ws/${this.sessionId}`;

    try {
      this.ws = new WebSocket(url);

      this.ws.onopen = () => {
        console.log(`[WS] Connected to session ${this.sessionId}`);
        this.reconnectAttempts = 0;
      };

      this.ws.onmessage = (event) => {
        try {
          const data: WebSocketEvent = JSON.parse(event.data);
          this.handlers.forEach((handler) => handler(data));
        } catch (e) {
          console.error("[WS] Failed to parse message:", e);
        }
      };

      this.ws.onclose = (event) => {
        console.log(`[WS] Disconnected (code: ${event.code})`);
        if (
          !event.wasClean &&
          this.reconnectAttempts < this.maxReconnectAttempts
        ) {
          this.reconnect();
        }
      };

      this.ws.onerror = (error) => {
        console.error("[WS] Error:", error);
      };
    } catch (e) {
      console.error("[WS] Connection failed:", e);
    }
  }

  private reconnect(): void {
    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    console.log(
      `[WS] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`
    );
    setTimeout(() => this.connect(), delay);
  }

  onEvent(handler: EventHandler): () => void {
    this.handlers.push(handler);
    return () => {
      this.handlers = this.handlers.filter((h) => h !== handler);
    };
  }

  disconnect(): void {
    if (this.ws) {
      this.maxReconnectAttempts = 0; // Prevent reconnect
      this.ws.close();
      this.ws = null;
    }
    this.handlers = [];
  }

  sendPing(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send("ping");
    }
  }
}
