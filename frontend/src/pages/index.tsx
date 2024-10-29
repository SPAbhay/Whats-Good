import { useEffect, useState } from 'react';
import Link from 'next/link';
import { brand } from '../services/api';
import { ProtectedRoute } from '../components/auth/ProtectedRoute';

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

export default function Home() {
  const [articles, setArticles] = useState<Article[]>([]);
  const [brandDetails, setBrandDetails] = useState<BrandDetails | null>(null);
  const [isLoadingArticles, setIsLoadingArticles] = useState(true);
  const [isLoadingBrand, setIsLoadingBrand] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    // Load articles and brand details independently
    const loadData = async () => {
      // Load articles
      try {
        console.log('Fetching articles...');
        const articlesResponse = await fetch('http://localhost:8000/api/articles');
        const articlesData = await articlesResponse.json();
        console.log('Received articles:', articlesData);
        setArticles(articlesData);
      } catch (err) {
        console.error('Error fetching articles:', err);
      } finally {
        setIsLoadingArticles(false);
      }

      try {
        console.log('Fetching brand details...');
        const brandData = await brand.getProfile();
        console.log('Received brand data:', brandData);
        setBrandDetails(brandData);
      } catch (err) {
        console.error('Error fetching brand details:', err);
      } finally {
        setIsLoadingBrand(false);
      }
    };

    loadData();
  }, []);

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50">
        <div className="flex">
          {/* Articles Section (2/3 width) */}
          <div className="w-2/3 p-8">
            <h1 className="text-2xl font-bold mb-6">Articles</h1>
            {isLoadingArticles ? (
              <div className="flex items-center justify-center space-x-4">
                <div className="w-3 h-3 bg-blue-500 rounded-full animate-bounce"></div>
                <div className="w-3 h-3 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                <div className="w-3 h-3 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
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
              </div>
            )}
          </div>

          {/* Brand Details Section (1/3 width) */}
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
        {/* ... existing brand details display ... */}
      </div>
    ) : (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-center space-y-4">
          <div className="text-yellow-600 bg-yellow-50 p-4 rounded-lg mb-4">
            <h3 className="font-semibold mb-2">Welcome to Your Brand Dashboard!</h3>
            <p className="text-sm text-yellow-700">
              To get started, please complete the brand questionnaire.
            </p>
          </div>
          <Link
            href="/onboarding/questions"
            className="inline-block px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors"
          >
            Complete Brand Questionnaire
          </Link>
          <p className="text-sm text-gray-500 mt-4">
            This will help us understand your brand better and provide personalized content recommendations.
          </p>
        </div>
      </div>
    )}
  </div>
</div>
        </div>
      </div>
    </ProtectedRoute>
  );
}
