# Frontend Integration Specification — Real-Time Communication Layer

## WebSocket Connection Manager

Base utility for all real-time hooks. Handles connection lifecycle, reconnection, heartbeat, and cleanup.

```
// lib/websocket.ts
```

### Connection Config
| Param | Type | Default | Description |
|---|---|---|---|
| `url` | `string` | — | WebSocket URL with token query param |
| `onMessage` | `(data) => void` | — | Message handler |
| `onOpen` | `() => void` | — | Connection open callback |
| `onClose` | `() => void` | — | Connection close callback |
| `reconnectInterval` | `number` | `1000` | Initial reconnect delay (ms) |
| `maxReconnectAttempts` | `number` | `10` | Max retries before giving up |
| `heartbeatInterval` | `number` | `30000` | Ping interval (ms) |
| `heartbeatTimeout` | `number` | `5000` | Wait for pong before reconnect |

### Reconnect Strategy
- Exponential backoff: `min(1000 * 2^attempt, 30000)` ms
- Jitter: ±20% random variance
- Max 10 attempts, then give up
- On reconnect success, reset attempt counter

### Heartbeat / Ping-Pong
- Client sends `{"type": "feed.ping"}` every 30s
- Server responds with `{"type": "feed.pong"}`
- If no pong within 5s, close connection and reconnect
- Consumer-specific ping events: `notification.ping`, `meeting.ping`, `investment.ping`, `feed.ping`

---

## Hook: `useChatSocket`

```
import { useChatSocket } from "@/hooks/useChatSocket"
```

### Usage
```tsx
const {
  messages,
  sendMessage,
  startTyping,
  stopTyping,
  markRead,
  onlineUsers,
  isConnected,
} = useChatSocket(conversationId: number)
```

### State
| State | Type | Initial | Description |
|---|---|---|---|
| `messages` | `Message[]` | `[]` | Sorted by `created_at`, newest appended |
| `typingUsers` | `{userId: number, email: string}[]` | `[]` | Users currently typing (with 3s auto-clear) |
| `onlineUsers` | `Set<number>` | `new Set()` | User IDs currently online in this conversation |
| `isConnected` | `boolean` | `false` | WebSocket connection status |

### Actions
| Action | Signature | Effect |
|---|---|---|
| `sendMessage` | `(content: string, messageType?: string) => void` | Sends `chat.message` event |
| `startTyping` | `() => void` | Sends `chat.typing {is_typing: true}` |
| `stopTyping` | `() => void` | Sends `chat.typing {is_typing: false}` |
| `markRead` | `(messageId: number) => void` | Sends `chat.read {message_id}` |

### Event Handlers
| Server Event | Handler Action |
|---|---|
| `chat.message` | Append message to `messages`, clear typing indicator for sender |
| `chat.typing` | Add/remove user from `typingUsers`, auto-clear after 3s |
| `chat.read` | Update message read status in `messages` |
| `chat.presence` | Add/remove user from `onlineUsers` |

### Connection URL
```
ws://host/ws/chat/{conversationId}/?token={jwt}
```

---

## Hook: `useNotificationSocket`

```
import { useNotificationSocket } from "@/hooks/useNotificationSocket"
```

### Usage
```tsx
const {
  notifications,
  unreadCount,
  markRead,
  markAllRead,
  isConnected,
} = useNotificationSocket()
```

### State
| State | Type | Initial | Description |
|---|---|---|---|
| `notifications` | `Notification[]` | `[]` | Cursor-paginated, prepend new |
| `unreadCount` | `number` | `0` | Live unread count |
| `isConnected` | `boolean` | `false` | Connection status |

### Actions
| Action | Signature | Effect |
|---|---|---|
| `markRead` | `(notificationId: number) => void` | Sends `notification.mark_read` |
| `markAllRead` | `() => void` | Sends `notification.mark_all_read` |

### Event Handlers
| Server Event | Handler Action |
|---|---|
| `notification.created` | Prepend to `notifications`, increment `unreadCount` |
| `notification.read` | Update notification status, decrement `unreadCount` |
| `notification.count_updated` | Update `unreadCount` |

### Connection URL
```
ws://host/ws/notifications/?token={jwt}
```

---

## Hook: `useFeedSocket`

```
import { useFeedSocket } from "@/hooks/useFeedSocket"
```

### Usage
```tsx
const { feedItems, isConnected } = useFeedSocket()
```

### State
| State | Type | Initial | Description |
|---|---|---|---|
| `feedItems` | `Activity[]` | `[]` | Prepend new activities |
| `isConnected` | `boolean` | `false` | Connection status |

### Event Handlers
| Server Event | Handler Action |
|---|---|
| `feed.created` | Prepend to `feedItems` |
| `feed.reaction` | Update reaction count on matching activity |
| `feed.comment` | Update comment count on matching activity |

### Connection URL
```
ws://host/ws/feed/?token={jwt}
```

---

## Hook: `usePresence`

```
import { usePresence } from "@/hooks/usePresence"
```

### Usage
```tsx
const { isOnline, lastSeen, onlineUsers } = usePresence(userId?: number)
```

Without `userId`, returns all online users. With `userId`, returns specific user presence.

### State
| State | Type | Initial | Description |
|---|---|---|---|
| `isOnline` | `boolean` | `false` | Whether the user is online (requires `userId`) |
| `lastSeen` | `Date \| null` | `null` | Last seen timestamp |
| `onlineUsers` | `Set<number>` | `new Set()` | All online user IDs (global) |

### Connection URL
```
ws://host/ws/notifications/?token={jwt}
```
Uses notification socket's `presence.update` events (piggybacked on the existing connection).

---

## Auth Token Handling

All WebSocket URLs include the JWT as a query parameter:
```ts
const token = getAccessToken() // from localStorage or auth context
const ws = new WebSocket(`ws://host${path}?token=${token}`)
```

Token refresh: when server closes with code 4001 (unauthorized), the hook should:
1. Attempt token refresh via `/api/v1/auth/refresh/`
2. Store new token
3. Reconnect with new token
4. If refresh fails, redirect to login

---

## Stale Connection Cleanup

- On `visibilitychange` (tab hidden → visible), check `ws.readyState`
- If not `OPEN`, reconnect immediately
- On `window.beforeunload`, close all connections gracefully
- Maximum 10 reconnect attempts, then set `isConnected = false` permanently
- Memory cleanup: all hooks clean up on unmount via `useEffect` return

---

## Types (TypeScript)

```ts
interface Message {
  id: number
  conversation_id: number
  sender_id: number
  sender_email: string
  sender_name: string
  content: string
  message_type: "text" | "file" | "image" | "system"
  created_at: string
  read_by: number[]
}

interface Notification {
  id: number
  type: string
  title: string
  message: string
  read: boolean
  created_at: string
  data?: Record<string, unknown>
}

interface FeedActivity {
  id: number
  type: string
  title: string
  description?: string
  actor_email: string
  created_at: string
  reaction_count?: number
  comment_count?: number
}
```

---

## Analytics Tracking

Each hook exposes connection diagnostics:
```ts
const { diagnostics } = useChatSocket(conversationId)
// diagnostics: { reconnectCount: number, lastPing: number, latencyMs: number }
```

Track these metrics in your analytics provider:
- `websocket_reconnect_count`
- `websocket_message_latency_ms`
- `websocket_disconnect_reason`
- `notification_delivery_latency_ms`
