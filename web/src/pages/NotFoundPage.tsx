import React from 'react';
import { Link } from 'react-router-dom';
import { FileQuestion, Home, ArrowLeft } from 'lucide-react';
import { Button } from '../components/ui/Button';

export const NotFoundPage: React.FC = () => {
  return (
    <div className="min-h-[70vh] flex items-center justify-center p-4 text-ink">
      <div className="bg-white rounded-2xl max-w-md w-full p-8 shadow-2xs border border-stone-200 text-center space-y-4">
        <div className="w-16 h-16 bg-paper text-ink-muted rounded-2xl flex items-center justify-center mx-auto border border-stone-200">
          <FileQuestion className="w-8 h-8 text-brand" />
        </div>

        <h1 className="text-2xl font-bold text-ink">
          Page not found
        </h1>

        <p className="text-sm text-ink-muted leading-relaxed">
          The page or prescription address you are looking for does not exist or has been moved.
        </p>

        <div className="flex flex-col sm:flex-row gap-3 justify-center pt-2">
          <Link to="/">
            <Button
              variant="primary"
              leftIcon={<Home className="w-4 h-4" />}
              className="w-full min-h-[48px]"
            >
              Go to home
            </Button>
          </Link>
          <Link to="/patient-portal">
            <Button
              variant="outline"
              className="w-full min-h-[48px]"
            >
              My prescriptions
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
};

export default NotFoundPage;

