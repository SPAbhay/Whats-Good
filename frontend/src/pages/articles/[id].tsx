import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import ChatInterface from '@/components/chat/ChatInterface';

interface Insight {
  type: string;  // Adjust properties as needed
  value: string;
}

interface Article {
  id: number;
  content: string;
  summarized_content: string;
  insights: Insight[]; // Now insights is an array of Insight
  brand_id: number;
}


export default function ArticlePage() {
  const router = useRouter();
  const { id } = router.query;
  const [article, setArticle] = useState<Article | null>(null);
  const [isChatReady, setIsChatReady] = useState(false);

  useEffect(() => {
    if (id) {
      console.log("Fetching article with ID:", id);
      // 1. First fetch article data
      fetch(`http://localhost:8000/api/articles/${id}`)
        .then(res => res.json())
        .then(data => {
          console.log("Article data:", data);
          setArticle(data);
          // 2. Then initialize chat session
          return fetch(`http://localhost:8000/api/articles/${id}/init-chat`, {
            method: 'POST'
          });
        })
        .then(res => res.json())
        .then(data => {
          console.log("Chat session initialized:", data);
          setIsChatReady(true);
        })
        .catch(error => {
          console.error("Error:", error);
          // Handle error appropriately
        });
    }
  }, [id]);

  if (!article) {
    return <div>Loading article...</div>;
  }

  return (
    <div className="flex min-h-screen bg-gray-50">
      {/* Main content area */}
      <div className="w-2/3 p-8">
        <h1 className="text-2xl font-bold mb-4">{article.summarized_content}</h1>
        <div className="prose">{article.content}</div>
        {/* Article content and insights */}
      </div>

      {/* Chat interface */}
      {isChatReady ? (
        <ChatInterface
          articleId={id as string}
          brandId={article.brand_id.toString()}  // Pass the actual brand_id
        />
      ) : (
        <div className="w-1/3 fixed right-0 top-[20vh] h-[80vh] border-l bg-white p-4">
          Preparing chat interface...
        </div>
      )}
    </div>
  );
}