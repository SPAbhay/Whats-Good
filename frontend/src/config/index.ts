type Environment = 'development' | 'production';

interface Config {
  API_URL: string;
  WS_URL: string;
  ENV: Environment;
}

const getConfig = (): Config => {
  const env = (process.env.NEXT_PUBLIC_ENV || 'development') as Environment;

  const configs: Record<Environment, Config> = {
    development: {
      API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
      WS_URL: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000',
      ENV: 'development'
    },
    production: {
      API_URL: process.env.NEXT_PUBLIC_API_URL || '',
      WS_URL: process.env.NEXT_PUBLIC_WS_URL || '',
      ENV: 'production'
    }
  };

  return configs[env];
};

export const config = getConfig();