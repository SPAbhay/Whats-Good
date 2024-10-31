import { useState, useEffect, useRef, useCallback } from 'react';
import { config } from '../../config';

interface Message {
    role: 'user' | 'assistant';
    content: string;
    metadata?: {
        platform?: string;
        error?: boolean;
        [key: string]: unknown;
    };
}

interface ChatInterfaceProps {
    articleId: string;
    brandId: string;
    isVisible?: boolean;
}

export default function ChatInterface({ articleId, brandId, isVisible = true }: ChatInterfaceProps) {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [isConnected, setIsConnected] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [processingStatuses, setProcessingStatuses] = useState<ProcessingStatus[]>([]);
    const [reconnectAttempts, setReconnectAttempts] = useState(0);
    const wsRef = useRef<WebSocket | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = useCallback(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, []);

    useEffect(() => {
        scrollToBottom();
    }, [messages, scrollToBottom]);

    // WebSocket connection logic
    const connectWebSocket = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.CONNECTING ||
        wsRef.current?.readyState === WebSocket.OPEN) {
        return; // Don't create new connection if one exists
    }

    try {
        const clientId = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        const ws = new WebSocket(`${config.WS_URL}/ws/${clientId}`);
        wsRef.current = ws;

        ws.onopen = () => {
            console.log('WebSocket Connected');
            setIsConnected(true);
            setReconnectAttempts(0);
        };

        ws.onclose = (event) => {
            console.log('WebSocket closed with code:', event.code);
            setIsConnected(false);
            wsRef.current = null;

            // Only reconnect if it's not an intentional close
            if (event.code !== 1000 && reconnectAttempts < 3) {
                setTimeout(() => {
                    setReconnectAttempts(prev => prev + 1);
                    connectWebSocket();
                }, 1000 * Math.pow(2, reconnectAttempts));
            }
        };

        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            setIsConnected(false);
        };

        ws.onmessage = (event) => {
        console.log('Received WebSocket message:', event.data);
        try {
            const data = JSON.parse(event.data);

            if (data.type === 'ping') {
                console.log('Received ping');
                return;
            }

            setIsLoading(false);

            if (data.type === 'status') {
                setProcessingStatuses(prev => [...prev, {
                    message: data.message,
                    timestamp: Date.now()
                }]);
                return;
            }

            if (data.type === 'message') {
                console.log('Received chat message:', data);
                setProcessingStatuses([]); // Clear processing statuses
                setMessages(prev => [...prev, {
                    role: 'assistant',
                    content: data.content,
                    metadata: data.metadata
                }]);
            } else if (data.type === 'error') {
                console.error('Received error:', data.error);
                setProcessingStatuses([]); // Clear processing statuses
                setMessages(prev => [...prev, {
                    role: 'assistant',
                    content: `Error: ${data.error}`,
                    metadata: { error: true }
                }]);
            }
        } catch (error) {
            console.error('Error parsing message:', error);
            setProcessingStatuses([]); // Clear processing statuses
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: 'Error: Failed to process response',
                metadata: { error: true }
            }]);
        }
    };

    } catch (error) {
        console.error('WebSocket connection error:', error);
    }
}, [reconnectAttempts]);

    useEffect(() => {
    if (isVisible) {
        connectWebSocket();
    }

    return () => {
        if (wsRef.current) {
            wsRef.current.close(1000, "Component unmounting");
            wsRef.current = null;
        }
    };
}, [connectWebSocket, isVisible]);

    const sendMessage = useCallback(async () => {
    try {
        setIsLoading(true);
        console.log('Sending message with data:', {
            message: input.trim(),
            article_id: articleId,
            brand_id: brandId,
            platform: "General"
        });

        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({
                message: input.trim(),
                article_id: articleId,
                brand_id: brandId,
                platform: "General"
            }));

            setMessages(prev => [...prev, {
                role: 'user',
                content: input.trim()
            }]);
            setInput('');
        } else {
            console.error('WebSocket not connected. State:', wsRef.current?.readyState);
            throw new Error('WebSocket is not connected');
        }
    } catch (error) {
        console.error('Error sending message:', error);
        setMessages(prev => [...prev, {
            role: 'assistant',
            content: 'Failed to send message. Please try again.',
            metadata: { error: true }
        }]);
    } finally {
        setIsLoading(false);
    }
}, [input, articleId, brandId]);

    if (!isVisible) return null;

    return (
        <div className="w-full h-full flex flex-col bg-white">
            {/* Header */}
            <div className="p-4 border-b">
                <div className="flex items-center justify-between">
                    <h2 className="text-lg font-semibold">Chat Assistant</h2>
                    <div className="flex items-center">
                        {isConnected ? (
                            <span className="text-green-500 text-sm flex items-center">
                                <span className="w-2 h-2 bg-green-500 rounded-full mr-2" />
                                Connected
                            </span>
                        ) : (
                            <span className="text-red-500 text-sm flex items-center">
                                <span className="w-2 h-2 bg-red-500 rounded-full mr-2" />
                                Disconnected
                            </span>
                        )}
                    </div>
                </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4">
                <div className="space-y-4">
                    {messages.map((msg, idx) => (
                        <div
                            key={idx}
                            className={`${
                                msg.role === 'user' ? 'ml-auto bg-blue-100' : 'mr-auto bg-gray-100'
                            } max-w-[80%] rounded-lg p-3 ${
                                msg.metadata?.error ? 'bg-red-100' : ''
                            }`}
                        >
                            <p className="whitespace-pre-wrap">{msg.content}</p>
                            {msg.metadata?.platform && (
                                <p className="text-xs text-gray-500 mt-1">
                                    Platform: {msg.metadata.platform}
                                </p>
                            )}
                        </div>
                    ))}
                    {processingStatuses.length > 0 && (
                        <div className="bg-gray-50 rounded p-3">
                            {processingStatuses.map((status, index) => (
                                <div key={status.timestamp} className="text-sm text-gray-600">
                                    {status.message}
                                </div>
                            ))}
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>
            </div>

            {/* Input */}
            <div className="p-4 border-t">
                <div className="flex space-x-2">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && !isLoading && sendMessage()}
                        placeholder="Type your message..."
                        className="flex-1 p-2 border rounded"
                        disabled={isLoading}
                    />
                    <button
                        onClick={sendMessage}
                        disabled={isLoading || !isConnected}
                        className={`px-4 py-2 rounded ${
                            isLoading || !isConnected
                                ? 'bg-gray-400'
                                : 'bg-blue-500 hover:bg-blue-600'
                        } text-white transition-colors`}
                    >
                        {isLoading ? 'Sending...' : 'Send'}
                    </button>
                </div>
            </div>
        </div>
    );
}