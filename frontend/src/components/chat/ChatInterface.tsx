// ... other imports
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

interface ProcessingStatus {
    message: string;
    timestamp: number;
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
        <div className="w-full h-full flex flex-col bg-white/70 backdrop-blur-md">
            {/* Header */}
            <div className="p-4 border-b border-surface-200 bg-white/50 backdrop-blur-md">
                <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                        <h2 className="text-lg font-bold text-gray-900">AI Assistant</h2>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium
                            ${isConnected
                                ? 'bg-green-100 text-green-700'
                                : 'bg-red-100 text-red-700'
                            }`}
                        >
                            {isConnected ? 'Connected' : 'Disconnected'}
                        </span>
                    </div>
                </div>
            </div>

            {/* Processing Status */}
            {processingStatuses.length > 0 && (
                <div className="p-2 text-gray-600">
                    {processingStatuses[processingStatuses.length - 1].message}
                </div>
            )}

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 bg-gradient-to-br from-gray-50 to-white">
                <div className="space-y-4">
                    {messages.length === 0 && (
                        <div className="text-center py-8">
                            <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
                                <svg className="w-8 h-8 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                                </svg>
                            </div>
                            <h3 className="text-gray-900 font-medium mb-2">Welcome to AI Chat Assistant</h3>
                            <p className="text-gray-600">Ask questions about the article or get recommendations</p>
                        </div>
                    )}

                    {messages.map((msg, idx) => (
                        <div
                            key={idx}
                            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                        >
                            <div
                                className={`max-w-[80%] rounded-2xl p-4 ${
                                    msg.role === 'user'
                                        ? 'bg-primary-500 text-white'
                                        : 'bg-white border border-surface-200 text-gray-800'
                                } ${msg.metadata?.error ? 'bg-red-50 border-red-100 text-red-600' : ''}`}
                            >
                                <p className="whitespace-pre-wrap leading-relaxed">
                                    {msg.content}
                                </p>
                                {msg.metadata?.platform && (
                                    <p className={`text-xs mt-2 ${
                                        msg.role === 'user' ? 'text-primary-100' : 'text-gray-500'
                                    }`}>
                                        Platform: {msg.metadata.platform}
                                    </p>
                                )}
                            </div>
                        </div>
                    ))}
                    <div ref={messagesEndRef} />
                </div>
            </div>

            {/* Input Area */}
            <div className="p-4 border-t border-surface-200 bg-white">
                <div className="flex items-center space-x-4">
                    <input
                        className="flex-1 border border-surface-300 rounded-md p-2 text-gray-800"
                        placeholder="Type your message..."
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
                    />
                    <button
                        className="bg-primary-600 text-white rounded-md px-4 py-2"
                        onClick={sendMessage}
                        disabled={isLoading || !input.trim()}
                    >
                        Send
                    </button>
                </div>
            </div>
        </div>
    );
}