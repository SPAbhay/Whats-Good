export interface Brand {
  id: number;
  raw_brand_name: string;
  raw_industry_focus: string;
  raw_target_audience: string;
  raw_unique_value: string;
  raw_social_platforms?: string;
  raw_successful_content?: string;
  processed_brand_name?: string;
  processed_industry?: string;
  processed_industry_focus?: string;
  processed_target_audience?: string;
  processed_brand_values?: string;
  processed_social_presence?: string;
  created_at: string;
  updated_at?: string;
}