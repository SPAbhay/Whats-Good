import { useEffect, useState } from 'react';
import Link from 'next/link';
import { ProtectedRoute } from '../components/auth/ProtectedRoute';
import { config } from '../config';
import api, { brand } from '../services/api';

interface RecommendedArticle {
  article_id: string;
  title: string;
  summarized_content: string;
  category: string;
  author?: string;
  publish_date?: string;
  score: number;
  retrieval_strategy: string;
  matched_aspects: string[];
  topic_1?: string;
  topic_2?: string;
  topic_3?: string;
}

interface BrandDetails {
  id: number;
  processed_brand_name: string;
  processed_industry: string;
  processed_target_audience: string;
  processed_brand_values: string;
}

interface ErrorState {
  articles?: string;
  brand?: string;
}

const LoadingStates = () => {
  const loadingSteps = [
    "Reading your brand's profile...",
    "Analyzing your industry preferences...",
    "Searching through our curated articles...",
    "Finding the best matches for your brand...",
    "Preparing personalized recommendations..."
  ];
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentStep((prev) => (prev + 1) % loadingSteps.length);
    }, 2000);

    return () => clearInterval(timer);
  }, []);

  return (
    <div className="flex flex-col items-center justify-center space-y-6 py-12">
      <div className="flex space-x-2">
        <div className="w-3 h-3 bg-brand-blue rounded-full animate-bounce"></div>
        <div className="w-3 h-3 bg-brand-blue rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
        <div className="w-3 h-3 bg-brand-blue rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
      </div>
      <p className="text-lg text-gray-700 fade-in">{loadingSteps[currentStep]}</p>
    </div>
  );
};

export default function Home() {
  const [articles, setArticles] = useState<RecommendedArticle[]>([]);
  const [brandDetails, setBrandDetails] = useState<BrandDetails | null>(null);
  const [isLoadingArticles, setIsLoadingArticles] = useState(true);
  const [isLoadingBrand, setIsLoadingBrand] = useState(true);
  const [errors, setErrors] = useState<ErrorState>({});

  useEffect(() => {
    const loadData = async () => {
      try {
        const brandData = await brand.getProfile();
        setBrandDetails(brandData);
        setErrors(prev => ({ ...prev, brand: undefined }));

        if (brandData?.id) {
          const articlesResponse = await api.get(`/api/articles/recommended/${brandData.id}`);
          setArticles(articlesResponse.data.articles || []);
          setErrors(prev => ({ ...prev, articles: undefined }));
        }
      } catch (err) {
        setErrors(prev => ({
          ...prev,
          articles: config.ENV === 'development'
            ? `Error: ${err instanceof Error ? err.message : 'Unknown error'}`
            : 'Failed to load articles'
        }));
      } finally {
        setIsLoadingArticles(false);
        setIsLoadingBrand(false);
      }
    };

    loadData();
  }, []);

  const renderArticlesSection = () => (
    <div className="w-2/3 p-8">
      <h1 className="text-2xl font-bold mb-6">Recommended Articles</h1>
      {isLoadingArticles ? (
        <LoadingStates />
      ) : (
        <div className="grid gap-6">
          {articles.map(article => (
            <div key={article.article_id} className="article-card bg-white rounded-lg shadow hover:shadow-md transition-all duration-200">
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex space-x-2">
                    <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-medium">
                      {article.category || 'General'}
                    </span>
                    {article.score > 0.8 && (
                      <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm font-medium">
                        High Relevance
                      </span>
                    )}
                  </div>
                  <span className="text-sm text-gray-500">
                    {article.publish_date && new Date(article.publish_date).toLocaleDateString()}
                  </span>
                </div>

                <Link href={`/articles/${article.article_id}`}>
                  <h2 className="text-xl font-semibold mb-3 line-clamp-2 hover:text-brand-blue transition-colors">
                    {article.title}
                  </h2>
                </Link>

                <p className="text-gray-600 mb-4 line-clamp-3">
                  {article.summarized_content}
                </p>

                <div className="flex flex-wrap gap-2 mb-4">
                  {[article.topic_1, article.topic_2, article.topic_3].filter(Boolean).map((topic, index) => (
                    <span key={index} className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm font-medium">
                      {topic}
                    </span>
                  ))}
                </div>

                <div className="flex items-center justify-between text-sm border-t pt-4 mt-4">
                  <span className="text-gray-600 font-medium">
                    By {article.author || 'Unknown Author'}
                  </span>
                </div>
              </div>
            </div>
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
          <LoadingStates />
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
      <div className="flex flex-col md:flex-row bg-gray-100">
        {renderArticlesSection()}
        {renderBrandSection()}
      </div>
    </ProtectedRoute>
  );
}
