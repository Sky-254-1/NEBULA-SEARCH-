import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class SearchState {
  final List<dynamic> results;
  final bool isLoading;
  final String? error;

  const SearchState({this.results = const [], this.isLoading = false, this.error});

  SearchState copyWith({List<dynamic>? results, bool? isLoading, String? error}) {
    return SearchState(
      results: results ?? this.results,
      isLoading: isLoading ?? this.isLoading,
      error: error,
    );
  }
}

class SearchNotifier extends StateNotifier<SearchState> {
  SearchNotifier() : super(const SearchState());

  Future<void> search(String query) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final response = await http.get(
        Uri.parse('http://localhost:8000/api/v1/search/web?q=$query&backend=wikipedia'),
      );
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        final results = (data['results'] as List?) ?? [];
        state = state.copyWith(results: results, isLoading: false);
      } else {
        state = state.copyWith(error: 'Search failed', isLoading: false);
      }
    } catch (e) {
      state = state.copyWith(error: e.toString(), isLoading: false);
    }
  }
}

final searchProvider = StateNotifierProvider<SearchNotifier, SearchState>((ref) {
  return SearchNotifier();
});