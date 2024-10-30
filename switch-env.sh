#!/bin/bash

# Check if environment argument is provided
if [ -z "$1" ]; then
    echo "Please specify environment (development/production)"
    exit 1
fi

ENV=$1

# Switch backend environment
echo "Switching backend environment..."
cd backend
cp .env.$ENV .env

# Switch frontend environment
echo "Switching frontend environment..."
cd ../frontend
cp .env.$ENV .env.local

echo "Switched to $ENV environment"