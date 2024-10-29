import { ProtectedRoute } from '../../components/auth/ProtectedRoute';
import QuestionnaireForm from '../../components/brand/QuestionnaireForm';
import { useEffect } from 'react';
import { useRouter } from 'next/router';
import { brand } from '../../services/api';

export default function QuestionnairePage() {
  const router = useRouter();

  useEffect(() => {
    const checkBrandStatus = async () => {
      try {
        const hasBrand = await brand.checkBrandExists();
        if (hasBrand) {
          router.replace('/dashboard');
        }
      } catch (error) {
        console.error('Error checking brand status:', error);
      }
    };

    checkBrandStatus();
  }, [router]);

  return (
    <ProtectedRoute>
      <QuestionnaireForm />
    </ProtectedRoute>
  );
}