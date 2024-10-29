import { useState, useEffect, useRef, useCallback } from 'react';

interface Message {
    role: 'user' | 'assistant';
    content: string;
    metadata?: any;
}

interface ProcessingStatus {
    message: string;
    timestamp: number;
}

interface ChatInterfaceProps {
    articleId: string;
    brandId: string;
}

export default function ChatInterface({ articleId, brandId }: ChatInterfaceProps) {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [isConnected, setIsConnected] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [reconnectAttempts, setReconnectAttempts] = useState(0);
    const wsRef = useRef<WebSocket | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
    const [processingStatuses, setProcessingStatuses] = useState<ProcessingStatus[]>([]);

    const scrollToBottom = useCallback(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, []);

    useEffect(() => {
        scrollToBottom();
    }, [messages, scrollToBottom]);

    // Debug logging function
    const debugLog = useCallback((message: string, data?: any) => {
        const timestamp = new Date().toISOString();
        console.log(`[${timestamp}] ${message}`, data || '');
    }, []);

    const connectWebSocket = useCallback(() => {
        debugLog('Attempting to connect WebSocket...');

        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
            reconnectTimeoutRef.current = undefined;
        }

        if (wsRef.current?.readyState === WebSocket.OPEN) {
            debugLog('WebSocket already connected');
            return;
        }

        if (wsRef.current?.readyState === WebSocket.CONNECTING) {
            debugLog('WebSocket already connecting');
            return;
        }

        if (wsRef.current) {
            debugLog('Closing existing WebSocket connection');
            wsRef.current.close();
            wsRef.current = null;
        }

        const clientId = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        const ws = new WebSocket(`ws://localhost:8000/ws/${clientId}`);
        wsRef.current = ws;

        ws.onopen = () => {
            debugLog('WebSocket Connected Successfully');
            setIsConnected(true);
            setReconnectAttempts(0);
        };

        ws.onmessage = (event) => {
            debugLog('Received WebSocket message:', event.data);
            try {
                const data = JSON.parse(event.data);

                if (data.type === 'ping') {
                    debugLog('Received ping');
                    return;
                }

                setIsLoading(false);

                if (data.type === 'processing_status') {
                    debugLog('Received processing status:', data.status);
                    setProcessingStatuses(prev => [...prev, {
                        message: data.status,
                        timestamp: Date.now()
                    }]);
                    return;
                }

                if (data.type === 'message') {
                    debugLog('Received chat message:', data);
                    setProcessingStatuses([]);
                    setMessages(prev => [...prev, {
                        role: 'assistant',
                        content: data.content,
                        metadata: data.metadata
                    }]);
                } else if (data.type === 'error') {
                    debugLog('Received error:', data.error);
                    setMessages(prev => [...prev, {
                        role: 'assistant',
                        content: `Error: ${data.error}`,
                        metadata: { error: true }
                    }]);
                }
            } catch (error) {
                debugLog('Error parsing message:', error);
            }
        };

        ws.onclose = (event) => {
            debugLog('WebSocket Disconnected', { code: event.code, reason: event.reason });
            setIsConnected(false);
            wsRef.current = null;

            if (event.code !== 1000 && reconnectAttempts < 3) {
                const timeout = Math.min(1000 * Math.pow(2, reconnectAttempts), 5000);
                debugLog(`Scheduling reconnect in ${timeout}ms`);
                reconnectTimeoutRef.current = setTimeout(() => {
                    setReconnectAttempts(prev => prev + 1);
                    connectWebSocket();
                }, timeout);
            }
        };

        ws.onerror = (error) => {
            debugLog('WebSocket error:', error);
            setIsConnected(false);
        };
    }, [articleId, brandId, reconnectAttempts, debugLog]);

    useEffect(() => {
        debugLog('Initializing chat interface', { articleId, brandId });
        connectWebSocket();

        // Cleanup function
        return () => {
            debugLog('Cleaning up chat interface');
            if (reconnectTimeoutRef.current) {
                clearTimeout(reconnectTimeoutRef.current);
            }
            if (wsRef.current) {
                wsRef.current.close(1000, "Component unmounting");
                wsRef.current = null;
            }
        };
    }, [articleId, brandId, connectWebSocket, debugLog]);

    const sendMessage = useCallback(async () => {
        debugLog('Attempting to send message...');

        if (!input.trim() || !wsRef.current || !isConnected || isLoading) {
            debugLog('Send prevented due to:', {
                noInput: !input.trim(),
                noWebSocket: !wsRef.current,
                notConnected: !isConnected,
                isLoading
            });
            return;
        }

        try {
            setIsLoading(true);
            const message = {
                message: input.trim(),
                article_id: articleId,
                brand_id: brandId,
                platform: "General"
            };

            debugLog('Sending message:', message);

            if (wsRef.current?.readyState === WebSocket.OPEN) {
                wsRef.current.send(JSON.stringify(message));

                setMessages(prev => [...prev, {
                    role: 'user',
                    content: input.trim()
                }]);

                setInput('');
            } else {
                throw new Error('WebSocket is not connected');
            }
        } catch (error) {
            debugLog('Error sending message:', error);
            setIsLoading(false);
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: 'Failed to send message. Please try again.',
                metadata: { error: true }
            }]);

            if (wsRef.current?.readyState !== WebSocket.OPEN) {
                connectWebSocket();
            }
        }
    }, [input, articleId, brandId, isConnected, isLoading, connectWebSocket, debugLog]);

    // Function to render processing status
    const renderProcessingStatus = () => {
        if (!isLoading || processingStatuses.length === 0) return null;

        return (
            <div className="space-y-3 my-4 bg-gray-50 rounded-lg p-4">
                {processingStatuses.map((status, index) => (
                    <div
                        key={status.timestamp}
                        className={`
                            flex items-center space-x-3
                            transition-all duration-500 ease-in-out
                            ${index === processingStatuses.length - 1 ? 'opacity-100' : 'opacity-50'}
                        `}
                    >
                        <div className="flex-shrink-0">
                            <div className={`
                                w-2 h-2 rounded-full
                                ${index === processingStatuses.length - 1
                                    ? 'bg-blue-500 animate-pulse'
                                    : 'bg-gray-400'}
                            `}/>
                        </div>
                        <div className={`
                            text-sm
                            ${index === processingStatuses.length - 1
                                ? 'text-blue-600 font-medium'
                                : 'text-gray-500'}
                        `}>
                            {status.message}
                        </div>
                    </div>
                ))}
            </div>
        );
    };

    return (
        <div className="w-1/3 fixed right-0 top-[20vh] h-[80vh] border-l bg-white">
            <div className="flex flex-col h-full">
                <div className="p-4 border-b">
                    <h2 className="text-lg font-semibold flex items-center justify-between">
                        Chat Assistant
                        <div className="flex items-center">
                            {isConnected ? (
                                <span className="text-green-500 text-sm flex items-center">
                                    <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                                    Connected
                                </span>
                            ) : (
                                <span className="text-red-500 text-sm flex items-center">
                                    <span className="w-2 h-2 bg-red-500 rounded-full mr-2"></span>
                                    Disconnected {reconnectAttempts > 0 ? `(Retry ${reconnectAttempts}/3)` : ''}
                                </span>
                            )}
                        </div>
                    </h2>
                </div>

                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                    {messages.map((msg, idx) => (
                        <div
                            key={idx}
                            className={`${
                                msg.role === 'user'
                                    ? 'ml-auto bg-blue-100'
                                    : 'mr-auto bg-gray-100'
                            } max-w-[80%] rounded-lg p-3 ${
                                msg.metadata?.error ? 'bg-red-100' : ''
                            }`}
                        >
                            <p>{msg.content}</p>
                            {msg.metadata?.platform && (
                                <p className="text-xs text-gray-500 mt-1">
                                    Platform: {msg.metadata.platform}
                                </p>
                            )}
                        </div>
                    ))}
                    {isLoading && renderProcessingStatus()}
                    <div ref={messagesEndRef} />
                </div>

                <div className="p-4 border-t">
                    <div className="flex space-x-2">
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyPress={(e) => {
                                if (e.key === 'Enter') {
                                    sendMessage();
                                }
                            }}
                            className="flex-1 border rounded-lg px-4 py-2"
                            placeholder="Type a message..."
                        />
                        <button
                            onClick={sendMessage}
                            className={`px-4 py-2 rounded-lg text-white ${
                                isLoading ? 'bg-gray-500' : 'bg-blue-500'
                            }`}
                            disabled={isLoading}
                        >
                            Send
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
