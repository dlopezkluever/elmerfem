// WebSocket message types for simulation progress

export enum WebSocketMessageType {
  PROGRESS = 'progress',
  STATUS = 'status',
  ERROR = 'error'
}

export interface ProgressData {
  pct: number;
  msg: string;
  timestamp: string;
}

export interface StatusData {
  status: string;
  timestamp: string;
}

export interface ErrorData {
  error: string;
  timestamp: string;
}

export interface WebSocketMessage {
  type: WebSocketMessageType;
  data: ProgressData | StatusData | ErrorData;
}

export interface ProgressMessage extends WebSocketMessage {
  type: WebSocketMessageType.PROGRESS;
  data: ProgressData;
}

export interface StatusMessage extends WebSocketMessage {
  type: WebSocketMessageType.STATUS;
  data: StatusData;
}

export interface ErrorMessage extends WebSocketMessage {
  type: WebSocketMessageType.ERROR;
  data: ErrorData;
}

export type SimulationWebSocketMessage = ProgressMessage | StatusMessage | ErrorMessage;

// Connection states
export enum WebSocketConnectionState {
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  DISCONNECTED = 'disconnected',
  RECONNECTING = 'reconnecting',
  ERROR = 'error'
} 