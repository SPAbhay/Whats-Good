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
      <h1 className="text-2xl font-bold mb-6">Articles</h1>
      {isLoadingArticles ? (
        <div className="flex items-center justify-center space-x-4">
          <div className="w-3 h-3 bg-blue-500 rounded-full animate-bounce"></div>
          <div className="w-3 h-3 bg-blue-500 rounded-full animate-bounce"
               style={{ animationDelay: '0.2s' }}></div>
          <div className="w-3 h-3 bg-blue-500 rounded-full animate-bounce"
               style={{ animationDelay: '0.4s' }}></div>
        </div>
      ) : (
        <>
          {errors.articles ? (
            <div className="text-red-500 bg-red-50 p-4 rounded-lg text-center">
              {errors.articles}
              {config.ENV === 'development' && (
                <button
                  onClick={() => window.location.reload()}
                  className="mt-2 text-sm text-blue-500 hover:underline"
                >
                  Retry
                </button>
              )}
            </div>
          ) : (
            <div className="grid gap-4">
              {articles.map(article => (
                <Link
                  href={`/articles/${article.id}`}
                  key={article.id}
                  className="block p-6 bg-white rounded-lg shadow hover:shadow-md transition-shadow"
                >
                  <h2 className="text-xl mb-2">{article.summarized_content}</h2>
                  <p className="text-sm text-gray-600">Source: {article.source_url}</p>
                </Link>
              ))}
              {articles.length === 0 && !errors.articles && (
                <div className="text-center text-gray-500">
                  No articles found
                </div>
              )}
            </div>
          )}
        </>
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
        ) : errors.brand ? (
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-red-500 text-center">
              {errors.brand}
              {config.ENV === 'development' && (
                <button
                  onClick={() => window.location.reload()}
                  className="mt-2 text-sm text-blue-500 hover:underline"
                >
                  Retry
                </button>
              )}
            </div>
          </div>
        ) : brandDetails ? (
          <div className="bg-white rounded-lg shadow p-6 space-y-4">
            <div>
              <h3 className="font-semibold text-gray-700">Brand Name</h3>
              <p>{brandDetails.processed_brand_name}</p>
            </div>
            <div>
              <h3 className="font-semibold text-gray-700">Industry</h3>
              <p>{brandDetails.processed_industry}</p>
            </div>
            <div>
              <h3 className="font-semibold text-gray-700">Target Audience</h3>
              <p>{brandDetails.processed_target_audience}</p>
            </div>
            <div>
              <h3 className="font-semibold text-gray-700">Brand Values</h3>
              <p>{brandDetails.processed_brand_values}</p>
            </div>
            {brandDetails.processed_social_presence && (
              <div>
                <h3 className="font-semibold text-gray-700">Social Media Presence</h3>
                <p>{brandDetails.processed_social_presence}</p>
              </div>
            )}
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-center space-y-4">
              <div className="text-yellow-600 bg-yellow-50 p-4 rounded-lg mb-4">
                <h3 className="font-semibold mb-2">Welcome to Your Brand Dashboard!</h3>
                <p className="text-sm text-yellow-700">
                  To get started, please complete your onboarding.
                </p>
              </div>
              <Link
                href="/onboarding/questions"
                className="inline-block px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors"
              >
                Complete Brand Questionnaire
              </Link>
            </div>
          </div>
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