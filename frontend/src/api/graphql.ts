import { apiClient } from './client';

/**
 * GraphQL API client for Nebula Search.
 * Provides typed access to the GraphQL endpoint at /graphql.
 */
export interface GraphQLSearchInput {
  query: string;
  page?: number;
  page_size?: number;
  filters?: Record<string, any>;
  search_type?: string;
  enable_reranking?: boolean;
  enable_diversity?: boolean;
}

export interface GraphQLDocument {
  id: string;
  title: string;
  content: string;
  url: string;
  source: string;
  score: number;
  published_date?: string;
  author?: string;
  tags?: string[];
  metadata?: Record<string, any>;
}

export interface GraphQLSearchResult {
  query: string;
  total: number;
  page: number;
  page_size: number;
  documents: GraphQLDocument[];
  facets?: Record<string, any>;
  suggestions?: string[];
}

export interface GraphQLSearchHistoryItem {
  id: string;
  query: string;
  results_count: number;
  timestamp: string;
  user_id?: string;
}

export interface GraphQLAISearchResult {
  answer: string;
  sources: GraphQLDocument[];
  nodes?: Array<{
    id: string;
    content: string;
    type: string;
    score: number;
    context?: Record<string, any>;
  }>;
  confidence: number;
}

class GraphQLClient {
  private async execute<T>(query: string, variables?: Record<string, any>): Promise<T> {
    const response = await apiClient.post<{ data: T; errors?: Array<{ message: string }> }>(
      '/graphql/',
      { query, variables },
    );
    if (response.errors && response.errors.length > 0) {
      throw new Error(response.errors[0].message);
    }
    return response.data;
  }

  async search(input: GraphQLSearchInput): Promise<GraphQLSearchResult> {
    const query = `
      query Search($input: SearchInput!) {
        search(input: $input) {
          query
          total
          page
          page_size
          documents {
            id
            title
            content
            url
            source
            score
          }
          suggestions
        }
      }
    `;
    return this.execute<{ search: GraphQLSearchResult }>(query, { input }).then(r => r.search);
  }

  async searchHistory(userId?: string, limit: number = 10): Promise<GraphQLSearchHistoryItem[]> {
    const query = `
      query SearchHistory($userId: String, $limit: Int) {
        search_history(user_id: $userId, limit: $limit) {
          id
          query
          results_count
          timestamp
          user_id
        }
      }
    `;
    return this.execute<{ search_history: GraphQLSearchHistoryItem[] }>(query, { userId, limit })
      .then(r => r.search_history);
  }

  async aiSearch(query: string, context?: Record<string, any>): Promise<GraphQLAISearchResult> {
    const gql = `
      query AISearch($query: String!, $context: JSON) {
        ai_search(query: $query, context: $context) {
          answer
          confidence
          sources {
            id
            title
            content
            url
            source
            score
          }
        }
      }
    `;
    return this.execute<{ ai_search: GraphQLAISearchResult }>(gql, { query, context })
      .then(r => r.ai_search);
  }

  async suggest(query: string, limit: number = 5): Promise<string[]> {
    const gql = `
      query Suggest($query: String!, $limit: Int) {
        suggest(query: $query, limit: $limit)
      }
    `;
    return this.execute<{ suggest: string[] }>(gql, { query, limit }).then(r => r.suggest);
  }

  async saveSearch(query: string, resultsCount: number, userId?: string): Promise<GraphQLSearchHistoryItem> {
    const gql = `
      mutation SaveSearch($query: String!, $resultsCount: Int!, $userId: String) {
        save_search(query: $query, results_count: $resultsCount, user_id: $userId) {
          id
          query
          results_count
          timestamp
          user_id
        }
      }
    `;
    return this.execute<{ save_search: GraphQLSearchHistoryItem }>(
      gql,
      { query, resultsCount, userId },
    ).then(r => r.save_search);
  }

  async clearSearchHistory(userId?: string): Promise<boolean> {
    const gql = `
      mutation ClearSearchHistory($userId: String) {
        clear_search_history(user_id: $userId)
      }
    `;
    return this.execute<{ clear_search_history: boolean }>(gql, { userId })
      .then(r => r.clear_search_history);
  }
}

export const graphqlClient = new GraphQLClient();
export default graphqlClient;