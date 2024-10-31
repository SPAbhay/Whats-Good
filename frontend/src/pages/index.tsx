import { useEffect, useState } from 'react';
import Link from 'next/link';
import { ProtectedRoute } from '../components/auth/ProtectedRoute';
import { config } from '../config';
import api, { brand } from '../services/api';
import { Navbar } from '../components/layout/Navbar';

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
  }, [loadingSteps.length]); // Include loadingSteps.length in the dependency array

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

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gradient-to-br from-surface-50 to-primary-50">
        <Navbar />
        <div className="flex flex-col md:flex-row max-w-7xl mx-auto">
          {/* Articles Section */}
          <div className="w-full md:w-2/3 p-6">
            <h1 className="text-3xl font-bold text-surface-800 mb-8">
              Recommended Articles
            </h1>
            {isLoadingArticles ? (
              <LoadingStates />
            ) : (
              <div className="grid gap-6">
                {articles.map(article => (
                  <div key={article.article_id}
                    className="bg-white/70 backdrop-blur-md rounded-xl shadow-md hover:shadow-lg transition-all duration-300 border border-surface-200"
                  >
                    <div className="p-6">
                      <div className="flex items-center justify-between mb-4">
                        <div className="flex gap-2">
                          <span className="px-3 py-1 bg-primary-100 text-primary-700 rounded-full text-sm font-medium">
                            {article.category || 'General'}
                          </span>
                          {article.score > 0.8 && (
                            <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm font-medium">
                              High Relevance
                            </span>
                          )}
                        </div>
                        <span className="text-sm text-surface-400">
                          {article.publish_date && new Date(article.publish_date).toLocaleDateString()}
                        </span>
                      </div>

                      <Link href={`/articles/${article.article_id}`}
                        className="group block"
                      >
                        <h2 className="text-xl font-semibold mb-3 text-surface-800 group-hover:text-primary-600 transition-colors">
                          {article.title}
                        </h2>
                      </Link>

                      <p className="mb-4 line-clamp-3 text-gray-800 leading-relaxed">
                        {article.summarized_content}
                      </p>

                      <div className="flex flex-wrap gap-2 mb-4">
                        {[article.topic_1, article.topic_2, article.topic_3]
                          .filter(Boolean)
                          .map((topic, index) => (
                            <span key={index}
                              className="px-3 py-1 bg-surface-100 text-surface-600 rounded-full text-sm font-medium"
                            >
                              {topic}
                            </span>
                          ))}
                      </div>

                      <div className="flex items-center justify-between pt-4 border-t border-surface-200">
                        <span className="text-surface-500 font-medium">
                          By {article.author || 'Unknown Author'}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
                {articles.length === 0 && !errors.articles && (
                  <div className="text-center py-12 bg-white/70 backdrop-blur-md rounded-xl border border-surface-200">
                    <p className="text-surface-500">No articles available</p>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Brand Section */}
          <div className="w-full md:w-1/3 p-6">
            <div className="sticky top-24">
              <h2 className="text-2xl font-bold text-surface-800 mb-6">
                Your Brand Profile
              </h2>
              {isLoadingBrand ? (
                <LoadingStates />
              ) : brandDetails ? (
                <div className="bg-white/70 backdrop-blur-md rounded-xl shadow-md p-6 space-y-6 border border-surface-200">
                  {[
                    { label: 'Brand Name', value: brandDetails.processed_brand_name },
                    { label: 'Industry', value: brandDetails.processed_industry },
                    { label: 'Target Audience', value: brandDetails.processed_target_audience },
                    { label: 'Brand Values', value: brandDetails.processed_brand_values }
                  ].map(({ label, value }) => (
                    <div key={label}>
                      <h3 className="font-semibold text-surface-800 mb-2">{label}</h3>
                      <p className="text-surface-600">{value || 'Not processed yet'}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <Link href="/onboarding/questions"
                  className="block bg-white/70 backdrop-blur-md rounded-xl shadow-md p-6 text-center hover:shadow-lg transition-all border border-surface-200"
                >
                  <div className="text-primary-600 mb-4 font-medium">
                    Complete your brand profile
                  </div>
                  <button className="px-6 py-2 bg-gradient-to-r from-primary-600 to-primary-500 text-white rounded-lg hover:from-primary-700 hover:to-primary-600 transition-all">
                    Get Started
                  </button>
                </Link>
              )}
            </div>
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}