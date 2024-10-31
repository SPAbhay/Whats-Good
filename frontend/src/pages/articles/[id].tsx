import { useState, useEffect, useMemo } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
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
  insights: any;
  created_at: string;
}

const InsightsSection = ({ insights }: { insights: any }) => {
  const [activeCategory, setActiveCategory] = useState<string | null>(null);

  const getCategoryIcon = (category: string) => {
    const icons = {
      sentiment: "🎯",
      key_points: "💡",
      market_trends: "📈",
      industry_impact: "🏢",
      action_items: "✅",
      predictions: "🔮"
    };
    return icons[category] || "📊";
  };

  const processedInsights = useMemo(() => {
    if (!insights) return {};

    return Object.entries(insights).reduce((acc, [key, value]) => {
      if (!value) return acc;

      let category = "key_points";
      if (key.includes("sentiment")) category = "sentiment";
      if (key.includes("trend") || key.includes("growth")) category = "market_trends";
      if (key.includes("impact") || key.includes("industry")) category = "industry_impact";
      if (key.includes("action") || key.includes("recommend")) category = "action_items";
      if (key.includes("predict") || key.includes("future")) category = "predictions";

      if (!acc[category]) acc[category] = [];
      acc[category].push({ key, value });
      return acc;
    }, {});
  }, [insights]);

  return (
    <div className="mt-8 bg-white rounded-lg shadow-lg p-6">
      <h2 className="text-2xl font-bold mb-6 text-gray-800">Article Insights</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        {Object.keys(processedInsights).map((category) => (
          <button
            key={category}
            onClick={() => setActiveCategory(activeCategory === category ? null : category)}
            className={`p-4 rounded-lg transition-all duration-200 text-left hover:shadow-md
              ${activeCategory === category
                ? 'bg-blue-50 border-2 border-blue-500'
                : 'bg-gray-50 hover:bg-gray-100 border-2 border-transparent'}`}
          >
            <div className="flex items-center space-x-3">
              <span className="text-2xl">{getCategoryIcon(category)}</span>
              <span className="font-medium capitalize">
                {category.replace(/_/g, ' ')}
              </span>
            </div>
          </button>
        ))}
      </div>
      {activeCategory && (
        <div className="mt-6 space-y-4 animate-fadeIn">
          <div className="bg-gray-50 rounded-lg p-6">
            <div className="grid gap-4">
              {processedInsights[activeCategory].map(({ key, value }, index) => (
                <div
                  key={key}
                  className="bg-white p-4 rounded-lg shadow-sm hover:shadow-md transition-shadow duration-200"
                >
                  <div className="flex items-start space-x-3">
                    <span className="flex-shrink-0 w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center text-blue-500 font-medium">
                      {index + 1}
                    </span>
                    <div>
                      <h4 className="font-medium text-gray-900 capitalize mb-1">
                        {key.replace(/_/g, ' ')}
                      </h4>
                      <p className="text-gray-600">
                        {typeof value === 'string' ? value : JSON.stringify(value)}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
      <div className="mt-8 grid grid-cols-2 md:grid-cols-4 gap-4">
        {Object.keys(processedInsights).map((category) => (
          <div key={category} className="text-center">
            <div className="text-sm text-gray-500 capitalize">
              {category.replace(/_/g, ' ')}
            </div>
            <div className="text-xl font-semibold text-gray-800">
              {processedInsights[category].length}
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
  const [chatInitialized, setChatInitialized] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isChatVisible, setIsChatVisible] = useState(true);

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
          setChatInitialized(true);
        }
      } catch (err) {
        setError(err.message);
      } finally {
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
    <div className="min-h-screen bg-gray-50">
      <div className={`transition-all duration-300 ${isChatVisible ? 'mr-[400px]' : ''}`}>
        <div className="max-w-4xl mx-auto px-4 py-8">
          <div className="flex items-center justify-between mb-6">
            <Link href="/" className="text-blue-500 hover:underline flex items-center">← Back to Articles</Link>
            <button
              onClick={() => setIsChatVisible(!isChatVisible)}
              className="flex items-center px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
            >
              {isChatVisible ? 'Hide Chat' : 'Show Chat'}
            </button>
          </div>

          <div className="bg-white rounded-lg shadow-lg p-8">
            <div className="flex items-center justify-between mb-6">
              <span className="px-3 py-1 bg-blue-100 text-blue-600 rounded-full">
                {article.category || 'General'}
              </span>
              <time className="text-gray-500">
                {new Date(article.publish_date).toLocaleDateString()}
              </time>
            </div>

            <h1 className="text-3xl font-bold mb-4">{article.title}</h1>
            {article.author && <p className="text-gray-600 mb-6">By {article.author}</p>}

            <div className="prose max-w-none mb-8">
              <p className="text-lg leading-relaxed">{article.summarized_content}</p>
            </div>

            {article.insights && <InsightsSection insights={article.insights} />}

            {article.topics?.length > 0 && (
              <div className="mb-6">
                <h2 className="text-xl font-semibold mb-3">Topics</h2>
                <div className="flex flex-wrap gap-2">
                  {article.topics.filter(Boolean).map((topic, index) => (
                    <span key={index} className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm">
                      {topic}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {article.source_url && (
              <Link href={article.source_url} target="_blank" className="text-blue-500 hover:underline">
                View Original Article
              </Link>
            )}
          </div>
        </div>
      </div>

      {isChatVisible && brandId && (
        <div className="fixed top-0 right-0 w-[400px] h-screen bg-white shadow-lg z-50 overflow-y-auto">
          <ChatInterface articleId={id as string} brandId={brandId} />
        </div>
      )}
    </div>
  );
}
