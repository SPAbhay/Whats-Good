import { useEffect, useState } from 'react';
import Link from 'next/link';
import { ProtectedRoute } from '../components/auth/ProtectedRoute';
import { config } from '../config';
import api, { brand } from '../services/api';

interface Article {
  id: number;
  summarized_content: string;
  source_url: string;
}

interface BrandDetails {
  processed_brand_name: string;
  processed_industry: string;
  processed_target_audience: string;
  processed_brand_values: string;
  processed_social_presence?: string;
}

interface ErrorState {
  articles?: string;
  brand?: string;
}

export default function Home() {
  const [articles, setArticles] = useState<Article[]>([]);
  const [brandDetails, setBrandDetails] = useState<BrandDetails | null>(null);
  const [isLoadingArticles, setIsLoadingArticles] = useState(true);
  const [isLoadingBrand, setIsLoadingBrand] = useState(true);
  const [errors, setErrors] = useState<ErrorState>({});

  useEffect(() => {
    const loadData = async () => {
      // Load articles using api instance
      try {
        console.log('Fetching articles...');
        console.log('API instance:', api); // Debugging
        const articlesResponse = await api.get('/api/articles');
        console.log('Received articles:', articlesResponse.data);
        setArticles(articlesResponse.data);
        setErrors(prev => ({ ...prev, articles: undefined }));
      } catch (err) {
        console.error('Error fetching articles:', err);
        setErrors(prev => ({
          ...prev,
          articles: config.ENV === 'development'
            ? `Error: ${err instanceof Error ? err.message : 'Unknown error'}`
            : 'Failed to load articles'
        }));
      } finally {
        setIsLoadingArticles(false);
      }

      // Load brand details
      try {
        console.log('Fetching brand details...');
        const brandData = await brand.getProfile();
        console.log('Received brand data:', brandData);
        setBrandDetails(brandData);
        setErrors(prev => ({ ...prev, brand: undefined }));
      } catch (err) {
        console.error('Error fetching brand details:', err);
        setErrors(prev => ({
          ...prev,
          brand: config.ENV === 'development'
            ? `Error: ${err instanceof Error ? err.message : 'Unknown error'}`
            : 'Failed to load brand details'
        }));
      } finally {
        setIsLoadingBrand(false);
      }
    };

    loadData();
  }, []);

  const renderArticlesSection = () => (
  <div className="w-2/3 p-8">
    <h1 className="text-2xl font-bold mb-6">Latest Updates</h1>
    {isLoadingArticles ? (
      <div className="flex items-center justify-center space-x-4">
        <div className="w-3 h-3 bg-blue-500 rounded-full animate-bounce"></div>
        <div className="w-3 h-3 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
        <div className="w-3 h-3 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
      </div>
    ) : (
      <div className="grid gap-6">
        {articles.map(article => (
          <Link
            href={`/articles/${article.article_id}`}
            key={article.article_id}
            className="block bg-white rounded-lg shadow hover:shadow-md transition-all duration-200 overflow-hidden"
          >
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <span className="px-3 py-1 bg-blue-100 text-blue-600 rounded-full text-sm">
                  {article.category || 'General'}
                </span>
                <span className="text-sm text-gray-500">
                  {new Date(article.publish_date).toLocaleDateString()}
                </span>
              </div>

              <h2 className="text-xl font-semibold mb-3 line-clamp-2">
                {article.title}
              </h2>

              <p className="text-gray-600 mb-4 line-clamp-3">
                {article.summarized_content}
              </p>

              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">
                  By {article.author || 'Unknown Author'}
                </span>
                <span className="text-blue-500 font-medium">
                  Read more →
                </span>
              </div>
            </div>
          </Link>
        ))}
        {articles.length === 0 && !errors.articles && (
          <div className="text-center py-12 bg-white rounded-lg">
            <p className="text-gray-500">No articles available</p>
          </div>
        )}
      </div>
    )}
  </div>
);

  const renderBrandSection = () => (
  <div className="w-1/3 p-8 border-l">
    <div className="sticky top-8">
      <h2 className="text-xl font-bold mb-6">Your Brand Profile</h2>
      {isLoadingBrand ? (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="animate-pulse space-y-4">
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
            <div className="h-4 bg-gray-200 rounded w-5/6"></div>
            <div className="h-4 bg-gray-200 rounded w-2/3"></div>
          </div>
        </div>
      ) : brandDetails ? (
        <div className="bg-white rounded-lg shadow p-6 space-y-4">
          <div>
            <h3 className="font-semibold text-gray-700">Brand Name</h3>
            <p>{brandDetails.processed_brand_name || 'Not processed yet'}</p>
          </div>
          <div>
            <h3 className="font-semibold text-gray-700">Industry</h3>
            <p>{brandDetails.processed_industry || 'Not processed yet'}</p>
          </div>
          <div>
            <h3 className="font-semibold text-gray-700">Target Audience</h3>
            <p>{brandDetails.processed_target_audience || 'Not processed yet'}</p>
          </div>
          <div>
            <h3 className="font-semibold text-gray-700">Brand Values</h3>
            <p>{brandDetails.processed_brand_values || 'Not processed yet'}</p>
          </div>
        </div>
      ) : (
        <Link
          href="/onboarding/questions"
          className="block bg-white rounded-lg shadow p-6 text-center hover:shadow-md transition-shadow"
        >
          <div className="text-yellow-600 mb-4">Complete your brand profile</div>
          <button className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600">
            Get Started
          </button>
        </Link>
      )}
    </div>
  </div>
);

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50">
        <div className="flex">
          {renderArticlesSection()}
          {renderBrandSection()}
        </div>
        {config.ENV === 'development' && (
          <div className="fixed bottom-4 right-4 bg-gray-800 text-white px-3 py-1 rounded-full text-xs">
            ENV: {config.ENV}
          </div>
        )}
      </div>
    </ProtectedRoute>
  );
}