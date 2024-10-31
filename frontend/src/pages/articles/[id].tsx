import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { Navbar } from '../../components/layout/Navbar';
import ChatInterface from '../../components/chat/ChatInterface';
import api from '../../services/api';

interface Article {
  article_id: string;
  title: string;
  author: string;
  source_url: string;
  publish_date: string;
  category: string;
  summarized_content: string;
  topics: string[];
  insights: Insights;
  created_at: string;
}

interface Insights {
  content_metrics: {
    engagement_potential?: number; // Use number or undefined if not guaranteed
    audience_sentiment?: number; // Use number or undefined if not guaranteed
  };
  recommendations: string[];
}

interface TooltipProps {
  text: string;
  children: React.ReactNode;
}

const Tooltip = ({ text, children }: TooltipProps) => {
  return (
    <div className="group relative inline-block">
      {children}
      <div className="opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 text-sm text-white bg-gray-900 rounded-lg whitespace-nowrap">
        {text}
        <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-2 h-2 bg-gray-900 rotate-45" />
      </div>
    </div>
  );
};

const InsightsSection = ({ insights }: { insights: Insights }) => {
  console.log('Raw insights data:', insights);

  const contentMetrics = insights?.content_metrics || {};
  const recommendations = insights?.recommendations || [];

  const insightCategories = [
    {
      key: 'engagement',
      title: 'Engagement Metrics',
      description: 'Content engagement potential and metrics',
      icon: '📊',
      data: [`Engagement Potential: ${contentMetrics.engagement_potential !== undefined ? contentMetrics.engagement_potential : 'N/A'}`],
    },
    {
      key: 'sentiment',
      title: 'Audience Sentiment',
      description: 'Overall audience sentiment, -1 to 1',
      icon: '🎯',
      data: [`Sentiment Score: ${contentMetrics.audience_sentiment !== undefined ? contentMetrics.audience_sentiment : 'N/A'}`],
    },
    {
      key: 'recommendations',
      title: 'Recommendations',
      description: 'Suggested improvements and actions',
      icon: '💡',
      data: recommendations,
    },
  ];

  const validCategories = insightCategories.filter(category =>
    category.data && category.data.length > 0 &&
    !category.data.every(item =>
      item === 'N/A' ||
      item === 'No data available' ||
      item === 'Unable to determine' ||
      item === 'Insufficient data',
    ),
  );

  if (validCategories.length === 0) {
    return (
      <div className="mt-8 text-center py-8 bg-gray-50 rounded-xl border border-surface-200">
        <p className="text-gray-600">No insights available for this article yet.</p>
      </div>
    );
  }

  return (
    <div className="mt-8 space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Article Insights</h2>
        <Tooltip text="AI-powered analysis of the article's key points and opportunities">
          <div className="cursor-help p-1">
            <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
        </Tooltip>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {validCategories.map(category => (
          <div
            key={category.key}
            className="bg-white/80 rounded-xl p-6 border border-surface-200 shadow-sm hover:shadow-md transition-all duration-200"
          >
            <div className="flex items-start space-x-4">
              <div className="text-2xl">{category.icon}</div>
              <div className="flex-1">
                <div className="flex items-center mb-3">
                  <h3 className="text-lg font-semibold text-gray-900">{category.title}</h3>
                  <Tooltip text={category.description}>
                    <div className="ml-2 cursor-help">
                      <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                  </Tooltip>
                </div>
                <ul className="space-y-2">
                  {category.data.map((item, index) => (
                    <li key={index} className="flex items-start space-x-2 text-gray-800">
                      <span className="text-primary-500 mt-1">•</span>
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default function ArticleDetailPage() {
  const router = useRouter();
  const { id } = router.query;
  const [article, setArticle] = useState<Article | null>(null);
  const [brandId, setBrandId] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isChatVisible] = useState(true); // Removed setIsChatVisible since it's not used

  useEffect(() => {
    const loadArticleAndInitChat = async () => {
      if (!id) return;
      try {
        setIsLoading(true);
        const articleResponse = await api.get(`/api/articles/${id}`);
        setArticle(articleResponse.data);

        const chatResponse = await api.post(`/api/articles/${id}/init-chat`);
        if (chatResponse.data.status === 'success') {
          setBrandId(chatResponse.data.brand_id);
        }
      } catch (err: unknown) {
  // Check if err is an instance of Error and has a message property
  if (err instanceof Error) {
    setError(err.message);
  } else {
    setError("An unexpected error occurred."); // Fallback error message
  }
}finally {
        setIsLoading(false);
      }
    };

    loadArticleAndInitChat();
  }, [id]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading article...</p>
        </div>
      </div>
    );
  }

  if (error || !article) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center p-6 bg-white rounded-lg shadow-md">
          <p className="text-red-500 mb-4">{error || 'Article not found'}</p>
          <Link href="/" className="text-blue-500 hover:underline">← Back to Articles</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-surface-50 to-primary-50">
      <Navbar />

      <main className={`transition-all duration-300 ${isChatVisible ? 'mr-[400px]' : ''}`}>
        <div className="max-w-4xl mx-auto px-4 py-8">
          <div className="flex items-center justify-between mb-8">
            <Link
              href="/"
              className="flex items-center text-primary-600 hover:text-primary-700 transition-colors"
            >
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Back to Articles
            </Link>
          </div>

          <div className="bg-white shadow-lg rounded-lg p-6">
            <h1 className="text-3xl font-bold text-gray-800 mb-2">{article.title}</h1>

            <p className="text-gray-500 mb-4">By {article.author} | {new Date(article.publish_date).toLocaleDateString()}</p>
            <p className="text-gray-700 mb-4">{article.summarized_content}</p>
            <Link href={article.source_url} target="_blank" className="text-blue-500 hover:underline">Read Full Article</Link>
          </div>

          <InsightsSection insights={article.insights} />
        </div>
      </main>

      {isChatVisible && brandId && (
  <div className="fixed top-0 right-0 w-[400px] h-screen bg-white/70 backdrop-blur-md shadow-lg z-50 border-l border-surface-200">
    <ChatInterface
      articleId={id as string}
      brandId={brandId.toString()}
    />
  </div>
)}
    </div>
  );
}
