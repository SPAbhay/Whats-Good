import { useState } from 'react';
import { useRouter } from 'next/router';
import { brand } from '../../services/api';

const QUESTIONS = [
  {
    id: 1,
    question: "What's your brand name?",
    emoji: "✨",
    maxLength: 50,
    placeholder: "Enter your brand name..."
  },
  {
    id: 2,
    question: "What industry is [brandName] in and what's your specific focus?",
    emoji: "🏢",
    maxLength: 100,
    placeholder: "e.g., Technology - Mobile App Development, Healthcare - Dental Services..."
  },
  {
    id: 3,
    question: "Describe [brandName]'s target audience and their key demographics",
    emoji: "👥",
    maxLength: 200,
    placeholder: "e.g., Tech-savvy professionals, 25-40 years old, urban areas..."
  },
  {
    id: 4,
    question: "What makes [brandName] unique and what are your core values?",
    emoji: "💫",
    maxLength: 200,
    placeholder: "Your unique selling points and guiding principles..."
  },
  {
    id: 5,
    question: "Which social media platforms do you currently use?",
    emoji: "📱",
    maxLength: 100,
    placeholder: "e.g., Instagram, LinkedIn, Twitter... (or 'None' if first time)"
  },
  {
    id: 6,
    question: "Share a successful social media post or campaign",
    emoji: "🏆",
    maxLength: 200,
    placeholder: "Briefly describe your best performing content, or type 'First time' if new to social media"
  }
];

export default function QuestionnaireForm() {
  const router = useRouter();
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [error, setError] = useState('');

  const progress = ((currentQuestion + 1) / QUESTIONS.length) * 100;

  const replaceBrandName = (text: string) => {
    return text.replace('[brandName]', answers[1] || 'your brand');
  };

  const handleAnswer = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setAnswers(prev => ({
      ...prev,
      [currentQuestion]: e.target.value
    }));
    setError('');
  };

  const goToNextQuestion = async () => {
    if (!answers[currentQuestion]?.trim()) {
      setError('Please provide an answer before continuing');
      return;
    }

    if (currentQuestion === QUESTIONS.length - 1) {
      try {
        // Log the data being sent
        const questionnaireData = {
          raw_brand_name: answers[1],
          raw_industry_focus: answers[2],
          raw_target_audience: answers[3],
          raw_unique_value: answers[4],
          raw_social_platforms: answers[5],
          raw_successful_content: answers[6]
        };
        console.log('All answers:', answers);
        console.log('Submitting data:', questionnaireData);

        // Submit the data
        const response = await brand.submitQuestionnaire(questionnaireData);
        console.log('Response:', response);

        router.push('/');
      } catch (err: any) {
        console.error('Submission error:', err);
        console.error('Error response:', err.response?.data);

        // More descriptive error message
        setError(
          err.response?.data?.detail ||
          err.message ||
          'Failed to submit answers. Please try again.'
        );
      }
    } else {
      setCurrentQuestion(prev => prev + 1);
    }
  };

  const goToPreviousQuestion = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion(prev => prev - 1);
    }
  };



  const currentQ = QUESTIONS[currentQuestion];

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-4">
      {/* Progress Bar */}
      <div className="fixed top-0 left-0 w-full h-2 bg-gray-200">
        <div
          className="h-full bg-blue-500 transition-all duration-300 ease-in-out"
          style={{ width: `${progress}%` }}
        />
      </div>

      <div className="w-full max-w-xl">
        {/* Progress Text */}
        <div className="text-center mb-8">
          <p className="text-sm text-gray-500">
            Question {currentQuestion + 1} of {QUESTIONS.length}
          </p>
        </div>

        {/* Question Card */}
        <div className="bg-white rounded-lg shadow-lg p-8 mb-8 transform transition-all duration-300">
          <div className="text-center mb-6">
            <span className="text-4xl mb-4 block">{currentQ.emoji}</span>
            <h2 className="text-xl font-semibold text-gray-800">
              {replaceBrandName(currentQ.question)}
            </h2>
          </div>

          <textarea
            value={answers[currentQuestion] || ''}
            onChange={handleAnswer}
            maxLength={currentQ.maxLength}
            placeholder={currentQ.placeholder}
            className="w-full p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[120px] resize-none"
          />

          {error && (
            <p className="text-red-500 text-sm mt-2">{error}</p>
          )}

          <div className="text-right text-sm text-gray-500 mt-2">
            {answers[currentQuestion]?.length || 0}/{currentQ.maxLength}
          </div>
        </div>

        {/* Navigation Buttons */}
        <div className="flex justify-between space-x-4">
          <button
            onClick={goToPreviousQuestion}
            disabled={currentQuestion === 0}
            className={`px-6 py-2 rounded-md ${
              currentQuestion === 0
                ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                : 'bg-white text-blue-500 hover:bg-gray-50'
            } transition-colors`}
          >
            Previous
          </button>

          <button
            onClick={goToNextQuestion}
            className="px-6 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors"
          >
            {currentQuestion === QUESTIONS.length - 1 ? 'Submit' : 'Next'}
          </button>
        </div>
      </div>
    </div>
  );
}
